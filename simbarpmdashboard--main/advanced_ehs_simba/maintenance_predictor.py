"""
Predictive Maintenance Engine for Advanced EHS Simba Drill System.

This module provides:
- Drill bit wear prediction using vibration analysis + drilling hours
- Hydraulic system health monitoring
- Component failure prediction (bearings, seals, pumps)
- Weibull distribution analysis for component lifespan
- RUL (Remaining Useful Life) calculation
- Maintenance scheduling optimizer

Author: EHS Simba Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar
from sklearn.ensemble import RandomForestRegressor

from config import MaintenanceModelConfig, get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class ComponentType(str, Enum):
    """Types of components that can be monitored."""
    DRILL_BIT = "drill_bit"
    BEARING = "bearing"
    SEAL = "seal"
    PUMP = "pump"
    MOTOR = "motor"
    HYDRAULIC_HOSE = "hydraulic_hose"
    FILTER = "filter"
    GEARBOX = "gearbox"


class HealthStatus(str, Enum):
    """Component health status levels."""
    EXCELLENT = "excellent"  # 80-100% health
    GOOD = "good"           # 60-80% health
    FAIR = "fair"           # 40-60% health
    POOR = "poor"           # 20-40% health
    CRITICAL = "critical"   # 0-20% health


class MaintenanceType(str, Enum):
    """Types of maintenance actions."""
    INSPECTION = "inspection"
    LUBRICATION = "lubrication"
    ADJUSTMENT = "adjustment"
    REPLACEMENT = "replacement"
    OVERHAUL = "overhaul"
    CALIBRATION = "calibration"


class MaintenancePriority(str, Enum):
    """Maintenance task priority levels."""
    EMERGENCY = "emergency"  # Immediate action required
    HIGH = "high"           # Within 24 hours
    MEDIUM = "medium"       # Within 7 days
    LOW = "low"             # Scheduled maintenance


@dataclass
class ComponentHealth:
    """
    Health assessment for a single component.
    
    Attributes:
        component_type: Type of component
        component_id: Unique identifier
        health_score: Health percentage (0-100)
        wear_percentage: Estimated wear (0-100)
        rul_hours: Remaining useful life in hours
        failure_probability: Probability of failure before next maintenance
        status: Overall health status
        metrics: Diagnostic metrics used for assessment
        recommendations: Suggested maintenance actions
    """
    component_type: ComponentType
    component_id: str
    health_score: float
    wear_percentage: float
    rul_hours: float
    failure_probability: float
    status: HealthStatus
    metrics: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component_type": self.component_type.value,
            "component_id": self.component_id,
            "health_score": self.health_score,
            "wear_percentage": self.wear_percentage,
            "rul_hours": self.rul_hours,
            "failure_probability": self.failure_probability,
            "status": self.status.value,
            "metrics": self.metrics,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MaintenanceTask:
    """
    Recommended maintenance task.
    
    Attributes:
        task_type: Type of maintenance
        component_type: Component requiring maintenance
        component_id: Specific component identifier
        priority: Task priority
        description: Detailed description
        estimated_duration_hours: Expected time to complete
        estimated_cost: Estimated cost in USD
        due_date: Recommended completion date
        parts_required: List of required spare parts
    """
    task_type: MaintenanceType
    component_type: ComponentType
    component_id: str
    priority: MaintenancePriority
    description: str
    estimated_duration_hours: float
    estimated_cost: float
    due_date: datetime
    parts_required: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_type": self.task_type.value,
            "component_type": self.component_type.value,
            "component_id": self.component_id,
            "priority": self.priority.value,
            "description": self.description,
            "estimated_duration_hours": self.estimated_duration_hours,
            "estimated_cost": self.estimated_cost,
            "due_date": self.due_date.isoformat(),
            "parts_required": self.parts_required,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class WeibullParameters:
    """
    Weibull distribution parameters for component lifetime modeling.
    
    The Weibull distribution is characterized by:
    - shape (β): Failure rate trend (β<1: decreasing, β=1: constant, β>1: increasing)
    - scale (η): Characteristic life (63.2% of components will fail by this time)
    
    Attributes:
        shape: Shape parameter (beta)
        scale_hours: Scale parameter in hours (eta)
        location: Location parameter (minimum life)
    """
    shape: float  # beta
    scale_hours: float  # eta (characteristic life)
    location: float = 0.0  # gamma (minimum life)
    
    def reliability(self, time_hours: float) -> float:
        """
        Calculate reliability (survival probability) at given time.
        
        Args:
            time_hours: Operating time in hours
            
        Returns:
            Probability of survival (0-1).
        """
        if time_hours <= self.location:
            return 1.0
        
        t = time_hours - self.location
        return np.exp(-((t / self.scale_hours) ** self.shape))
    
    def failure_probability(self, time_hours: float) -> float:
        """Calculate cumulative failure probability."""
        return 1.0 - self.reliability(time_hours)
    
    def hazard_rate(self, time_hours: float) -> float:
        """
        Calculate instantaneous failure rate (hazard function).
        
        Args:
            time_hours: Operating time in hours
            
        Returns:
            Failure rate per hour.
        """
        if time_hours <= self.location:
            return 0.0
        
        t = time_hours - self.location
        return (self.shape / self.scale_hours) * ((t / self.scale_hours) ** (self.shape - 1))
    
    def mean_life(self) -> float:
        """Calculate mean time to failure (MTTF)."""
        from scipy.special import gamma as gamma_func
        return self.location + self.scale_hours * gamma_func(1 + 1/self.shape)
    
    def percentile_life(self, percentile: float) -> float:
        """
        Calculate life at given percentile (B-life).
        
        Args:
            percentile: Failure percentile (e.g., 0.1 for B10 life)
            
        Returns:
            Hours at which specified percentage will have failed.
        """
        return self.location + self.scale_hours * ((-np.log(1 - percentile)) ** (1/self.shape))


# =============================================================================
# Weibull Analysis
# =============================================================================

class WeibullAnalyzer:
    """
    Weibull distribution analyzer for component lifetime modeling.
    
    Uses Maximum Likelihood Estimation (MLE) to fit Weibull parameters
    from failure data.
    """
    
    def __init__(self):
        """Initialize Weibull analyzer."""
        self._default_params = {
            ComponentType.DRILL_BIT: WeibullParameters(shape=2.5, scale_hours=500),
            ComponentType.BEARING: WeibullParameters(shape=2.0, scale_hours=8000),
            ComponentType.SEAL: WeibullParameters(shape=1.8, scale_hours=4000),
            ComponentType.PUMP: WeibullParameters(shape=2.2, scale_hours=10000),
            ComponentType.MOTOR: WeibullParameters(shape=2.5, scale_hours=15000),
            ComponentType.HYDRAULIC_HOSE: WeibullParameters(shape=2.0, scale_hours=6000),
            ComponentType.FILTER: WeibullParameters(shape=3.0, scale_hours=1000),
            ComponentType.GEARBOX: WeibullParameters(shape=2.3, scale_hours=12000),
        }
    
    def get_default_params(self, component_type: ComponentType) -> WeibullParameters:
        """Get default Weibull parameters for component type."""
        return self._default_params.get(
            component_type,
            WeibullParameters(shape=2.0, scale_hours=5000)
        )
    
    def fit_from_failures(
        self,
        failure_times: list[float],
        censored_times: Optional[list[float]] = None,
    ) -> WeibullParameters:
        """
        Fit Weibull parameters from failure data using MLE.
        
        Args:
            failure_times: List of times to failure (hours)
            censored_times: List of censored (still running) times
            
        Returns:
            Fitted WeibullParameters.
        """
        if not failure_times:
            return WeibullParameters(shape=2.0, scale_hours=5000)
        
        failures = np.array(failure_times)
        
        if censored_times:
            censored = np.array(censored_times)
        else:
            censored = np.array([])
        
        # Simple MLE for shape parameter
        def neg_log_likelihood(beta):
            if beta <= 0:
                return np.inf
            
            # Calculate scale given shape (profile likelihood)
            n = len(failures)
            eta = ((failures ** beta).sum() / n) ** (1/beta)
            
            # Log-likelihood for failures
            ll = n * np.log(beta) - n * beta * np.log(eta)
            ll += (beta - 1) * np.log(failures).sum()
            ll -= ((failures / eta) ** beta).sum()
            
            # Add censored observations
            if len(censored) > 0:
                ll -= ((censored / eta) ** beta).sum()
            
            return -ll
        
        # Optimize
        result = minimize_scalar(neg_log_likelihood, bounds=(0.5, 10), method='bounded')
        shape = result.x
        
        # Calculate scale from optimal shape
        n = len(failures)
        scale = ((failures ** shape).sum() / n) ** (1/shape)
        
        return WeibullParameters(shape=shape, scale_hours=scale)
    
    def calculate_rul(
        self,
        params: WeibullParameters,
        current_hours: float,
        target_reliability: float = 0.9,
    ) -> float:
        """
        Calculate Remaining Useful Life (RUL).
        
        Args:
            params: Weibull parameters
            current_hours: Current operating hours
            target_reliability: Minimum acceptable reliability
            
        Returns:
            Estimated remaining hours until reliability drops below target.
        """
        # Current reliability
        current_reliability = params.reliability(current_hours)
        
        if current_reliability <= target_reliability:
            return 0.0
        
        # Find time when reliability = target
        # R(t) = exp(-(t/η)^β) = target
        # t = η * (-ln(target))^(1/β)
        target_time = params.scale_hours * ((-np.log(target_reliability)) ** (1/params.shape))
        
        rul = max(0, target_time - current_hours)
        return rul


# =============================================================================
# Component Health Analyzers
# =============================================================================

class DrillBitAnalyzer:
    """
    Analyzer for drill bit wear and health.
    
    Uses vibration analysis and drilling hours to predict wear.
    """
    
    def __init__(self, config: Optional[MaintenanceModelConfig] = None):
        """Initialize drill bit analyzer."""
        self.config = config or get_settings().ml.maintenance
        self.weibull = WeibullAnalyzer()
        
        # Weibull parameters for drill bits
        self.weibull_params = WeibullParameters(
            shape=self.config.drill_bit_weibull_shape,
            scale_hours=self.config.drill_bit_weibull_scale_hours,
        )
        
        # Wear factors for different materials
        self.material_wear_factors = {
            "soft_soil": 0.5,
            "clay": 0.6,
            "sandstone": 1.0,
            "limestone": 1.2,
            "granite": 2.5,
            "basalt": 3.0,
            "ore_body": 2.0,
        }
    
    def analyze(
        self,
        operating_hours: float,
        vibration_history: list[float],
        materials_drilled: Optional[dict[str, float]] = None,
        current_vibration: float = 0.0,
    ) -> ComponentHealth:
        """
        Analyze drill bit health.
        
        Args:
            operating_hours: Total operating hours
            vibration_history: Recent vibration readings (g)
            materials_drilled: Dict of material -> hours drilled in each
            current_vibration: Current vibration level
            
        Returns:
            ComponentHealth assessment.
        """
        # Calculate effective wear hours based on materials
        effective_hours = self._calculate_effective_hours(
            operating_hours, materials_drilled
        )
        
        # Vibration-based wear indicator
        vibration_wear = self._analyze_vibration_wear(vibration_history)
        
        # Weibull-based reliability
        reliability = self.weibull_params.reliability(effective_hours)
        
        # Combined wear estimation
        wear_from_hours = (effective_hours / self.weibull_params.scale_hours) * 100
        wear_from_vibration = vibration_wear * 100
        
        # Weighted combination
        wear_percentage = min(100, 0.6 * wear_from_hours + 0.4 * wear_from_vibration)
        
        # Health score is inverse of wear
        health_score = max(0, 100 - wear_percentage)
        
        # RUL calculation
        rul = self.weibull.calculate_rul(
            self.weibull_params,
            effective_hours,
            target_reliability=0.9,
        )
        
        # Failure probability in next 100 hours
        failure_prob = (
            self.weibull_params.failure_probability(effective_hours + 100) -
            self.weibull_params.failure_probability(effective_hours)
        )
        
        # Determine status
        status = self._determine_status(health_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            health_score, rul, current_vibration
        )
        
        return ComponentHealth(
            component_type=ComponentType.DRILL_BIT,
            component_id="drill_bit_main",
            health_score=health_score,
            wear_percentage=wear_percentage,
            rul_hours=rul,
            failure_probability=failure_prob,
            status=status,
            metrics={
                "operating_hours": operating_hours,
                "effective_hours": effective_hours,
                "reliability": reliability,
                "vibration_wear_index": vibration_wear,
                "current_vibration_g": current_vibration,
            },
            recommendations=recommendations,
        )
    
    def _calculate_effective_hours(
        self,
        total_hours: float,
        materials_drilled: Optional[dict[str, float]],
    ) -> float:
        """Calculate effective wear hours based on material hardness."""
        if not materials_drilled:
            return total_hours
        
        effective = 0.0
        for material, hours in materials_drilled.items():
            factor = self.material_wear_factors.get(material, 1.0)
            effective += hours * factor
        
        return effective
    
    def _analyze_vibration_wear(self, vibration_history: list[float]) -> float:
        """
        Analyze vibration patterns for wear indicators.
        
        Returns wear index 0-1.
        """
        if not vibration_history or len(vibration_history) < 10:
            return 0.0
        
        values = np.array(vibration_history)
        
        # Worn bits typically show:
        # 1. Higher mean vibration
        # 2. More variance
        # 3. Higher frequency components
        
        mean_vib = np.mean(values)
        std_vib = np.std(values)
        
        # Normalize to 0-1 based on typical ranges
        # Normal: 0.5-2.0 g, Worn: 3.0-5.0 g
        mean_factor = np.clip((mean_vib - 1.0) / 3.0, 0, 1)
        std_factor = np.clip(std_vib / 1.0, 0, 1)
        
        # Trend detection (increasing vibration over time)
        if len(values) >= 20:
            first_half = np.mean(values[:len(values)//2])
            second_half = np.mean(values[len(values)//2:])
            trend_factor = np.clip((second_half - first_half) / first_half, 0, 1) if first_half > 0 else 0
        else:
            trend_factor = 0.0
        
        # Combined wear index
        wear_index = 0.4 * mean_factor + 0.3 * std_factor + 0.3 * trend_factor
        
        return float(wear_index)
    
    def _determine_status(self, health_score: float) -> HealthStatus:
        """Determine status from health score."""
        if health_score >= 80:
            return HealthStatus.EXCELLENT
        elif health_score >= 60:
            return HealthStatus.GOOD
        elif health_score >= 40:
            return HealthStatus.FAIR
        elif health_score >= 20:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL
    
    def _generate_recommendations(
        self,
        health_score: float,
        rul: float,
        current_vibration: float,
    ) -> list[str]:
        """Generate maintenance recommendations."""
        recommendations = []
        
        if health_score < 20:
            recommendations.append("URGENT: Replace drill bit immediately")
        elif health_score < 40:
            recommendations.append("Schedule drill bit replacement within 24 hours")
        elif health_score < 60:
            recommendations.append("Plan drill bit replacement for next maintenance window")
        
        if rul < 24:
            recommendations.append(f"Estimated {rul:.0f} hours remaining - plan replacement")
        
        if current_vibration > 4.0:
            recommendations.append("High vibration detected - inspect for damage")
        elif current_vibration > 3.0:
            recommendations.append("Elevated vibration - monitor closely")
        
        return recommendations


class HydraulicSystemAnalyzer:
    """
    Analyzer for hydraulic system health.
    
    Monitors pressure, temperature, and fluid quality.
    """
    
    def __init__(self, config: Optional[MaintenanceModelConfig] = None):
        """Initialize hydraulic system analyzer."""
        self.config = config or get_settings().ml.maintenance
        self.weibull = WeibullAnalyzer()
        
        # Component Weibull parameters
        self.seal_params = WeibullParameters(
            shape=self.config.seal_weibull_shape,
            scale_hours=self.config.seal_weibull_scale_hours,
        )
    
    def analyze(
        self,
        operating_hours: float,
        pressure_history: list[float],
        temperature_history: list[float],
        current_pressure: float,
        current_temperature: float,
        fluid_hours: float = 0.0,  # Hours since last fluid change
    ) -> dict[str, ComponentHealth]:
        """
        Analyze hydraulic system health.
        
        Args:
            operating_hours: Total system operating hours
            pressure_history: Recent pressure readings (bar)
            temperature_history: Recent temperature readings (°C)
            current_pressure: Current pressure
            current_temperature: Current temperature
            fluid_hours: Hours since last fluid change
            
        Returns:
            Dictionary of component health assessments.
        """
        results = {}
        
        # Analyze seals
        seal_health = self._analyze_seals(
            operating_hours, pressure_history, current_pressure
        )
        results["seals"] = seal_health
        
        # Analyze pump
        pump_health = self._analyze_pump(
            operating_hours, pressure_history, current_pressure
        )
        results["pump"] = pump_health
        
        # Analyze fluid condition
        fluid_health = self._analyze_fluid(
            fluid_hours, temperature_history, current_temperature
        )
        results["fluid"] = fluid_health
        
        # Analyze hoses
        hose_health = self._analyze_hoses(
            operating_hours, pressure_history, temperature_history
        )
        results["hoses"] = hose_health
        
        return results
    
    def _analyze_seals(
        self,
        operating_hours: float,
        pressure_history: list[float],
        current_pressure: float,
    ) -> ComponentHealth:
        """Analyze hydraulic seal condition."""
        # Pressure fluctuations indicate seal wear
        pressure_variance = np.std(pressure_history) if pressure_history else 0
        
        # High variance or low pressure suggests seal issues
        reliability = self.seal_params.reliability(operating_hours)
        
        # Pressure-based degradation
        if pressure_history:
            mean_pressure = np.mean(pressure_history)
            pressure_factor = 1.0 - np.clip((200 - mean_pressure) / 100, 0, 0.5)
        else:
            pressure_factor = 1.0
        
        # Variance factor (high variance = seal wear)
        variance_factor = 1.0 - np.clip(pressure_variance / 30, 0, 0.3)
        
        health_score = reliability * pressure_factor * variance_factor * 100
        wear_percentage = 100 - health_score
        
        rul = self.weibull.calculate_rul(self.seal_params, operating_hours)
        
        recommendations = []
        if health_score < 40:
            recommendations.append("Schedule seal replacement")
        if pressure_variance > 20:
            recommendations.append("High pressure variance - inspect seals for leaks")
        
        return ComponentHealth(
            component_type=ComponentType.SEAL,
            component_id="hydraulic_seals",
            health_score=health_score,
            wear_percentage=wear_percentage,
            rul_hours=rul,
            failure_probability=self.seal_params.failure_probability(operating_hours + 100),
            status=self._determine_status(health_score),
            metrics={
                "operating_hours": operating_hours,
                "pressure_variance": pressure_variance,
                "current_pressure": current_pressure,
            },
            recommendations=recommendations,
        )
    
    def _analyze_pump(
        self,
        operating_hours: float,
        pressure_history: list[float],
        current_pressure: float,
    ) -> ComponentHealth:
        """Analyze hydraulic pump condition."""
        pump_params = self.weibull.get_default_params(ComponentType.PUMP)
        reliability = pump_params.reliability(operating_hours)
        
        # Pump degradation shows as pressure drop
        pressure_trend = 0.0
        if len(pressure_history) >= 20:
            first_avg = np.mean(pressure_history[:len(pressure_history)//2])
            second_avg = np.mean(pressure_history[len(pressure_history)//2:])
            pressure_trend = (second_avg - first_avg) / max(first_avg, 1)
        
        # Negative trend indicates pump wear
        trend_factor = 1.0 + min(0, pressure_trend * 2)
        
        health_score = reliability * trend_factor * 100
        
        recommendations = []
        if health_score < 50:
            recommendations.append("Schedule pump inspection")
        if pressure_trend < -0.1:
            recommendations.append("Pressure declining - check pump efficiency")
        
        return ComponentHealth(
            component_type=ComponentType.PUMP,
            component_id="hydraulic_pump_main",
            health_score=health_score,
            wear_percentage=100 - health_score,
            rul_hours=self.weibull.calculate_rul(pump_params, operating_hours),
            failure_probability=pump_params.failure_probability(operating_hours + 100),
            status=self._determine_status(health_score),
            metrics={
                "operating_hours": operating_hours,
                "pressure_trend": pressure_trend,
                "current_pressure": current_pressure,
            },
            recommendations=recommendations,
        )
    
    def _analyze_fluid(
        self,
        fluid_hours: float,
        temperature_history: list[float],
        current_temperature: float,
    ) -> ComponentHealth:
        """Analyze hydraulic fluid condition."""
        # Fluid typically needs change every 2000-3000 hours
        fluid_life_hours = 2500
        
        # Temperature affects fluid degradation
        if temperature_history:
            avg_temp = np.mean(temperature_history)
            # Higher temperatures accelerate degradation
            temp_factor = 1.0 + max(0, (avg_temp - 50) / 50)
        else:
            temp_factor = 1.0
        
        # Effective fluid age
        effective_hours = fluid_hours * temp_factor
        
        health_score = max(0, (1 - effective_hours / fluid_life_hours) * 100)
        
        recommendations = []
        if health_score < 20:
            recommendations.append("URGENT: Change hydraulic fluid immediately")
        elif health_score < 40:
            recommendations.append("Schedule hydraulic fluid change")
        
        if current_temperature > 70:
            recommendations.append("High fluid temperature - check cooling system")
        
        return ComponentHealth(
            component_type=ComponentType.FILTER,  # Using filter as proxy for fluid
            component_id="hydraulic_fluid",
            health_score=health_score,
            wear_percentage=100 - health_score,
            rul_hours=max(0, fluid_life_hours - effective_hours),
            failure_probability=0.0,  # Fluid doesn't "fail" suddenly
            status=self._determine_status(health_score),
            metrics={
                "fluid_hours": fluid_hours,
                "effective_hours": effective_hours,
                "avg_temperature": np.mean(temperature_history) if temperature_history else 0,
                "current_temperature": current_temperature,
            },
            recommendations=recommendations,
        )
    
    def _analyze_hoses(
        self,
        operating_hours: float,
        pressure_history: list[float],
        temperature_history: list[float],
    ) -> ComponentHealth:
        """Analyze hydraulic hose condition."""
        hose_params = self.weibull.get_default_params(ComponentType.HYDRAULIC_HOSE)
        reliability = hose_params.reliability(operating_hours)
        
        # Pressure cycles cause fatigue
        if pressure_history:
            pressure_range = np.max(pressure_history) - np.min(pressure_history)
            cycle_factor = 1.0 - np.clip(pressure_range / 200, 0, 0.3)
        else:
            cycle_factor = 1.0
        
        # High temperatures degrade rubber
        if temperature_history:
            max_temp = np.max(temperature_history)
            temp_factor = 1.0 - np.clip((max_temp - 60) / 40, 0, 0.3)
        else:
            temp_factor = 1.0
        
        health_score = reliability * cycle_factor * temp_factor * 100
        
        recommendations = []
        if health_score < 40:
            recommendations.append("Schedule hose inspection and replacement")
        
        return ComponentHealth(
            component_type=ComponentType.HYDRAULIC_HOSE,
            component_id="hydraulic_hoses",
            health_score=health_score,
            wear_percentage=100 - health_score,
            rul_hours=self.weibull.calculate_rul(hose_params, operating_hours),
            failure_probability=hose_params.failure_probability(operating_hours + 100),
            status=self._determine_status(health_score),
            metrics={
                "operating_hours": operating_hours,
                "pressure_range": np.max(pressure_history) - np.min(pressure_history) if pressure_history else 0,
            },
            recommendations=recommendations,
        )
    
    def _determine_status(self, health_score: float) -> HealthStatus:
        """Determine status from health score."""
        if health_score >= 80:
            return HealthStatus.EXCELLENT
        elif health_score >= 60:
            return HealthStatus.GOOD
        elif health_score >= 40:
            return HealthStatus.FAIR
        elif health_score >= 20:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL


class BearingAnalyzer:
    """
    Analyzer for bearing health using vibration analysis.
    
    Uses frequency analysis to detect bearing defects:
    - BPFO (Ball Pass Frequency Outer race)
    - BPFI (Ball Pass Frequency Inner race)
    - BSF (Ball Spin Frequency)
    - FTF (Fundamental Train Frequency)
    """
    
    def __init__(self, config: Optional[MaintenanceModelConfig] = None):
        """Initialize bearing analyzer."""
        self.config = config or get_settings().ml.maintenance
        self.weibull = WeibullAnalyzer()
        
        self.weibull_params = WeibullParameters(
            shape=self.config.bearing_weibull_shape,
            scale_hours=self.config.bearing_weibull_scale_hours,
        )
    
    def analyze(
        self,
        operating_hours: float,
        vibration_waveform: Optional[np.ndarray] = None,
        vibration_rms: float = 0.0,
        temperature: float = 0.0,
        sampling_rate: int = 1000,
    ) -> ComponentHealth:
        """
        Analyze bearing health.
        
        Args:
            operating_hours: Total operating hours
            vibration_waveform: Time-domain vibration signal
            vibration_rms: RMS vibration level
            temperature: Bearing temperature
            sampling_rate: Vibration signal sampling rate
            
        Returns:
            ComponentHealth assessment.
        """
        # Base reliability from Weibull
        reliability = self.weibull_params.reliability(operating_hours)
        
        # Vibration analysis
        if vibration_waveform is not None and len(vibration_waveform) >= 512:
            vib_health = self._analyze_vibration_spectrum(
                vibration_waveform, sampling_rate
            )
        else:
            # Use RMS as simple indicator
            vib_health = 1.0 - np.clip((vibration_rms - 1.0) / 3.0, 0, 0.5)
        
        # Temperature factor
        temp_factor = 1.0 - np.clip((temperature - 60) / 40, 0, 0.3)
        
        # Combined health score
        health_score = reliability * vib_health * temp_factor * 100
        
        # RUL calculation
        rul = self.weibull.calculate_rul(self.weibull_params, operating_hours)
        
        recommendations = []
        if health_score < 30:
            recommendations.append("URGENT: Replace bearing immediately")
        elif health_score < 50:
            recommendations.append("Schedule bearing replacement")
        
        if vibration_rms > 3.0:
            recommendations.append("High vibration - inspect bearing for damage")
        
        if temperature > 80:
            recommendations.append("High bearing temperature - check lubrication")
        
        return ComponentHealth(
            component_type=ComponentType.BEARING,
            component_id="main_bearing",
            health_score=health_score,
            wear_percentage=100 - health_score,
            rul_hours=rul,
            failure_probability=self.weibull_params.failure_probability(operating_hours + 100),
            status=self._determine_status(health_score),
            metrics={
                "operating_hours": operating_hours,
                "vibration_rms": vibration_rms,
                "temperature": temperature,
                "vibration_health_index": vib_health,
            },
            recommendations=recommendations,
        )
    
    def _analyze_vibration_spectrum(
        self,
        waveform: np.ndarray,
        sampling_rate: int,
    ) -> float:
        """
        Analyze vibration spectrum for bearing defect frequencies.
        
        Returns health index 0-1.
        """
        # Compute FFT
        fft_vals = np.abs(np.fft.rfft(waveform))
        freqs = np.fft.rfftfreq(len(waveform), 1.0 / sampling_rate)
        
        # Total energy
        total_energy = np.sum(fft_vals ** 2)
        if total_energy == 0:
            return 1.0
        
        # Check for energy in typical defect frequency bands
        # These would be calculated from bearing geometry in real applications
        defect_bands = [
            (50, 150),   # Typical BPFO range
            (100, 250),  # Typical BPFI range
            (150, 350),  # Typical BSF range
        ]
        
        defect_energy = 0.0
        for low, high in defect_bands:
            mask = (freqs >= low) & (freqs <= high)
            defect_energy += np.sum(fft_vals[mask] ** 2)
        
        # High ratio of defect energy indicates problems
        defect_ratio = defect_energy / total_energy
        
        # Also check overall energy level
        energy_factor = 1.0 - np.clip(total_energy / 1e6, 0, 0.5)
        
        # Combined health index
        health_index = (1.0 - defect_ratio * 2) * energy_factor
        
        return float(np.clip(health_index, 0, 1))
    
    def _determine_status(self, health_score: float) -> HealthStatus:
        """Determine status from health score."""
        if health_score >= 80:
            return HealthStatus.EXCELLENT
        elif health_score >= 60:
            return HealthStatus.GOOD
        elif health_score >= 40:
            return HealthStatus.FAIR
        elif health_score >= 20:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL


# =============================================================================
# Maintenance Scheduler
# =============================================================================

class MaintenanceScheduler:
    """
    Optimizes maintenance scheduling based on component health.
    
    Considers:
    - Component criticality and failure impact
    - RUL predictions
    - Available maintenance windows
    - Parts availability
    - Labor resources
    """
    
    def __init__(self):
        """Initialize maintenance scheduler."""
        # Criticality weights (1-10, higher = more critical)
        self.criticality = {
            ComponentType.DRILL_BIT: 6,
            ComponentType.BEARING: 8,
            ComponentType.SEAL: 7,
            ComponentType.PUMP: 9,
            ComponentType.MOTOR: 10,
            ComponentType.HYDRAULIC_HOSE: 7,
            ComponentType.FILTER: 4,
            ComponentType.GEARBOX: 9,
        }
        
        # Typical maintenance durations (hours)
        self.durations = {
            ComponentType.DRILL_BIT: 1.0,
            ComponentType.BEARING: 4.0,
            ComponentType.SEAL: 2.0,
            ComponentType.PUMP: 6.0,
            ComponentType.MOTOR: 8.0,
            ComponentType.HYDRAULIC_HOSE: 2.0,
            ComponentType.FILTER: 0.5,
            ComponentType.GEARBOX: 12.0,
        }
        
        # Estimated costs (USD)
        self.costs = {
            ComponentType.DRILL_BIT: 500,
            ComponentType.BEARING: 1200,
            ComponentType.SEAL: 300,
            ComponentType.PUMP: 5000,
            ComponentType.MOTOR: 15000,
            ComponentType.HYDRAULIC_HOSE: 400,
            ComponentType.FILTER: 100,
            ComponentType.GEARBOX: 8000,
        }
    
    def generate_schedule(
        self,
        health_reports: list[ComponentHealth],
        planning_horizon_days: int = 30,
    ) -> list[MaintenanceTask]:
        """
        Generate optimized maintenance schedule.
        
        Args:
            health_reports: List of component health assessments
            planning_horizon_days: Days to plan ahead
            
        Returns:
            List of scheduled maintenance tasks.
        """
        tasks = []
        now = datetime.utcnow()
        
        for health in health_reports:
            task = self._create_task_from_health(health, now, planning_horizon_days)
            if task:
                tasks.append(task)
        
        # Sort by priority and due date
        priority_order = {
            MaintenancePriority.EMERGENCY: 0,
            MaintenancePriority.HIGH: 1,
            MaintenancePriority.MEDIUM: 2,
            MaintenancePriority.LOW: 3,
        }
        
        tasks.sort(key=lambda t: (priority_order[t.priority], t.due_date))
        
        return tasks
    
    def _create_task_from_health(
        self,
        health: ComponentHealth,
        now: datetime,
        horizon_days: int,
    ) -> Optional[MaintenanceTask]:
        """Create maintenance task from health report if needed."""
        # Determine if maintenance is needed
        if health.status == HealthStatus.EXCELLENT:
            return None
        
        # Determine priority and due date
        if health.status == HealthStatus.CRITICAL or health.rul_hours < 24:
            priority = MaintenancePriority.EMERGENCY
            due_date = now + timedelta(hours=4)
            task_type = MaintenanceType.REPLACEMENT
        elif health.status == HealthStatus.POOR or health.rul_hours < 100:
            priority = MaintenancePriority.HIGH
            due_date = now + timedelta(days=1)
            task_type = MaintenanceType.REPLACEMENT
        elif health.status == HealthStatus.FAIR:
            priority = MaintenancePriority.MEDIUM
            due_date = now + timedelta(days=7)
            task_type = MaintenanceType.INSPECTION
        else:  # GOOD status
            priority = MaintenancePriority.LOW
            due_date = now + timedelta(days=min(horizon_days, 14))
            task_type = MaintenanceType.INSPECTION
        
        # Check if within planning horizon
        if due_date > now + timedelta(days=horizon_days):
            return None
        
        # Generate description
        description = self._generate_description(health, task_type)
        
        return MaintenanceTask(
            task_type=task_type,
            component_type=health.component_type,
            component_id=health.component_id,
            priority=priority,
            description=description,
            estimated_duration_hours=self.durations.get(health.component_type, 2.0),
            estimated_cost=self.costs.get(health.component_type, 500),
            due_date=due_date,
            parts_required=self._get_required_parts(health.component_type, task_type),
        )
    
    def _generate_description(
        self,
        health: ComponentHealth,
        task_type: MaintenanceType,
    ) -> str:
        """Generate task description."""
        descriptions = {
            MaintenanceType.REPLACEMENT: f"Replace {health.component_type.value} - "
                f"Health: {health.health_score:.1f}%, RUL: {health.rul_hours:.0f}h",
            MaintenanceType.INSPECTION: f"Inspect {health.component_type.value} - "
                f"Health: {health.health_score:.1f}%",
            MaintenanceType.LUBRICATION: f"Lubricate {health.component_type.value}",
            MaintenanceType.ADJUSTMENT: f"Adjust/calibrate {health.component_type.value}",
            MaintenanceType.OVERHAUL: f"Overhaul {health.component_type.value} - "
                f"Health: {health.health_score:.1f}%",
        }
        return descriptions.get(task_type, f"Maintain {health.component_type.value}")
    
    def _get_required_parts(
        self,
        component_type: ComponentType,
        task_type: MaintenanceType,
    ) -> list[str]:
        """Get list of required spare parts."""
        if task_type != MaintenanceType.REPLACEMENT:
            return []
        
        parts_map = {
            ComponentType.DRILL_BIT: ["Drill bit assembly", "O-rings"],
            ComponentType.BEARING: ["Bearing kit", "Grease", "Seals"],
            ComponentType.SEAL: ["Seal kit", "O-ring set"],
            ComponentType.PUMP: ["Pump assembly", "Seals", "Gaskets"],
            ComponentType.HYDRAULIC_HOSE: ["Hydraulic hose", "Fittings"],
            ComponentType.FILTER: ["Filter element"],
        }
        return parts_map.get(component_type, [])


# =============================================================================
# Main Predictive Maintenance Engine
# =============================================================================

class PredictiveMaintenanceEngine:
    """
    Main predictive maintenance engine for EHS Simba system.
    
    Integrates all component analyzers and provides unified interface
    for health monitoring and maintenance scheduling.
    
    Example:
        >>> engine = PredictiveMaintenanceEngine()
        >>> 
        >>> # Update with sensor data
        >>> engine.update_drill_bit_data(
        ...     operating_hours=350,
        ...     vibration_history=[1.2, 1.4, 1.5, 1.8],
        ...     materials_drilled={"granite": 100, "sandstone": 250}
        ... )
        >>> 
        >>> # Get health report
        >>> health = engine.get_system_health()
        >>> 
        >>> # Get maintenance schedule
        >>> schedule = engine.get_maintenance_schedule()
    """
    
    def __init__(self, config: Optional[MaintenanceModelConfig] = None):
        """Initialize predictive maintenance engine."""
        self.config = config or get_settings().ml.maintenance
        
        # Initialize analyzers
        self.drill_bit_analyzer = DrillBitAnalyzer(self.config)
        self.hydraulic_analyzer = HydraulicSystemAnalyzer(self.config)
        self.bearing_analyzer = BearingAnalyzer(self.config)
        self.scheduler = MaintenanceScheduler()
        
        # Current state
        self._drill_bit_state: dict[str, Any] = {}
        self._hydraulic_state: dict[str, Any] = {}
        self._bearing_state: dict[str, Any] = {}
        
        # Health reports cache
        self._health_reports: dict[str, ComponentHealth] = {}
        self._last_update = datetime.utcnow()
        
        logger.info("PredictiveMaintenanceEngine initialized")
    
    def update_drill_bit_data(
        self,
        operating_hours: float,
        vibration_history: list[float],
        materials_drilled: Optional[dict[str, float]] = None,
        current_vibration: float = 0.0,
    ) -> ComponentHealth:
        """
        Update drill bit data and get health assessment.
        
        Args:
            operating_hours: Total operating hours
            vibration_history: Recent vibration readings
            materials_drilled: Hours drilled in each material type
            current_vibration: Current vibration level
            
        Returns:
            Drill bit health assessment.
        """
        self._drill_bit_state = {
            "operating_hours": operating_hours,
            "vibration_history": vibration_history,
            "materials_drilled": materials_drilled,
            "current_vibration": current_vibration,
        }
        
        health = self.drill_bit_analyzer.analyze(
            operating_hours=operating_hours,
            vibration_history=vibration_history,
            materials_drilled=materials_drilled,
            current_vibration=current_vibration,
        )
        
        self._health_reports["drill_bit"] = health
        return health
    
    def update_hydraulic_data(
        self,
        operating_hours: float,
        pressure_history: list[float],
        temperature_history: list[float],
        current_pressure: float,
        current_temperature: float,
        fluid_hours: float = 0.0,
    ) -> dict[str, ComponentHealth]:
        """
        Update hydraulic system data and get health assessments.
        
        Returns:
            Dictionary of hydraulic component health assessments.
        """
        self._hydraulic_state = {
            "operating_hours": operating_hours,
            "pressure_history": pressure_history,
            "temperature_history": temperature_history,
            "current_pressure": current_pressure,
            "current_temperature": current_temperature,
            "fluid_hours": fluid_hours,
        }
        
        health_reports = self.hydraulic_analyzer.analyze(
            operating_hours=operating_hours,
            pressure_history=pressure_history,
            temperature_history=temperature_history,
            current_pressure=current_pressure,
            current_temperature=current_temperature,
            fluid_hours=fluid_hours,
        )
        
        for key, health in health_reports.items():
            self._health_reports[f"hydraulic_{key}"] = health
        
        return health_reports
    
    def update_bearing_data(
        self,
        operating_hours: float,
        vibration_waveform: Optional[np.ndarray] = None,
        vibration_rms: float = 0.0,
        temperature: float = 0.0,
    ) -> ComponentHealth:
        """
        Update bearing data and get health assessment.
        
        Returns:
            Bearing health assessment.
        """
        self._bearing_state = {
            "operating_hours": operating_hours,
            "vibration_rms": vibration_rms,
            "temperature": temperature,
        }
        
        health = self.bearing_analyzer.analyze(
            operating_hours=operating_hours,
            vibration_waveform=vibration_waveform,
            vibration_rms=vibration_rms,
            temperature=temperature,
        )
        
        self._health_reports["bearing"] = health
        return health
    
    def get_system_health(self) -> dict[str, ComponentHealth]:
        """
        Get health status for all monitored components.
        
        Returns:
            Dictionary mapping component names to health reports.
        """
        return self._health_reports.copy()
    
    def get_critical_components(self) -> list[ComponentHealth]:
        """
        Get list of components in critical or poor condition.
        
        Returns:
            List of unhealthy components sorted by severity.
        """
        critical = [
            h for h in self._health_reports.values()
            if h.status in [HealthStatus.CRITICAL, HealthStatus.POOR]
        ]
        
        # Sort by health score (worst first)
        critical.sort(key=lambda h: h.health_score)
        
        return critical
    
    def get_maintenance_schedule(
        self,
        planning_horizon_days: int = 30,
    ) -> list[MaintenanceTask]:
        """
        Generate optimized maintenance schedule.
        
        Args:
            planning_horizon_days: Days to plan ahead
            
        Returns:
            List of scheduled maintenance tasks.
        """
        health_list = list(self._health_reports.values())
        return self.scheduler.generate_schedule(health_list, planning_horizon_days)
    
    def get_rul_summary(self) -> dict[str, float]:
        """
        Get RUL summary for all components.
        
        Returns:
            Dictionary mapping component names to RUL in hours.
        """
        return {
            name: health.rul_hours
            for name, health in self._health_reports.items()
        }
    
    def get_overall_system_health(self) -> float:
        """
        Calculate overall system health score.
        
        Returns weighted average based on component criticality.
        """
        if not self._health_reports:
            return 100.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for name, health in self._health_reports.items():
            weight = self.scheduler.criticality.get(health.component_type, 5)
            weighted_sum += health.health_score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 100.0


# =============================================================================
# Convenience Functions
# =============================================================================

_maintenance_engine: Optional[PredictiveMaintenanceEngine] = None


def get_maintenance_engine() -> PredictiveMaintenanceEngine:
    """
    Get or create the global predictive maintenance engine.
    
    Returns:
        PredictiveMaintenanceEngine: Singleton engine instance.
    """
    global _maintenance_engine
    if _maintenance_engine is None:
        _maintenance_engine = PredictiveMaintenanceEngine()
    return _maintenance_engine


# Convenience exports
__all__ = [
    "ComponentType",
    "HealthStatus",
    "MaintenanceType",
    "MaintenancePriority",
    "ComponentHealth",
    "MaintenanceTask",
    "WeibullParameters",
    "WeibullAnalyzer",
    "DrillBitAnalyzer",
    "HydraulicSystemAnalyzer",
    "BearingAnalyzer",
    "MaintenanceScheduler",
    "PredictiveMaintenanceEngine",
    "get_maintenance_engine",
]

