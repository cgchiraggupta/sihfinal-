"""
Safety & Hazard Detection Module for Advanced EHS Simba Drill System.

This module provides:
- Abnormal vibration detection (potential collapse zones)
- Overheat protection (hydraulic fluid, motor)
- Ground stability warnings from drilling resistance patterns
- Operator fatigue detection (optional)
- Emergency shutdown trigger logic

Author: EHS Simba Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

import numpy as np

from config import SafetyConfig, get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class HazardType(str, Enum):
    """Types of safety hazards."""
    EXCESSIVE_VIBRATION = "excessive_vibration"
    OVERHEAT_HYDRAULIC = "overheat_hydraulic"
    OVERHEAT_MOTOR = "overheat_motor"
    OVERPRESSURE = "overpressure"
    UNDERPRESSURE = "underpressure"
    GROUND_INSTABILITY = "ground_instability"
    VOID_DETECTED = "void_detected"
    EQUIPMENT_FAULT = "equipment_fault"
    OPERATOR_FATIGUE = "operator_fatigue"
    COLLISION_RISK = "collision_risk"


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"           # Informational only
    WARNING = "warning"     # Requires attention
    CRITICAL = "critical"   # Immediate action needed
    EMERGENCY = "emergency" # Automatic shutdown triggered


class SafetyAction(str, Enum):
    """Safety actions that can be taken."""
    NONE = "none"
    ALERT_OPERATOR = "alert_operator"
    REDUCE_SPEED = "reduce_speed"
    PAUSE_DRILLING = "pause_drilling"
    EMERGENCY_STOP = "emergency_stop"
    EVACUATE = "evacuate"


@dataclass
class SafetyAlert:
    """
    Safety alert record.
    
    Attributes:
        alert_id: Unique alert identifier
        hazard_type: Type of hazard detected
        level: Alert severity level
        message: Human-readable message
        value: Triggering value
        threshold: Threshold that was exceeded
        recommended_action: Recommended safety action
        auto_action_taken: Action taken automatically
        timestamp: Alert timestamp
        acknowledged: Whether alert has been acknowledged
    """
    alert_id: str
    hazard_type: HazardType
    level: AlertLevel
    message: str
    value: float
    threshold: float
    recommended_action: SafetyAction
    auto_action_taken: Optional[SafetyAction] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "hazard_type": self.hazard_type.value,
            "level": self.level.value,
            "message": self.message,
            "value": self.value,
            "threshold": self.threshold,
            "recommended_action": self.recommended_action.value,
            "auto_action_taken": self.auto_action_taken.value if self.auto_action_taken else None,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }


@dataclass
class SafetyStatus:
    """
    Overall safety system status.
    
    Attributes:
        is_safe: Whether system is in safe state
        active_alerts: Number of active alerts
        highest_alert_level: Highest current alert level
        emergency_stop_active: Whether e-stop is engaged
        last_check_time: Last safety check timestamp
        system_health: Overall safety system health (0-100)
    """
    is_safe: bool
    active_alerts: int
    highest_alert_level: Optional[AlertLevel]
    emergency_stop_active: bool
    last_check_time: datetime
    system_health: float
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_safe": self.is_safe,
            "active_alerts": self.active_alerts,
            "highest_alert_level": self.highest_alert_level.value if self.highest_alert_level else None,
            "emergency_stop_active": self.emergency_stop_active,
            "last_check_time": self.last_check_time.isoformat(),
            "system_health": self.system_health,
        }


@dataclass
class OperatorSession:
    """
    Operator work session tracking.
    
    Attributes:
        operator_id: Operator identifier
        session_start: Session start time
        total_operating_time_min: Total operating time
        last_break_time: Last break timestamp
        fatigue_score: Estimated fatigue level (0-100)
        alerts_acknowledged: Number of alerts acknowledged
    """
    operator_id: str
    session_start: datetime
    total_operating_time_min: float = 0.0
    last_break_time: Optional[datetime] = None
    fatigue_score: float = 0.0
    alerts_acknowledged: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operator_id": self.operator_id,
            "session_start": self.session_start.isoformat(),
            "total_operating_time_min": self.total_operating_time_min,
            "last_break_time": self.last_break_time.isoformat() if self.last_break_time else None,
            "fatigue_score": self.fatigue_score,
            "alerts_acknowledged": self.alerts_acknowledged,
        }


# =============================================================================
# Vibration Monitor
# =============================================================================

class VibrationMonitor:
    """
    Monitors vibration levels for safety hazards.
    
    Detects:
    - Excessive vibration (equipment damage risk)
    - Abnormal patterns (potential collapse/instability)
    - Sudden spikes (impact events)
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """Initialize vibration monitor."""
        self.config = config or get_settings().safety
        
        # Thresholds
        self._warning_g = get_settings().sensors.vibration.warning_threshold_g
        self._critical_g = get_settings().sensors.vibration.critical_threshold_g
        self._emergency_g = self.config.emergency_vibration_g
        
        # History for pattern analysis
        self._history: list[tuple[datetime, float]] = []
        self._max_history = 1000
        
        # Baseline (learned from normal operation)
        self._baseline_mean = 1.5
        self._baseline_std = 0.5
        
        logger.info("VibrationMonitor initialized")
    
    def check(self, vibration_g: float) -> Optional[SafetyAlert]:
        """
        Check vibration level and generate alert if needed.
        
        Args:
            vibration_g: Current vibration in g-force
            
        Returns:
            SafetyAlert if threshold exceeded, None otherwise.
        """
        now = datetime.utcnow()
        self._history.append((now, vibration_g))
        
        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        # Check thresholds (highest first)
        if vibration_g >= self._emergency_g:
            return SafetyAlert(
                alert_id=f"VIB-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.EXCESSIVE_VIBRATION,
                level=AlertLevel.EMERGENCY,
                message=f"EMERGENCY: Extreme vibration {vibration_g:.1f}g - Auto shutdown triggered",
                value=vibration_g,
                threshold=self._emergency_g,
                recommended_action=SafetyAction.EMERGENCY_STOP,
                auto_action_taken=SafetyAction.EMERGENCY_STOP,
            )
        
        if vibration_g >= self._critical_g:
            return SafetyAlert(
                alert_id=f"VIB-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.EXCESSIVE_VIBRATION,
                level=AlertLevel.CRITICAL,
                message=f"CRITICAL: High vibration {vibration_g:.1f}g - Stop drilling immediately",
                value=vibration_g,
                threshold=self._critical_g,
                recommended_action=SafetyAction.PAUSE_DRILLING,
            )
        
        if vibration_g >= self._warning_g:
            return SafetyAlert(
                alert_id=f"VIB-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.EXCESSIVE_VIBRATION,
                level=AlertLevel.WARNING,
                message=f"WARNING: Elevated vibration {vibration_g:.1f}g - Monitor closely",
                value=vibration_g,
                threshold=self._warning_g,
                recommended_action=SafetyAction.REDUCE_SPEED,
            )
        
        # Check for abnormal patterns (sudden changes)
        pattern_alert = self._check_patterns(vibration_g)
        if pattern_alert:
            return pattern_alert
        
        return None
    
    def _check_patterns(self, current: float) -> Optional[SafetyAlert]:
        """Check for abnormal vibration patterns."""
        if len(self._history) < 20:
            return None
        
        recent = [v for _, v in self._history[-20:]]
        
        # Check for sudden spike
        baseline = np.mean([v for _, v in self._history[-100:-20]]) if len(self._history) > 100 else self._baseline_mean
        
        if current > baseline * 3:  # 3x baseline
            return SafetyAlert(
                alert_id=f"VIB-SPIKE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.GROUND_INSTABILITY,
                level=AlertLevel.WARNING,
                message=f"Sudden vibration spike detected: {current:.1f}g (baseline: {baseline:.1f}g)",
                value=current,
                threshold=baseline * 3,
                recommended_action=SafetyAction.ALERT_OPERATOR,
            )
        
        # Check for increasing trend (potential instability)
        if len(recent) >= 10:
            first_half = np.mean(recent[:10])
            second_half = np.mean(recent[10:])
            
            if second_half > first_half * 1.5 and second_half > self._warning_g * 0.8:
                return SafetyAlert(
                    alert_id=f"VIB-TREND-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    hazard_type=HazardType.GROUND_INSTABILITY,
                    level=AlertLevel.WARNING,
                    message="Increasing vibration trend detected - possible ground instability",
                    value=second_half,
                    threshold=first_half * 1.5,
                    recommended_action=SafetyAction.REDUCE_SPEED,
                )
        
        return None


