"""
Database Module for Advanced EHS Simba Drill System.

This module provides:
- SQLAlchemy async database models
- Database session management
- CRUD operations for sensor data, predictions, maintenance records
- Data aggregation and retention policies

Author: EHS Simba Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncGenerator, Optional, Sequence
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    and_,
    delete,
    desc,
    func,
    select,
    text,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import DatabaseConfig, get_settings


# =============================================================================
# Enums for Database
# =============================================================================

class AlertStatus(str, Enum):
    """Alert status types."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class MaintenanceStatus(str, Enum):
    """Maintenance task status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class ComponentType(str, Enum):
    """Drill component types."""
    DRILL_BIT = "drill_bit"
    BEARING = "bearing"
    SEAL = "seal"
    PUMP = "pump"
    MOTOR = "motor"
    HYDRAULIC_HOSE = "hydraulic_hose"
    FILTER = "filter"


class SensorType(str, Enum):
    """Sensor types."""
    VIBRATION = "vibration"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    ACOUSTIC = "acoustic"
    POWER = "power"
    RPM = "rpm"
    DEPTH = "depth"
    CURRENT = "current"


# =============================================================================
# Base Model
# =============================================================================

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# =============================================================================
# Database Models
# =============================================================================

class SensorReading(Base):
    """
    Real-time sensor readings from the drill.
    
    This table stores high-frequency sensor data with automatic partitioning
    and retention policies.
    """
    __tablename__ = "sensor_readings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    sensor_type: Mapped[str] = mapped_column(String(50), index=True)
    sensor_id: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))
    quality: Mapped[float] = mapped_column(Float, default=1.0)  # 0-1 data quality score
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    __table_args__ = (
        Index("idx_sensor_time", "sensor_type", "timestamp"),
        Index("idx_sensor_id_time", "sensor_id", "timestamp"),
    )


class AggregatedSensorData(Base):
    """
    Aggregated sensor data for historical analysis.
    
    Raw data is aggregated into this table after the retention period
    to save storage while preserving trends.
    """
    __tablename__ = "aggregated_sensor_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    sensor_type: Mapped[str] = mapped_column(String(50), index=True)
    sensor_id: Mapped[str] = mapped_column(String(100))
    interval_minutes: Mapped[int] = mapped_column(Integer)  # Aggregation interval
    
    # Statistical aggregates
    min_value: Mapped[float] = mapped_column(Float)
    max_value: Mapped[float] = mapped_column(Float)
    avg_value: Mapped[float] = mapped_column(Float)
    std_value: Mapped[float] = mapped_column(Float)
    sample_count: Mapped[int] = mapped_column(Integer)
    
    __table_args__ = (
        Index("idx_agg_sensor_time", "sensor_type", "timestamp"),
    )


class DrillingSession(Base):
    """
    Drilling session records.
    
    Each session represents a continuous drilling operation from start to end.
    """
    __tablename__ = "drilling_sessions"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Location
    hole_id: Mapped[str] = mapped_column(String(100), index=True)
    grid_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grid_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    collar_elevation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Drilling parameters
    target_depth_m: Mapped[float] = mapped_column(Float)
    actual_depth_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hole_diameter_mm: Mapped[float] = mapped_column(Float, default=127.0)
    
    # Performance metrics
    total_drilling_time_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_penetration_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    energy_consumed_kwh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    completion_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    predictions: Mapped[list["MaterialPrediction"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class MaterialPrediction(Base):
    """
    Material type predictions from the ML model.
    """
    __tablename__ = "material_predictions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("drilling_sessions.id"), index=True
    )
    
    # Prediction details
    depth_m: Mapped[float] = mapped_column(Float, index=True)
    predicted_material: Mapped[str] = mapped_column(String(50), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    
    # Feature values used for prediction
    rpm: Mapped[float] = mapped_column(Float)
    current_a: Mapped[float] = mapped_column(Float)
    vibration_g: Mapped[float] = mapped_column(Float)
    pressure_bar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # All class probabilities (for analysis)
    class_probabilities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationship
    session: Mapped["DrillingSession"] = relationship(back_populates="predictions")
    
    __table_args__ = (
        Index("idx_prediction_session_depth", "session_id", "depth_m"),
    )


class Alert(Base):
    """
    System alerts and warnings.
    """
    __tablename__ = "alerts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Alert details
    alert_type: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(
        String(20), default=AlertStatus.ACTIVE.value, index=True
    )
    
    # Content
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100))  # Which component generated it
    
    # Context
    sensor_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Resolution
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Notification tracking
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_channels: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    __table_args__ = (
        Index("idx_alert_status_severity", "status", "severity"),
    )


class ComponentHealth(Base):
    """
    Component health and wear tracking.
    """
    __tablename__ = "component_health"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # Component identification
    component_type: Mapped[str] = mapped_column(String(50), index=True)
    component_id: Mapped[str] = mapped_column(String(100), index=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Usage tracking
    operating_hours: Mapped[float] = mapped_column(Float)
    cycles_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Health metrics
    health_score: Mapped[float] = mapped_column(Float)  # 0-100
    wear_percentage: Mapped[float] = mapped_column(Float)  # 0-100
    
    # Predictions
    estimated_rul_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    failure_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Additional data
    diagnostic_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    __table_args__ = (
        Index("idx_component_type_id", "component_type", "component_id"),
    )


class MaintenanceRecord(Base):
    """
    Maintenance tasks and history.
    """
    __tablename__ = "maintenance_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # Task details
    task_type: Mapped[str] = mapped_column(String(50), index=True)
    component_type: Mapped[str] = mapped_column(String(50), index=True)
    component_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Scheduling
    scheduled_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=MaintenanceStatus.SCHEDULED.value, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=2)  # 1=high, 2=medium, 3=low
    
    # Details
    description: Mapped[str] = mapped_column(Text)
    work_performed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parts_replaced: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Personnel
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    completed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Trigger
    triggered_by: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # "predictive", "scheduled", "reactive"
    related_alert_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class EnergyLog(Base):
    """
    Energy consumption logging.
    """
    __tablename__ = "energy_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # Energy measurements
    power_kw: Mapped[float] = mapped_column(Float)
    energy_kwh: Mapped[float] = mapped_column(Float)
    voltage_v: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    power_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Context
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    drilling_state: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # "drilling", "idle", "repositioning"
    
    # Cost tracking
    is_peak_hours: Mapped[bool] = mapped_column(Boolean, default=False)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    __table_args__ = (
        Index("idx_energy_session", "session_id", "timestamp"),
    )


class SensorHealth(Base):
    """
    Sensor health monitoring.
    """
    __tablename__ = "sensor_health"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    sensor_id: Mapped[str] = mapped_column(String(100), index=True)
    sensor_type: Mapped[str] = mapped_column(String(50))
    
    # Health metrics
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    last_reading_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    readings_per_second: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Quality metrics
    noise_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    drift: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    out_of_range_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status
    status_message: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    requires_calibration: Mapped[bool] = mapped_column(Boolean, default=False)


# =============================================================================
# Database Manager
# =============================================================================

class DatabaseManager:
    """
    Async database manager for the EHS Simba system.
    
    Provides connection management, session handling, and common database operations.
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize the database manager.
        
        Args:
            config: Database configuration. Uses default settings if not provided.
        """
        self.config = config or get_settings().database
        self._engine = None
        self._session_factory = None
    
    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        self._engine = create_async_engine(
            self.config.url,
            echo=self.config.echo,
            pool_pre_ping=True,
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create all tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.
        
        Yields:
            AsyncSession: Database session for operations.
        """
        if not self._session_factory:
            await self.initialize()
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    # =========================================================================
    # Sensor Data Operations
    # =========================================================================
    
    async def insert_sensor_reading(
        self,
        session: AsyncSession,
        sensor_type: str,
        sensor_id: str,
        value: float,
        unit: str,
        quality: float = 1.0,
        metadata: Optional[dict] = None,
    ) -> SensorReading:
        """Insert a new sensor reading."""
        reading = SensorReading(
            sensor_type=sensor_type,
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            quality=quality,
            metadata_json=metadata,
        )
        session.add(reading)
        await session.flush()
        return reading
    
    async def bulk_insert_readings(
        self,
        session: AsyncSession,
        readings: list[dict[str, Any]],
    ) -> int:
        """
        Bulk insert sensor readings for performance.
        
        Args:
            session: Database session
            readings: List of reading dictionaries
            
        Returns:
            Number of inserted records.
        """
        objects = [SensorReading(**r) for r in readings]
        session.add_all(objects)
        await session.flush()
        return len(objects)
    
    async def get_sensor_readings(
        self,
        session: AsyncSession,
        sensor_type: Optional[str] = None,
        sensor_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> Sequence[SensorReading]:
        """Query sensor readings with filters."""
        query = select(SensorReading)
        
        conditions = []
        if sensor_type:
            conditions.append(SensorReading.sensor_type == sensor_type)
        if sensor_id:
            conditions.append(SensorReading.sensor_id == sensor_id)
        if start_time:
            conditions.append(SensorReading.timestamp >= start_time)
        if end_time:
            conditions.append(SensorReading.timestamp <= end_time)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(SensorReading.timestamp)).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    # =========================================================================
    # Drilling Session Operations
    # =========================================================================
    
    async def create_drilling_session(
        self,
        session: AsyncSession,
        hole_id: str,
        target_depth_m: float,
        **kwargs,
    ) -> DrillingSession:
        """Create a new drilling session."""
        drilling_session = DrillingSession(
            hole_id=hole_id,
            target_depth_m=target_depth_m,
            start_time=datetime.utcnow(),
            **kwargs,
        )
        session.add(drilling_session)
        await session.flush()
        return drilling_session
    
    async def get_active_session(
        self,
        session: AsyncSession,
    ) -> Optional[DrillingSession]:
        """Get the currently active drilling session."""
        query = select(DrillingSession).where(
            DrillingSession.is_active == True
        ).order_by(desc(DrillingSession.start_time))
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def end_drilling_session(
        self,
        session: AsyncSession,
        session_id: str,
        actual_depth_m: float,
        completion_status: str = "completed",
    ) -> Optional[DrillingSession]:
        """End a drilling session."""
        query = select(DrillingSession).where(DrillingSession.id == session_id)
        result = await session.execute(query)
        drilling_session = result.scalar_one_or_none()
        
        if drilling_session:
            drilling_session.end_time = datetime.utcnow()
            drilling_session.actual_depth_m = actual_depth_m
            drilling_session.is_active = False
            drilling_session.completion_status = completion_status
            
            # Calculate total drilling time
            drilling_session.total_drilling_time_s = (
                drilling_session.end_time - drilling_session.start_time
            ).total_seconds()
            
            await session.flush()
        
        return drilling_session
    
    # =========================================================================
    # Alert Operations
    # =========================================================================
    
    async def create_alert(
        self,
        session: AsyncSession,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        source: str,
        **kwargs,
    ) -> Alert:
        """Create a new alert."""
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            source=source,
            **kwargs,
        )
        session.add(alert)
        await session.flush()
        return alert
    
    async def get_active_alerts(
        self,
        session: AsyncSession,
        severity: Optional[str] = None,
    ) -> Sequence[Alert]:
        """Get all active alerts."""
        query = select(Alert).where(Alert.status == AlertStatus.ACTIVE.value)
        
        if severity:
            query = query.where(Alert.severity == severity)
        
        query = query.order_by(desc(Alert.created_at))
        result = await session.execute(query)
        return result.scalars().all()
    
    async def acknowledge_alert(
        self,
        session: AsyncSession,
        alert_id: int,
        acknowledged_by: str,
    ) -> Optional[Alert]:
        """Acknowledge an alert."""
        query = select(Alert).where(Alert.id == alert_id)
        result = await session.execute(query)
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.status = AlertStatus.ACKNOWLEDGED.value
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            await session.flush()
        
        return alert
    
    # =========================================================================
    # Maintenance Operations
    # =========================================================================
    
    async def create_maintenance_task(
        self,
        session: AsyncSession,
        task_type: str,
        component_type: str,
        description: str,
        scheduled_date: datetime,
        **kwargs,
    ) -> MaintenanceRecord:
        """Create a new maintenance task."""
        task = MaintenanceRecord(
            task_type=task_type,
            component_type=component_type,
            description=description,
            scheduled_date=scheduled_date,
            **kwargs,
        )
        session.add(task)
        await session.flush()
        return task
    
    async def get_pending_maintenance(
        self,
        session: AsyncSession,
        days_ahead: int = 7,
    ) -> Sequence[MaintenanceRecord]:
        """Get maintenance tasks due within specified days."""
        cutoff = datetime.utcnow() + timedelta(days=days_ahead)
        
        query = select(MaintenanceRecord).where(
            and_(
                MaintenanceRecord.status.in_([
                    MaintenanceStatus.SCHEDULED.value,
                    MaintenanceStatus.OVERDUE.value,
                ]),
                MaintenanceRecord.scheduled_date <= cutoff,
            )
        ).order_by(MaintenanceRecord.scheduled_date)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    # =========================================================================
    # Data Retention Operations
    # =========================================================================
    
    async def aggregate_old_sensor_data(
        self,
        session: AsyncSession,
        older_than_days: Optional[int] = None,
    ) -> int:
        """
        Aggregate old sensor data and delete raw records.
        
        Args:
            session: Database session
            older_than_days: Days threshold. Uses config default if not specified.
            
        Returns:
            Number of aggregated records created.
        """
        days = older_than_days or self.config.raw_data_aggregation_after_days
        cutoff = datetime.utcnow() - timedelta(days=days)
        interval = self.config.aggregation_interval_minutes
        
        # This would be implemented with proper SQL aggregation
        # For SQLite, we'd need to handle this differently than PostgreSQL
        # Placeholder for the aggregation logic
        
        return 0
    
    async def cleanup_old_data(
        self,
        session: AsyncSession,
    ) -> dict[str, int]:
        """
        Remove data older than retention period.
        
        Returns:
            Dictionary with counts of deleted records per table.
        """
        deleted = {}
        now = datetime.utcnow()
        
        # Sensor readings
        sensor_cutoff = now - timedelta(days=self.config.sensor_data_retention_days)
        result = await session.execute(
            delete(SensorReading).where(SensorReading.timestamp < sensor_cutoff)
        )
        deleted["sensor_readings"] = result.rowcount
        
        # Predictions
        pred_cutoff = now - timedelta(days=self.config.prediction_retention_days)
        result = await session.execute(
            delete(MaterialPrediction).where(MaterialPrediction.timestamp < pred_cutoff)
        )
        deleted["predictions"] = result.rowcount
        
        # Alerts
        alert_cutoff = now - timedelta(days=self.config.alert_retention_days)
        result = await session.execute(
            delete(Alert).where(Alert.created_at < alert_cutoff)
        )
        deleted["alerts"] = result.rowcount
        
        await session.commit()
        return deleted


# =============================================================================
# Global Database Instance
# =============================================================================

_db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get or create the global database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    db = await get_db_manager()
    async for session in db.get_session():
        yield session


# Convenience exports
__all__ = [
    "Base",
    "SensorReading",
    "AggregatedSensorData",
    "DrillingSession",
    "MaterialPrediction",
    "Alert",
    "ComponentHealth",
    "MaintenanceRecord",
    "EnergyLog",
    "SensorHealth",
    "AlertStatus",
    "MaintenanceStatus",
    "ComponentType",
    "SensorType",
    "DatabaseManager",
    "get_db_manager",
    "get_db_session",
]

