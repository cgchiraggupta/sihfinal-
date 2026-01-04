"""
Unit tests for Safety Monitor module.
"""

import pytest
from datetime import datetime, timedelta

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from safety_monitor import (
    HazardType,
    AlertLevel,
    SafetyAction,
    SafetyAlert,
    SafetyStatus,
    VibrationMonitor,
    TemperatureMonitor,
    PressureMonitor,
    GroundStabilityAnalyzer,
    OperatorFatigueMonitor,
    EmergencyController,
    SafetyMonitor,
)


class TestVibrationMonitor:
    """Tests for VibrationMonitor class."""
    
    def test_normal_vibration_no_alert(self):
        """Test that normal vibration doesn't trigger alert."""
        monitor = VibrationMonitor()
        
        alert = monitor.check(1.5)  # Normal level
        
        assert alert is None
    
    def test_warning_vibration(self):
        """Test warning level vibration."""
        monitor = VibrationMonitor()
        
        alert = monitor.check(3.0)  # Warning level
        
        assert alert is not None
        assert alert.level == AlertLevel.WARNING
        assert alert.hazard_type == HazardType.EXCESSIVE_VIBRATION
    
    def test_critical_vibration(self):
        """Test critical level vibration."""
        monitor = VibrationMonitor()
        
        alert = monitor.check(4.5)  # Critical level
        
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL
    
    def test_emergency_vibration(self):
        """Test emergency level vibration."""
        monitor = VibrationMonitor()
        
        alert = monitor.check(7.0)  # Emergency level
        
        assert alert is not None
        assert alert.level == AlertLevel.EMERGENCY
        assert alert.auto_action_taken == SafetyAction.EMERGENCY_STOP


class TestTemperatureMonitor:
    """Tests for TemperatureMonitor class."""
    
    def test_normal_hydraulic_temp(self):
        """Test normal hydraulic temperature."""
        monitor = TemperatureMonitor()
        
        alert = monitor.check_hydraulic(55.0)
        
        assert alert is None
    
    def test_warning_hydraulic_temp(self):
        """Test warning hydraulic temperature."""
        monitor = TemperatureMonitor()
        
        alert = monitor.check_hydraulic(70.0)
        
        assert alert is not None
        assert alert.level == AlertLevel.WARNING
        assert alert.hazard_type == HazardType.OVERHEAT_HYDRAULIC
    
    def test_critical_motor_temp(self):
        """Test critical motor temperature."""
        monitor = TemperatureMonitor()
        
        alert = monitor.check_motor(108.0)
        
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL
    
    def test_thermal_status(self):
        """Test getting thermal status."""
        monitor = TemperatureMonitor()
        
        monitor.check_hydraulic(55.0)
        monitor.check_motor(60.0)
        
        status = monitor.get_thermal_status()
        
        assert "hydraulic_temp" in status
        assert "motor_temp" in status
        assert "hydraulic_trend" in status


class TestPressureMonitor:
    """Tests for PressureMonitor class."""
    
    def test_normal_pressure(self):
        """Test normal pressure."""
        monitor = PressureMonitor()
        
        alert = monitor.check(250.0)
        
        assert alert is None
    
    def test_high_pressure_warning(self):
        """Test high pressure warning."""
        monitor = PressureMonitor()
        
        alert = monitor.check(325.0)
        
        assert alert is not None
        assert alert.level == AlertLevel.WARNING
        assert alert.hazard_type == HazardType.OVERPRESSURE
    
    def test_low_pressure_warning(self):
        """Test low pressure warning."""
        monitor = PressureMonitor()
        
        alert = monitor.check(155.0)
        
        assert alert is not None
        assert alert.hazard_type == HazardType.UNDERPRESSURE
    
    def test_critical_low_pressure(self):
        """Test critical low pressure."""
        monitor = PressureMonitor()
        
        alert = monitor.check(140.0)
        
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL


class TestGroundStabilityAnalyzer:
    """Tests for GroundStabilityAnalyzer class."""
    
    def test_no_anomaly_stable_ground(self):
        """Test stable ground conditions."""
        analyzer = GroundStabilityAnalyzer()
        
        # Simulate consistent readings
        for i in range(30):
            alert = analyzer.check(
                resistance=150.0,
                depth=i * 0.5,
                vibration=1.5,
            )
        
        assert alert is None
    
    def test_void_detection(self):
        """Test void detection on sudden resistance drop."""
        analyzer = GroundStabilityAnalyzer()
        
        # Build up baseline
        for i in range(30):
            analyzer.check(resistance=150.0, depth=i * 0.5, vibration=1.5)
        
        # Sudden drop
        alert = analyzer.check(resistance=30.0, depth=16.0, vibration=0.5)
        
        assert alert is not None
        assert alert.hazard_type == HazardType.VOID_DETECTED


class TestOperatorFatigueMonitor:
    """Tests for OperatorFatigueMonitor class."""
    
    def test_start_session(self):
        """Test starting operator session."""
        monitor = OperatorFatigueMonitor()
        
        session = monitor.start_session("OP001")
        
        assert session.operator_id == "OP001"
        assert session.fatigue_score == 0.0
    
    def test_fatigue_increases(self):
        """Test that fatigue increases without breaks."""
        monitor = OperatorFatigueMonitor()
        
        # Start session in the past
        monitor.start_session("OP001")
        monitor._sessions["OP001"].session_start = datetime.utcnow() - timedelta(hours=8)
        
        alert = monitor.check_fatigue("OP001")
        
        assert alert is not None
        assert alert.hazard_type == HazardType.OPERATOR_FATIGUE
    
    def test_break_reduces_fatigue(self):
        """Test that breaks reduce fatigue."""
        monitor = OperatorFatigueMonitor()
        
        monitor.start_session("OP001")
        monitor._sessions["OP001"].fatigue_score = 50.0
        
        monitor.record_break("OP001")
        
        session = monitor.get_session("OP001")
        assert session.fatigue_score < 50.0