# =============================================================================
# Temperature Monitor
# =============================================================================

class TemperatureMonitor:
    """
    Monitors temperature for overheat protection.
    
    Tracks:
    - Hydraulic fluid temperature
    - Motor temperature
    - Ambient temperature
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """Initialize temperature monitor."""
        self.config = config or get_settings().safety
        sensor_config = get_settings().sensors.temperature
        
        # Thresholds
        self._hydraulic_warning = sensor_config.hydraulic_warning_c
        self._hydraulic_critical = sensor_config.hydraulic_critical_c
        self._motor_warning = sensor_config.motor_warning_c
        self._motor_critical = sensor_config.motor_critical_c
        self._emergency_temp = self.config.emergency_temperature_c
        
        # Trend tracking
        self._hydraulic_history: list[tuple[datetime, float]] = []
        self._motor_history: list[tuple[datetime, float]] = []
        
        logger.info("TemperatureMonitor initialized")
    
    def check_hydraulic(self, temp_c: float) -> Optional[SafetyAlert]:
        """Check hydraulic fluid temperature."""
        now = datetime.utcnow()
        self._hydraulic_history.append((now, temp_c))
        
        # Trim history
        if len(self._hydraulic_history) > 500:
            self._hydraulic_history = self._hydraulic_history[-500:]
        
        if temp_c >= self._emergency_temp:
            return SafetyAlert(
                alert_id=f"TEMP-HYD-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OVERHEAT_HYDRAULIC,
                level=AlertLevel.EMERGENCY,
                message=f"EMERGENCY: Hydraulic overheat {temp_c:.1f}°C - Auto shutdown",
                value=temp_c,
                threshold=self._emergency_temp,
                recommended_action=SafetyAction.EMERGENCY_STOP,
                auto_action_taken=SafetyAction.EMERGENCY_STOP,
            )
        
        if temp_c >= self._hydraulic_critical:
            return SafetyAlert(
                alert_id=f"TEMP-HYD-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OVERHEAT_HYDRAULIC,
                level=AlertLevel.CRITICAL,
                message=f"CRITICAL: Hydraulic temp {temp_c:.1f}°C - Stop and cool down",
                value=temp_c,
                threshold=self._hydraulic_critical,
                recommended_action=SafetyAction.PAUSE_DRILLING,
            )
        
        if temp_c >= self._hydraulic_warning:
            return SafetyAlert(
                alert_id=f"TEMP-HYD-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OVERHEAT_HYDRAULIC,
                level=AlertLevel.WARNING,
                message=f"WARNING: Hydraulic temp elevated {temp_c:.1f}°C",
                value=temp_c,
                threshold=self._hydraulic_warning,
                recommended_action=SafetyAction.REDUCE_SPEED,
            )
        
        return None
    
    def check_motor(self, temp_c: float) -> Optional[SafetyAlert]:
        """Check motor temperature."""
        now = datetime.utcnow()
        self._motor_history.append((now, temp_c))
        
        if len(self._motor_history) > 500:
            self._motor_history = self._motor_history[-500:]
        
        if temp_c >= self._emergency_temp:
            return SafetyAlert(
                alert_id=f"TEMP-MOT-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OVERHEAT_MOTOR,
                level=AlertLevel.EMERGENCY,
                message=f"EMERGENCY: Motor overheat {temp_c:.1f}°C - Auto shutdown",
                value=temp_c,
                threshold=self._emergency_temp,
                recommended_action=SafetyAction.EMERGENCY_STOP,
                auto_action_taken=SafetyAction.EMERGENCY_STOP,
            )
        
        if temp_c >= self._motor_critical:
            return SafetyAlert(
                alert_id=f"TEMP-MOT-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OVERHEAT_MOTOR,
                level=AlertLevel.CRITICAL,
                message=f"CRITICAL: Motor temp {temp_c:.1f}°C - Stop immediately",
                value=temp_c,
                threshold=self._motor_critical,
                recommended_action=SafetyAction.PAUSE_DRILLING,
            )
        
        if temp_c >= self._motor_warning:
            return SafetyAlert(
                alert_id=f"TEMP-MOT-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OVERHEAT_MOTOR,
                level=AlertLevel.WARNING,
                message=f"WARNING: Motor temp elevated {temp_c:.1f}°C",
                value=temp_c,
                threshold=self._motor_warning,
                recommended_action=SafetyAction.REDUCE_SPEED,
            )
        
        return None
    
    def get_thermal_status(self) -> dict[str, Any]:
        """Get current thermal status."""
        return {
            "hydraulic_temp": self._hydraulic_history[-1][1] if self._hydraulic_history else None,
            "motor_temp": self._motor_history[-1][1] if self._motor_history else None,
            "hydraulic_trend": self._calculate_trend(self._hydraulic_history),
            "motor_trend": self._calculate_trend(self._motor_history),
        }
    
    def _calculate_trend(
        self,
        history: list[tuple[datetime, float]],
    ) -> str:
        """Calculate temperature trend."""
        if len(history) < 10:
            return "stable"
        
        recent = [t for _, t in history[-20:]]
        first_half = np.mean(recent[:len(recent)//2])
        second_half = np.mean(recent[len(recent)//2:])
        
        change = (second_half - first_half) / max(first_half, 1) * 100
        
        if change > 5:
            return "rising"
        elif change < -5:
            return "falling"
        else:
            return "stable"


# =============================================================================
# Pressure Monitor
# =============================================================================

class PressureMonitor:
    """
    Monitors hydraulic pressure for safety.
    
    Detects:
    - Overpressure (burst risk)
    - Underpressure (pump failure, leak)
    - Pressure fluctuations (system issues)
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """Initialize pressure monitor."""
        self.config = config or get_settings().safety
        sensor_config = get_settings().sensors.pressure
        
        # Thresholds
        self._min_bar = sensor_config.hydraulic_min_bar
        self._max_bar = sensor_config.hydraulic_max_bar
        self._warning_low = sensor_config.hydraulic_warning_low_bar
        self._warning_high = sensor_config.hydraulic_warning_high_bar
        self._critical_high = sensor_config.hydraulic_critical_high_bar
        self._emergency_high = self.config.emergency_pressure_bar
        
        # History
        self._history: list[tuple[datetime, float]] = []
        
        logger.info("PressureMonitor initialized")
    
    def check(self, pressure_bar: float) -> Optional[SafetyAlert]:
        """Check hydraulic pressure."""
        now = datetime.utcnow()
        self._history.append((now, pressure_bar))
        
        if len(self._history) > 500:
            self._history = self._history[-500:]
        
        # Check high pressure
        if pressure_bar >= self._emergency_high:
            return SafetyAlert(
                alert_id=f"PRES-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OVERPRESSURE,
                level=AlertLevel.EMERGENCY,
                message=f"EMERGENCY: Hydraulic overpressure {pressure_bar:.0f} bar - Auto shutdown",
                value=pressure_bar,
                threshold=self._emergency_high,
                recommended_action=SafetyAction.EMERGENCY_STOP,
                auto_action_taken=SafetyAction.EMERGENCY_STOP,
            )
        
        if pressure_bar >= self._critical_high:
            return SafetyAlert(
                alert_id=f"PRES-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OVERPRESSURE,
                level=AlertLevel.CRITICAL,
                message=f"CRITICAL: High pressure {pressure_bar:.0f} bar",
                value=pressure_bar,
                threshold=self._critical_high,
                recommended_action=SafetyAction.PAUSE_DRILLING,
            )
        
        if pressure_bar >= self._warning_high:
            return SafetyAlert(
                alert_id=f"PRES-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OVERPRESSURE,
                level=AlertLevel.WARNING,
                message=f"WARNING: Elevated pressure {pressure_bar:.0f} bar",
                value=pressure_bar,
                threshold=self._warning_high,
                recommended_action=SafetyAction.REDUCE_SPEED,
            )
        
        # Check low pressure
        if pressure_bar < self._min_bar:
            return SafetyAlert(
                alert_id=f"PRES-LOW-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.UNDERPRESSURE,
                level=AlertLevel.CRITICAL,
                message=f"CRITICAL: Low pressure {pressure_bar:.0f} bar - Check for leaks",
                value=pressure_bar,
                threshold=self._min_bar,
                recommended_action=SafetyAction.PAUSE_DRILLING,
            )
        
        if pressure_bar < self._warning_low:
            return SafetyAlert(
                alert_id=f"PRES-LOW-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.UNDERPRESSURE,
                level=AlertLevel.WARNING,
                message=f"WARNING: Low pressure {pressure_bar:.0f} bar",
                value=pressure_bar,
                threshold=self._warning_low,
                recommended_action=SafetyAction.ALERT_OPERATOR,
            )
        
        return None


