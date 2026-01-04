"""
Energy Efficiency Analyzer for Advanced EHS Simba Drill System.

This module provides:
- Power consumption monitoring and anomaly detection
- RPM vs material optimization recommendations
- Electric vs hydraulic efficiency tracking
- Cost savings calculator (EHS vs conventional pneumatic)
- Peak demand management

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

from config import EnergyConfig, get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class DrillState(str, Enum):
    """Drill operational state."""
    IDLE = "idle"
    DRILLING = "drilling"
    REPOSITIONING = "repositioning"
    MAINTENANCE = "maintenance"
    STANDBY = "standby"


class EfficiencyRating(str, Enum):
    """Energy efficiency rating."""
    EXCELLENT = "excellent"  # >90%
    GOOD = "good"           # 80-90%
    FAIR = "fair"           # 70-80%
    POOR = "poor"           # 60-70%
    CRITICAL = "critical"   # <60%


@dataclass
class PowerReading:
    """
    Power consumption reading.
    
    Attributes:
        timestamp: Reading timestamp
        power_kw: Instantaneous power in kW
        voltage_v: Voltage in volts
        current_a: Current in amps
        power_factor: Power factor (0-1)
        energy_kwh: Cumulative energy in kWh
        state: Current drill state
    """
    timestamp: datetime
    power_kw: float
    voltage_v: float = 0.0
    current_a: float = 0.0
    power_factor: float = 1.0
    energy_kwh: float = 0.0
    state: DrillState = DrillState.DRILLING
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "power_kw": self.power_kw,
            "voltage_v": self.voltage_v,
            "current_a": self.current_a,
            "power_factor": self.power_factor,
            "energy_kwh": self.energy_kwh,
            "state": self.state.value,
        }


@dataclass
class EnergyMetrics:
    """
    Energy consumption metrics for a time period.
    
    Attributes:
        start_time: Period start
        end_time: Period end
        total_energy_kwh: Total energy consumed
        peak_power_kw: Maximum power draw
        avg_power_kw: Average power draw
        min_power_kw: Minimum power draw
        drilling_energy_kwh: Energy used during drilling
        idle_energy_kwh: Energy used while idle
        efficiency_percent: Overall energy efficiency
        cost_usd: Total energy cost
    """
    start_time: datetime
    end_time: datetime
    total_energy_kwh: float
    peak_power_kw: float
    avg_power_kw: float
    min_power_kw: float
    drilling_energy_kwh: float
    idle_energy_kwh: float
    efficiency_percent: float
    cost_usd: float
    drilling_hours: float = 0.0
    idle_hours: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_energy_kwh": self.total_energy_kwh,
            "peak_power_kw": self.peak_power_kw,
            "avg_power_kw": self.avg_power_kw,
            "min_power_kw": self.min_power_kw,
            "drilling_energy_kwh": self.drilling_energy_kwh,
            "idle_energy_kwh": self.idle_energy_kwh,
            "efficiency_percent": self.efficiency_percent,
            "cost_usd": self.cost_usd,
            "drilling_hours": self.drilling_hours,
            "idle_hours": self.idle_hours,
        }


@dataclass
class OptimizationRecommendation:
    """
    Energy optimization recommendation.
    
    Attributes:
        category: Recommendation category
        description: Detailed description
        potential_savings_kwh: Estimated energy savings per day
        potential_savings_usd: Estimated cost savings per day
        priority: Implementation priority (1-5, 1=highest)
        implementation_effort: Low/Medium/High
    """
    category: str
    description: str
    potential_savings_kwh: float
    potential_savings_usd: float
    priority: int
    implementation_effort: str
    current_value: Optional[float] = None
    recommended_value: Optional[float] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category,
            "description": self.description,
            "potential_savings_kwh": self.potential_savings_kwh,
            "potential_savings_usd": self.potential_savings_usd,
            "priority": self.priority,
            "implementation_effort": self.implementation_effort,
            "current_value": self.current_value,
            "recommended_value": self.recommended_value,
        }


@dataclass
class CostComparison:
    """
    Cost comparison between EHS and conventional drilling.
    
    Attributes:
        period_hours: Comparison period in hours
        ehs_energy_kwh: EHS energy consumption
        ehs_cost_usd: EHS energy cost
        pneumatic_energy_kwh: Equivalent pneumatic energy
        pneumatic_cost_usd: Equivalent pneumatic cost
        savings_kwh: Energy saved
        savings_usd: Cost saved
        savings_percent: Percentage savings
        co2_reduction_kg: CO2 reduction in kg
    """
    period_hours: float
    ehs_energy_kwh: float
    ehs_cost_usd: float
    pneumatic_energy_kwh: float
    pneumatic_cost_usd: float
    savings_kwh: float
    savings_usd: float
    savings_percent: float
    co2_reduction_kg: float
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "period_hours": self.period_hours,
            "ehs_energy_kwh": self.ehs_energy_kwh,
            "ehs_cost_usd": self.ehs_cost_usd,
            "pneumatic_energy_kwh": self.pneumatic_energy_kwh,
            "pneumatic_cost_usd": self.pneumatic_cost_usd,
            "savings_kwh": self.savings_kwh,
            "savings_usd": self.savings_usd,
            "savings_percent": self.savings_percent,
            "co2_reduction_kg": self.co2_reduction_kg,
        }


# =============================================================================
# Power Monitor
# =============================================================================

class PowerMonitor:
    """
    Real-time power consumption monitoring.
    
    Tracks power usage, detects anomalies, and calculates efficiency metrics.
    """
    
    def __init__(self, config: Optional[EnergyConfig] = None):
        """Initialize power monitor."""
        self.config = config or get_settings().energy
        
        # Reading buffer (last 24 hours at 10 Hz = 864,000 readings)
        # Use 1-minute aggregations for storage efficiency
        self._minute_aggregates: list[dict] = []
        self._current_minute_readings: list[PowerReading] = []
        
        # Current state
        self._current_reading: Optional[PowerReading] = None
        self._cumulative_energy_kwh = 0.0
        self._session_start: Optional[datetime] = None
        
        # Anomaly detection
        self._baseline_power: Optional[float] = None
        self._baseline_std: Optional[float] = None
        
        logger.info("PowerMonitor initialized")
    
    def add_reading(self, reading: PowerReading) -> Optional[str]:
        """
        Add a new power reading.
        
        Args:
            reading: Power reading to add
            
        Returns:
            Anomaly message if detected, None otherwise.
        """
        self._current_reading = reading
        self._current_minute_readings.append(reading)
        
        # Update cumulative energy
        if len(self._current_minute_readings) > 1:
            prev = self._current_minute_readings[-2]
            time_diff = (reading.timestamp - prev.timestamp).total_seconds() / 3600
            self._cumulative_energy_kwh += reading.power_kw * time_diff
        
        # Check for minute boundary
        if self._current_minute_readings:
            first = self._current_minute_readings[0]
            if (reading.timestamp - first.timestamp).total_seconds() >= 60:
                self._aggregate_minute()
        
        # Check for anomalies
        return self._check_anomaly(reading)
    
    def _aggregate_minute(self) -> None:
        """Aggregate current minute readings."""
        if not self._current_minute_readings:
            return
        
        powers = [r.power_kw for r in self._current_minute_readings]
        
        aggregate = {
            "timestamp": self._current_minute_readings[0].timestamp,
            "avg_power_kw": np.mean(powers),
            "max_power_kw": np.max(powers),
            "min_power_kw": np.min(powers),
            "std_power_kw": np.std(powers),
            "reading_count": len(powers),
            "state": self._current_minute_readings[-1].state.value,
        }
        
        self._minute_aggregates.append(aggregate)
        
        # Keep only last 24 hours (1440 minutes)
        if len(self._minute_aggregates) > 1440:
            self._minute_aggregates = self._minute_aggregates[-1440:]
        
        # Update baseline if we have enough data
        if len(self._minute_aggregates) >= 60:
            recent = [a["avg_power_kw"] for a in self._minute_aggregates[-60:]]
            self._baseline_power = np.mean(recent)
            self._baseline_std = np.std(recent)
        
        self._current_minute_readings = []
    
    def _check_anomaly(self, reading: PowerReading) -> Optional[str]:
        """Check for power anomalies."""
        anomalies = []
        
        # Check absolute limits
        if reading.power_kw > self.config.max_power_kw * 1.1:
            anomalies.append(f"Power exceeds maximum: {reading.power_kw:.1f} kW")
        
        if reading.power_kw > self.config.peak_demand_threshold_kw:
            anomalies.append(f"Peak demand warning: {reading.power_kw:.1f} kW")
        
        # Check for sudden changes
        if self._baseline_power and self._baseline_std:
            z_score = abs(reading.power_kw - self._baseline_power) / max(self._baseline_std, 1)
            if z_score > 3.5:
                anomalies.append(
                    f"Unusual power consumption: {reading.power_kw:.1f} kW "
                    f"(baseline: {self._baseline_power:.1f} kW)"
                )
        
        # Check power factor
        if reading.power_factor < 0.8:
            anomalies.append(f"Low power factor: {reading.power_factor:.2f}")
        
        return "; ".join(anomalies) if anomalies else None
    
    def get_current_power(self) -> float:
        """Get current power consumption in kW."""
        return self._current_reading.power_kw if self._current_reading else 0.0
    
    def get_metrics(
        self,
        hours: float = 24.0,
    ) -> EnergyMetrics:
        """
        Get energy metrics for specified period.
        
        Args:
            hours: Time period in hours
            
        Returns:
            EnergyMetrics for the period.
        """
        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours)
        
        # Filter aggregates for period
        period_data = [
            a for a in self._minute_aggregates
            if a["timestamp"] >= start_time
        ]
        
        if not period_data:
            return EnergyMetrics(
                start_time=start_time,
                end_time=now,
                total_energy_kwh=0.0,
                peak_power_kw=0.0,
                avg_power_kw=0.0,
                min_power_kw=0.0,
                drilling_energy_kwh=0.0,
                idle_energy_kwh=0.0,
                efficiency_percent=0.0,
                cost_usd=0.0,
            )
        
        # Calculate metrics
        powers = [a["avg_power_kw"] for a in period_data]
        
        # Energy calculation (kW * hours)
        total_energy = sum(p / 60 for p in powers)  # Each aggregate is 1 minute
        
        # Separate by state
        drilling_energy = sum(
            a["avg_power_kw"] / 60 for a in period_data
            if a["state"] == DrillState.DRILLING.value
        )
        idle_energy = sum(
            a["avg_power_kw"] / 60 for a in period_data
            if a["state"] in [DrillState.IDLE.value, DrillState.STANDBY.value]
        )
        
        # Calculate hours by state
        drilling_minutes = sum(
            1 for a in period_data
            if a["state"] == DrillState.DRILLING.value
        )
        idle_minutes = sum(
            1 for a in period_data
            if a["state"] in [DrillState.IDLE.value, DrillState.STANDBY.value]
        )
        
        # Efficiency: useful drilling energy / total energy
        efficiency = (drilling_energy / total_energy * 100) if total_energy > 0 else 0
        
        # Cost calculation
        cost = self._calculate_cost(period_data)
        
        return EnergyMetrics(
            start_time=start_time,
            end_time=now,
            total_energy_kwh=total_energy,
            peak_power_kw=max(powers),
            avg_power_kw=np.mean(powers),
            min_power_kw=min(powers),
            drilling_energy_kwh=drilling_energy,
            idle_energy_kwh=idle_energy,
            efficiency_percent=efficiency,
            cost_usd=cost,
            drilling_hours=drilling_minutes / 60,
            idle_hours=idle_minutes / 60,
        )
    
    def _calculate_cost(self, aggregates: list[dict]) -> float:
        """Calculate energy cost considering peak hours."""
        cost = 0.0
        base_rate = self.config.electricity_cost_per_kwh
        
        for agg in aggregates:
            hour = agg["timestamp"].hour
            is_peak = self.config.peak_hours_start <= hour < self.config.peak_hours_end
            
            rate = base_rate * self.config.peak_rate_multiplier if is_peak else base_rate
            energy = agg["avg_power_kw"] / 60  # kWh for 1 minute
            cost += energy * rate
        
        return cost
    
    def get_efficiency_rating(self) -> EfficiencyRating:
        """Get current efficiency rating."""
        metrics = self.get_metrics(hours=1.0)
        
        if metrics.efficiency_percent >= 90:
            return EfficiencyRating.EXCELLENT
        elif metrics.efficiency_percent >= 80:
            return EfficiencyRating.GOOD
        elif metrics.efficiency_percent >= 70:
            return EfficiencyRating.FAIR
        elif metrics.efficiency_percent >= 60:
            return EfficiencyRating.POOR
        else:
            return EfficiencyRating.CRITICAL


# =============================================================================
# RPM Optimizer
# =============================================================================

class RPMOptimizer:
    """
    Optimizes RPM settings based on material type for energy efficiency.
    
    Different materials have optimal RPM ranges that balance:
    - Penetration rate
    - Bit wear
    - Energy consumption
    """
    
    def __init__(self, config: Optional[EnergyConfig] = None):
        """Initialize RPM optimizer."""
        self.config = config or get_settings().energy
        
        # Optimal RPM ranges by material (min, optimal, max)
        self._rpm_profiles = {
            "soft_soil": (100, 130, 150),
            "clay": (90, 120, 140),
            "sandstone": (70, 90, 110),
            "limestone": (60, 80, 100),
            "granite": (40, 55, 70),
            "basalt": (35, 50, 65),
            "ore_body": (50, 70, 90),
            "void": (80, 100, 120),  # Fast through voids
        }
        
        # Power consumption models (kW at optimal RPM)
        self._power_profiles = {
            "soft_soil": 80,
            "clay": 100,
            "sandstone": 130,
            "limestone": 150,
            "granite": 200,
            "basalt": 220,
            "ore_body": 180,
            "void": 50,
        }
        
        # Learning data
        self._performance_history: list[dict] = []
    
    def get_optimal_rpm(
        self,
        material: str,
        current_rpm: float,
        current_power: float,
        penetration_rate: float,
    ) -> dict[str, Any]:
        """
        Get optimal RPM recommendation for current conditions.
        
        Args:
            material: Current material type
            current_rpm: Current RPM setting
            current_power: Current power consumption (kW)
            penetration_rate: Current penetration rate (m/min)
            
        Returns:
            Dictionary with recommendation details.
        """
        # Get profile for material
        rpm_range = self._rpm_profiles.get(material, (60, 80, 100))
        expected_power = self._power_profiles.get(material, 150)
        
        min_rpm, optimal_rpm, max_rpm = rpm_range
        
        # Calculate efficiency metrics
        # Specific energy: kWh per meter drilled
        specific_energy = (
            (current_power / 60) / max(penetration_rate, 0.01)
            if penetration_rate > 0 else float('inf')
        )
        
        # Expected specific energy at optimal RPM
        # (simplified model - in practice would use ML)
        expected_penetration = self._estimate_penetration(material, optimal_rpm)
        expected_specific_energy = (expected_power / 60) / max(expected_penetration, 0.01)
        
        # Determine recommendation
        if current_rpm < min_rpm:
            recommendation = "INCREASE"
            reason = f"RPM below minimum ({min_rpm}) for {material}"
            target_rpm = optimal_rpm
        elif current_rpm > max_rpm:
            recommendation = "DECREASE"
            reason = f"RPM above maximum ({max_rpm}) for {material}"
            target_rpm = optimal_rpm
        elif abs(current_rpm - optimal_rpm) > 15:
            recommendation = "ADJUST"
            reason = f"Adjusting toward optimal ({optimal_rpm}) for efficiency"
            target_rpm = optimal_rpm
        else:
            recommendation = "MAINTAIN"
            reason = "RPM within optimal range"
            target_rpm = current_rpm
        
        # Calculate potential savings
        if recommendation != "MAINTAIN":
            power_savings = current_power - expected_power
            energy_savings_per_hour = max(0, power_savings)
        else:
            energy_savings_per_hour = 0
        
        return {
            "recommendation": recommendation,
            "reason": reason,
            "current_rpm": current_rpm,
            "target_rpm": target_rpm,
            "rpm_range": {"min": min_rpm, "optimal": optimal_rpm, "max": max_rpm},
            "current_specific_energy": specific_energy,
            "expected_specific_energy": expected_specific_energy,
            "potential_savings_kw": energy_savings_per_hour,
            "material": material,
        }
    
    def _estimate_penetration(self, material: str, rpm: float) -> float:
        """Estimate penetration rate based on material and RPM."""
        # Simplified model - higher RPM generally means faster penetration
        # but with diminishing returns and material-dependent curves
        base_rates = {
            "soft_soil": 1.5,
            "clay": 1.2,
            "sandstone": 0.8,
            "limestone": 0.6,
            "granite": 0.3,
            "basalt": 0.25,
            "ore_body": 0.4,
            "void": 2.0,
        }
        
        base = base_rates.get(material, 0.5)
        optimal_rpm = self._rpm_profiles.get(material, (60, 80, 100))[1]
        
        # Penetration rate peaks near optimal RPM
        rpm_factor = 1.0 - 0.3 * ((rpm - optimal_rpm) / optimal_rpm) ** 2
        
        return base * max(0.5, rpm_factor)
    
    def record_performance(
        self,
        material: str,
        rpm: float,
        power_kw: float,
        penetration_rate: float,
        bit_wear_rate: float,
    ) -> None:
        """Record performance data for learning."""
        self._performance_history.append({
            "timestamp": datetime.utcnow(),
            "material": material,
            "rpm": rpm,
            "power_kw": power_kw,
            "penetration_rate": penetration_rate,
            "bit_wear_rate": bit_wear_rate,
            "specific_energy": (power_kw / 60) / max(penetration_rate, 0.01),
        })
        
        # Keep last 10000 records
        if len(self._performance_history) > 10000:
            self._performance_history = self._performance_history[-10000:]


# =============================================================================
# Cost Calculator
# =============================================================================

class CostCalculator:
    """
    Calculates cost savings comparing EHS to conventional pneumatic drills.
    """
    
    def __init__(self, config: Optional[EnergyConfig] = None):
        """Initialize cost calculator."""
        self.config = config or get_settings().energy
        
        # CO2 emission factors (kg CO2 per kWh)
        self.co2_factor_grid = 0.4  # Average grid electricity
        self.co2_factor_diesel = 2.7  # Diesel generator
    
    def calculate_savings(
        self,
        ehs_energy_kwh: float,
        drilling_hours: float,
        use_peak_rates: bool = False,
    ) -> CostComparison:
        """
        Calculate cost savings vs conventional pneumatic drill.
        
        Args:
            ehs_energy_kwh: Actual EHS energy consumption
            drilling_hours: Hours of drilling
            use_peak_rates: Whether to use peak electricity rates
            
        Returns:
            CostComparison with detailed breakdown.
        """
        # EHS cost
        rate = self.config.electricity_cost_per_kwh
        if use_peak_rates:
            rate *= self.config.peak_rate_multiplier
        
        ehs_cost = ehs_energy_kwh * rate
        
        # Pneumatic equivalent
        # Pneumatic drills are typically 25-30% efficient vs 85%+ for EHS
        pneumatic_power = self.config.pneumatic_power_kw
        pneumatic_efficiency = self.config.pneumatic_efficiency_percent / 100
        ehs_efficiency = self.config.ehs_efficiency_percent / 100
        
        # Calculate equivalent work done
        work_done = ehs_energy_kwh * ehs_efficiency
        
        # Energy needed by pneumatic to do same work
        pneumatic_energy = work_done / pneumatic_efficiency
        
        # Pneumatic typically uses diesel compressor
        # Diesel cost roughly $1.50/gallon, ~10kWh per gallon
        diesel_cost_per_kwh = 0.15  # Approximate
        pneumatic_cost = pneumatic_energy * diesel_cost_per_kwh
        
        # Savings
        savings_kwh = pneumatic_energy - ehs_energy_kwh
        savings_usd = pneumatic_cost - ehs_cost
        savings_percent = (savings_usd / pneumatic_cost * 100) if pneumatic_cost > 0 else 0
        
        # CO2 reduction
        ehs_co2 = ehs_energy_kwh * self.co2_factor_grid
        pneumatic_co2 = pneumatic_energy * self.co2_factor_diesel
        co2_reduction = pneumatic_co2 - ehs_co2
        
        return CostComparison(
            period_hours=drilling_hours,
            ehs_energy_kwh=ehs_energy_kwh,
            ehs_cost_usd=ehs_cost,
            pneumatic_energy_kwh=pneumatic_energy,
            pneumatic_cost_usd=pneumatic_cost,
            savings_kwh=savings_kwh,
            savings_usd=savings_usd,
            savings_percent=savings_percent,
            co2_reduction_kg=co2_reduction,
        )
    
    def project_annual_savings(
        self,
        daily_drilling_hours: float = 16.0,
        operating_days_per_year: int = 300,
        avg_power_kw: float = 150.0,
    ) -> dict[str, Any]:
        """
        Project annual savings for EHS vs pneumatic.
        
        Args:
            daily_drilling_hours: Average drilling hours per day
            operating_days_per_year: Operating days per year
            avg_power_kw: Average power consumption during drilling
            
        Returns:
            Dictionary with annual projections.
        """
        # Annual energy consumption
        annual_hours = daily_drilling_hours * operating_days_per_year
        annual_energy_kwh = annual_hours * avg_power_kw
        
        # Calculate savings
        comparison = self.calculate_savings(
            ehs_energy_kwh=annual_energy_kwh,
            drilling_hours=annual_hours,
        )
        
        # TCO components
        # EHS has higher capital but lower operating costs
        ehs_annual_maintenance = 15000  # Estimated
        pneumatic_annual_maintenance = 35000  # Higher due to wear
        
        maintenance_savings = pneumatic_annual_maintenance - ehs_annual_maintenance
        
        total_annual_savings = comparison.savings_usd + maintenance_savings
        
        return {
            "annual_drilling_hours": annual_hours,
            "annual_energy_kwh": annual_energy_kwh,
            "annual_energy_cost_ehs": comparison.ehs_cost_usd,
            "annual_energy_cost_pneumatic": comparison.pneumatic_cost_usd,
            "annual_energy_savings": comparison.savings_usd,
            "annual_maintenance_savings": maintenance_savings,
            "total_annual_savings": total_annual_savings,
            "annual_co2_reduction_kg": comparison.co2_reduction_kg,
            "annual_co2_reduction_tons": comparison.co2_reduction_kg / 1000,
            "payback_years": 200000 / total_annual_savings if total_annual_savings > 0 else float('inf'),  # Assuming $200k price difference
        }


# =============================================================================
# Energy Optimizer
# =============================================================================

class EnergyOptimizer:
    """
    Main energy optimization engine for EHS Simba system.
    
    Combines monitoring, analysis, and optimization recommendations.
    
    Example:
        >>> optimizer = EnergyOptimizer()
        >>> 
        >>> # Add power readings
        >>> reading = PowerReading(
        ...     timestamp=datetime.utcnow(),
        ...     power_kw=150.0,
        ...     voltage_v=480.0,
        ...     current_a=195.0,
        ...     power_factor=0.95,
        ...     state=DrillState.DRILLING
        ... )
        >>> anomaly = optimizer.add_power_reading(reading)
        >>> 
        >>> # Get optimization recommendations
        >>> recommendations = optimizer.get_recommendations()
    """
    
    def __init__(self, config: Optional[EnergyConfig] = None):
        """Initialize energy optimizer."""
        self.config = config or get_settings().energy
        
        self.power_monitor = PowerMonitor(self.config)
        self.rpm_optimizer = RPMOptimizer(self.config)
        self.cost_calculator = CostCalculator(self.config)
        
        # State tracking
        self._current_material: str = "unknown"
        self._current_rpm: float = 80.0
        self._current_penetration_rate: float = 0.5
        
        logger.info("EnergyOptimizer initialized")
    
    def add_power_reading(self, reading: PowerReading) -> Optional[str]:
        """
        Add power reading and check for anomalies.
        
        Args:
            reading: Power reading
            
        Returns:
            Anomaly message if detected.
        """
        return self.power_monitor.add_reading(reading)
    
    def update_drilling_state(
        self,
        material: str,
        rpm: float,
        penetration_rate: float,
    ) -> None:
        """Update current drilling state for optimization."""
        self._current_material = material
        self._current_rpm = rpm
        self._current_penetration_rate = penetration_rate
    
    def get_rpm_recommendation(self) -> dict[str, Any]:
        """Get RPM optimization recommendation."""
        current_power = self.power_monitor.get_current_power()
        
        return self.rpm_optimizer.get_optimal_rpm(
            material=self._current_material,
            current_rpm=self._current_rpm,
            current_power=current_power,
            penetration_rate=self._current_penetration_rate,
        )
    
    def get_energy_metrics(self, hours: float = 24.0) -> EnergyMetrics:
        """Get energy metrics for specified period."""
        return self.power_monitor.get_metrics(hours)
    
    def get_cost_comparison(self, hours: float = 24.0) -> CostComparison:
        """Get cost comparison with pneumatic drill."""
        metrics = self.get_energy_metrics(hours)
        
        return self.cost_calculator.calculate_savings(
            ehs_energy_kwh=metrics.total_energy_kwh,
            drilling_hours=metrics.drilling_hours,
        )
    
    def get_recommendations(self) -> list[OptimizationRecommendation]:
        """
        Generate energy optimization recommendations.
        
        Returns:
            List of recommendations sorted by priority.
        """
        recommendations = []
        
        # Get current metrics
        metrics = self.get_energy_metrics(hours=24.0)
        
        # 1. RPM optimization
        rpm_rec = self.get_rpm_recommendation()
        if rpm_rec["recommendation"] != "MAINTAIN":
            savings_kwh = rpm_rec["potential_savings_kw"] * 8  # 8-hour shift
            recommendations.append(OptimizationRecommendation(
                category="RPM Optimization",
                description=rpm_rec["reason"],
                potential_savings_kwh=savings_kwh,
                potential_savings_usd=savings_kwh * self.config.electricity_cost_per_kwh,
                priority=2,
                implementation_effort="Low",
                current_value=rpm_rec["current_rpm"],
                recommended_value=rpm_rec["target_rpm"],
            ))
        
        # 2. Idle time reduction
        if metrics.idle_hours > metrics.drilling_hours * 0.3:
            idle_ratio = metrics.idle_hours / max(metrics.drilling_hours, 1)
            target_idle_ratio = 0.2
            potential_idle_reduction = (idle_ratio - target_idle_ratio) * metrics.drilling_hours
            idle_power = self.config.idle_power_kw
            
            recommendations.append(OptimizationRecommendation(
                category="Idle Time Reduction",
                description=f"Idle time is {idle_ratio:.1%} of drilling time. Target: <20%",
                potential_savings_kwh=potential_idle_reduction * idle_power,
                potential_savings_usd=potential_idle_reduction * idle_power * self.config.electricity_cost_per_kwh,
                priority=1,
                implementation_effort="Medium",
                current_value=idle_ratio * 100,
                recommended_value=target_idle_ratio * 100,
            ))
        
        # 3. Peak demand management
        if metrics.peak_power_kw > self.config.peak_demand_threshold_kw:
            excess = metrics.peak_power_kw - self.config.peak_demand_threshold_kw
            # Demand charges can be significant
            demand_charge = excess * 15  # Rough estimate: $15/kW/month
            
            recommendations.append(OptimizationRecommendation(
                category="Peak Demand Management",
                description=f"Peak demand {metrics.peak_power_kw:.0f} kW exceeds threshold",
                potential_savings_kwh=0,  # Demand charges not energy-based
                potential_savings_usd=demand_charge / 30,  # Daily
                priority=2,
                implementation_effort="Medium",
                current_value=metrics.peak_power_kw,
                recommended_value=self.config.peak_demand_threshold_kw,
            ))
        
        # 4. Power factor correction
        # (Would need power factor data)
        
        # 5. Off-peak operation
        if metrics.cost_usd > 0:
            # Estimate savings from shifting to off-peak
            peak_premium = self.config.peak_rate_multiplier - 1.0
            estimated_peak_portion = 0.4  # Assume 40% during peak
            potential_savings = metrics.cost_usd * estimated_peak_portion * (peak_premium / self.config.peak_rate_multiplier)
            
            if potential_savings > 10:  # Only if meaningful
                recommendations.append(OptimizationRecommendation(
                    category="Off-Peak Operation",
                    description="Shift drilling to off-peak hours when possible",
                    potential_savings_kwh=0,
                    potential_savings_usd=potential_savings,
                    priority=3,
                    implementation_effort="High",
                ))
        
        # 6. Efficiency rating warning
        rating = self.power_monitor.get_efficiency_rating()
        if rating in [EfficiencyRating.POOR, EfficiencyRating.CRITICAL]:
            recommendations.append(OptimizationRecommendation(
                category="System Efficiency",
                description=f"Overall efficiency is {rating.value}. Check for mechanical issues.",
                potential_savings_kwh=metrics.total_energy_kwh * 0.1,
                potential_savings_usd=metrics.cost_usd * 0.1,
                priority=1,
                implementation_effort="High",
                current_value=metrics.efficiency_percent,
                recommended_value=80.0,
            ))
        
        # Sort by priority
        recommendations.sort(key=lambda r: r.priority)
        
        return recommendations
    
    def get_efficiency_summary(self) -> dict[str, Any]:
        """Get comprehensive efficiency summary."""
        metrics_24h = self.get_energy_metrics(hours=24.0)
        metrics_7d = self.get_energy_metrics(hours=168.0)
        
        comparison = self.get_cost_comparison(hours=24.0)
        annual_projection = self.cost_calculator.project_annual_savings(
            daily_drilling_hours=metrics_24h.drilling_hours,
            avg_power_kw=metrics_24h.avg_power_kw,
        )
        
        return {
            "current_power_kw": self.power_monitor.get_current_power(),
            "efficiency_rating": self.power_monitor.get_efficiency_rating().value,
            "metrics_24h": metrics_24h.to_dict(),
            "metrics_7d": metrics_7d.to_dict(),
            "vs_pneumatic_24h": comparison.to_dict(),
            "annual_projection": annual_projection,
            "recommendations_count": len(self.get_recommendations()),
        }


# =============================================================================
# Convenience Functions
# =============================================================================

_energy_optimizer: Optional[EnergyOptimizer] = None


def get_energy_optimizer() -> EnergyOptimizer:
    """
    Get or create the global energy optimizer.
    
    Returns:
        EnergyOptimizer: Singleton optimizer instance.
    """
    global _energy_optimizer
    if _energy_optimizer is None:
        _energy_optimizer = EnergyOptimizer()
    return _energy_optimizer


# Convenience exports
__all__ = [
    "DrillState",
    "EfficiencyRating",
    "PowerReading",
    "EnergyMetrics",
    "OptimizationRecommendation",
    "CostComparison",
    "PowerMonitor",
    "RPMOptimizer",
    "CostCalculator",
    "EnergyOptimizer",
    "get_energy_optimizer",
]

