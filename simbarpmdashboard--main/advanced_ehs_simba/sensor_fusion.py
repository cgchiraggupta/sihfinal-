"""
IoT Sensor Integration Module for Advanced EHS Simba Drill System.

This module provides:
- Real-time data collection from multiple sensors
- MQTT/WebSocket connectivity for live sensor streams
- Data buffering and preprocessing pipeline
- Sensor health monitoring and fault detection
- Integration with MaterialPredictor

Author: EHS Simba Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

import numpy as np
from scipy import signal

from config import MQTTConfig, SensorConfig, get_settings
from ml_predictor import MaterialPredictor, PredictionResult, SensorInput

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class SensorStatus(str, Enum):
    """Sensor health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAULTY = "faulty"
    OFFLINE = "offline"
    CALIBRATING = "calibrating"


class DataQuality(str, Enum):
    """Data quality indicators."""
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    INVALID = "invalid"


@dataclass
class SensorReading:
    """
    Individual sensor reading.
    
    Attributes:
        sensor_id: Unique identifier for the sensor
        sensor_type: Type of sensor (vibration, temperature, etc.)
        value: Measured value
        unit: Measurement unit
        timestamp: Reading timestamp
        quality: Data quality score (0-1)
        metadata: Additional metadata
    """
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    quality: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "quality": self.quality,
            "metadata": self.metadata,
        }


@dataclass
class FusedSensorData:
    """
    Fused data from all sensors at a point in time.
    
    This represents a complete snapshot of all sensor values,
    ready for ML prediction and analysis.
    """
    timestamp: datetime
    rpm: float
    current_a: float
    vibration_g: float
    depth_m: float
    pressure_bar: float
    temperature_hydraulic_c: float
    temperature_motor_c: float
    acoustic_db: float
    power_kw: float
    feed_rate_m_min: float
    
    # Quality metrics
    overall_quality: float = 1.0
    sensors_active: int = 0
    sensors_total: int = 0
    
    # Raw readings for detailed analysis
    raw_readings: dict[str, SensorReading] = field(default_factory=dict)
    
    def to_sensor_input(self) -> SensorInput:
        """Convert to SensorInput for ML prediction."""
        return SensorInput(
            rpm=self.rpm,
            current_a=self.current_a,
            vibration_g=self.vibration_g,
            depth_m=self.depth_m,
            pressure_bar=self.pressure_bar,
            temperature_c=max(self.temperature_hydraulic_c, self.temperature_motor_c),
            acoustic_db=self.acoustic_db,
            timestamp=self.timestamp,
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "rpm": self.rpm,
            "current_a": self.current_a,
            "vibration_g": self.vibration_g,
            "depth_m": self.depth_m,
            "pressure_bar": self.pressure_bar,
            "temperature_hydraulic_c": self.temperature_hydraulic_c,
            "temperature_motor_c": self.temperature_motor_c,
            "acoustic_db": self.acoustic_db,
            "power_kw": self.power_kw,
            "feed_rate_m_min": self.feed_rate_m_min,
            "overall_quality": self.overall_quality,
            "sensors_active": self.sensors_active,
            "sensors_total": self.sensors_total,
        }


@dataclass
class SensorHealthReport:
    """Health report for a single sensor."""
    sensor_id: str
    sensor_type: str
    status: SensorStatus
    last_reading_time: Optional[datetime]
    readings_per_second: float
    noise_level: float
    drift: float
    out_of_range_percent: float
    requires_calibration: bool
    message: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "status": self.status.value,
            "last_reading_time": self.last_reading_time.isoformat() if self.last_reading_time else None,
            "readings_per_second": self.readings_per_second,
            "noise_level": self.noise_level,
            "drift": self.drift,
            "out_of_range_percent": self.out_of_range_percent,
            "requires_calibration": self.requires_calibration,
            "message": self.message,
        }


# =============================================================================
# Sensor Buffer
# =============================================================================

