"""
Advanced EHS Simba Drill Monitoring & Predictive System.

A comprehensive solution for Electric Hydraulic System (EHS) Simba drill
monitoring, featuring:

- Machine learning-based material prediction
- IoT sensor integration and fusion
- Predictive maintenance with Weibull analysis
- Real-time energy optimization
- Advanced drilling analytics
- Safety monitoring and hazard detection
- FastAPI-based dashboard backend

Version: 1.0.0
Author: EHS Simba Team
"""

__version__ = "1.0.0"
__author__ = "EHS Simba Team"

from .ml_predictor import (
    MaterialPredictor,
    SensorInput,
    PredictionResult,
    get_material_predictor,
)
from .sensor_fusion import (
    SensorFusionEngine,
    SensorReading,
    FusedSensorData,
)
from .maintenance_predictor import (
    PredictiveMaintenanceEngine,
    ComponentHealth,
    MaintenanceTask,
    get_maintenance_engine,
)
from .energy_optimizer import (
    EnergyOptimizer,
    PowerReading,
    EnergyMetrics,
    get_energy_optimizer,
)
from .analytics_engine import (
    AnalyticsEngine,
    MaterialLayer,
    HoleQualityScore,
    ROIAnalysis,
    get_analytics_engine,
)
from .safety_monitor import (
    SafetyMonitor,
    SafetyAlert,
    SafetyStatus,
    get_safety_monitor,
)
from .config import Settings, get_settings
from .supabase_client import (
    SupabaseManager,
    get_supabase_manager,
    get_supabase_client,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # ML Predictor
    "MaterialPredictor",
    "SensorInput", 
    "PredictionResult",
    "get_material_predictor",
    
    # Sensor Fusion
    "SensorFusionEngine",
    "SensorReading",
    "FusedSensorData",
    
    # Maintenance
    "PredictiveMaintenanceEngine",
    "ComponentHealth",
    "MaintenanceTask",
    "get_maintenance_engine",
    
    # Energy
    "EnergyOptimizer",
    "PowerReading",
    "EnergyMetrics",
    "get_energy_optimizer",
    
    # Analytics
    "AnalyticsEngine",
    "MaterialLayer",
    "HoleQualityScore",
    "ROIAnalysis",
    "get_analytics_engine",
    
    # Safety
    "SafetyMonitor",
    "SafetyAlert",
    "SafetyStatus",
    "get_safety_monitor",
    
    # Config
    "Settings",
    "get_settings",
    
    # Supabase
    "SupabaseManager",
    "get_supabase_manager",
    "get_supabase_client",
]