# =============================================================================
# Ground Stability Analyzer
# =============================================================================

class GroundStabilityAnalyzer:
    """
    Analyzes drilling resistance patterns for ground stability.
    
    Detects:
    - Sudden resistance drops (voids, cavities)
    - Resistance spikes with vibration (fractured zones)
    - Progressive weakening (collapse risk)
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """Initialize ground stability analyzer."""
        self.config = config or get_settings().safety
        
        self._spike_threshold = self.config.resistance_spike_threshold_percent / 100
        self._void_detection_enabled = self.config.void_detection_enabled
        
        # History
        self._resistance_history: list[tuple[datetime, float]] = []
        self._depth_history: list[float] = []
        
        logger.info("GroundStabilityAnalyzer initialized")
    
    def check(
        self,
        resistance: float,
        depth: float,
        vibration: float,
    ) -> Optional[SafetyAlert]:
        """
        Check for ground stability issues.
        
        Args:
            resistance: Current drilling resistance
            depth: Current depth
            vibration: Current vibration level
            
        Returns:
            SafetyAlert if issue detected.
        """
        now = datetime.utcnow()
        self._resistance_history.append((now, resistance))
        self._depth_history.append(depth)
        
        if len(self._resistance_history) > 500:
            self._resistance_history = self._resistance_history[-500:]
            self._depth_history = self._depth_history[-500:]
        
        if len(self._resistance_history) < 20:
            return None
        
        # Calculate baseline
        recent = [r for _, r in self._resistance_history[-50:-10]]
        if not recent:
            return None
        
        baseline = np.mean(recent)
        current = resistance
        
        # Check for void (sudden drop)
        if self._void_detection_enabled and baseline > 0:
            drop_percent = (baseline - current) / baseline
            
            if drop_percent > 0.7:  # 70% drop
                return SafetyAlert(
                    alert_id=f"VOID-{now.strftime('%Y%m%d%H%M%S')}",
                    hazard_type=HazardType.VOID_DETECTED,
                    level=AlertLevel.CRITICAL,
                    message=f"CRITICAL: Possible void at {depth:.1f}m - {drop_percent:.0%} resistance drop",
                    value=current,
                    threshold=baseline * 0.3,
                    recommended_action=SafetyAction.PAUSE_DRILLING,
                )
            elif drop_percent > 0.5:  # 50% drop
                return SafetyAlert(
                    alert_id=f"VOID-{now.strftime('%Y%m%d%H%M%S')}",
                    hazard_type=HazardType.VOID_DETECTED,
                    level=AlertLevel.WARNING,
                    message=f"WARNING: Possible cavity at {depth:.1f}m",
                    value=current,
                    threshold=baseline * 0.5,
                    recommended_action=SafetyAction.REDUCE_SPEED,
                )
        
        # Check for resistance spike (hard inclusion or fractured zone)
        if baseline > 0:
            spike_percent = (current - baseline) / baseline
            
            if spike_percent > self._spike_threshold and vibration > 3.0:
                return SafetyAlert(
                    alert_id=f"FRACTURE-{now.strftime('%Y%m%d%H%M%S')}",
                    hazard_type=HazardType.GROUND_INSTABILITY,
                    level=AlertLevel.WARNING,
                    message=f"Fractured zone detected at {depth:.1f}m - high resistance with vibration",
                    value=current,
                    threshold=baseline * (1 + self._spike_threshold),
                    recommended_action=SafetyAction.REDUCE_SPEED,
                )
        
        return None


# =============================================================================
# Operator Fatigue Monitor
# =============================================================================

class OperatorFatigueMonitor:
    """
    Monitors operator work hours for fatigue prevention.
    
    Tracks:
    - Continuous operation time
    - Break intervals
    - Response times (if available)
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """Initialize operator fatigue monitor."""
        self.config = config or get_settings().safety
        
        self._max_continuous_hours = self.config.max_continuous_operation_hours
        self._mandatory_break_minutes = self.config.mandatory_break_minutes
        
        # Active sessions
        self._sessions: dict[str, OperatorSession] = {}
        
        logger.info("OperatorFatigueMonitor initialized")
    
    def start_session(self, operator_id: str) -> OperatorSession:
        """Start a new operator session."""
        session = OperatorSession(
            operator_id=operator_id,
            session_start=datetime.utcnow(),
        )
        self._sessions[operator_id] = session
        return session
    
    def record_break(self, operator_id: str) -> None:
        """Record that operator took a break."""
        if operator_id in self._sessions:
            self._sessions[operator_id].last_break_time = datetime.utcnow()
            # Reset fatigue score somewhat
            self._sessions[operator_id].fatigue_score = max(
                0, self._sessions[operator_id].fatigue_score - 20
            )
    
    def check_fatigue(self, operator_id: str) -> Optional[SafetyAlert]:
        """
        Check operator fatigue level.
        
        Args:
            operator_id: Operator identifier
            
        Returns:
            SafetyAlert if fatigue threshold exceeded.
        """
        if operator_id not in self._sessions:
            return None
        
        session = self._sessions[operator_id]
        now = datetime.utcnow()
        
        # Calculate continuous operating time
        session_duration_hours = (now - session.session_start).total_seconds() / 3600
        
        # Time since last break
        if session.last_break_time:
            since_break_hours = (now - session.last_break_time).total_seconds() / 3600
        else:
            since_break_hours = session_duration_hours
        
        # Update fatigue score (simplified model)
        # Fatigue increases with time, decreases with breaks
        base_fatigue = min(100, since_break_hours / self._max_continuous_hours * 100)
        session.fatigue_score = base_fatigue
        session.total_operating_time_min = session_duration_hours * 60
        
        # Check thresholds
        if since_break_hours >= self._max_continuous_hours:
            return SafetyAlert(
                alert_id=f"FATIGUE-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OPERATOR_FATIGUE,
                level=AlertLevel.CRITICAL,
                message=f"CRITICAL: Operator {operator_id} exceeded max continuous operation ({since_break_hours:.1f}h)",
                value=since_break_hours,
                threshold=self._max_continuous_hours,
                recommended_action=SafetyAction.PAUSE_DRILLING,
            )
        
        if since_break_hours >= self._max_continuous_hours * 0.8:
            return SafetyAlert(
                alert_id=f"FATIGUE-{now.strftime('%Y%m%d%H%M%S')}",
                hazard_type=HazardType.OPERATOR_FATIGUE,
                level=AlertLevel.WARNING,
                message=f"WARNING: Operator {operator_id} approaching fatigue limit - break recommended",
                value=since_break_hours,
                threshold=self._max_continuous_hours * 0.8,
                recommended_action=SafetyAction.ALERT_OPERATOR,
            )
        
        return None
    
    def end_session(self, operator_id: str) -> Optional[OperatorSession]:
        """End an operator session."""
        return self._sessions.pop(operator_id, None)
    
    def get_session(self, operator_id: str) -> Optional[OperatorSession]:
        """Get operator session info."""
        return self._sessions.get(operator_id)