class SensorBuffer:
    """
    Circular buffer for sensor data with statistics tracking.
    
    Provides:
    - Rolling window of recent readings
    - Statistical aggregation (mean, std, min, max)
    - Outlier detection
    - Data quality assessment
    """
    
    def __init__(
        self,
        sensor_id: str,
        sensor_type: str,
        buffer_size: int = 1000,
        expected_rate_hz: float = 10.0,
    ):
        """
        Initialize sensor buffer.
        
        Args:
            sensor_id: Unique sensor identifier
            sensor_type: Type of sensor
            buffer_size: Maximum readings to keep
            expected_rate_hz: Expected reading frequency
        """
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.buffer_size = buffer_size
        self.expected_rate_hz = expected_rate_hz
        
        self._buffer: deque[SensorReading] = deque(maxlen=buffer_size)
        self._last_reading: Optional[SensorReading] = None
        self._reading_count = 0
        self._out_of_range_count = 0
        
        # Statistics
        self._running_sum = 0.0
        self._running_sum_sq = 0.0
        
        # Health tracking
        self._last_health_check = datetime.utcnow()
        self._status = SensorStatus.OFFLINE
    
    @property
    def count(self) -> int:
        """Number of readings in buffer."""
        return len(self._buffer)
    
    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self._buffer) == 0
    
    @property
    def latest(self) -> Optional[SensorReading]:
        """Get most recent reading."""
        return self._last_reading
    
    @property
    def status(self) -> SensorStatus:
        """Get current sensor status."""
        return self._status
    
    def add(self, reading: SensorReading) -> None:
        """
        Add a new reading to the buffer.
        
        Args:
            reading: Sensor reading to add
        """
        # Remove oldest reading from statistics if buffer is full
        if len(self._buffer) >= self.buffer_size:
            oldest = self._buffer[0]
            self._running_sum -= oldest.value
            self._running_sum_sq -= oldest.value ** 2
        
        # Add new reading
        self._buffer.append(reading)
        self._last_reading = reading
        self._reading_count += 1
        
        # Update running statistics
        self._running_sum += reading.value
        self._running_sum_sq += reading.value ** 2
    
    def get_recent(self, n: int = 100) -> list[SensorReading]:
        """Get n most recent readings."""
        return list(self._buffer)[-n:]
    
    def get_values(self, n: Optional[int] = None) -> np.ndarray:
        """Get values as numpy array."""
        readings = list(self._buffer)[-n:] if n else list(self._buffer)
        return np.array([r.value for r in readings])
    
    def get_statistics(self) -> dict[str, float]:
        """
        Calculate buffer statistics.
        
        Returns:
            Dictionary with mean, std, min, max, count.
        """
        if self.is_empty:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0,
            }
        
        values = self.get_values()
        n = len(values)
        
        mean = self._running_sum / n
        variance = (self._running_sum_sq / n) - (mean ** 2)
        std = np.sqrt(max(0, variance))
        
        return {
            "mean": float(mean),
            "std": float(std),
            "min": float(values.min()),
            "max": float(values.max()),
            "count": n,
        }
    
    def get_rate_hz(self) -> float:
        """Calculate actual reading rate in Hz."""
        if len(self._buffer) < 2:
            return 0.0
        
        readings = list(self._buffer)[-100:]  # Use last 100 readings
        if len(readings) < 2:
            return 0.0
        
        time_span = (readings[-1].timestamp - readings[0].timestamp).total_seconds()
        if time_span <= 0:
            return 0.0
        
        return len(readings) / time_span
    
    def detect_outliers(self, z_threshold: float = 3.0) -> list[SensorReading]:
        """
        Detect outliers using z-score method.
        
        Args:
            z_threshold: Z-score threshold for outlier detection
            
        Returns:
            List of outlier readings.
        """
        if len(self._buffer) < 10:
            return []
        
        stats = self.get_statistics()
        if stats["std"] == 0:
            return []
        
        outliers = []
        for reading in self._buffer:
            z_score = abs((reading.value - stats["mean"]) / stats["std"])
            if z_score > z_threshold:
                outliers.append(reading)
        
        return outliers
    
    def assess_health(
        self,
        valid_range: tuple[float, float],
        max_data_age_s: float = 5.0,
    ) -> SensorHealthReport:
        """
        Assess sensor health based on buffer data.
        
        Args:
            valid_range: (min, max) valid value range
            max_data_age_s: Maximum acceptable data age in seconds
            
        Returns:
            SensorHealthReport with status and metrics.
        """
        now = datetime.utcnow()
        
        # Check for offline sensor
        if self._last_reading is None:
            self._status = SensorStatus.OFFLINE
            return SensorHealthReport(
                sensor_id=self.sensor_id,
                sensor_type=self.sensor_type,
                status=SensorStatus.OFFLINE,
                last_reading_time=None,
                readings_per_second=0.0,
                noise_level=0.0,
                drift=0.0,
                out_of_range_percent=0.0,
                requires_calibration=True,
                message="Sensor offline - no readings received",
            )
        
        # Check data age
        data_age = (now - self._last_reading.timestamp).total_seconds()
        if data_age > max_data_age_s:
            self._status = SensorStatus.OFFLINE
            return SensorHealthReport(
                sensor_id=self.sensor_id,
                sensor_type=self.sensor_type,
                status=SensorStatus.OFFLINE,
                last_reading_time=self._last_reading.timestamp,
                readings_per_second=0.0,
                noise_level=0.0,
                drift=0.0,
                out_of_range_percent=0.0,
                requires_calibration=False,
                message=f"Sensor offline - last reading {data_age:.1f}s ago",
            )
        
        # Calculate metrics
        rate_hz = self.get_rate_hz()
        stats = self.get_statistics()
        
        # Calculate out-of-range percentage
        values = self.get_values()
        out_of_range = np.sum((values < valid_range[0]) | (values > valid_range[1]))
        out_of_range_pct = (out_of_range / len(values)) * 100 if len(values) > 0 else 0
        
        # Calculate noise level (coefficient of variation)
        noise_level = stats["std"] / abs(stats["mean"]) if stats["mean"] != 0 else 0
        
        # Calculate drift (trend in recent readings)
        drift = 0.0
        if len(values) >= 50:
            first_half = values[:len(values)//2].mean()
            second_half = values[len(values)//2:].mean()
            drift = (second_half - first_half) / (abs(first_half) + 1e-10)
        
        # Determine status
        requires_calibration = False
        
        if out_of_range_pct > 20 or rate_hz < self.expected_rate_hz * 0.5:
            status = SensorStatus.FAULTY
            message = f"Sensor faulty - {out_of_range_pct:.1f}% out of range"
        elif out_of_range_pct > 5 or noise_level > 0.3 or abs(drift) > 0.2:
            status = SensorStatus.DEGRADED
            message = "Sensor degraded - elevated noise or drift"
            requires_calibration = abs(drift) > 0.1
        else:
            status = SensorStatus.HEALTHY
            message = "Sensor operating normally"
        
        self._status = status
        
        return SensorHealthReport(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            status=status,
            last_reading_time=self._last_reading.timestamp,
            readings_per_second=rate_hz,
            noise_level=noise_level,
            drift=drift,
            out_of_range_percent=out_of_range_pct,
            requires_calibration=requires_calibration,
            message=message,
        )
    
    def clear(self) -> None:
        """Clear all buffer data."""
        self._buffer.clear()
        self._last_reading = None
        self._running_sum = 0.0
        self._running_sum_sq = 0.0


# =============================================================================
# Data Preprocessor
# =============================================================================

class DataPreprocessor:
    """
    Preprocesses raw sensor data for ML pipeline.
    
    Provides:
    - Noise filtering
    - Outlier removal
    - Signal smoothing
    - Resampling
    """
    
    def __init__(self, config: Optional[SensorConfig] = None):
        """Initialize preprocessor with configuration."""
        self.config = config or get_settings().sensors
    
    def filter_noise(
        self,
        values: np.ndarray,
        cutoff_freq: float = 100.0,
        sampling_rate: float = 1000.0,
        order: int = 4,
    ) -> np.ndarray:
        """
        Apply low-pass Butterworth filter to remove noise.
        
        Args:
            values: Input signal
            cutoff_freq: Cutoff frequency in Hz
            sampling_rate: Sampling rate in Hz
            order: Filter order
            
        Returns:
            Filtered signal.
        """
        if len(values) < 12:  # Need enough samples for filter
            return values
        
        nyquist = sampling_rate / 2
        normalized_cutoff = min(cutoff_freq / nyquist, 0.99)
        
        b, a = signal.butter(order, normalized_cutoff, btype='low')
        
        # Use filtfilt for zero-phase filtering
        try:
            filtered = signal.filtfilt(b, a, values)
            return filtered
        except ValueError:
            return values
    
    def remove_outliers(
        self,
        values: np.ndarray,
        z_threshold: float = 3.0,
    ) -> np.ndarray:
        """
        Remove outliers using z-score method, replacing with median.
        
        Args:
            values: Input values
            z_threshold: Z-score threshold
            
        Returns:
            Values with outliers replaced.
        """
        if len(values) < 3:
            return values
        
        median = np.median(values)
        std = np.std(values)
        
        if std == 0:
            return values
        
        z_scores = np.abs((values - median) / std)
        cleaned = values.copy()
        cleaned[z_scores > z_threshold] = median
        
        return cleaned
    
    def smooth(
        self,
        values: np.ndarray,
        window_size: int = 5,
    ) -> np.ndarray:
        """
        Apply moving average smoothing.
        
        Args:
            values: Input values
            window_size: Smoothing window size
            
        Returns:
            Smoothed values.
        """
        if len(values) < window_size:
            return values
        
        kernel = np.ones(window_size) / window_size
        smoothed = np.convolve(values, kernel, mode='same')
        
        return smoothed
    
    def resample(
        self,
        readings: list[SensorReading],
        target_rate_hz: float,
    ) -> list[SensorReading]:
        """
        Resample readings to target rate using interpolation.
        
        Args:
            readings: Input readings
            target_rate_hz: Target sampling rate
            
        Returns:
            Resampled readings.
        """
        if len(readings) < 2:
            return readings
        
        # Get time range
        start_time = readings[0].timestamp
        end_time = readings[-1].timestamp
        duration = (end_time - start_time).total_seconds()
        
        if duration <= 0:
            return readings
        
        # Create new timestamps
        n_samples = int(duration * target_rate_hz)
        if n_samples < 1:
            return readings
        
        # Extract values and timestamps
        times = np.array([
            (r.timestamp - start_time).total_seconds()
            for r in readings
        ])
        values = np.array([r.value for r in readings])
        
        # Interpolate
        new_times = np.linspace(0, duration, n_samples)
        new_values = np.interp(new_times, times, values)
        
        # Create new readings
        resampled = []
        template = readings[0]
        
        for i, (t, v) in enumerate(zip(new_times, new_values)):
            new_timestamp = start_time + timedelta(seconds=t)
            resampled.append(SensorReading(
                sensor_id=template.sensor_id,
                sensor_type=template.sensor_type,
                value=float(v),
                unit=template.unit,
                timestamp=new_timestamp,
                quality=template.quality,
            ))
        
        return resampled
    
    def preprocess_pipeline(
        self,
        values: np.ndarray,
        sensor_type: str,
    ) -> np.ndarray:
        """
        Apply full preprocessing pipeline based on sensor type.
        
        Args:
            values: Raw sensor values
            sensor_type: Type of sensor
            
        Returns:
            Preprocessed values.
        """
        # Type-specific processing
        if sensor_type == "vibration":
            # Heavy filtering for vibration
            values = self.remove_outliers(values, z_threshold=4.0)
            values = self.filter_noise(
                values,
                cutoff_freq=200.0,
                sampling_rate=self.config.vibration.sampling_rate_hz
            )
        elif sensor_type == "acoustic":
            values = self.remove_outliers(values, z_threshold=3.5)
            values = self.smooth(values, window_size=3)
        else:
            # Standard processing
            values = self.remove_outliers(values)
            values = self.smooth(values, window_size=5)
        
        return values


# =============================================================================
# Sensor Fusion Engine
# =============================================================================

class SensorFusionEngine:
    """
    Main sensor fusion engine for the EHS Simba system.
    
    Combines data from multiple sensors into a unified data stream,
    performs real-time preprocessing, and integrates with the ML predictor.
    
    Example:
        >>> engine = SensorFusionEngine()
        >>> await engine.start()
        >>> 
        >>> # Process incoming sensor data
        >>> reading = SensorReading("vib_01", "vibration", 2.5, "g")
        >>> await engine.process_reading(reading)
        >>> 
        >>> # Get fused data for prediction
        >>> fused = engine.get_fused_data()
        >>> if fused:
        >>>     prediction = predictor.predict(fused.to_sensor_input())
    """
    
    def __init__(
        self,
        config: Optional[SensorConfig] = None,
        predictor: Optional[MaterialPredictor] = None,
    ):
        """
        Initialize sensor fusion engine.
        
        Args:
            config: Sensor configuration
            predictor: Material predictor instance (optional)
        """
        self.config = config or get_settings().sensors
        self.predictor = predictor
        self.preprocessor = DataPreprocessor(self.config)
        
        # Sensor buffers by sensor_id
        self._buffers: dict[str, SensorBuffer] = {}
        
        # Latest fused data
        self._fused_data: Optional[FusedSensorData] = None
        self._last_fusion_time: Optional[datetime] = None
        
        # Callbacks for new data
        self._data_callbacks: list[Callable[[FusedSensorData], None]] = []
        self._prediction_callbacks: list[Callable[[PredictionResult], None]] = []
        
        # State
        self._is_running = False
        self._fusion_task: Optional[asyncio.Task] = None
        
        # Sensor mapping (sensor_id -> sensor_type)
        self._sensor_mapping: dict[str, str] = {}
        
        # Expected sensors
        self._expected_sensors = {
            "rpm": "rpm_01",
            "current": "current_01",
            "vibration": "vib_01",
            "depth": "depth_01",
            "pressure": "pressure_01",
            "temperature_hydraulic": "temp_hyd_01",
            "temperature_motor": "temp_motor_01",
            "acoustic": "acoustic_01",
            "power": "power_01",
        }
        
        logger.info("SensorFusionEngine initialized")
    
    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._is_running
    
    @property
    def fused_data(self) -> Optional[FusedSensorData]:
        """Get latest fused sensor data."""
        return self._fused_data
    
    async def start(self) -> None:
        """Start the sensor fusion engine."""
        if self._is_running:
            return
        
        self._is_running = True
        
        # Initialize buffers for expected sensors
        for sensor_type, sensor_id in self._expected_sensors.items():
            expected_rate = self._get_expected_rate(sensor_type)
            self._buffers[sensor_id] = SensorBuffer(
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                buffer_size=int(expected_rate * 60),  # 1 minute of data
                expected_rate_hz=expected_rate,
            )
            self._sensor_mapping[sensor_id] = sensor_type
        
        # Start fusion loop
        self._fusion_task = asyncio.create_task(self._fusion_loop())
        
        logger.info("SensorFusionEngine started")
    
    async def stop(self) -> None:
        """Stop the sensor fusion engine."""
        self._is_running = False
        
        if self._fusion_task:
            self._fusion_task.cancel()
            try:
                await self._fusion_task
            except asyncio.CancelledError:
                pass
        
        logger.info("SensorFusionEngine stopped")
    
    async def process_reading(self, reading: SensorReading) -> None:
        """
        Process an incoming sensor reading.
        
        Args:
            reading: Sensor reading to process
        """
        sensor_id = reading.sensor_id
        
        # Create buffer if needed
        if sensor_id not in self._buffers:
            sensor_type = reading.sensor_type
            expected_rate = self._get_expected_rate(sensor_type)
            self._buffers[sensor_id] = SensorBuffer(
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                buffer_size=int(expected_rate * 60),
                expected_rate_hz=expected_rate,
            )
            self._sensor_mapping[sensor_id] = sensor_type
        
        # Add to buffer
        self._buffers[sensor_id].add(reading)
    
    async def process_batch(self, readings: list[SensorReading]) -> None:
        """Process a batch of readings efficiently."""
        for reading in readings:
            await self.process_reading(reading)
    
    def register_data_callback(
        self,
        callback: Callable[[FusedSensorData], None],
    ) -> None:
        """Register callback for new fused data."""
        self._data_callbacks.append(callback)
    
    def register_prediction_callback(
        self,
        callback: Callable[[PredictionResult], None],
    ) -> None:
        """Register callback for new predictions."""
        self._prediction_callbacks.append(callback)
    
    def get_fused_data(self) -> Optional[FusedSensorData]:
        """Get current fused sensor data."""
        return self._fuse_sensors()
    
    def get_sensor_health(self) -> dict[str, SensorHealthReport]:
        """
        Get health status for all sensors.
        
        Returns:
            Dictionary mapping sensor_id to health report.
        """
        reports = {}
        
        for sensor_id, buffer in self._buffers.items():
            sensor_type = self._sensor_mapping.get(sensor_id, "unknown")
            valid_range = self._get_valid_range(sensor_type)
            
            report = buffer.assess_health(
                valid_range=valid_range,
                max_data_age_s=self.config.max_data_age_s,
            )
            reports[sensor_id] = report
        
        return reports
    
    def get_buffer_statistics(self) -> dict[str, dict[str, float]]:
        """Get statistics for all sensor buffers."""
        return {
            sensor_id: buffer.get_statistics()
            for sensor_id, buffer in self._buffers.items()
        }
    
    async def _fusion_loop(self) -> None:
        """Main fusion loop running at regular intervals."""
        fusion_interval = 0.1  # 10 Hz fusion rate
        
        while self._is_running:
            try:
                # Fuse sensor data
                fused = self._fuse_sensors()
                
                if fused:
                    self._fused_data = fused
                    self._last_fusion_time = datetime.utcnow()
                    
                    # Notify callbacks
                    for callback in self._data_callbacks:
                        try:
                            callback(fused)
                        except Exception as e:
                            logger.error(f"Data callback error: {e}")
                    
                    # Run prediction if predictor available
                    if self.predictor and self.predictor.is_trained:
                        try:
                            prediction = self.predictor.predict(fused.to_sensor_input())
                            
                            for callback in self._prediction_callbacks:
                                try:
                                    callback(prediction)
                                except Exception as e:
                                    logger.error(f"Prediction callback error: {e}")
                        except Exception as e:
                            logger.error(f"Prediction error: {e}")
                
                await asyncio.sleep(fusion_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Fusion loop error: {e}")
                await asyncio.sleep(1.0)
    
    def _fuse_sensors(self) -> Optional[FusedSensorData]:
        """
        Fuse all sensor readings into a single data point.
        
        Returns:
            FusedSensorData or None if insufficient data.
        """
        # Collect latest values from each sensor type
        values = {}
        raw_readings = {}
        sensors_active = 0
        
        for sensor_type, default_sensor_id in self._expected_sensors.items():
            # Find buffer for this sensor type
            buffer = None
            for sid, buf in self._buffers.items():
                if self._sensor_mapping.get(sid) == sensor_type:
                    buffer = buf
                    break
            
            if buffer is None or buffer.is_empty:
                values[sensor_type] = self._get_default_value(sensor_type)
                continue
            
            # Check data freshness
            latest = buffer.latest
            if latest:
                age = (datetime.utcnow() - latest.timestamp).total_seconds()
                if age <= self.config.max_data_age_s:
                    values[sensor_type] = latest.value
                    raw_readings[sensor_type] = latest
                    sensors_active += 1
                else:
                    values[sensor_type] = self._get_default_value(sensor_type)
            else:
                values[sensor_type] = self._get_default_value(sensor_type)
        
        # Calculate overall quality
        total_sensors = len(self._expected_sensors)
        quality = sensors_active / total_sensors if total_sensors > 0 else 0
        
        # Need at least basic sensors (rpm, current, vibration, depth)
        essential = ["rpm", "current", "vibration", "depth"]
        has_essentials = all(
            sensor_type in values and values[sensor_type] != self._get_default_value(sensor_type)
            for sensor_type in essential
        )
        
        if not has_essentials and sensors_active < 2:
            return None
        
        # Calculate feed rate from depth changes
        feed_rate = 0.0
        depth_buffer = self._buffers.get(self._expected_sensors.get("depth"))
        if depth_buffer and depth_buffer.count >= 10:
            recent_depths = depth_buffer.get_values(10)
            if len(recent_depths) >= 2:
                depth_change = recent_depths[-1] - recent_depths[0]
                # Assume 10 readings over ~1 second
                feed_rate = abs(depth_change) * 60  # m/min
        
        return FusedSensorData(
            timestamp=datetime.utcnow(),
            rpm=values.get("rpm", 0.0),
            current_a=values.get("current", 0.0),
            vibration_g=values.get("vibration", 0.0),
            depth_m=values.get("depth", 0.0),
            pressure_bar=values.get("pressure", 200.0),
            temperature_hydraulic_c=values.get("temperature_hydraulic", 45.0),
            temperature_motor_c=values.get("temperature_motor", 50.0),
            acoustic_db=values.get("acoustic", 70.0),
            power_kw=values.get("power", 50.0),
            feed_rate_m_min=feed_rate,
            overall_quality=quality,
            sensors_active=sensors_active,
            sensors_total=total_sensors,
            raw_readings=raw_readings,
        )
    
    def _get_expected_rate(self, sensor_type: str) -> float:
        """Get expected sampling rate for sensor type."""
        rates = {
            "vibration": self.config.vibration.sampling_rate_hz,
            "temperature": self.config.temperature.sampling_rate_hz,
            "temperature_hydraulic": self.config.temperature.sampling_rate_hz,
            "temperature_motor": self.config.temperature.sampling_rate_hz,
            "pressure": self.config.pressure.sampling_rate_hz,
            "acoustic": 100.0,  # Downsampled from high rate
            "power": self.config.power.sampling_rate_hz,
            "rpm": 10.0,
            "current": 10.0,
            "depth": 10.0,
        }
        return rates.get(sensor_type, 10.0)
    
    def _get_valid_range(self, sensor_type: str) -> tuple[float, float]:
        """Get valid value range for sensor type."""
        ranges = {
            "vibration": (0.0, 15.0),
            "temperature": (0.0, 150.0),
            "temperature_hydraulic": (0.0, 120.0),
            "temperature_motor": (0.0, 150.0),
            "pressure": (0.0, 500.0),
            "acoustic": (20.0, 140.0),
            "power": (0.0, 500.0),
            "rpm": (0.0, 300.0),
            "current": (0.0, 500.0),
            "depth": (0.0, 100.0),
        }
        return ranges.get(sensor_type, (0.0, 1000.0))
    
    def _get_default_value(self, sensor_type: str) -> float:
        """Get default value for missing sensor data."""
        defaults = {
            "rpm": 0.0,
            "current": 0.0,
            "vibration": 0.0,
            "depth": 0.0,
            "pressure": 200.0,
            "temperature_hydraulic": 45.0,
            "temperature_motor": 50.0,
            "acoustic": 70.0,
            "power": 0.0,
        }
        return defaults.get(sensor_type, 0.0)


# =============================================================================
# MQTT Client for Sensor Data
# =============================================================================

class MQTTSensorClient:
    """
    MQTT client for receiving sensor data from IoT devices.
    
    Connects to MQTT broker and routes incoming sensor messages
    to the SensorFusionEngine.
    """
    
    def __init__(
        self,
        fusion_engine: SensorFusionEngine,
        config: Optional[MQTTConfig] = None,
    ):
        """
        Initialize MQTT client.
        
        Args:
            fusion_engine: Sensor fusion engine to send data to
            config: MQTT configuration
        """
        self.fusion_engine = fusion_engine
        self.config = config or get_settings().mqtt
        
        self._client = None
        self._is_connected = False
        self._reconnect_task: Optional[asyncio.Task] = None
        
        logger.info(f"MQTTSensorClient initialized for {self.config.broker_host}:{self.config.broker_port}")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self._is_connected
    
    async def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connected successfully.
        """
        if not self.config.enabled:
            logger.info("MQTT disabled in configuration")
            return False
        
        try:
            # Import aiomqtt here to avoid issues if not installed
            import aiomqtt
            
            self._client = aiomqtt.Client(
                hostname=self.config.broker_host,
                port=self.config.broker_port,
                username=self.config.username,
                password=self.config.password,
                identifier=self.config.client_id,
            )
            
            await self._client.__aenter__()
            self._is_connected = True
            
            # Subscribe to sensor topics
            topic = f"{self.config.sensor_topic_prefix}/#"
            await self._client.subscribe(topic, qos=self.config.qos)
            
            logger.info(f"Connected to MQTT broker, subscribed to {topic}")
            return True
            
        except ImportError:
            logger.warning("aiomqtt not installed, MQTT client unavailable")
            return False
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self._client and self._is_connected:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"MQTT disconnect error: {e}")
            finally:
                self._is_connected = False
    
    async def listen(self) -> None:
        """
        Listen for incoming sensor messages.
        
        This is a blocking call that processes messages until stopped.
        """
        if not self._is_connected or not self._client:
            logger.warning("Cannot listen - not connected")
            return
        
        try:
            async for message in self._client.messages:
                await self._process_message(message)
        except Exception as e:
            logger.error(f"MQTT listen error: {e}")
            self._is_connected = False
    
    async def _process_message(self, message) -> None:
        """Process incoming MQTT message."""
        try:
            # Parse topic to get sensor info
            # Expected format: ehs/simba/sensors/<sensor_type>/<sensor_id>
            topic_parts = str(message.topic).split("/")
            
            if len(topic_parts) >= 5:
                sensor_type = topic_parts[-2]
                sensor_id = topic_parts[-1]
            else:
                sensor_type = "unknown"
                sensor_id = topic_parts[-1] if topic_parts else "unknown"
            
            # Parse payload
            payload = json.loads(message.payload.decode())
            
            # Create sensor reading
            reading = SensorReading(
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                value=float(payload.get("value", 0)),
                unit=payload.get("unit", ""),
                timestamp=datetime.fromisoformat(payload["timestamp"]) 
                    if "timestamp" in payload else datetime.utcnow(),
                quality=float(payload.get("quality", 1.0)),
                metadata=payload.get("metadata", {}),
            )
            
            # Send to fusion engine
            await self.fusion_engine.process_reading(reading)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in MQTT message: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")


# =============================================================================
# Convenience Functions
# =============================================================================

_fusion_engine: Optional[SensorFusionEngine] = None


async def get_fusion_engine() -> SensorFusionEngine:
    """
    Get or create the global sensor fusion engine.
    
    Returns:
        SensorFusionEngine: Singleton engine instance.
    """
    global _fusion_engine
    if _fusion_engine is None:
        _fusion_engine = SensorFusionEngine()
        await _fusion_engine.start()
    return _fusion_engine


# Convenience exports
__all__ = [
    "SensorStatus",
    "DataQuality",
    "SensorReading",
    "FusedSensorData",
    "SensorHealthReport",
    "SensorBuffer",
    "DataPreprocessor",
    "SensorFusionEngine",
    "MQTTSensorClient",
    "get_fusion_engine",
]

