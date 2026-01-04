"""
Real-time Dashboard Backend for Advanced EHS Simba Drill System.

This module provides FastAPI REST and WebSocket endpoints for:
- Current drilling status
- Material prediction + confidence scores
- Maintenance alerts and warnings
- Energy consumption metrics
- Drilling efficiency KPIs
- Live sensor streaming
- Historical data queries
- Alert notification system

Author: EHS Simba Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from analytics_engine import AnalyticsEngine, get_analytics_engine
from config import Settings, get_settings
from supabase_client import (
    SupabaseManager,
    get_supabase_manager,
)
from energy_optimizer import (
    DrillState,
    EnergyOptimizer,
    PowerReading,
    get_energy_optimizer,
)
from maintenance_predictor import (
    PredictiveMaintenanceEngine,
    get_maintenance_engine,
)
from ml_predictor import (
    MaterialPredictor,
    SensorInput,
    get_material_predictor,
)
from safety_monitor import SafetyMonitor, get_safety_monitor
from sensor_fusion import (
    FusedSensorData,
    SensorFusionEngine,
    SensorReading,
    get_fusion_engine,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models for API
# =============================================================================

class StatusResponse(BaseModel):
    """System status response."""
    status: str
    timestamp: str
    version: str
    is_drilling: bool
    current_depth_m: Optional[float] = None
    current_session_id: Optional[str] = None


class SensorDataRequest(BaseModel):
    """Request model for sensor data input."""
    rpm: float = Field(..., ge=0, le=300)
    current_a: float = Field(..., ge=0, le=500)
    vibration_g: float = Field(..., ge=0, le=20)
    depth_m: float = Field(..., ge=0, le=100)
    pressure_bar: Optional[float] = Field(None, ge=0, le=500)
    temperature_c: Optional[float] = Field(None, ge=0, le=150)
    acoustic_db: Optional[float] = Field(None, ge=0, le=150)
    timestamp: Optional[str] = None


class PredictionResponse(BaseModel):
    """Material prediction response."""
    material: str
    confidence: float
    probabilities: dict[str, float]
    recommended_rpm: Optional[int]
    is_transition: bool
    depth_m: float
    timestamp: str


class AlertResponse(BaseModel):
    """Alert response model."""
    alert_id: Optional[int] = None
    alert_type: str
    severity: str
    title: str
    message: str
    source: str
    timestamp: str
    status: str
    acknowledged: bool = False


class MaintenanceResponse(BaseModel):
    """Maintenance task response."""
    task_type: str
    component_type: str
    component_id: str
    priority: str
    description: str
    due_date: str
    estimated_duration_hours: float
    estimated_cost: float


class EnergyMetricsResponse(BaseModel):
    """Energy metrics response."""
    total_energy_kwh: float
    peak_power_kw: float
    avg_power_kw: float
    drilling_energy_kwh: float
    idle_energy_kwh: float
    efficiency_percent: float
    cost_usd: float
    period_hours: float


class ComponentHealthResponse(BaseModel):
    """Component health response."""
    component_type: str
    component_id: str
    health_score: float
    wear_percentage: float
    rul_hours: float
    status: str
    recommendations: list[str]


class SafetyStatusResponse(BaseModel):
    """Safety status response."""
    is_safe: bool
    active_alerts: int
    highest_alert_level: Optional[str]
    emergency_stop_active: bool
    system_health: float


class DrillingSummaryResponse(BaseModel):
    """Drilling session summary."""
    session_id: str
    hole_id: str
    start_time: str
    end_time: Optional[str]
    target_depth_m: float
    actual_depth_m: Optional[float]
    is_active: bool
    materials_encountered: list[str] = []
    energy_consumed_kwh: Optional[float]


class KPIResponse(BaseModel):
    """KPI dashboard response."""
    total_holes_today: int
    total_meters_today: float
    avg_penetration_rate: float
    drill_utilization_percent: float
    quality_rate_percent: float
    energy_efficiency_rating: str
    active_alerts: int
    maintenance_due_count: int


# =============================================================================
# WebSocket Connection Manager
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections for live streaming."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected client."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        
        data = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)
    
    async def send_personal(
        self,
        websocket: WebSocket,
        message: dict[str, Any],
    ) -> None:
        """Send message to specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")


