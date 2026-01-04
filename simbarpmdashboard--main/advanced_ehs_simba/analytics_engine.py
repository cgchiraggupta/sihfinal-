"""
Advanced Analytics Module for Advanced EHS Simba Drill System.

This module provides:
- Drilling pattern analysis (material layers, voids, fractures)
- Hole deviation tracking and prediction
- Blast hole quality scoring
- Comparative analysis: EHS vs conventional drills
- ROI calculator with TCO breakdown

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
from scipy import signal, stats
from scipy.ndimage import gaussian_filter1d

from config import get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class GeologicalFeature(str, Enum):
    """Types of geological features detected during drilling."""
    LAYER_BOUNDARY = "layer_boundary"
    VOID = "void"
    FRACTURE = "fracture"
    WATER_BEARING = "water_bearing"
    FAULT_ZONE = "fault_zone"
    HARD_INCLUSION = "hard_inclusion"
    SOFT_INCLUSION = "soft_inclusion"


class HoleQualityGrade(str, Enum):
    """Blast hole quality grades."""
    A = "A"  # Excellent - optimal for blasting
    B = "B"  # Good - minor deviations
    C = "C"  # Acceptable - may affect blast
    D = "D"  # Poor - significant issues
    F = "F"  # Failed - requires redrilling


@dataclass
class MaterialLayer:
    """
    Detected material layer during drilling.
    
    Attributes:
        start_depth_m: Layer start depth
        end_depth_m: Layer end depth
        material_type: Predicted material type
        confidence: Prediction confidence
        avg_penetration_rate: Average penetration rate in layer
        avg_vibration: Average vibration level
        hardness_index: Relative hardness (0-10)
    """
    start_depth_m: float
    end_depth_m: float
    material_type: str
    confidence: float
    avg_penetration_rate: float
    avg_vibration: float
    hardness_index: float
    
    @property
    def thickness_m(self) -> float:
        """Layer thickness in meters."""
        return self.end_depth_m - self.start_depth_m
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_depth_m": self.start_depth_m,
            "end_depth_m": self.end_depth_m,
            "thickness_m": self.thickness_m,
            "material_type": self.material_type,
            "confidence": self.confidence,
            "avg_penetration_rate": self.avg_penetration_rate,
            "avg_vibration": self.avg_vibration,
            "hardness_index": self.hardness_index,
        }


@dataclass
class GeologicalAnomaly:
    """
    Detected geological anomaly.
    
    Attributes:
        depth_m: Depth of anomaly
        feature_type: Type of geological feature
        severity: Severity level (0-1)
        description: Human-readable description
        sensor_signatures: Sensor data that triggered detection
    """
    depth_m: float
    feature_type: GeologicalFeature
    severity: float
    description: str
    sensor_signatures: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "depth_m": self.depth_m,
            "feature_type": self.feature_type.value,
            "severity": self.severity,
            "description": self.description,
            "sensor_signatures": self.sensor_signatures,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class HoleDeviation:
    """
    Hole deviation measurement.
    
    Attributes:
        depth_m: Measurement depth
        azimuth_deg: Azimuth angle in degrees
        inclination_deg: Inclination from vertical
        deviation_m: Total deviation from planned path
        direction: Deviation direction (compass)
    """
    depth_m: float
    azimuth_deg: float
    inclination_deg: float
    deviation_m: float
    direction: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "depth_m": self.depth_m,
            "azimuth_deg": self.azimuth_deg,
            "inclination_deg": self.inclination_deg,
            "deviation_m": self.deviation_m,
            "direction": self.direction,
        }


@dataclass
class HoleQualityScore:
    """
    Blast hole quality assessment.
    
    Attributes:
        hole_id: Hole identifier
        overall_grade: Quality grade (A-F)
        overall_score: Numeric score (0-100)
        depth_score: Depth accuracy score
        deviation_score: Deviation score
        collar_score: Collar positioning score
        angle_score: Drilling angle score
        issues: List of identified issues
        recommendations: Improvement recommendations
    """
    hole_id: str
    overall_grade: HoleQualityGrade
    overall_score: float
    depth_score: float
    deviation_score: float
    collar_score: float
    angle_score: float
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hole_id": self.hole_id,
            "overall_grade": self.overall_grade.value,
            "overall_score": self.overall_score,
            "depth_score": self.depth_score,
            "deviation_score": self.deviation_score,
            "collar_score": self.collar_score,
            "angle_score": self.angle_score,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DrillPerformanceStats:
    """
    Drilling performance statistics.
    
    Attributes:
        total_holes: Total holes drilled
        total_meters: Total meters drilled
        avg_penetration_rate: Average penetration rate
        avg_hole_time_min: Average time per hole
        utilization_percent: Drill utilization rate
        quality_rate_percent: Holes meeting quality standards
    """
    total_holes: int
    total_meters: float
    avg_penetration_rate: float
    avg_hole_time_min: float
    utilization_percent: float
    quality_rate_percent: float
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_holes": self.total_holes,
            "total_meters": self.total_meters,
            "avg_penetration_rate": self.avg_penetration_rate,
            "avg_hole_time_min": self.avg_hole_time_min,
            "utilization_percent": self.utilization_percent,
            "quality_rate_percent": self.quality_rate_percent,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
        }


@dataclass
class ROIAnalysis:
    """
    ROI and TCO analysis for EHS vs conventional drills.
    
    Attributes:
        analysis_period_years: Analysis time period
        ehs_capital_cost: EHS purchase cost
        conventional_capital_cost: Conventional drill cost
        ehs_annual_operating: Annual operating cost for EHS
        conventional_annual_operating: Annual operating cost for conventional
        annual_savings: Annual cost savings
        simple_payback_years: Simple payback period
        npv: Net Present Value
        irr_percent: Internal Rate of Return
    """
    analysis_period_years: int
    ehs_capital_cost: float
    conventional_capital_cost: float
    ehs_annual_operating: float
    conventional_annual_operating: float
    annual_savings: float
    simple_payback_years: float
    npv: float
    irr_percent: float
    additional_benefits: dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analysis_period_years": self.analysis_period_years,
            "ehs_capital_cost": self.ehs_capital_cost,
            "conventional_capital_cost": self.conventional_capital_cost,
            "ehs_annual_operating": self.ehs_annual_operating,
            "conventional_annual_operating": self.conventional_annual_operating,
            "annual_savings": self.annual_savings,
            "simple_payback_years": self.simple_payback_years,
            "npv": self.npv,
            "irr_percent": self.irr_percent,
            "additional_benefits": self.additional_benefits,
        }


# =============================================================================
# Geological Analyzer
# =============================================================================

class GeologicalAnalyzer:
    """
    Analyzes drilling data to detect geological features.
    
    Uses sensor patterns to identify:
    - Material layer boundaries
    - Voids and cavities
    - Fracture zones
    - Water-bearing formations
    """
    
    def __init__(self):
        """Initialize geological analyzer."""
        # Detection thresholds
        self._void_resistance_drop = 0.5  # 50% drop indicates void
        self._fracture_vibration_spike = 2.0  # 2x increase
        self._layer_change_threshold = 0.3  # 30% change in parameters
        
        # Current analysis state
        self._depth_history: list[float] = []
        self._resistance_history: list[float] = []
        self._vibration_history: list[float] = []
        self._material_history: list[str] = []
        
        logger.info("GeologicalAnalyzer initialized")
    
    def add_data_point(
        self,
        depth: float,
        resistance: float,
        vibration: float,
        material: str,
    ) -> Optional[GeologicalAnomaly]:
        """
        Add drilling data point and check for anomalies.
        
        Args:
            depth: Current depth in meters
            resistance: Drilling resistance (proportional to current)
            vibration: Vibration level in g
            material: Predicted material type
            
        Returns:
            GeologicalAnomaly if detected, None otherwise.
        """
        self._depth_history.append(depth)
        self._resistance_history.append(resistance)
        self._vibration_history.append(vibration)
        self._material_history.append(material)
        
        # Keep last 1000 points
        max_history = 1000
        if len(self._depth_history) > max_history:
            self._depth_history = self._depth_history[-max_history:]
            self._resistance_history = self._resistance_history[-max_history:]
            self._vibration_history = self._vibration_history[-max_history:]
            self._material_history = self._material_history[-max_history:]
        
        # Need enough history for analysis
        if len(self._depth_history) < 20:
            return None
        
        # Check for anomalies
        anomaly = self._detect_anomaly()
        return anomaly
    
    def _detect_anomaly(self) -> Optional[GeologicalAnomaly]:
        """Detect geological anomalies from recent data."""
        # Get recent values
        recent_resistance = np.array(self._resistance_history[-20:])
        recent_vibration = np.array(self._vibration_history[-20:])
        current_depth = self._depth_history[-1]
        
        # Baseline from earlier data
        baseline_resistance = np.mean(self._resistance_history[-50:-20]) if len(self._resistance_history) > 50 else np.mean(recent_resistance)
        baseline_vibration = np.mean(self._vibration_history[-50:-20]) if len(self._vibration_history) > 50 else np.mean(recent_vibration)
        
        # Check for void (sudden resistance drop)
        if baseline_resistance > 0:
            resistance_drop = (baseline_resistance - recent_resistance[-1]) / baseline_resistance
            if resistance_drop > self._void_resistance_drop:
                return GeologicalAnomaly(
                    depth_m=current_depth,
                    feature_type=GeologicalFeature.VOID,
                    severity=min(1.0, resistance_drop),
                    description=f"Possible void detected - {resistance_drop:.0%} resistance drop",
                    sensor_signatures={
                        "resistance_drop": resistance_drop,
                        "current_resistance": recent_resistance[-1],
                        "baseline_resistance": baseline_resistance,
                    },
                )
        
        # Check for fracture (vibration spike with resistance variation)
        if baseline_vibration > 0:
            vibration_increase = recent_vibration[-1] / baseline_vibration
            resistance_variance = np.std(recent_resistance[-10:]) / max(np.mean(recent_resistance[-10:]), 1)
            
            if vibration_increase > self._fracture_vibration_spike and resistance_variance > 0.2:
                return GeologicalAnomaly(
                    depth_m=current_depth,
                    feature_type=GeologicalFeature.FRACTURE,
                    severity=min(1.0, (vibration_increase - 1) / 2),
                    description=f"Fracture zone - {vibration_increase:.1f}x vibration increase",
                    sensor_signatures={
                        "vibration_increase": vibration_increase,
                        "resistance_variance": resistance_variance,
                    },
                )
        
        # Check for hard inclusion
        if baseline_resistance > 0:
            resistance_increase = (recent_resistance[-1] - baseline_resistance) / baseline_resistance
            if resistance_increase > 0.5:
                return GeologicalAnomaly(
                    depth_m=current_depth,
                    feature_type=GeologicalFeature.HARD_INCLUSION,
                    severity=min(1.0, resistance_increase / 2),
                    description=f"Hard inclusion - {resistance_increase:.0%} resistance increase",
                    sensor_signatures={
                        "resistance_increase": resistance_increase,
                    },
                )
        
        return None
    
    def analyze_layers(
        self,
        depth_data: list[float],
        material_predictions: list[str],
        penetration_rates: list[float],
        vibration_data: list[float],
    ) -> list[MaterialLayer]:
        """
        Analyze drilling data to identify material layers.
        
        Args:
            depth_data: Depth measurements
            material_predictions: Material predictions at each depth
            penetration_rates: Penetration rates
            vibration_data: Vibration measurements
            
        Returns:
            List of identified material layers.
        """
        if len(depth_data) < 10:
            return []
        
        layers = []
        current_material = material_predictions[0]
        layer_start_idx = 0
        
        # Find layer boundaries
        for i in range(1, len(material_predictions)):
            material_changed = material_predictions[i] != current_material
            
            # Also detect layers from sensor data changes
            if i >= 5:
                pen_rate_change = abs(
                    np.mean(penetration_rates[i-5:i]) - 
                    np.mean(penetration_rates[max(0, i-10):i-5])
                ) / max(np.mean(penetration_rates[max(0, i-10):i-5]), 0.01)
                
                if pen_rate_change > self._layer_change_threshold:
                    material_changed = True
            
            if material_changed or i == len(material_predictions) - 1:
                # Create layer record
                layer_depths = depth_data[layer_start_idx:i]
                layer_pen_rates = penetration_rates[layer_start_idx:i]
                layer_vibration = vibration_data[layer_start_idx:i]
                
                if layer_depths:
                    layer = MaterialLayer(
                        start_depth_m=layer_depths[0],
                        end_depth_m=layer_depths[-1],
                        material_type=current_material,
                        confidence=0.8,  # Would come from ML predictions
                        avg_penetration_rate=np.mean(layer_pen_rates),
                        avg_vibration=np.mean(layer_vibration),
                        hardness_index=self._estimate_hardness(
                            np.mean(layer_pen_rates),
                            np.mean(layer_vibration)
                        ),
                    )
                    layers.append(layer)
                
                current_material = material_predictions[i]
                layer_start_idx = i
        
        return layers
    
    def _estimate_hardness(
        self,
        penetration_rate: float,
        vibration: float,
    ) -> float:
        """Estimate material hardness from drilling parameters."""
        # Lower penetration + higher vibration = harder material
        # Normalize to 0-10 scale
        
        # Penetration rate typically 0.1-2.0 m/min
        pen_factor = 1.0 - np.clip(penetration_rate / 2.0, 0, 1)
        
        # Vibration typically 0.5-5.0 g
        vib_factor = np.clip((vibration - 0.5) / 4.5, 0, 1)
        
        hardness = (pen_factor * 0.6 + vib_factor * 0.4) * 10
        return float(hardness)


# =============================================================================
# Hole Quality Analyzer
# =============================================================================

class HoleQualityAnalyzer:
    """
    Analyzes and scores blast hole quality.
    
    Evaluates:
    - Depth accuracy
    - Hole deviation
    - Collar positioning
    - Drilling angle
    """
    
    def __init__(self):
        """Initialize hole quality analyzer."""
        # Quality thresholds
        self._depth_tolerance_m = 0.3  # ±30cm from target
        self._deviation_tolerance_m = 0.5  # Max 50cm deviation
        self._collar_tolerance_m = 0.1  # ±10cm collar position
        self._angle_tolerance_deg = 2.0  # ±2° from planned angle
        
        logger.info("HoleQualityAnalyzer initialized")
    
    def score_hole(
        self,
        hole_id: str,
        target_depth_m: float,
        actual_depth_m: float,
        max_deviation_m: float,
        collar_offset_m: float,
        angle_deviation_deg: float,
        deviations: Optional[list[HoleDeviation]] = None,
    ) -> HoleQualityScore:
        """
        Calculate comprehensive hole quality score.
        
        Args:
            hole_id: Hole identifier
            target_depth_m: Planned depth
            actual_depth_m: Achieved depth
            max_deviation_m: Maximum deviation from plan
            collar_offset_m: Collar position offset
            angle_deviation_deg: Angle deviation from plan
            deviations: List of deviation measurements (optional)
            
        Returns:
            HoleQualityScore with detailed assessment.
        """
        issues = []
        recommendations = []
        
        # Depth score (0-100)
        depth_error = abs(actual_depth_m - target_depth_m)
        if depth_error <= self._depth_tolerance_m:
            depth_score = 100 - (depth_error / self._depth_tolerance_m) * 20
        else:
            depth_score = max(0, 80 - (depth_error - self._depth_tolerance_m) * 40)
            issues.append(f"Depth deviation: {depth_error:.2f}m from target")
            recommendations.append("Verify depth measurement system calibration")
        
        # Deviation score (0-100)
        if max_deviation_m <= self._deviation_tolerance_m:
            deviation_score = 100 - (max_deviation_m / self._deviation_tolerance_m) * 20
        else:
            deviation_score = max(0, 80 - (max_deviation_m - self._deviation_tolerance_m) * 60)
            issues.append(f"Excessive deviation: {max_deviation_m:.2f}m")
            recommendations.append("Check drill alignment and guide system")
        
        # Collar score (0-100)
        if collar_offset_m <= self._collar_tolerance_m:
            collar_score = 100 - (collar_offset_m / self._collar_tolerance_m) * 20
        else:
            collar_score = max(0, 80 - (collar_offset_m - self._collar_tolerance_m) * 100)
            issues.append(f"Collar offset: {collar_offset_m:.2f}m")
            recommendations.append("Improve collar positioning procedure")
        
        # Angle score (0-100)
        if angle_deviation_deg <= self._angle_tolerance_deg:
            angle_score = 100 - (angle_deviation_deg / self._angle_tolerance_deg) * 20
        else:
            angle_score = max(0, 80 - (angle_deviation_deg - self._angle_tolerance_deg) * 20)
            issues.append(f"Angle deviation: {angle_deviation_deg:.1f}°")
            recommendations.append("Check drill mast alignment")
        
        # Overall score (weighted average)
        overall_score = (
            depth_score * 0.30 +
            deviation_score * 0.35 +
            collar_score * 0.15 +
            angle_score * 0.20
        )
        
        # Determine grade
        if overall_score >= 90:
            grade = HoleQualityGrade.A
        elif overall_score >= 80:
            grade = HoleQualityGrade.B
        elif overall_score >= 70:
            grade = HoleQualityGrade.C
        elif overall_score >= 50:
            grade = HoleQualityGrade.D
        else:
            grade = HoleQualityGrade.F
            recommendations.append("Consider redrilling this hole")
        
        return HoleQualityScore(
            hole_id=hole_id,
            overall_grade=grade,
            overall_score=overall_score,
            depth_score=depth_score,
            deviation_score=deviation_score,
            collar_score=collar_score,
            angle_score=angle_score,
            issues=issues,
            recommendations=recommendations,
        )
    
    def analyze_pattern(
        self,
        hole_scores: list[HoleQualityScore],
    ) -> dict[str, Any]:
        """
        Analyze quality patterns across multiple holes.
        
        Args:
            hole_scores: List of individual hole scores
            
        Returns:
            Pattern analysis results.
        """
        if not hole_scores:
            return {"error": "No holes to analyze"}
        
        scores = [h.overall_score for h in hole_scores]
        grades = [h.overall_grade.value for h in hole_scores]
        
        # Grade distribution
        grade_counts = {}
        for grade in HoleQualityGrade:
            grade_counts[grade.value] = grades.count(grade.value)
        
        # Quality rate
        passing_grades = [HoleQualityGrade.A.value, HoleQualityGrade.B.value, HoleQualityGrade.C.value]
        quality_rate = sum(1 for g in grades if g in passing_grades) / len(grades) * 100
        
        # Common issues
        all_issues = []
        for h in hole_scores:
            all_issues.extend(h.issues)
        
        issue_counts = {}
        for issue in all_issues:
            # Simplify issue to category
            if "Depth" in issue:
                category = "Depth accuracy"
            elif "deviation" in issue.lower():
                category = "Hole deviation"
            elif "Collar" in issue:
                category = "Collar positioning"
            elif "Angle" in issue:
                category = "Drilling angle"
            else:
                category = "Other"
            
            issue_counts[category] = issue_counts.get(category, 0) + 1
        
        return {
            "total_holes": len(hole_scores),
            "avg_score": np.mean(scores),
            "std_score": np.std(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "grade_distribution": grade_counts,
            "quality_rate_percent": quality_rate,
            "common_issues": issue_counts,
            "needs_improvement": list(issue_counts.keys())[:3] if issue_counts else [],
        }


# =============================================================================
# Deviation Tracker
# =============================================================================

class DeviationTracker:
    """
    Tracks and predicts hole deviation during drilling.
    
    Uses sensor data to estimate current deviation and
    predict future path.
    """
    
    def __init__(self):
        """Initialize deviation tracker."""
        # Deviation history
        self._measurements: list[HoleDeviation] = []
        
        # Prediction model coefficients (simplified)
        self._drift_rate_x = 0.0  # degrees per meter
        self._drift_rate_y = 0.0
        
        logger.info("DeviationTracker initialized")
    
    def add_measurement(
        self,
        depth_m: float,
        azimuth_deg: float,
        inclination_deg: float,
    ) -> HoleDeviation:
        """
        Add deviation measurement and calculate deviation.
        
        Args:
            depth_m: Current depth
            azimuth_deg: Azimuth (compass direction)
            inclination_deg: Inclination from vertical
            
        Returns:
            HoleDeviation with calculated offset.
        """
        # Calculate horizontal deviation from vertical
        # For inclined holes, this would be from the planned path
        
        # Horizontal offset calculation (simplified)
        # Real calculation would use the full survey path
        horizontal_offset = depth_m * np.sin(np.radians(inclination_deg))
        
        # Direction (simplified to compass quadrant)
        if azimuth_deg < 45 or azimuth_deg >= 315:
            direction = "N"
        elif azimuth_deg < 135:
            direction = "E"
        elif azimuth_deg < 225:
            direction = "S"
        else:
            direction = "W"
        
        deviation = HoleDeviation(
            depth_m=depth_m,
            azimuth_deg=azimuth_deg,
            inclination_deg=inclination_deg,
            deviation_m=horizontal_offset,
            direction=direction,
        )
        
        self._measurements.append(deviation)
        
        # Update drift prediction if we have enough data
        if len(self._measurements) >= 3:
            self._update_drift_model()
        
        return deviation
    
    def _update_drift_model(self) -> None:
        """Update drift prediction model from measurements."""
        if len(self._measurements) < 3:
            return
        
        # Simple linear regression on inclination vs depth
        depths = np.array([m.depth_m for m in self._measurements])
        inclinations = np.array([m.inclination_deg for m in self._measurements])
        
        if len(depths) > 1 and depths[-1] - depths[0] > 0:
            self._drift_rate_y = (inclinations[-1] - inclinations[0]) / (depths[-1] - depths[0])
    
    def predict_deviation(
        self,
        target_depth_m: float,
    ) -> dict[str, float]:
        """
        Predict deviation at target depth.
        
        Args:
            target_depth_m: Depth to predict deviation for
            
        Returns:
            Dictionary with predicted deviation values.
        """
        if not self._measurements:
            return {
                "predicted_deviation_m": 0.0,
                "predicted_inclination_deg": 0.0,
                "confidence": 0.0,
            }
        
        last = self._measurements[-1]
        depth_diff = target_depth_m - last.depth_m
        
        # Predict inclination at target depth
        predicted_inclination = last.inclination_deg + self._drift_rate_y * depth_diff
        
        # Predict total deviation
        # Integration of sin(inclination) over depth
        avg_inclination = (last.inclination_deg + predicted_inclination) / 2
        additional_deviation = depth_diff * np.sin(np.radians(avg_inclination))
        predicted_deviation = last.deviation_m + additional_deviation
        
        # Confidence decreases with prediction distance
        confidence = max(0.3, 1.0 - (depth_diff / 20))
        
        return {
            "predicted_deviation_m": predicted_deviation,
            "predicted_inclination_deg": predicted_inclination,
            "confidence": confidence,
            "drift_rate_deg_per_m": self._drift_rate_y,
        }
    
    def get_max_deviation(self) -> float:
        """Get maximum deviation recorded."""
        if not self._measurements:
            return 0.0
        return max(m.deviation_m for m in self._measurements)
    
    def clear(self) -> None:
        """Clear measurements for new hole."""
        self._measurements = []
        self._drift_rate_x = 0.0
        self._drift_rate_y = 0.0


# =============================================================================
# ROI Calculator
# =============================================================================

class ROICalculator:
    """
    Calculates ROI and TCO for EHS vs conventional drills.
    """
    
    def __init__(self):
        """Initialize ROI calculator."""
        # Default cost assumptions
        self._ehs_capital = 850000  # USD
        self._conventional_capital = 650000  # USD
        
        # Annual operating costs
        self._ehs_energy_annual = 50000
        self._ehs_maintenance_annual = 25000
        self._ehs_consumables_annual = 40000
        
        self._conventional_energy_annual = 120000
        self._conventional_maintenance_annual = 45000
        self._conventional_consumables_annual = 60000
        
        # Productivity
        self._ehs_productivity_factor = 1.15  # 15% more productive
        
        logger.info("ROICalculator initialized")
    
    def calculate_roi(
        self,
        analysis_period_years: int = 10,
        discount_rate: float = 0.08,
        ehs_capital: Optional[float] = None,
        conventional_capital: Optional[float] = None,
        annual_operating_hours: int = 4000,
    ) -> ROIAnalysis:
        """
        Calculate comprehensive ROI analysis.
        
        Args:
            analysis_period_years: Analysis time horizon
            discount_rate: Discount rate for NPV
            ehs_capital: EHS capital cost (optional)
            conventional_capital: Conventional capital cost (optional)
            annual_operating_hours: Annual operating hours
            
        Returns:
            ROIAnalysis with detailed breakdown.
        """
        ehs_cap = ehs_capital or self._ehs_capital
        conv_cap = conventional_capital or self._conventional_capital
        
        # Scale operating costs by utilization
        utilization_factor = annual_operating_hours / 4000
        
        ehs_annual = (
            self._ehs_energy_annual +
            self._ehs_maintenance_annual +
            self._ehs_consumables_annual
        ) * utilization_factor
        
        conv_annual = (
            self._conventional_energy_annual +
            self._conventional_maintenance_annual +
            self._conventional_consumables_annual
        ) * utilization_factor
        
        # Annual savings
        annual_savings = conv_annual - ehs_annual
        
        # Add productivity benefit
        # Assume $50/meter margin, 0.5 m/min avg, productivity difference
        productivity_value = (
            50 * 0.5 * 60 * annual_operating_hours *
            (self._ehs_productivity_factor - 1.0)
        )
        annual_savings += productivity_value
        
        # Capital difference (incremental investment)
        incremental_capital = ehs_cap - conv_cap
        
        # Simple payback
        simple_payback = incremental_capital / annual_savings if annual_savings > 0 else float('inf')
        
        # NPV calculation
        npv = -incremental_capital
        for year in range(1, analysis_period_years + 1):
            npv += annual_savings / ((1 + discount_rate) ** year)
        
        # IRR calculation (simplified)
        # Find rate where NPV = 0
        irr = self._calculate_irr(incremental_capital, annual_savings, analysis_period_years)
        
        # Additional benefits
        additional_benefits = {
            "productivity_value_annual": productivity_value,
            "co2_reduction_value_annual": 5000,  # Assume carbon credit value
            "safety_improvement_value": 10000,
            "noise_reduction_value": 3000,
        }
        
        return ROIAnalysis(
            analysis_period_years=analysis_period_years,
            ehs_capital_cost=ehs_cap,
            conventional_capital_cost=conv_cap,
            ehs_annual_operating=ehs_annual,
            conventional_annual_operating=conv_annual,
            annual_savings=annual_savings,
            simple_payback_years=simple_payback,
            npv=npv,
            irr_percent=irr * 100,
            additional_benefits=additional_benefits,
        )
    
    def _calculate_irr(
        self,
        investment: float,
        annual_cashflow: float,
        years: int,
    ) -> float:
        """Calculate IRR using bisection method."""
        if annual_cashflow <= 0:
            return 0.0
        
        def npv_at_rate(rate):
            npv = -investment
            for year in range(1, years + 1):
                npv += annual_cashflow / ((1 + rate) ** year)
            return npv
        
        # Bisection search
        low, high = 0.0, 1.0
        
        for _ in range(50):
            mid = (low + high) / 2
            npv = npv_at_rate(mid)
            
            if abs(npv) < 100:  # Close enough
                return mid
            elif npv > 0:
                low = mid
            else:
                high = mid
        
        return mid
    
    def generate_tco_breakdown(
        self,
        years: int = 10,
    ) -> dict[str, Any]:
        """
        Generate detailed TCO breakdown comparison.
        
        Args:
            years: Analysis period
            
        Returns:
            Dictionary with TCO breakdown.
        """
        # EHS TCO
        ehs_capital = self._ehs_capital
        ehs_operating_total = (
            self._ehs_energy_annual +
            self._ehs_maintenance_annual +
            self._ehs_consumables_annual
        ) * years
        ehs_tco = ehs_capital + ehs_operating_total
        
        # Conventional TCO
        conv_capital = self._conventional_capital
        conv_operating_total = (
            self._conventional_energy_annual +
            self._conventional_maintenance_annual +
            self._conventional_consumables_annual
        ) * years
        conv_tco = conv_capital + conv_operating_total
        
        return {
            "analysis_years": years,
            "ehs": {
                "capital": ehs_capital,
                "energy": self._ehs_energy_annual * years,
                "maintenance": self._ehs_maintenance_annual * years,
                "consumables": self._ehs_consumables_annual * years,
                "total_tco": ehs_tco,
                "annual_avg": ehs_tco / years,
            },
            "conventional": {
                "capital": conv_capital,
                "energy": self._conventional_energy_annual * years,
                "maintenance": self._conventional_maintenance_annual * years,
                "consumables": self._conventional_consumables_annual * years,
                "total_tco": conv_tco,
                "annual_avg": conv_tco / years,
            },
            "savings": {
                "total": conv_tco - ehs_tco,
                "percent": (conv_tco - ehs_tco) / conv_tco * 100,
            },
        }


# =============================================================================
# Main Analytics Engine
# =============================================================================

class AnalyticsEngine:
    """
    Main analytics engine for EHS Simba system.
    
    Integrates all analytical components for comprehensive
    drilling analysis and optimization.
    
    Example:
        >>> engine = AnalyticsEngine()
        >>> 
        >>> # Analyze drilling pattern
        >>> layers = engine.analyze_material_layers(depths, materials, rates, vibrations)
        >>> 
        >>> # Score hole quality
        >>> quality = engine.score_hole("HOLE-001", 30.0, 29.8, 0.3, 0.05, 1.2)
        >>> 
        >>> # Calculate ROI
        >>> roi = engine.calculate_roi(years=10)
    """
    
    def __init__(self):
        """Initialize analytics engine."""
        self.geological_analyzer = GeologicalAnalyzer()
        self.hole_quality_analyzer = HoleQualityAnalyzer()
        self.deviation_tracker = DeviationTracker()
        self.roi_calculator = ROICalculator()
        
        # Performance tracking
        self._hole_scores: list[HoleQualityScore] = []
        self._anomalies: list[GeologicalAnomaly] = []
        self._performance_history: list[DrillPerformanceStats] = []
        
        logger.info("AnalyticsEngine initialized")
    
    def process_drilling_data(
        self,
        depth: float,
        resistance: float,
        vibration: float,
        material: str,
    ) -> Optional[GeologicalAnomaly]:
        """
        Process real-time drilling data for anomaly detection.
        
        Args:
            depth: Current depth
            resistance: Drilling resistance
            vibration: Vibration level
            material: Predicted material
            
        Returns:
            GeologicalAnomaly if detected.
        """
        anomaly = self.geological_analyzer.add_data_point(
            depth, resistance, vibration, material
        )
        
        if anomaly:
            self._anomalies.append(anomaly)
        
        return anomaly
    
    def analyze_material_layers(
        self,
        depth_data: list[float],
        material_predictions: list[str],
        penetration_rates: list[float],
        vibration_data: list[float],
    ) -> list[MaterialLayer]:
        """
        Analyze drilling data to identify material layers.
        
        Returns list of identified layers.
        """
        return self.geological_analyzer.analyze_layers(
            depth_data, material_predictions, penetration_rates, vibration_data
        )
    
    def score_hole(
        self,
        hole_id: str,
        target_depth_m: float,
        actual_depth_m: float,
        max_deviation_m: float,
        collar_offset_m: float,
        angle_deviation_deg: float,
    ) -> HoleQualityScore:
        """
        Score a completed blast hole.
        
        Returns comprehensive quality score.
        """
        score = self.hole_quality_analyzer.score_hole(
            hole_id=hole_id,
            target_depth_m=target_depth_m,
            actual_depth_m=actual_depth_m,
            max_deviation_m=max_deviation_m,
            collar_offset_m=collar_offset_m,
            angle_deviation_deg=angle_deviation_deg,
        )
        
        self._hole_scores.append(score)
        return score
    
    def add_deviation_measurement(
        self,
        depth_m: float,
        azimuth_deg: float,
        inclination_deg: float,
    ) -> HoleDeviation:
        """Add deviation measurement during drilling."""
        return self.deviation_tracker.add_measurement(
            depth_m, azimuth_deg, inclination_deg
        )
    
    def predict_final_deviation(
        self,
        target_depth_m: float,
    ) -> dict[str, float]:
        """Predict final hole deviation at target depth."""
        return self.deviation_tracker.predict_deviation(target_depth_m)
    
    def calculate_roi(
        self,
        years: int = 10,
        discount_rate: float = 0.08,
    ) -> ROIAnalysis:
        """Calculate ROI analysis."""
        return self.roi_calculator.calculate_roi(
            analysis_period_years=years,
            discount_rate=discount_rate,
        )
    
    def get_tco_breakdown(self, years: int = 10) -> dict[str, Any]:
        """Get TCO breakdown comparison."""
        return self.roi_calculator.generate_tco_breakdown(years)
    
    def get_quality_summary(self) -> dict[str, Any]:
        """Get summary of hole quality across all scored holes."""
        if not self._hole_scores:
            return {"error": "No holes scored yet"}
        
        return self.hole_quality_analyzer.analyze_pattern(self._hole_scores)
    
    def get_anomaly_summary(self) -> dict[str, Any]:
        """Get summary of detected geological anomalies."""
        if not self._anomalies:
            return {
                "total_anomalies": 0,
                "by_type": {},
            }
        
        # Count by type
        type_counts = {}
        for anomaly in self._anomalies:
            type_name = anomaly.feature_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            "total_anomalies": len(self._anomalies),
            "by_type": type_counts,
            "most_recent": self._anomalies[-1].to_dict() if self._anomalies else None,
            "high_severity": [
                a.to_dict() for a in self._anomalies
                if a.severity > 0.7
            ],
        }
    
    def new_hole(self) -> None:
        """Reset state for new hole."""
        self.deviation_tracker.clear()
    
    def get_performance_kpis(
        self,
        total_holes: int,
        total_meters: float,
        total_drilling_hours: float,
        total_available_hours: float,
    ) -> DrillPerformanceStats:
        """
        Calculate drilling performance KPIs.
        
        Args:
            total_holes: Total holes drilled in period
            total_meters: Total meters drilled
            total_drilling_hours: Active drilling hours
            total_available_hours: Total available hours
            
        Returns:
            DrillPerformanceStats with calculated KPIs.
        """
        # Calculate KPIs
        avg_penetration = total_meters / total_drilling_hours if total_drilling_hours > 0 else 0
        avg_hole_time = total_drilling_hours * 60 / total_holes if total_holes > 0 else 0
        utilization = total_drilling_hours / total_available_hours * 100 if total_available_hours > 0 else 0
        
        # Quality rate from scored holes
        if self._hole_scores:
            passing = sum(
                1 for s in self._hole_scores
                if s.overall_grade in [HoleQualityGrade.A, HoleQualityGrade.B, HoleQualityGrade.C]
            )
            quality_rate = passing / len(self._hole_scores) * 100
        else:
            quality_rate = 100.0  # Assume good if no data
        
        stats = DrillPerformanceStats(
            total_holes=total_holes,
            total_meters=total_meters,
            avg_penetration_rate=avg_penetration,
            avg_hole_time_min=avg_hole_time,
            utilization_percent=utilization,
            quality_rate_percent=quality_rate,
        )
        
        self._performance_history.append(stats)
        return stats


# =============================================================================
# Convenience Functions
# =============================================================================

_analytics_engine: Optional[AnalyticsEngine] = None


def get_analytics_engine() -> AnalyticsEngine:
    """
    Get or create the global analytics engine.
    
    Returns:
        AnalyticsEngine: Singleton engine instance.
    """
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine


# Convenience exports
__all__ = [
    "GeologicalFeature",
    "HoleQualityGrade",
    "MaterialLayer",
    "GeologicalAnomaly",
    "HoleDeviation",
    "HoleQualityScore",
    "DrillPerformanceStats",
    "ROIAnalysis",
    "GeologicalAnalyzer",
    "HoleQualityAnalyzer",
    "DeviationTracker",
    "ROICalculator",
    "AnalyticsEngine",
    "get_analytics_engine",
]

