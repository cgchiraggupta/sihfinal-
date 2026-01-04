"""
Configuration Management for Advanced EHS Simba Drill System.

This module provides centralized configuration management including:
- Sensor thresholds and calibration
- Alert rules and notification settings
- ML model parameters
- Database and MQTT connection settings
- Data retention policies

Author: EHS Simba Team
Version: 1.0.0
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


# =============================================================================
# Sensor Configuration
# =============================================================================

class VibrationSensorConfig(BaseModel):
    """Configuration for vibration sensors."""
    sampling_rate_hz: int = Field(default=1000, ge=100, le=10000)
    warning_threshold_g: float = Field(default=2.5, ge=0.1, le=10.0)
    critical_threshold_g: float = Field(default=4.0, ge=0.5, le=15.0)
    fft_window_size: int = Field(default=1024, ge=256, le=4096)
    calibration_offset: float = Field(default=0.0)


class TemperatureSensorConfig(BaseModel):
    """Configuration for temperature sensors."""
    sampling_rate_hz: int = Field(default=10, ge=1, le=100)
    hydraulic_warning_c: float = Field(default=65.0, ge=40.0, le=80.0)
    hydraulic_critical_c: float = Field(default=80.0, ge=60.0, le=100.0)
    motor_warning_c: float = Field(default=85.0, ge=60.0, le=100.0)
    motor_critical_c: float = Field(default=105.0, ge=80.0, le=120.0)
    ambient_max_c: float = Field(default=50.0)


class PressureSensorConfig(BaseModel):
    """Configuration for pressure sensors."""
    sampling_rate_hz: int = Field(default=100, ge=10, le=1000)
    hydraulic_min_bar: float = Field(default=150.0, ge=50.0, le=200.0)
    hydraulic_max_bar: float = Field(default=350.0, ge=250.0, le=500.0)
    hydraulic_warning_low_bar: float = Field(default=160.0)
    hydraulic_warning_high_bar: float = Field(default=320.0)
    hydraulic_critical_high_bar: float = Field(default=340.0)


class AcousticSensorConfig(BaseModel):
    """Configuration for acoustic emission sensors."""
    sampling_rate_hz: int = Field(default=50000, ge=10000, le=100000)
    noise_floor_db: float = Field(default=40.0)
    anomaly_threshold_db: float = Field(default=85.0)
    void_detection_freq_hz: tuple[int, int] = Field(default=(5000, 15000))


class PowerSensorConfig(BaseModel):
    """Configuration for power consumption monitoring."""
    sampling_rate_hz: int = Field(default=10, ge=1, le=100)
    max_power_kw: float = Field(default=250.0, ge=50.0, le=500.0)
    idle_power_kw: float = Field(default=15.0, ge=5.0, le=50.0)
    efficiency_warning_percent: float = Field(default=70.0)
    peak_demand_threshold_kw: float = Field(default=200.0)


class SensorConfig(BaseModel):
    """Combined sensor configuration."""
    vibration: VibrationSensorConfig = Field(default_factory=VibrationSensorConfig)
    temperature: TemperatureSensorConfig = Field(default_factory=TemperatureSensorConfig)
    pressure: PressureSensorConfig = Field(default_factory=PressureSensorConfig)
    acoustic: AcousticSensorConfig = Field(default_factory=AcousticSensorConfig)
    power: PowerSensorConfig = Field(default_factory=PowerSensorConfig)
    
    # Sensor health monitoring
    health_check_interval_s: int = Field(default=60, ge=10, le=300)
    max_data_age_s: float = Field(default=5.0, ge=1.0, le=30.0)
    min_valid_readings_percent: float = Field(default=95.0, ge=80.0, le=100.0)


# =============================================================================
# Alert Configuration
# =============================================================================

class EmailConfig(BaseModel):
    """Email notification configuration."""
    enabled: bool = Field(default=False)
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    username: str = Field(default="")
    password: str = Field(default="")
    from_address: str = Field(default="")
    recipients: list[str] = Field(default_factory=list)


class SMSConfig(BaseModel):
    """SMS notification configuration (Twilio)."""
    enabled: bool = Field(default=False)
    account_sid: str = Field(default="")
    auth_token: str = Field(default="")
    from_number: str = Field(default="")
    to_numbers: list[str] = Field(default_factory=list)


class WebhookConfig(BaseModel):
    """Webhook notification configuration."""
    enabled: bool = Field(default=True)
    urls: list[str] = Field(default_factory=list)
    timeout_s: float = Field(default=10.0)
    retry_attempts: int = Field(default=3)


class AlertConfig(BaseModel):
    """Alert and notification configuration."""
    email: EmailConfig = Field(default_factory=EmailConfig)
    sms: SMSConfig = Field(default_factory=SMSConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)
    
    # Alert rate limiting
    min_alert_interval_s: int = Field(default=300, ge=60, le=3600)
    max_alerts_per_hour: int = Field(default=20, ge=5, le=100)
    
    # Alert escalation
    escalation_delay_minutes: int = Field(default=15)
    auto_acknowledge_after_hours: int = Field(default=24)


# =============================================================================
# ML Model Configuration
# =============================================================================

class MaterialPredictorConfig(BaseModel):
    """Configuration for material prediction model."""
    model_path: str = Field(default="models/material_classifier.joblib")
    confidence_threshold: float = Field(default=0.7, ge=0.5, le=0.99)
    prediction_window_s: float = Field(default=1.0, ge=0.1, le=10.0)
    features: list[str] = Field(default=[
        "rpm", "current_a", "vibration_g", "depth_m",
        "pressure_bar", "temperature_c", "acoustic_db"
    ])
    
    # Material classes
    material_classes: list[str] = Field(default=[
        "soft_soil", "clay", "sandstone", "limestone",
        "granite", "basalt", "ore_body", "void"
    ])


class MaintenanceModelConfig(BaseModel):
    """Configuration for maintenance prediction model."""
    drill_bit_model_path: str = Field(default="models/drill_bit_wear.joblib")
    hydraulic_model_path: str = Field(default="models/hydraulic_health.joblib")
    bearing_model_path: str = Field(default="models/bearing_failure.joblib")
    
    # Weibull parameters (default estimates)
    drill_bit_weibull_shape: float = Field(default=2.5)
    drill_bit_weibull_scale_hours: float = Field(default=500.0)
    bearing_weibull_shape: float = Field(default=2.0)
    bearing_weibull_scale_hours: float = Field(default=8000.0)
    seal_weibull_shape: float = Field(default=1.8)
    seal_weibull_scale_hours: float = Field(default=4000.0)
    
    # RUL thresholds
    rul_warning_hours: float = Field(default=100.0)
    rul_critical_hours: float = Field(default=24.0)


class MLConfig(BaseModel):
    """Combined ML configuration."""
    material_predictor: MaterialPredictorConfig = Field(default_factory=MaterialPredictorConfig)
    maintenance: MaintenanceModelConfig = Field(default_factory=MaintenanceModelConfig)
    
    # Training settings
    retrain_interval_days: int = Field(default=30)
    min_training_samples: int = Field(default=10000)
    validation_split: float = Field(default=0.2)


# =============================================================================
# Database Configuration
# =============================================================================

class SupabaseConfig(BaseModel):
    """Supabase configuration."""
    url: str = Field(default="https://ntxqedcyxsqdpauphunc.supabase.co")
    anon_key: str = Field(default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50eHFlZGN5eHNxZHBhdXBodW5jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5MzA3MjQsImV4cCI6MjA3NTUwNjcyNH0.WmL5Ly6utECuTt2qTWbKqltLP73V3hYPLUeylBELKTk")
    service_role_key: Optional[str] = Field(default=None)
    
    # Table prefixes for EHS Simba
    table_prefix: str = Field(default="ehs_")


class DatabaseConfig(BaseModel):
    """Database configuration."""
    # Supabase settings (primary)
    supabase: SupabaseConfig = Field(default_factory=SupabaseConfig)
    
    # Legacy SQLite settings (fallback)
    url: str = Field(default="sqlite+aiosqlite:///./ehs_simba.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    
    # Use Supabase as primary database
    use_supabase: bool = Field(default=True)
    
    # Data retention
    sensor_data_retention_days: int = Field(default=90)
    prediction_retention_days: int = Field(default=365)
    alert_retention_days: int = Field(default=365)
    maintenance_retention_days: int = Field(default=730)  # 2 years
    
    # Aggregation
    raw_data_aggregation_after_days: int = Field(default=7)
    aggregation_interval_minutes: int = Field(default=5)


# =============================================================================
# MQTT Configuration
# =============================================================================

class MQTTConfig(BaseModel):
    """MQTT broker configuration for sensor data streaming."""
    enabled: bool = Field(default=True)
    broker_host: str = Field(default="localhost")
    broker_port: int = Field(default=1883)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    client_id: str = Field(default="ehs_simba_controller")
    
    # Topics
    sensor_topic_prefix: str = Field(default="ehs/simba/sensors")
    command_topic: str = Field(default="ehs/simba/commands")
    status_topic: str = Field(default="ehs/simba/status")
    
    # QoS and persistence
    qos: int = Field(default=1, ge=0, le=2)
    retain: bool = Field(default=False)
    keepalive_s: int = Field(default=60)


# =============================================================================
# Drilling Parameters
# =============================================================================

class DrillingConfig(BaseModel):
    """Drilling operation parameters."""
    # RPM limits
    min_rpm: int = Field(default=30, ge=10, le=100)
    max_rpm: int = Field(default=150, ge=100, le=300)
    optimal_rpm_soft: int = Field(default=120)
    optimal_rpm_hard: int = Field(default=60)
    
    # Depth tracking
    max_hole_depth_m: float = Field(default=60.0, ge=10.0, le=100.0)
    depth_increment_mm: float = Field(default=10.0)
    
    # Feed rate
    max_feed_rate_m_min: float = Field(default=1.5)
    min_feed_rate_m_min: float = Field(default=0.1)
    
    # Hole specifications
    standard_hole_diameter_mm: float = Field(default=127.0)
    tolerance_mm: float = Field(default=2.0)


# =============================================================================
# Energy Configuration
# =============================================================================

class EnergyConfig(BaseModel):
    """Energy monitoring and optimization configuration."""
    electricity_cost_per_kwh: float = Field(default=0.12, ge=0.01, le=1.0)
    peak_hours_start: int = Field(default=9, ge=0, le=23)
    peak_hours_end: int = Field(default=17, ge=0, le=23)
    peak_rate_multiplier: float = Field(default=1.5, ge=1.0, le=3.0)
    
    # Comparison baselines (conventional pneumatic drill)
    pneumatic_power_kw: float = Field(default=350.0)
    pneumatic_efficiency_percent: float = Field(default=25.0)
    
    # EHS baseline
    ehs_efficiency_percent: float = Field(default=85.0)
    
    # Anomaly detection
    consumption_anomaly_threshold_percent: float = Field(default=20.0)


# =============================================================================
# Safety Configuration
# =============================================================================

class SafetyConfig(BaseModel):
    """Safety thresholds and emergency procedures."""
    # Emergency shutdown triggers
    emergency_vibration_g: float = Field(default=6.0)
    emergency_temperature_c: float = Field(default=110.0)
    emergency_pressure_bar: float = Field(default=380.0)
    
    # Ground stability
    resistance_spike_threshold_percent: float = Field(default=50.0)
    void_detection_enabled: bool = Field(default=True)
    
    # Operator safety
    max_continuous_operation_hours: float = Field(default=10.0)
    mandatory_break_minutes: int = Field(default=30)
    
    # Emergency contacts
    emergency_contacts: list[str] = Field(default_factory=list)
    auto_shutdown_enabled: bool = Field(default=True)


# =============================================================================
# Main Settings Class
# =============================================================================

class Settings(BaseSettings):
    """
    Main application settings.
    
    Settings can be configured via:
    1. Environment variables (prefixed with EHS_)
    2. .env file
    3. Direct instantiation
    """
    
    model_config = SettingsConfigDict(
        env_prefix="EHS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application settings
    app_name: str = Field(default="Advanced EHS Simba Drill System")
    version: str = Field(default="1.0.0")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)
    log_level: LogLevel = Field(default=LogLevel.INFO)
    
    # API settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=4)
    cors_origins: list[str] = Field(default=["*"])
    
    # Paths
    base_path: Path = Field(default=Path(__file__).parent)
    models_path: Path = Field(default=Path(__file__).parent / "models")
    logs_path: Path = Field(default=Path(__file__).parent / "logs")
    
    # Component configurations
    sensors: SensorConfig = Field(default_factory=SensorConfig)
    alerts: AlertConfig = Field(default_factory=AlertConfig)
    ml: MLConfig = Field(default_factory=MLConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mqtt: MQTTConfig = Field(default_factory=MQTTConfig)
    drilling: DrillingConfig = Field(default_factory=DrillingConfig)
    energy: EnergyConfig = Field(default_factory=EnergyConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    
    @field_validator("models_path", "logs_path", mode="after")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    def get_sensor_threshold(
        self,
        sensor_type: str,
        threshold_type: str
    ) -> Optional[float]:
        """
        Get a specific sensor threshold value.
        
        Args:
            sensor_type: Type of sensor (vibration, temperature, pressure, etc.)
            threshold_type: Type of threshold (warning, critical, etc.)
            
        Returns:
            Threshold value or None if not found.
        """
        sensor_config = getattr(self.sensors, sensor_type, None)
        if sensor_config:
            return getattr(sensor_config, f"{threshold_type}_threshold", None)
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive data)."""
        data = self.model_dump()
        # Remove sensitive fields
        if "alerts" in data:
            if "email" in data["alerts"]:
                data["alerts"]["email"]["password"] = "***"
            if "sms" in data["alerts"]:
                data["alerts"]["sms"]["auth_token"] = "***"
        if "mqtt" in data and data["mqtt"].get("password"):
            data["mqtt"]["password"] = "***"
        return data


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create the global settings instance.
    
    Returns:
        Settings: Application settings singleton.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment/files.
    
    Returns:
        Settings: New settings instance.
    """
    global _settings
    _settings = Settings()
    return _settings


# Convenience exports
__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
    "Environment",
    "LogLevel",
    "AlertSeverity",
    "SensorConfig",
    "AlertConfig",
    "MLConfig",
    "DatabaseConfig",
    "SupabaseConfig",
    "MQTTConfig",
    "DrillingConfig",
    "EnergyConfig",
    "SafetyConfig",
]