# Global connection manager
ws_manager = ConnectionManager()


# =============================================================================
# Application State
# =============================================================================

class AppState:
    """Application state container."""
    
    def __init__(self):
        self.material_predictor: Optional[MaterialPredictor] = None
        self.sensor_fusion: Optional[SensorFusionEngine] = None
        self.maintenance_engine: Optional[PredictiveMaintenanceEngine] = None
        self.energy_optimizer: Optional[EnergyOptimizer] = None
        self.analytics_engine: Optional[AnalyticsEngine] = None
        self.safety_monitor: Optional[SafetyMonitor] = None
        self.supabase: Optional[SupabaseManager] = None
        
        # Drilling state
        self.is_drilling = False
        self.current_session_id: Optional[str] = None
        self.current_depth_m = 0.0
        self.current_material = "unknown"
        
        # Streaming task
        self._streaming_task: Optional[asyncio.Task] = None


app_state = AppState()


# =============================================================================
# Lifespan Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Advanced EHS Simba Dashboard API...")
    
    # Initialize Supabase
    try:
        app_state.supabase = await get_supabase_manager()
        logger.info("Supabase connection established")
    except Exception as e:
        logger.warning(f"Supabase connection failed: {e}. Using local mode.")
        app_state.supabase = None
    
    # Initialize components
    app_state.material_predictor = get_material_predictor()
    app_state.sensor_fusion = await get_fusion_engine()
    app_state.maintenance_engine = get_maintenance_engine()
    app_state.energy_optimizer = get_energy_optimizer()
    app_state.analytics_engine = get_analytics_engine()
    app_state.safety_monitor = get_safety_monitor()
    
    # Register callbacks for real-time updates
    def on_new_prediction(prediction):
        asyncio.create_task(ws_manager.broadcast({
            "type": "prediction",
            "data": prediction.to_dict(),
        }))
    
    def on_safety_alert(alert):
        asyncio.create_task(ws_manager.broadcast({
            "type": "safety_alert",
            "data": alert.to_dict(),
        }))
    
    app_state.sensor_fusion.register_prediction_callback(on_new_prediction)
    app_state.safety_monitor.register_alert_callback(on_safety_alert)
    
    logger.info("Dashboard API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Dashboard API...")
    
    if app_state.sensor_fusion:
        await app_state.sensor_fusion.stop()
    
    if app_state._streaming_task:
        app_state._streaming_task.cancel()
    
    logger.info("Dashboard API shutdown complete")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Advanced EHS Simba Drill System API",
    description="Real-time monitoring, prediction, and analytics API for EHS Simba drill operations",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Status Endpoints
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": "Advanced EHS Simba Drill System API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "predictor": app_state.material_predictor is not None,
            "sensor_fusion": app_state.sensor_fusion is not None,
            "maintenance": app_state.maintenance_engine is not None,
            "energy": app_state.energy_optimizer is not None,
            "analytics": app_state.analytics_engine is not None,
            "safety": app_state.safety_monitor is not None,
        },
    }


@app.get("/status", response_model=StatusResponse, tags=["Status"])
async def get_system_status():
    """Get current system status."""
    return StatusResponse(
        status="operational",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        is_drilling=app_state.is_drilling,
        current_depth_m=app_state.current_depth_m if app_state.is_drilling else None,
        current_session_id=app_state.current_session_id,
    )


# =============================================================================
# Material Prediction Endpoints
# =============================================================================

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_material(data: SensorDataRequest):
    """
    Predict material type from sensor data.
    
    Accepts current sensor readings and returns material prediction
    with confidence scores and recommendations.
    """
    if not app_state.material_predictor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Predictor not initialized",
        )
    
    # Create sensor input
    sensor_input = SensorInput(
        rpm=data.rpm,
        current_a=data.current_a,
        vibration_g=data.vibration_g,
        depth_m=data.depth_m,
        pressure_bar=data.pressure_bar,
        temperature_c=data.temperature_c,
        acoustic_db=data.acoustic_db,
        timestamp=datetime.fromisoformat(data.timestamp) if data.timestamp else datetime.utcnow(),
    )
    
    # Get prediction
    result = app_state.material_predictor.predict(sensor_input)
    
    # Update state
    app_state.current_depth_m = data.depth_m
    app_state.current_material = result.material
    
    return PredictionResponse(
        material=result.material,
        confidence=result.confidence,
        probabilities=result.probabilities,
        recommended_rpm=result.recommended_rpm,
        is_transition=result.is_transition,
        depth_m=result.depth_m,
        timestamp=result.timestamp.isoformat(),
    )