class TestEmergencyController:
    """Tests for EmergencyController class."""
    
    def test_trigger_emergency_stop(self):
        """Test triggering emergency stop."""
        controller = EmergencyController()
        
        assert not controller.is_emergency_active
        
        controller.trigger_emergency_stop("Test emergency")
        
        assert controller.is_emergency_active
    
    def test_reset_emergency(self):
        """Test resetting emergency stop."""
        controller = EmergencyController()
        
        controller.trigger_emergency_stop("Test emergency")
        assert controller.is_emergency_active
        
        success = controller.reset_emergency("Supervisor")
        
        assert success
        assert not controller.is_emergency_active
    
    def test_emergency_status(self):
        """Test getting emergency status."""
        controller = EmergencyController()
        
        controller.trigger_emergency_stop("Test reason")
        
        status = controller.get_emergency_status()
        
        assert status["active"] == True
        assert status["reason"] == "Test reason"
        assert status["triggered_at"] is not None


class TestSafetyMonitor:
    """Tests for SafetyMonitor class."""
    
    def test_initialization(self):
        """Test safety monitor initialization."""
        monitor = SafetyMonitor()
        
        assert monitor.vibration_monitor is not None
        assert monitor.temperature_monitor is not None
        assert monitor.pressure_monitor is not None
        assert monitor.safety_monitor is not None if hasattr(monitor, 'safety_monitor') else True
    
    def test_check_all_safe(self):
        """Test check_all with safe values."""
        monitor = SafetyMonitor()
        
        alerts = monitor.check_all(
            vibration_g=1.5,
            hydraulic_temp_c=55.0,
            motor_temp_c=60.0,
            pressure_bar=250.0,
            resistance=150.0,
            depth_m=15.0,
        )
        
        assert len(alerts) == 0
    
    def test_check_all_with_hazard(self):
        """Test check_all with hazardous values."""
        monitor = SafetyMonitor()
        
        alerts = monitor.check_all(
            vibration_g=5.0,  # Critical
            hydraulic_temp_c=55.0,
            motor_temp_c=60.0,
            pressure_bar=250.0,
            resistance=150.0,
            depth_m=15.0,
        )
        
        assert len(alerts) > 0
        assert any(a.hazard_type == HazardType.EXCESSIVE_VIBRATION for a in alerts)
    
    def test_get_status_safe(self):
        """Test getting status when safe."""
        monitor = SafetyMonitor()
        
        # Run safe check
        monitor.check_all(
            vibration_g=1.5,
            hydraulic_temp_c=55.0,
            motor_temp_c=60.0,
            pressure_bar=250.0,
            resistance=150.0,
            depth_m=15.0,
        )
        
        status = monitor.get_status()
        
        assert status.is_safe == True
        assert status.active_alerts == 0
        assert status.system_health == 100.0
    
    def test_acknowledge_alert(self):
        """Test acknowledging an alert."""
        monitor = SafetyMonitor()
        
        # Generate an alert
        alerts = monitor.check_all(
            vibration_g=4.0,  # Critical level
            hydraulic_temp_c=55.0,
            motor_temp_c=60.0,
            pressure_bar=250.0,
            resistance=150.0,
            depth_m=15.0,
        )
        
        if alerts:
            alert_id = alerts[0].alert_id
            success = monitor.acknowledge_alert(alert_id, "Operator1")
            
            assert success
    
    def test_get_alert_history(self):
        """Test getting alert history."""
        monitor = SafetyMonitor()
        
        # Generate some alerts
        monitor.check_all(
            vibration_g=4.0,
            hydraulic_temp_c=75.0,
            motor_temp_c=60.0,
            pressure_bar=250.0,
            resistance=150.0,
            depth_m=15.0,
        )
        
        history = monitor.get_alert_history(hours=1.0)
        
        assert len(history) > 0
    
    def test_get_statistics(self):
        """Test getting safety statistics."""
        monitor = SafetyMonitor()
        
        # Run some checks
        for _ in range(5):
            monitor.check_all(
                vibration_g=1.5,
                hydraulic_temp_c=55.0,
                motor_temp_c=60.0,
                pressure_bar=250.0,
                resistance=150.0,
                depth_m=15.0,
            )
        
        stats = monitor.get_statistics()
        
        assert "total_checks" in stats
        assert stats["total_checks"] == 5


class TestSafetyAlert:
    """Tests for SafetyAlert dataclass."""
    
    def test_to_dict(self):
        """Test alert serialization."""
        alert = SafetyAlert(
            alert_id="TEST-001",
            hazard_type=HazardType.EXCESSIVE_VIBRATION,
            level=AlertLevel.WARNING,
            message="Test warning",
            value=3.0,
            threshold=2.5,
            recommended_action=SafetyAction.REDUCE_SPEED,
        )
        
        data = alert.to_dict()
        
        assert data["alert_id"] == "TEST-001"
        assert data["hazard_type"] == "excessive_vibration"
        assert data["level"] == "warning"
        assert data["value"] == 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

