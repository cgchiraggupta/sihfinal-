"""
Unit tests for Maintenance Predictor module.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from maintenance_predictor import (
    ComponentType,
    HealthStatus,
    MaintenanceType,
    MaintenancePriority,
    ComponentHealth,
    MaintenanceTask,
    WeibullParameters,
    WeibullAnalyzer,
    DrillBitAnalyzer,
    HydraulicSystemAnalyzer,
    BearingAnalyzer,
    MaintenanceScheduler,
    PredictiveMaintenanceEngine,
)


class TestWeibullParameters:
    """Tests for WeibullParameters class."""
    
    def test_reliability_at_zero(self):
        """Test reliability at time zero."""
        params = WeibullParameters(shape=2.0, scale_hours=1000.0)
        
        assert params.reliability(0) == 1.0
    
    def test_reliability_decreases(self):
        """Test that reliability decreases over time."""
        params = WeibullParameters(shape=2.0, scale_hours=1000.0)
        
        r1 = params.reliability(100)
        r2 = params.reliability(500)
        r3 = params.reliability(1000)
        
        assert r1 > r2 > r3
    
    def test_reliability_at_scale(self):
        """Test reliability at scale parameter (characteristic life)."""
        params = WeibullParameters(shape=2.0, scale_hours=1000.0)
        
        # At scale parameter, reliability should be ~36.8% (e^-1)
        r = params.reliability(1000)
        
        assert 0.36 < r < 0.38
    
    def test_failure_probability_complement(self):
        """Test that failure probability is complement of reliability."""
        params = WeibullParameters(shape=2.0, scale_hours=1000.0)
        
        for t in [100, 500, 1000]:
            r = params.reliability(t)
            f = params.failure_probability(t)
            
            assert abs(r + f - 1.0) < 1e-10
    
    def test_hazard_rate_increasing(self):
        """Test that hazard rate increases for shape > 1."""
        params = WeibullParameters(shape=2.5, scale_hours=1000.0)
        
        h1 = params.hazard_rate(100)
        h2 = params.hazard_rate(500)
        h3 = params.hazard_rate(800)
        
        assert h1 < h2 < h3
    
    def test_mean_life(self):
        """Test mean life calculation."""
        params = WeibullParameters(shape=2.0, scale_hours=1000.0)
        
        mean = params.mean_life()
        
        # Mean should be close to scale for shape near 2
        assert 800 < mean < 1000
    
    def test_percentile_life(self):
        """Test B10 life calculation."""
        params = WeibullParameters(shape=2.0, scale_hours=1000.0)
        
        b10 = params.percentile_life(0.10)  # 10% failure
        
        # B10 should be less than scale
        assert b10 < params.scale_hours
        
        # Verify by checking reliability at B10
        r = params.reliability(b10)
        assert abs(r - 0.90) < 0.01


class TestWeibullAnalyzer:
    """Tests for WeibullAnalyzer class."""
    
    def test_default_params(self):
        """Test getting default parameters."""
        analyzer = WeibullAnalyzer()
        
        params = analyzer.get_default_params(ComponentType.DRILL_BIT)
        
        assert params.shape > 0
        assert params.scale_hours > 0
    
    def test_fit_from_failures(self):
        """Test fitting Weibull from failure data."""
        analyzer = WeibullAnalyzer()
        
        # Generate some failure times
        failure_times = [400, 450, 500, 520, 600, 650, 700, 750, 800, 850]
        
        params = analyzer.fit_from_failures(failure_times)
        
        assert params.shape > 0
        assert params.scale_hours > 0
    
    def test_calculate_rul(self):
        """Test RUL calculation."""
        analyzer = WeibullAnalyzer()
        params = WeibullParameters(shape=2.0, scale_hours=500.0)
        
        rul = analyzer.calculate_rul(params, current_hours=200)
        
        assert rul > 0
        assert rul < params.scale_hours
    
    def test_rul_decreases_with_usage(self):
        """Test that RUL decreases with operating hours."""
        analyzer = WeibullAnalyzer()
        params = WeibullParameters(shape=2.0, scale_hours=500.0)
        
        rul_100 = analyzer.calculate_rul(params, current_hours=100)
        rul_200 = analyzer.calculate_rul(params, current_hours=200)
        rul_300 = analyzer.calculate_rul(params, current_hours=300)
        
        assert rul_100 > rul_200 > rul_300


class TestDrillBitAnalyzer:
    """Tests for DrillBitAnalyzer class."""
    
    def test_analyze_new_bit(self):
        """Test analysis of a new drill bit."""
        analyzer = DrillBitAnalyzer()
        
        health = analyzer.analyze(
            operating_hours=10,
            vibration_history=[1.0, 1.1, 1.0, 0.9, 1.1],
            current_vibration=1.0,
        )
        
        assert health.health_score > 80
        assert health.status == HealthStatus.EXCELLENT
    
    def test_analyze_worn_bit(self):
        """Test analysis of a worn drill bit."""
        analyzer = DrillBitAnalyzer()
        
        health = analyzer.analyze(
            operating_hours=450,
            vibration_history=[3.0, 3.2, 3.5, 3.8, 4.0] * 10,
            current_vibration=4.0,
        )
        
        assert health.health_score < 50
        assert health.status in [HealthStatus.POOR, HealthStatus.CRITICAL]
        assert len(health.recommendations) > 0
    
    def test_material_wear_factors(self):
        """Test that harder materials increase wear."""
        analyzer = DrillBitAnalyzer()
        
        # Same hours, different materials
        health_soft = analyzer.analyze(
            operating_hours=200,
            vibration_history=[1.5] * 20,
            materials_drilled={"soft_soil": 200},
            current_vibration=1.5,
        )
        
        health_hard = analyzer.analyze(
            operating_hours=200,
            vibration_history=[3.0] * 20,
            materials_drilled={"granite": 200},
            current_vibration=3.0,
        )
        
        assert health_soft.health_score > health_hard.health_score


class TestHydraulicSystemAnalyzer:
    """Tests for HydraulicSystemAnalyzer class."""
    
    def test_analyze_healthy_system(self):
        """Test analysis of healthy hydraulic system."""
        analyzer = HydraulicSystemAnalyzer()
        
        results = analyzer.analyze(
            operating_hours=500,
            pressure_history=[250, 252, 248, 251, 250] * 10,
            temperature_history=[55, 56, 54, 55, 55] * 10,
            current_pressure=250,
            current_temperature=55,
            fluid_hours=500,
        )
        
        assert "seals" in results
        assert "pump" in results
        assert "fluid" in results
        assert "hoses" in results
        
        # All should be reasonably healthy
        for component, health in results.items():
            assert health.health_score > 50
    
    def test_fluid_degradation(self):
        """Test fluid degradation over time."""
        analyzer = HydraulicSystemAnalyzer()
        
        # Old fluid
        results = analyzer.analyze(
            operating_hours=2500,
            pressure_history=[250] * 20,
            temperature_history=[55] * 20,
            current_pressure=250,
            current_temperature=55,
            fluid_hours=2400,  # Close to change interval
        )
        
        fluid_health = results["fluid"]
        assert fluid_health.health_score < 30
        assert "fluid change" in fluid_health.recommendations[0].lower()


class TestBearingAnalyzer:
    """Tests for BearingAnalyzer class."""
    
    def test_analyze_healthy_bearing(self):
        """Test analysis of healthy bearing."""
        analyzer = BearingAnalyzer()
        
        health = analyzer.analyze(
            operating_hours=1000,
            vibration_rms=1.5,
            temperature=50,
        )
        
        assert health.health_score > 70
        assert health.status in [HealthStatus.EXCELLENT, HealthStatus.GOOD]
    
    def test_analyze_worn_bearing(self):
        """Test analysis of worn bearing."""
        analyzer = BearingAnalyzer()
        
        health = analyzer.analyze(
            operating_hours=7000,
            vibration_rms=4.0,
            temperature=85,
        )
        
        assert health.health_score < 50
        assert len(health.recommendations) > 0


class TestMaintenanceScheduler:
    """Tests for MaintenanceScheduler class."""
    
    def test_generate_schedule_no_issues(self):
        """Test schedule generation with healthy components."""
        scheduler = MaintenanceScheduler()
        
        health_reports = [
            ComponentHealth(
                component_type=ComponentType.DRILL_BIT,
                component_id="drill_bit_main",
                health_score=90,
                wear_percentage=10,
                rul_hours=400,
                failure_probability=0.01,
                status=HealthStatus.EXCELLENT,
            ),
        ]
        
        tasks = scheduler.generate_schedule(health_reports)
        
        # No immediate tasks needed for excellent health
        assert len([t for t in tasks if t.priority == MaintenancePriority.EMERGENCY]) == 0
    
    def test_generate_schedule_critical(self):
        """Test schedule generation with critical component."""
        scheduler = MaintenanceScheduler()
        
        health_reports = [
            ComponentHealth(
                component_type=ComponentType.DRILL_BIT,
                component_id="drill_bit_main",
                health_score=15,
                wear_percentage=85,
                rul_hours=10,
                failure_probability=0.8,
                status=HealthStatus.CRITICAL,
            ),
        ]
        
        tasks = scheduler.generate_schedule(health_reports)
        
        assert len(tasks) > 0
        assert tasks[0].priority == MaintenancePriority.EMERGENCY
        assert tasks[0].task_type == MaintenanceType.REPLACEMENT


class TestPredictiveMaintenanceEngine:
    """Tests for PredictiveMaintenanceEngine class."""
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = PredictiveMaintenanceEngine()
        
        assert engine.drill_bit_analyzer is not None
        assert engine.hydraulic_analyzer is not None
        assert engine.bearing_analyzer is not None
        assert engine.scheduler is not None
    
    def test_update_drill_bit_data(self):
        """Test updating drill bit data."""
        engine = PredictiveMaintenanceEngine()
        
        health = engine.update_drill_bit_data(
            operating_hours=200,
            vibration_history=[1.5, 1.6, 1.5, 1.7, 1.5] * 10,
            current_vibration=1.6,
        )
        
        assert isinstance(health, ComponentHealth)
        assert health.component_type == ComponentType.DRILL_BIT
    
    def test_get_system_health(self):
        """Test getting system health."""
        engine = PredictiveMaintenanceEngine()
        
        # Add some data
        engine.update_drill_bit_data(
            operating_hours=200,
            vibration_history=[1.5] * 20,
            current_vibration=1.5,
        )
        
        health = engine.get_system_health()
        
        assert "drill_bit" in health
    
    def test_get_overall_system_health(self):
        """Test overall system health calculation."""
        engine = PredictiveMaintenanceEngine()
        
        # Add some data
        engine.update_drill_bit_data(
            operating_hours=100,
            vibration_history=[1.5] * 20,
            current_vibration=1.5,
        )
        
        overall = engine.get_overall_system_health()
        
        assert 0 <= overall <= 100
    
    def test_get_critical_components(self):
        """Test getting critical components."""
        engine = PredictiveMaintenanceEngine()
        
        # Add healthy component
        engine.update_drill_bit_data(
            operating_hours=100,
            vibration_history=[1.5] * 20,
            current_vibration=1.5,
        )
        
        critical = engine.get_critical_components()
        
        # Healthy system should have no critical components
        assert len(critical) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