@app.get("/predict/history", tags=["Prediction"])
async def get_prediction_history(
    hours: float = Query(24.0, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get historical material predictions."""
    # This would query the database
    return {
        "message": "Historical predictions",
        "period_hours": hours,
        "limit": limit,
        "predictions": [],  # Would be populated from database
    }


# =============================================================================
# Sensor Data Endpoints
# =============================================================================

@app.post("/sensors/reading", tags=["Sensors"])
async def submit_sensor_reading(data: SensorDataRequest):
    """
    Submit a sensor reading for processing.
    
    The reading will be processed through the sensor fusion engine
    and trigger predictions and safety checks.
    """
    if not app_state.sensor_fusion:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sensor fusion not initialized",
        )
    
    # Create sensor readings for each value
    timestamp = datetime.fromisoformat(data.timestamp) if data.timestamp else datetime.utcnow()
    
    readings = [
        SensorReading("rpm_01", "rpm", data.rpm, "rpm", timestamp),
        SensorReading("current_01", "current", data.current_a, "A", timestamp),
        SensorReading("vib_01", "vibration", data.vibration_g, "g", timestamp),
        SensorReading("depth_01", "depth", data.depth_m, "m", timestamp),
    ]
    
    if data.pressure_bar is not None:
        readings.append(SensorReading("pressure_01", "pressure", data.pressure_bar, "bar", timestamp))
    if data.temperature_c is not None:
        readings.append(SensorReading("temp_hyd_01", "temperature_hydraulic", data.temperature_c, "C", timestamp))
    if data.acoustic_db is not None:
        readings.append(SensorReading("acoustic_01", "acoustic", data.acoustic_db, "dB", timestamp))
    
    # Process readings
    await app_state.sensor_fusion.process_batch(readings)
    
    # Run safety checks
    if app_state.safety_monitor:
        alerts = app_state.safety_monitor.check_all(
            vibration_g=data.vibration_g,
            hydraulic_temp_c=data.temperature_c or 45.0,
            motor_temp_c=data.temperature_c or 50.0 if data.temperature_c else 50.0,
            pressure_bar=data.pressure_bar or 200.0,
            resistance=data.current_a,  # Using current as proxy for resistance
            depth_m=data.depth_m,
        )
        
        return {
            "status": "processed",
            "timestamp": timestamp.isoformat(),
            "alerts_generated": len(alerts),
        }
    
    return {
        "status": "processed",
        "timestamp": timestamp.isoformat(),
    }


@app.get("/sensors/status", tags=["Sensors"])
async def get_sensor_status():
    """Get current sensor health status."""
    if not app_state.sensor_fusion:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sensor fusion not initialized",
        )
    
    health = app_state.sensor_fusion.get_sensor_health()
    stats = app_state.sensor_fusion.get_buffer_statistics()
    
    return {
        "sensors": {
            sensor_id: report.to_dict()
            for sensor_id, report in health.items()
        },
        "statistics": stats,
    }


@app.get("/sensors/current", tags=["Sensors"])
async def get_current_readings():
    """Get current (most recent) sensor readings."""
    if not app_state.sensor_fusion:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sensor fusion not initialized",
        )
    
    fused = app_state.sensor_fusion.get_fused_data()
    
    if fused:
        return fused.to_dict()
    else:
        return {"message": "No recent sensor data available"}


# =============================================================================
# Maintenance Endpoints
# =============================================================================

@app.get("/maintenance/health", tags=["Maintenance"])
async def get_component_health():
    """Get health status for all monitored components."""
    if not app_state.maintenance_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Maintenance engine not initialized",
        )
    
    health_reports = app_state.maintenance_engine.get_system_health()
    
    return {
        "overall_health": app_state.maintenance_engine.get_overall_system_health(),
        "components": {
            name: health.to_dict()
            for name, health in health_reports.items()
        },
    }


@app.get("/maintenance/schedule", tags=["Maintenance"])
async def get_maintenance_schedule(
    days_ahead: int = Query(30, ge=1, le=365),
):
    """Get upcoming maintenance schedule."""
    if not app_state.maintenance_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Maintenance engine not initialized",
        )
    
    tasks = app_state.maintenance_engine.get_maintenance_schedule(days_ahead)
    
    return {
        "planning_horizon_days": days_ahead,
        "tasks": [task.to_dict() for task in tasks],
        "total_tasks": len(tasks),
    }


@app.get("/maintenance/rul", tags=["Maintenance"])
async def get_remaining_useful_life():
    """Get RUL (Remaining Useful Life) for all components."""
    if not app_state.maintenance_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Maintenance engine not initialized",
        )
    
    rul_summary = app_state.maintenance_engine.get_rul_summary()
    
    return {
        "components": rul_summary,
        "critical": {
            name: hours
            for name, hours in rul_summary.items()
            if hours < 100
        },
    }


@app.post("/maintenance/update/drill-bit", tags=["Maintenance"])
async def update_drill_bit_data(
    operating_hours: float,
    vibration_history: list[float],
    current_vibration: float,
    materials_drilled: Optional[dict[str, float]] = None,
):
    """Update drill bit operating data for health assessment."""
    if not app_state.maintenance_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Maintenance engine not initialized",
        )
    
    health = app_state.maintenance_engine.update_drill_bit_data(
        operating_hours=operating_hours,
        vibration_history=vibration_history,
        materials_drilled=materials_drilled,
        current_vibration=current_vibration,
    )
    
    return health.to_dict()


# =============================================================================
# Energy Endpoints
# =============================================================================

@app.get("/energy/metrics", response_model=EnergyMetricsResponse, tags=["Energy"])
async def get_energy_metrics(
    hours: float = Query(24.0, ge=1, le=168),
):
    """Get energy consumption metrics for specified period."""
    if not app_state.energy_optimizer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Energy optimizer not initialized",
        )
    
    metrics = app_state.energy_optimizer.get_energy_metrics(hours)
    
    return EnergyMetricsResponse(
        total_energy_kwh=metrics.total_energy_kwh,
        peak_power_kw=metrics.peak_power_kw,
        avg_power_kw=metrics.avg_power_kw,
        drilling_energy_kwh=metrics.drilling_energy_kwh,
        idle_energy_kwh=metrics.idle_energy_kwh,
        efficiency_percent=metrics.efficiency_percent,
        cost_usd=metrics.cost_usd,
        period_hours=hours,
    )


@app.get("/energy/comparison", tags=["Energy"])
async def get_energy_comparison(
    hours: float = Query(24.0, ge=1, le=168),
):
    """Get energy cost comparison vs conventional pneumatic drill."""
    if not app_state.energy_optimizer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Energy optimizer not initialized",
        )
    
    comparison = app_state.energy_optimizer.get_cost_comparison(hours)
    
    return comparison.to_dict()


@app.get("/energy/recommendations", tags=["Energy"])
async def get_energy_recommendations():
    """Get energy optimization recommendations."""
    if not app_state.energy_optimizer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Energy optimizer not initialized",
        )
    
    recommendations = app_state.energy_optimizer.get_recommendations()
    
    return {
        "recommendations": [r.to_dict() for r in recommendations],
        "total": len(recommendations),
    }


@app.get("/energy/efficiency", tags=["Energy"])
async def get_efficiency_summary():
    """Get comprehensive efficiency summary."""
    if not app_state.energy_optimizer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Energy optimizer not initialized",
        )
    
    return app_state.energy_optimizer.get_efficiency_summary()


@app.post("/energy/reading", tags=["Energy"])
async def submit_power_reading(
    power_kw: float,
    voltage_v: float = 0.0,
    current_a: float = 0.0,
    power_factor: float = 1.0,
    state: str = "drilling",
):
    """Submit a power reading."""
    if not app_state.energy_optimizer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Energy optimizer not initialized",
        )
    
    # Map state string to enum
    drill_state = DrillState(state) if state in [s.value for s in DrillState] else DrillState.DRILLING
    
    reading = PowerReading(
        timestamp=datetime.utcnow(),
        power_kw=power_kw,
        voltage_v=voltage_v,
        current_a=current_a,
        power_factor=power_factor,
        state=drill_state,
    )
    
    anomaly = app_state.energy_optimizer.add_power_reading(reading)
    
    return {
        "status": "recorded",
        "anomaly": anomaly,
    }


# =============================================================================
# Analytics Endpoints
# =============================================================================

@app.get("/analytics/quality", tags=["Analytics"])
async def get_hole_quality_summary():
    """Get hole quality summary across all scored holes."""
    if not app_state.analytics_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics engine not initialized",
        )
    
    return app_state.analytics_engine.get_quality_summary()


@app.get("/analytics/anomalies", tags=["Analytics"])
async def get_geological_anomalies():
    """Get detected geological anomalies."""
    if not app_state.analytics_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics engine not initialized",
        )
    
    return app_state.analytics_engine.get_anomaly_summary()


@app.get("/analytics/roi", tags=["Analytics"])
async def get_roi_analysis(
    years: int = Query(10, ge=1, le=20),
    discount_rate: float = Query(0.08, ge=0.01, le=0.25),
):
    """Get ROI analysis for EHS vs conventional drill."""
    if not app_state.analytics_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics engine not initialized",
        )
    
    roi = app_state.analytics_engine.calculate_roi(years, discount_rate)
    
    return roi.to_dict()


@app.get("/analytics/tco", tags=["Analytics"])
async def get_tco_breakdown(
    years: int = Query(10, ge=1, le=20),
):
    """Get TCO breakdown comparison."""
    if not app_state.analytics_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics engine not initialized",
        )
    
    return app_state.analytics_engine.get_tco_breakdown(years)


@app.post("/analytics/score-hole", tags=["Analytics"])
async def score_hole(
    hole_id: str,
    target_depth_m: float,
    actual_depth_m: float,
    max_deviation_m: float,
    collar_offset_m: float,
    angle_deviation_deg: float,
):
    """Score a completed blast hole."""
    if not app_state.analytics_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics engine not initialized",
        )
    
    score = app_state.analytics_engine.score_hole(
        hole_id=hole_id,
        target_depth_m=target_depth_m,
        actual_depth_m=actual_depth_m,
        max_deviation_m=max_deviation_m,
        collar_offset_m=collar_offset_m,
        angle_deviation_deg=angle_deviation_deg,
    )
    
    return score.to_dict()


# =============================================================================
# Safety Endpoints
# =============================================================================

@app.get("/safety/status", response_model=SafetyStatusResponse, tags=["Safety"])
async def get_safety_status():
    """Get current safety system status."""
    if not app_state.safety_monitor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Safety monitor not initialized",
        )
    
    status_obj = app_state.safety_monitor.get_status()
    
    return SafetyStatusResponse(
        is_safe=status_obj.is_safe,
        active_alerts=status_obj.active_alerts,
        highest_alert_level=status_obj.highest_alert_level.value if status_obj.highest_alert_level else None,
        emergency_stop_active=status_obj.emergency_stop_active,
        system_health=status_obj.system_health,
    )


@app.get("/safety/alerts", tags=["Safety"])
async def get_active_alerts():
    """Get all active safety alerts."""
    if not app_state.safety_monitor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Safety monitor not initialized",
        )
    
    alerts = app_state.safety_monitor.get_active_alerts()
    
    return {
        "alerts": [a.to_dict() for a in alerts],
        "count": len(alerts),
    }


@app.get("/safety/alerts/history", tags=["Safety"])
async def get_alert_history(
    hours: float = Query(24.0, ge=1, le=168),
):
    """Get historical alerts."""
    if not app_state.safety_monitor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Safety monitor not initialized",
        )
    
    alerts = app_state.safety_monitor.get_alert_history(hours)
    
    return {
        "period_hours": hours,
        "alerts": [a.to_dict() for a in alerts],
        "count": len(alerts),
    }


@app.post("/safety/alerts/{alert_id}/acknowledge", tags=["Safety"])
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str,
):
    """Acknowledge a safety alert."""
    if not app_state.safety_monitor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Safety monitor not initialized",
        )
    
    success = app_state.safety_monitor.acknowledge_alert(alert_id, acknowledged_by)
    
    if success:
        return {"status": "acknowledged", "alert_id": alert_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )


@app.post("/safety/emergency/reset", tags=["Safety"])
async def reset_emergency_stop(
    authorized_by: str,
):
    """Reset emergency stop (requires authorization)."""
    if not app_state.safety_monitor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Safety monitor not initialized",
        )
    
    success = app_state.safety_monitor.reset_emergency(authorized_by)
    
    return {
        "status": "reset" if success else "failed",
        "authorized_by": authorized_by,
    }


@app.get("/safety/thermal", tags=["Safety"])
async def get_thermal_status():
    """Get current thermal status."""
    if not app_state.safety_monitor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Safety monitor not initialized",
        )
    
    return app_state.safety_monitor.get_thermal_status()


@app.get("/safety/statistics", tags=["Safety"])
async def get_safety_statistics():
    """Get safety monitoring statistics."""
    if not app_state.safety_monitor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Safety monitor not initialized",
        )
    
    return app_state.safety_monitor.get_statistics()


# =============================================================================
# KPI Dashboard Endpoint
# =============================================================================

@app.get("/kpi/dashboard", response_model=KPIResponse, tags=["KPI"])
async def get_kpi_dashboard():
    """Get all key performance indicators for dashboard display."""
    # Aggregate data from all systems
    
    # Energy efficiency
    efficiency_rating = "good"
    if app_state.energy_optimizer:
        from energy_optimizer import EfficiencyRating
        rating = app_state.energy_optimizer.power_monitor.get_efficiency_rating()
        efficiency_rating = rating.value
    
    # Active alerts
    active_alerts = 0
    if app_state.safety_monitor:
        status_obj = app_state.safety_monitor.get_status()
        active_alerts = status_obj.active_alerts
    
    # Maintenance due
    maintenance_due = 0
    if app_state.maintenance_engine:
        tasks = app_state.maintenance_engine.get_maintenance_schedule(7)
        maintenance_due = len([t for t in tasks if t.priority.value in ["emergency", "high"]])
    
    return KPIResponse(
        total_holes_today=0,  # Would come from database
        total_meters_today=0.0,  # Would come from database
        avg_penetration_rate=0.5,  # Would be calculated
        drill_utilization_percent=75.0,  # Would be calculated
        quality_rate_percent=95.0,  # Would come from analytics
        energy_efficiency_rating=efficiency_rating,
        active_alerts=active_alerts,
        maintenance_due_count=maintenance_due,
    )


# =============================================================================
# WebSocket Endpoint for Live Streaming
# =============================================================================

@app.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket):
    """
    WebSocket endpoint for live sensor data and predictions.
    
    Streams:
    - Real-time sensor readings
    - Material predictions
    - Safety alerts
    - System status updates
    """
    await ws_manager.connect(websocket)
    
    try:
        # Send initial status
        await ws_manager.send_personal(websocket, {
            "type": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to EHS Simba live stream",
        })
        
        while True:
            # Wait for messages from client (heartbeat, commands)
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,
                )
                
                message = json.loads(data)
                
                # Handle client messages
                if message.get("type") == "ping":
                    await ws_manager.send_personal(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                elif message.get("type") == "subscribe":
                    # Handle subscription requests
                    await ws_manager.send_personal(websocket, {
                        "type": "subscribed",
                        "channels": message.get("channels", ["all"]),
                    })
                    
            except asyncio.TimeoutError:
                # Send periodic status update on timeout
                if app_state.sensor_fusion:
                    fused = app_state.sensor_fusion.get_fused_data()
                    if fused:
                        await ws_manager.send_personal(websocket, {
                            "type": "sensor_update",
                            "data": fused.to_dict(),
                        })
                
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)


# =============================================================================
# Drilling Session Endpoints
# =============================================================================

@app.post("/drilling/start", tags=["Drilling"])
async def start_drilling_session(
    hole_id: str,
    target_depth_m: float,
    grid_x: Optional[float] = None,
    grid_y: Optional[float] = None,
):
    """Start a new drilling session."""
    app_state.is_drilling = True
    app_state.current_depth_m = 0.0
    app_state.current_session_id = f"SESSION-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Reset analytics for new hole
    if app_state.analytics_engine:
        app_state.analytics_engine.new_hole()
    
    return {
        "session_id": app_state.current_session_id,
        "hole_id": hole_id,
        "target_depth_m": target_depth_m,
        "start_time": datetime.utcnow().isoformat(),
        "status": "started",
    }


@app.post("/drilling/stop", tags=["Drilling"])
async def stop_drilling_session(
    completion_status: str = "completed",
):
    """Stop the current drilling session."""
    session_id = app_state.current_session_id
    final_depth = app_state.current_depth_m
    
    app_state.is_drilling = False
    app_state.current_session_id = None
    
    return {
        "session_id": session_id,
        "final_depth_m": final_depth,
        "completion_status": completion_status,
        "end_time": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Configuration Endpoint
# =============================================================================

@app.get("/config", tags=["Configuration"])
async def get_configuration():
    """Get current system configuration (non-sensitive)."""
    settings = get_settings()
    return settings.to_dict()


# =============================================================================
# Supabase Data Endpoints
# =============================================================================

@app.get("/db/sessions", tags=["Database"])
async def get_drilling_sessions(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get drilling sessions from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    result = (
        app_state.supabase.client.table("ehs_drilling_sessions")
        .select("*")
        .gte("start_time", cutoff)
        .order("start_time", desc=True)
        .limit(limit)
        .execute()
    )
    
    return {
        "sessions": result.data or [],
        "count": len(result.data) if result.data else 0,
    }


@app.get("/db/sessions/stats", tags=["Database"])
async def get_session_statistics(
    days: int = Query(30, ge=1, le=365),
):
    """Get drilling session statistics from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    stats = await app_state.supabase.get_session_statistics(days)
    return stats


@app.get("/db/alerts", tags=["Database"])
async def get_database_alerts(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get alerts from Supabase database."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    query = app_state.supabase.client.table("ehs_alerts").select("*")
    
    if status_filter:
        query = query.eq("status", status_filter)
    if severity:
        query = query.eq("severity", severity)
    
    result = query.order("created_at", desc=True).limit(limit).execute()
    
    return {
        "alerts": result.data or [],
        "count": len(result.data) if result.data else 0,
    }


@app.get("/db/alerts/stats", tags=["Database"])
async def get_alert_statistics(
    days: int = Query(30, ge=1, le=365),
):
    """Get alert statistics from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    stats = await app_state.supabase.get_alert_statistics(days)
    return stats


@app.get("/db/maintenance", tags=["Database"])
async def get_maintenance_tasks(
    days_ahead: int = Query(30, ge=1, le=365),
):
    """Get pending maintenance tasks from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    tasks = await app_state.supabase.get_pending_maintenance(days_ahead)
    
    return {
        "tasks": tasks,
        "count": len(tasks),
    }


@app.get("/db/energy", tags=["Database"])
async def get_energy_data(
    hours: float = Query(24.0, ge=1, le=168),
    session_id: Optional[str] = None,
):
    """Get energy consumption data from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    consumption = await app_state.supabase.get_energy_consumption(
        session_id=session_id,
        start_time=start_time,
    )
    
    return consumption


@app.get("/db/components/health", tags=["Database"])
async def get_components_health(
    component_type: Optional[str] = None,
):
    """Get component health records from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    health_records = await app_state.supabase.get_component_health(
        component_type=component_type
    )
    
    return {
        "components": health_records,
        "count": len(health_records),
    }


@app.get("/db/components/attention", tags=["Database"])
async def get_components_needing_attention(
    threshold: float = Query(50.0, ge=0, le=100),
):
    """Get components with low health scores from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    components = await app_state.supabase.get_components_needing_attention(threshold)
    
    return {
        "components": components,
        "count": len(components),
        "threshold": threshold,
    }


@app.get("/db/predictions", tags=["Database"])
async def get_material_predictions(
    session_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    """Get material predictions from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    if session_id:
        predictions = await app_state.supabase.get_predictions_for_session(
            session_id, limit
        )
    else:
        result = (
            app_state.supabase.client.table("ehs_material_predictions")
            .select("*")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        predictions = result.data or []
    
    return {
        "predictions": predictions,
        "count": len(predictions),
    }


@app.get("/db/predictions/distribution", tags=["Database"])
async def get_material_distribution(
    session_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
):
    """Get material type distribution from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    distribution = await app_state.supabase.get_material_distribution(
        session_id=session_id,
        days=days,
    )
    
    return {
        "distribution": distribution,
        "total_predictions": sum(distribution.values()),
    }


@app.get("/db/sensors/health", tags=["Database"])
async def get_sensor_health_status():
    """Get sensor health status from Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    unhealthy = await app_state.supabase.get_unhealthy_sensors()
    
    return {
        "unhealthy_sensors": unhealthy,
        "count": len(unhealthy),
    }


@app.post("/db/sensor-reading", tags=["Database"])
async def store_sensor_reading(
    sensor_type: str,
    sensor_id: str,
    value: float,
    unit: str,
    quality: float = 1.0,
):
    """Store a sensor reading in Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    result = await app_state.supabase.insert_sensor_reading(
        sensor_type=sensor_type,
        sensor_id=sensor_id,
        value=value,
        unit=unit,
        quality=quality,
    )
    
    return {
        "status": "stored",
        "data": result,
    }


@app.post("/db/prediction", tags=["Database"])
async def store_prediction(
    session_id: str,
    depth_m: float,
    predicted_material: str,
    confidence: float,
    rpm: float,
    current_a: float,
    vibration_g: float,
    pressure_bar: Optional[float] = None,
    temperature_c: Optional[float] = None,
):
    """Store a material prediction in Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    result = await app_state.supabase.insert_prediction(
        session_id=session_id,
        depth_m=depth_m,
        predicted_material=predicted_material,
        confidence=confidence,
        rpm=rpm,
        current_a=current_a,
        vibration_g=vibration_g,
        pressure_bar=pressure_bar,
        temperature_c=temperature_c,
    )
    
    return {
        "status": "stored",
        "data": result,
    }


@app.post("/db/alert", tags=["Database"])
async def create_database_alert(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    source: str,
):
    """Create an alert in Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    result = await app_state.supabase.create_alert(
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=message,
        source=source,
    )
    
    return {
        "status": "created",
        "data": result,
    }


@app.post("/db/session/start", tags=["Database"])
async def start_database_session(
    hole_id: str,
    target_depth_m: float,
    grid_x: Optional[float] = None,
    grid_y: Optional[float] = None,
):
    """Start a new drilling session in Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    session_data = await app_state.supabase.create_drilling_session(
        hole_id=hole_id,
        target_depth_m=target_depth_m,
        grid_x=grid_x,
        grid_y=grid_y,
    )
    
    # Update app state
    app_state.is_drilling = True
    app_state.current_session_id = session_data.get("id")
    app_state.current_depth_m = 0.0
    
    return {
        "status": "started",
        "session": session_data,
    }


@app.post("/db/session/end", tags=["Database"])
async def end_database_session(
    session_id: str,
    actual_depth_m: float,
    completion_status: str = "completed",
):
    """End a drilling session in Supabase."""
    if not app_state.supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    
    session_data = await app_state.supabase.end_drilling_session(
        session_id=session_id,
        actual_depth_m=actual_depth_m,
        completion_status=completion_status,
    )
    
    # Update app state
    if app_state.current_session_id == session_id:
        app_state.is_drilling = False
        app_state.current_session_id = None
    
    return {
        "status": "ended",
        "session": session_data,
    }


# =============================================================================
# Run Server
# =============================================================================

def run_server():
    """Run the FastAPI server."""
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "dashboard_api:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run_server()