# =============================================================================
# Emergency Controller
# =============================================================================

class EmergencyController:
    """
    Handles emergency shutdown logic and recovery.
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """Initialize emergency controller."""
        self.config = config or get_settings().safety
        
        self._emergency_active = False
        self._emergency_reason: Optional[str] = None
        self._emergency_time: Optional[datetime] = None
        self._shutdown_callbacks: list[Callable[[], None]] = []
        
        logger.info("EmergencyController initialized")
    
    @property
    def is_emergency_active(self) -> bool:
        """Check if emergency stop is active."""
        return self._emergency_active
    
    def register_shutdown_callback(self, callback: Callable[[], None]) -> None:
        """Register callback to be called on emergency shutdown."""
        self._shutdown_callbacks.append(callback)
    
    def trigger_emergency_stop(self, reason: str) -> None:
        """
        Trigger emergency stop.
        
        Args:
            reason: Reason for emergency stop
        """
        if self._emergency_active:
            return  # Already in emergency state
        
        self._emergency_active = True
        self._emergency_reason = reason
        self._emergency_time = datetime.utcnow()
        
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")
        
        # Execute shutdown callbacks
        for callback in self._shutdown_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Shutdown callback failed: {e}")
    
    def reset_emergency(self, authorized_by: str) -> bool:
        """
        Reset emergency stop (requires authorization).
        
        Args:
            authorized_by: Person authorizing reset
            
        Returns:
            True if reset successful.
        """
        if not self._emergency_active:
            return True
        
        logger.warning(f"Emergency stop reset by: {authorized_by}")
        
        self._emergency_active = False
        self._emergency_reason = None
        self._emergency_time = None
        
        return True
    
    def get_emergency_status(self) -> dict[str, Any]:
        """Get current emergency status."""
        return {
            "active": self._emergency_active,
            "reason": self._emergency_reason,
            "triggered_at": self._emergency_time.isoformat() if self._emergency_time else None,
            "duration_seconds": (
                (datetime.utcnow() - self._emergency_time).total_seconds()
                if self._emergency_time else None
            ),
        }


# =============================================================================
# Main Safety Monitor
# =============================================================================

class SafetyMonitor:
    """
    Main safety monitoring system for EHS Simba.
    
    Integrates all safety subsystems and provides unified
    monitoring interface.
    
    Example:
        >>> monitor = SafetyMonitor()
        >>> 
        >>> # Check sensor readings
        >>> alerts = monitor.check_all(
        ...     vibration_g=2.5,
        ...     hydraulic_temp_c=65,
        ...     motor_temp_c=80,
        ...     pressure_bar=250,
        ...     resistance=150,
        ...     depth_m=25
        ... )
        >>> 
        >>> # Get safety status
        >>> status = monitor.get_status()
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """Initialize safety monitor."""
        self.config = config or get_settings().safety
        
        # Initialize subsystems
        self.vibration_monitor = VibrationMonitor(self.config)
        self.temperature_monitor = TemperatureMonitor(self.config)
        self.pressure_monitor = PressureMonitor(self.config)
        self.ground_analyzer = GroundStabilityAnalyzer(self.config)
        self.fatigue_monitor = OperatorFatigueMonitor(self.config)
        self.emergency_controller = EmergencyController(self.config)
        
        # Alert tracking
        self._active_alerts: dict[str, SafetyAlert] = {}
        self._alert_history: list[SafetyAlert] = []
        self._max_history = 1000
        
        # Alert callbacks
        self._alert_callbacks: list[Callable[[SafetyAlert], None]] = []
        
        # State
        self._last_check_time = datetime.utcnow()
        self._check_count = 0
        
        logger.info("SafetyMonitor initialized")
    
    def register_alert_callback(
        self,
        callback: Callable[[SafetyAlert], None],
    ) -> None:
        """Register callback for new alerts."""
        self._alert_callbacks.append(callback)
    
    def check_all(
        self,
        vibration_g: float,
        hydraulic_temp_c: float,
        motor_temp_c: float,
        pressure_bar: float,
        resistance: float,
        depth_m: float,
        operator_id: Optional[str] = None,
    ) -> list[SafetyAlert]:
        """
        Run all safety checks on current sensor readings.
        
        Args:
            vibration_g: Vibration level in g
            hydraulic_temp_c: Hydraulic fluid temperature
            motor_temp_c: Motor temperature
            pressure_bar: Hydraulic pressure
            resistance: Drilling resistance
            depth_m: Current depth
            operator_id: Optional operator ID for fatigue check
            
        Returns:
            List of new alerts generated.
        """
        new_alerts = []
        self._last_check_time = datetime.utcnow()
        self._check_count += 1
        
        # Check each subsystem
        alerts_to_check = [
            self.vibration_monitor.check(vibration_g),
            self.temperature_monitor.check_hydraulic(hydraulic_temp_c),
            self.temperature_monitor.check_motor(motor_temp_c),
            self.pressure_monitor.check(pressure_bar),
            self.ground_analyzer.check(resistance, depth_m, vibration_g),
        ]
        
        # Check operator fatigue if ID provided
        if operator_id:
            alerts_to_check.append(self.fatigue_monitor.check_fatigue(operator_id))
        
        # Process alerts
        for alert in alerts_to_check:
            if alert:
                new_alerts.append(alert)
                self._process_alert(alert)
        
        return new_alerts
    
    def _process_alert(self, alert: SafetyAlert) -> None:
        """Process a new alert."""
        # Add to active alerts
        self._active_alerts[alert.alert_id] = alert
        
        # Add to history
        self._alert_history.append(alert)
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history:]
        
        # Handle emergency alerts
        if alert.level == AlertLevel.EMERGENCY and self.config.auto_shutdown_enabled:
            self.emergency_controller.trigger_emergency_stop(alert.message)
        
        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        # Log alert
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.CRITICAL: logger.critical,
            AlertLevel.EMERGENCY: logger.critical,
        }.get(alert.level, logger.warning)
        
        log_method(f"SAFETY ALERT: {alert.message}")
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
    ) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID to acknowledge
            acknowledged_by: Person acknowledging
            
        Returns:
            True if acknowledged successfully.
        """
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            
            # Remove from active if not emergency level
            if alert.level != AlertLevel.EMERGENCY:
                del self._active_alerts[alert_id]
            
            return True
        return False
    
    def get_status(self) -> SafetyStatus:
        """Get overall safety system status."""
        active_count = len(self._active_alerts)
        
        # Find highest alert level
        highest_level = None
        for alert in self._active_alerts.values():
            if highest_level is None or self._level_priority(alert.level) > self._level_priority(highest_level):
                highest_level = alert.level
        
        # Calculate system health
        # Deduct points for active alerts
        health = 100.0
        for alert in self._active_alerts.values():
            if alert.level == AlertLevel.EMERGENCY:
                health -= 50
            elif alert.level == AlertLevel.CRITICAL:
                health -= 25
            elif alert.level == AlertLevel.WARNING:
                health -= 10
            else:
                health -= 5
        
        health = max(0, health)
        
        # System is safe if no critical/emergency alerts
        is_safe = highest_level not in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]
        
        return SafetyStatus(
            is_safe=is_safe,
            active_alerts=active_count,
            highest_alert_level=highest_level,
            emergency_stop_active=self.emergency_controller.is_emergency_active,
            last_check_time=self._last_check_time,
            system_health=health,
        )
    
    def _level_priority(self, level: AlertLevel) -> int:
        """Get numeric priority for alert level."""
        priorities = {
            AlertLevel.INFO: 1,
            AlertLevel.WARNING: 2,
            AlertLevel.CRITICAL: 3,
            AlertLevel.EMERGENCY: 4,
        }
        return priorities.get(level, 0)
    
    def get_active_alerts(self) -> list[SafetyAlert]:
        """Get all active alerts."""
        return list(self._active_alerts.values())
    
    def get_alert_history(
        self,
        hours: float = 24.0,
        level: Optional[AlertLevel] = None,
    ) -> list[SafetyAlert]:
        """
        Get alert history.
        
        Args:
            hours: Hours of history to retrieve
            level: Optional filter by alert level
            
        Returns:
            List of historical alerts.
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        alerts = [
            a for a in self._alert_history
            if a.timestamp >= cutoff
        ]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts
    
    def reset_emergency(self, authorized_by: str) -> bool:
        """Reset emergency stop."""
        return self.emergency_controller.reset_emergency(authorized_by)
    
    def start_operator_session(self, operator_id: str) -> OperatorSession:
        """Start tracking an operator session."""
        return self.fatigue_monitor.start_session(operator_id)
    
    def record_operator_break(self, operator_id: str) -> None:
        """Record that operator took a break."""
        self.fatigue_monitor.record_break(operator_id)
    
    def get_thermal_status(self) -> dict[str, Any]:
        """Get current thermal status."""
        return self.temperature_monitor.get_thermal_status()
    
    def get_statistics(self) -> dict[str, Any]:
        """Get safety monitoring statistics."""
        return {
            "total_checks": self._check_count,
            "total_alerts_generated": len(self._alert_history),
            "active_alerts": len(self._active_alerts),
            "alerts_by_type": self._count_alerts_by_type(),
            "alerts_by_level": self._count_alerts_by_level(),
            "emergency_stops": sum(
                1 for a in self._alert_history
                if a.auto_action_taken == SafetyAction.EMERGENCY_STOP
            ),
        }
    
    def _count_alerts_by_type(self) -> dict[str, int]:
        """Count historical alerts by type."""
        counts: dict[str, int] = {}
        for alert in self._alert_history:
            type_name = alert.hazard_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def _count_alerts_by_level(self) -> dict[str, int]:
        """Count historical alerts by level."""
        counts: dict[str, int] = {}
        for alert in self._alert_history:
            level_name = alert.level.value
            counts[level_name] = counts.get(level_name, 0) + 1
        return counts


# =============================================================================
# Convenience Functions
# =============================================================================

_safety_monitor: Optional[SafetyMonitor] = None


def get_safety_monitor() -> SafetyMonitor:
    """
    Get or create the global safety monitor.
    
    Returns:
        SafetyMonitor: Singleton monitor instance.
    """
    global _safety_monitor
    if _safety_monitor is None:
        _safety_monitor = SafetyMonitor()
    return _safety_monitor


# Convenience exports
__all__ = [
    "HazardType",
    "AlertLevel",
    "SafetyAction",
    "SafetyAlert",
    "SafetyStatus",
    "OperatorSession",
    "VibrationMonitor",
    "TemperatureMonitor",
    "PressureMonitor",
    "GroundStabilityAnalyzer",
    "OperatorFatigueMonitor",
    "EmergencyController",
    "SafetyMonitor",
    "get_safety_monitor",
]

