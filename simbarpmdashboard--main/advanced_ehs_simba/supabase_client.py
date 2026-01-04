"""
Supabase Client Module for Advanced EHS Simba Drill System.

This module provides:
- Async Supabase client for database operations
- CRUD operations for all EHS tables
- Real-time subscriptions for sensor data
- Data aggregation and retention operations

Author: EHS Simba Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence
from uuid import uuid4

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from config import get_settings, SupabaseConfig


# =============================================================================
# Table Names (with prefix)
# =============================================================================

TABLE_SENSOR_READINGS = "ehs_sensor_readings"
TABLE_AGGREGATED_SENSOR_DATA = "ehs_aggregated_sensor_data"
TABLE_DRILLING_SESSIONS = "ehs_drilling_sessions"
TABLE_MATERIAL_PREDICTIONS = "ehs_material_predictions"
TABLE_ALERTS = "ehs_alerts"
TABLE_COMPONENT_HEALTH = "ehs_component_health"
TABLE_MAINTENANCE_RECORDS = "ehs_maintenance_records"
TABLE_ENERGY_LOGS = "ehs_energy_logs"
TABLE_SENSOR_HEALTH = "ehs_sensor_health"


# =============================================================================
# Supabase Database Manager
# =============================================================================

class SupabaseManager:
    """
    Supabase database manager for the EHS Simba system.
    
    Provides connection management and common database operations.
    """
    
    def __init__(self, config: Optional[SupabaseConfig] = None):
        """
        Initialize the Supabase manager.
        
        Args:
            config: Supabase configuration. Uses default settings if not provided.
        """
        self.config = config or get_settings().database.supabase
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get or create the Supabase client."""
        if self._client is None:
            self._client = create_client(
                self.config.url,
                self.config.anon_key,
            )
        return self._client
    
    async def initialize(self) -> None:
        """Initialize the Supabase connection."""
        # Test connection by fetching a simple query
        try:
            self.client.table(TABLE_DRILLING_SESSIONS).select("id").limit(1).execute()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {e}")
    
    async def close(self) -> None:
        """Close Supabase connection."""
        # Supabase Python client doesn't require explicit closing
        self._client = None
    
    # =========================================================================
    # Sensor Data Operations
    # =========================================================================
    
    async def insert_sensor_reading(
        self,
        sensor_type: str,
        sensor_id: str,
        value: float,
        unit: str,
        quality: float = 1.0,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Insert a new sensor reading."""
        data = {
            "sensor_type": sensor_type,
            "sensor_id": sensor_id,
            "value": value,
            "unit": unit,
            "quality": quality,
            "metadata": metadata or {},
        }
        
        result = self.client.table(TABLE_SENSOR_READINGS).insert(data).execute()
        return result.data[0] if result.data else {}
    
    async def bulk_insert_readings(
        self,
        readings: list[dict[str, Any]],
    ) -> int:
        """
        Bulk insert sensor readings for performance.
        
        Args:
            readings: List of reading dictionaries
            
        Returns:
            Number of inserted records.
        """
        if not readings:
            return 0
        
        result = self.client.table(TABLE_SENSOR_READINGS).insert(readings).execute()
        return len(result.data) if result.data else 0
    
    async def get_sensor_readings(
        self,
        sensor_type: Optional[str] = None,
        sensor_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """Query sensor readings with filters."""
        query = self.client.table(TABLE_SENSOR_READINGS).select("*")
        
        if sensor_type:
            query = query.eq("sensor_type", sensor_type)
        if sensor_id:
            query = query.eq("sensor_id", sensor_id)
        if start_time:
            query = query.gte("timestamp", start_time.isoformat())
        if end_time:
            query = query.lte("timestamp", end_time.isoformat())
        
        query = query.order("timestamp", desc=True).limit(limit)
        
        result = query.execute()
        return result.data or []
    
    async def get_latest_sensor_reading(
        self,
        sensor_type: str,
        sensor_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Get the most recent sensor reading."""
        query = self.client.table(TABLE_SENSOR_READINGS).select("*")
        query = query.eq("sensor_type", sensor_type)
        
        if sensor_id:
            query = query.eq("sensor_id", sensor_id)
        
        query = query.order("timestamp", desc=True).limit(1)
        
        result = query.execute()
        return result.data[0] if result.data else None
    
    # =========================================================================
    # Drilling Session Operations
    # =========================================================================
    
    async def create_drilling_session(
        self,
        hole_id: str,
        target_depth_m: float,
        **kwargs,
    ) -> dict:
        """Create a new drilling session."""
        data = {
            "id": str(uuid4()),
            "hole_id": hole_id,
            "target_depth_m": target_depth_m,
            "start_time": datetime.utcnow().isoformat(),
            "is_active": True,
            **kwargs,
        }
        
        result = self.client.table(TABLE_DRILLING_SESSIONS).insert(data).execute()
        return result.data[0] if result.data else {}
    
    async def get_active_session(self) -> Optional[dict]:
        """Get the currently active drilling session."""
        result = (
            self.client.table(TABLE_DRILLING_SESSIONS)
            .select("*")
            .eq("is_active", True)
            .order("start_time", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    
    async def get_drilling_session(self, session_id: str) -> Optional[dict]:
        """Get a specific drilling session by ID."""
        result = (
            self.client.table(TABLE_DRILLING_SESSIONS)
            .select("*")
            .eq("id", session_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    
    async def end_drilling_session(
        self,
        session_id: str,
        actual_depth_m: float,
        completion_status: str = "completed",
    ) -> Optional[dict]:
        """End a drilling session."""
        session = await self.get_drilling_session(session_id)
        if not session:
            return None
        
        start_time = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
        end_time = datetime.now(start_time.tzinfo)  # Use same timezone
        total_time = (end_time - start_time).total_seconds()
        
        update_data = {
            "end_time": end_time.isoformat(),
            "actual_depth_m": actual_depth_m,
            "is_active": False,
            "completion_status": completion_status,
            "total_drilling_time_s": total_time,
        }
        
        result = (
            self.client.table(TABLE_DRILLING_SESSIONS)
            .update(update_data)
            .eq("id", session_id)
            .execute()
        )
        return result.data[0] if result.data else None
    
    async def get_session_statistics(
        self,
        days: int = 30,
    ) -> dict:
        """Get drilling session statistics."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        result = (
            self.client.table(TABLE_DRILLING_SESSIONS)
            .select("*")
            .gte("start_time", cutoff)
            .execute()
        )
        
        sessions = result.data or []
        
        if not sessions:
            return {
                "total_sessions": 0,
                "completed_sessions": 0,
                "total_depth_m": 0,
                "avg_penetration_rate": 0,
                "total_energy_kwh": 0,
            }
        
        completed = [s for s in sessions if s.get("completion_status") == "completed"]
        
        return {
            "total_sessions": len(sessions),
            "completed_sessions": len(completed),
            "total_depth_m": sum(s.get("actual_depth_m", 0) or 0 for s in sessions),
            "avg_penetration_rate": sum(s.get("avg_penetration_rate", 0) or 0 for s in completed) / len(completed) if completed else 0,
            "total_energy_kwh": sum(s.get("energy_consumed_kwh", 0) or 0 for s in sessions),
        }
    
    # =========================================================================
    # Material Prediction Operations
    # =========================================================================
    
    async def insert_prediction(
        self,
        session_id: str,
        depth_m: float,
        predicted_material: str,
        confidence: float,
        rpm: float,
        current_a: float,
        vibration_g: float,
        pressure_bar: Optional[float] = None,
        temperature_c: Optional[float] = None,
        class_probabilities: Optional[dict] = None,
    ) -> dict:
        """Insert a new material prediction."""
        data = {
            "session_id": session_id,
            "depth_m": depth_m,
            "predicted_material": predicted_material,
            "confidence": confidence,
            "rpm": rpm,
            "current_a": current_a,
            "vibration_g": vibration_g,
            "pressure_bar": pressure_bar,
            "temperature_c": temperature_c,
            "class_probabilities": class_probabilities or {},
        }
        
        result = self.client.table(TABLE_MATERIAL_PREDICTIONS).insert(data).execute()
        return result.data[0] if result.data else {}
    
    async def get_predictions_for_session(
        self,
        session_id: str,
        limit: int = 1000,
    ) -> list[dict]:
        """Get all predictions for a drilling session."""
        result = (
            self.client.table(TABLE_MATERIAL_PREDICTIONS)
            .select("*")
            .eq("session_id", session_id)
            .order("depth_m")
            .limit(limit)
            .execute()
        )
        return result.data or []
    
    async def get_material_distribution(
        self,
        session_id: Optional[str] = None,
        days: int = 30,
    ) -> dict[str, int]:
        """Get material type distribution."""
        query = self.client.table(TABLE_MATERIAL_PREDICTIONS).select("predicted_material")
        
        if session_id:
            query = query.eq("session_id", session_id)
        else:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            query = query.gte("timestamp", cutoff)
        
        result = query.execute()
        
        distribution = {}
        for row in result.data or []:
            material = row["predicted_material"]
            distribution[material] = distribution.get(material, 0) + 1
        
        return distribution
    
    # =========================================================================
    # Alert Operations
    # =========================================================================
    
    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        source: str,
        **kwargs,
    ) -> dict:
        """Create a new alert."""
        data = {
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "source": source,
            "status": "active",
            **kwargs,
        }
        
        result = self.client.table(TABLE_ALERTS).insert(data).execute()
        return result.data[0] if result.data else {}
    
    async def get_active_alerts(
        self,
        severity: Optional[str] = None,
    ) -> list[dict]:
        """Get all active alerts."""
        query = self.client.table(TABLE_ALERTS).select("*").eq("status", "active")
        
        if severity:
            query = query.eq("severity", severity)
        
        query = query.order("created_at", desc=True)
        
        result = query.execute()
        return result.data or []
    
    async def acknowledge_alert(
        self,
        alert_id: int,
        acknowledged_by: str,
    ) -> Optional[dict]:
        """Acknowledge an alert."""
        update_data = {
            "status": "acknowledged",
            "acknowledged_at": datetime.utcnow().isoformat(),
            "acknowledged_by": acknowledged_by,
        }
        
        result = (
            self.client.table(TABLE_ALERTS)
            .update(update_data)
            .eq("id", alert_id)
            .execute()
        )
        return result.data[0] if result.data else None
    
    async def resolve_alert(
        self,
        alert_id: int,
        resolution_notes: Optional[str] = None,
    ) -> Optional[dict]:
        """Resolve an alert."""
        update_data = {
            "status": "resolved",
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution_notes": resolution_notes,
        }
        
        result = (
            self.client.table(TABLE_ALERTS)
            .update(update_data)
            .eq("id", alert_id)
            .execute()
        )
        return result.data[0] if result.data else None
    
    async def get_alert_statistics(
        self,
        days: int = 30,
    ) -> dict:
        """Get alert statistics."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        result = (
            self.client.table(TABLE_ALERTS)
            .select("*")
            .gte("created_at", cutoff)
            .execute()
        )
        
        alerts = result.data or []
        
        by_severity = {}
        by_type = {}
        
        for alert in alerts:
            severity = alert.get("severity", "unknown")
            alert_type = alert.get("alert_type", "unknown")
            
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
        
        return {
            "total_alerts": len(alerts),
            "active_alerts": len([a for a in alerts if a.get("status") == "active"]),
            "by_severity": by_severity,
            "by_type": by_type,
        }
    
    # =========================================================================
    # Component Health Operations
    # =========================================================================
    
    async def update_component_health(
        self,
        component_type: str,
        component_id: str,
        health_score: float,
        wear_percentage: float,
        operating_hours: float,
        **kwargs,
    ) -> dict:
        """Update or insert component health record."""
        data = {
            "component_type": component_type,
            "component_id": component_id,
            "health_score": health_score,
            "wear_percentage": wear_percentage,
            "operating_hours": operating_hours,
            **kwargs,
        }
        
        result = self.client.table(TABLE_COMPONENT_HEALTH).insert(data).execute()
        return result.data[0] if result.data else {}
    
    async def get_component_health(
        self,
        component_type: Optional[str] = None,
        component_id: Optional[str] = None,
    ) -> list[dict]:
        """Get latest component health records."""
        query = self.client.table(TABLE_COMPONENT_HEALTH).select("*")
        
        if component_type:
            query = query.eq("component_type", component_type)
        if component_id:
            query = query.eq("component_id", component_id)
        
        query = query.order("timestamp", desc=True).limit(100)
        
        result = query.execute()
        return result.data or []
    
    async def get_components_needing_attention(
        self,
        health_threshold: float = 50.0,
    ) -> list[dict]:
        """Get components with low health scores."""
        result = (
            self.client.table(TABLE_COMPONENT_HEALTH)
            .select("*")
            .lt("health_score", health_threshold)
            .order("health_score")
            .execute()
        )
        return result.data or []
    
    # =========================================================================
    # Maintenance Operations
    # =========================================================================
    
    async def create_maintenance_task(
        self,
        task_type: str,
        component_type: str,
        description: str,
        scheduled_date: datetime,
        **kwargs,
    ) -> dict:
        """Create a new maintenance task."""
        data = {
            "task_type": task_type,
            "component_type": component_type,
            "description": description,
            "scheduled_date": scheduled_date.isoformat(),
            "status": "scheduled",
            **kwargs,
        }
        
        result = self.client.table(TABLE_MAINTENANCE_RECORDS).insert(data).execute()
        return result.data[0] if result.data else {}
    
    async def get_pending_maintenance(
        self,
        days_ahead: int = 7,
    ) -> list[dict]:
        """Get maintenance tasks due within specified days."""
        cutoff = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
        
        result = (
            self.client.table(TABLE_MAINTENANCE_RECORDS)
            .select("*")
            .in_("status", ["scheduled", "overdue"])
            .lte("scheduled_date", cutoff)
            .order("scheduled_date")
            .execute()
        )
        return result.data or []
    
    async def complete_maintenance_task(
        self,
        task_id: int,
        work_performed: str,
        completed_by: str,
        parts_replaced: Optional[list] = None,
        cost: Optional[float] = None,
    ) -> Optional[dict]:
        """Mark a maintenance task as completed."""
        update_data = {
            "status": "completed",
            "completed_date": datetime.utcnow().isoformat(),
            "work_performed": work_performed,
            "completed_by": completed_by,
            "parts_replaced": parts_replaced or [],
            "cost": cost,
        }
        
        result = (
            self.client.table(TABLE_MAINTENANCE_RECORDS)
            .update(update_data)
            .eq("id", task_id)
            .execute()
        )
        return result.data[0] if result.data else None
    
    # =========================================================================
    # Energy Log Operations
    # =========================================================================
    
    async def log_energy(
        self,
        power_kw: float,
        energy_kwh: float,
        session_id: Optional[str] = None,
        drilling_state: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Log energy consumption."""
        data = {
            "power_kw": power_kw,
            "energy_kwh": energy_kwh,
            "session_id": session_id,
            "drilling_state": drilling_state,
            **kwargs,
        }
        
        result = self.client.table(TABLE_ENERGY_LOGS).insert(data).execute()
        return result.data[0] if result.data else {}
    
    async def get_energy_consumption(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict:
        """Get energy consumption statistics."""
        query = self.client.table(TABLE_ENERGY_LOGS).select("*")
        
        if session_id:
            query = query.eq("session_id", session_id)
        if start_time:
            query = query.gte("timestamp", start_time.isoformat())
        if end_time:
            query = query.lte("timestamp", end_time.isoformat())
        
        result = query.execute()
        logs = result.data or []
        
        if not logs:
            return {
                "total_energy_kwh": 0,
                "avg_power_kw": 0,
                "peak_power_kw": 0,
                "total_cost_usd": 0,
            }
        
        return {
            "total_energy_kwh": sum(l.get("energy_kwh", 0) for l in logs),
            "avg_power_kw": sum(l.get("power_kw", 0) for l in logs) / len(logs),
            "peak_power_kw": max(l.get("power_kw", 0) for l in logs),
            "total_cost_usd": sum(l.get("cost_usd", 0) or 0 for l in logs),
        }
    
    # =========================================================================
    # Sensor Health Operations
    # =========================================================================
    
    async def update_sensor_health(
        self,
        sensor_id: str,
        sensor_type: str,
        is_healthy: bool,
        **kwargs,
    ) -> dict:
        """Update sensor health status."""
        data = {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "is_healthy": is_healthy,
            **kwargs,
        }
        
        result = self.client.table(TABLE_SENSOR_HEALTH).insert(data).execute()
        return result.data[0] if result.data else {}
    
    async def get_unhealthy_sensors(self) -> list[dict]:
        """Get list of unhealthy sensors."""
        result = (
            self.client.table(TABLE_SENSOR_HEALTH)
            .select("*")
            .eq("is_healthy", False)
            .order("timestamp", desc=True)
            .execute()
        )
        return result.data or []
    
    # =========================================================================
    # Data Cleanup Operations
    # =========================================================================
    
    async def cleanup_old_data(self, retention_days: int = 90) -> dict[str, int]:
        """
        Remove data older than retention period.
        
        Returns:
            Dictionary with counts of deleted records per table.
        """
        deleted = {}
        cutoff = (datetime.utcnow() - timedelta(days=retention_days)).isoformat()
        
        # Sensor readings
        result = (
            self.client.table(TABLE_SENSOR_READINGS)
            .delete()
            .lt("timestamp", cutoff)
            .execute()
        )
        deleted["sensor_readings"] = len(result.data) if result.data else 0
        
        return deleted


# =============================================================================
# Global Supabase Instance
# =============================================================================

_supabase_manager: Optional[SupabaseManager] = None


async def get_supabase_manager() -> SupabaseManager:
    """Get or create the global Supabase manager."""
    global _supabase_manager
    if _supabase_manager is None:
        _supabase_manager = SupabaseManager()
        await _supabase_manager.initialize()
    return _supabase_manager


def get_supabase_client() -> Client:
    """Get the Supabase client synchronously."""
    global _supabase_manager
    if _supabase_manager is None:
        _supabase_manager = SupabaseManager()
    return _supabase_manager.client


# Convenience exports
__all__ = [
    "SupabaseManager",
    "get_supabase_manager",
    "get_supabase_client",
    "TABLE_SENSOR_READINGS",
    "TABLE_AGGREGATED_SENSOR_DATA",
    "TABLE_DRILLING_SESSIONS",
    "TABLE_MATERIAL_PREDICTIONS",
    "TABLE_ALERTS",
    "TABLE_COMPONENT_HEALTH",
    "TABLE_MAINTENANCE_RECORDS",
    "TABLE_ENERGY_LOGS",
    "TABLE_SENSOR_HEALTH",
]

