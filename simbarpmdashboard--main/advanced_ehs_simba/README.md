# Advanced EHS Simba Drill Monitoring & Predictive System

A comprehensive Python-based solution for Electric Hydraulic System (EHS) Simba drill monitoring, predictive maintenance, and real-time analytics.

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0.0-orange)

## 🎯 Overview

The Advanced EHS Simba System provides:

- **Machine Learning Material Prediction**: Real-time rock/material type classification using sensor data
- **IoT Sensor Integration**: Multi-sensor data fusion with MQTT/WebSocket connectivity
- **Predictive Maintenance**: Component health monitoring with Weibull distribution analysis
- **Energy Optimization**: Power consumption tracking and efficiency recommendations
- **Advanced Analytics**: Drilling pattern analysis, hole quality scoring, and ROI calculations
- **Safety Monitoring**: Real-time hazard detection with automatic emergency shutdown

## 📁 Project Structure

```
advanced_ehs_simba/
├── __init__.py              # Package initialization
├── ml_predictor.py          # Material prediction ML model
├── sensor_fusion.py         # IoT sensor integration & data fusion
├── maintenance_predictor.py # Predictive maintenance engine
├── energy_optimizer.py      # Energy efficiency analyzer
├── analytics_engine.py      # Advanced drilling analytics
├── safety_monitor.py        # Safety & hazard detection
├── dashboard_api.py         # FastAPI REST/WebSocket backend
├── database.py              # SQLAlchemy database models
├── config.py                # Configuration management
├── models/                  # ML model storage
├── tests/                   # Unit tests
│   ├── test_ml_predictor.py
│   ├── test_maintenance_predictor.py
│   └── test_safety_monitor.py
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd advanced_ehs_simba
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Initialize the database**
```python
from database import get_db_manager
import asyncio

async def init():
    db = await get_db_manager()
    print("Database initialized!")

asyncio.run(init())
```

5. **Start the API server**
```bash
python dashboard_api.py
# Or using uvicorn directly:
uvicorn dashboard_api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

## 📖 Module Documentation

### Material Prediction (`ml_predictor.py`)

Predicts rock/material types using sensor data with ensemble ML models.

```python
from ml_predictor import MaterialPredictor, SensorInput

# Initialize predictor
predictor = MaterialPredictor()
predictor.load_or_train()

# Make prediction
sensor_data = SensorInput(
    rpm=80.0,
    current_a=150.0,
    vibration_g=2.5,
    depth_m=15.0,
    pressure_bar=250.0,
    temperature_c=55.0
)

result = predictor.predict(sensor_data)
print(f"Material: {result.material} ({result.confidence:.1%})")
print(f"Recommended RPM: {result.recommended_rpm}")
```

**Supported Material Types:**
- soft_soil, clay, sandstone, limestone
- granite, basalt, ore_body, void

### Sensor Fusion (`sensor_fusion.py`)

Real-time multi-sensor data collection and preprocessing.

```python
from sensor_fusion import SensorFusionEngine, SensorReading
import asyncio

async def main():
    engine = SensorFusionEngine()
    await engine.start()
    
    # Process sensor reading
    reading = SensorReading(
        sensor_id="vib_01",
        sensor_type="vibration",
        value=2.5,
        unit="g"
    )
    await engine.process_reading(reading)
    
    # Get fused data
    fused = engine.get_fused_data()
    if fused:
        print(f"RPM: {fused.rpm}, Depth: {fused.depth_m}m")
    
    await engine.stop()

asyncio.run(main())
```

**Features:**
- Circular buffers with rolling statistics
- Outlier detection and noise filtering
- Sensor health monitoring
- MQTT integration for IoT devices

### Predictive Maintenance (`maintenance_predictor.py`)

Component health monitoring with RUL (Remaining Useful Life) prediction.

```python
from maintenance_predictor import PredictiveMaintenanceEngine

engine = PredictiveMaintenanceEngine()

# Update drill bit data
health = engine.update_drill_bit_data(
    operating_hours=350,
    vibration_history=[1.5, 1.6, 1.8, 2.0, 2.2],
    materials_drilled={"granite": 100, "sandstone": 250},
    current_vibration=2.2
)

print(f"Drill Bit Health: {health.health_score:.1f}%")
print(f"RUL: {health.rul_hours:.0f} hours")
print(f"Status: {health.status.value}")

# Get maintenance schedule
tasks = engine.get_maintenance_schedule(days_ahead=30)
for task in tasks:
    print(f"- {task.description} (Due: {task.due_date})")
```

**Monitored Components:**
- Drill bits (wear tracking)
- Bearings (vibration analysis)
- Hydraulic seals, pumps, hoses
- Filters and gearboxes

### Energy Optimizer (`energy_optimizer.py`)

Power consumption monitoring and optimization recommendations.

```python
from energy_optimizer import EnergyOptimizer, PowerReading, DrillState
from datetime import datetime

optimizer = EnergyOptimizer()

# Add power reading
reading = PowerReading(
    timestamp=datetime.utcnow(),
    power_kw=150.0,
    voltage_v=480.0,
    current_a=195.0,
    power_factor=0.95,
    state=DrillState.DRILLING
)
optimizer.add_power_reading(reading)

# Get metrics
metrics = optimizer.get_energy_metrics(hours=24.0)
print(f"Energy: {metrics.total_energy_kwh:.1f} kWh")
print(f"Cost: ${metrics.cost_usd:.2f}")
print(f"Efficiency: {metrics.efficiency_percent:.1f}%")

# Get recommendations
for rec in optimizer.get_recommendations():
    print(f"- {rec.description}")
    print(f"  Potential savings: ${rec.potential_savings_usd:.2f}/day")
```

**Features:**
- Real-time power monitoring
- Peak demand management
- EHS vs pneumatic cost comparison
- RPM optimization by material

### Safety Monitor (`safety_monitor.py`)

Real-time hazard detection with automatic emergency response.

```python
from safety_monitor import SafetyMonitor

monitor = SafetyMonitor()

# Check all sensors
alerts = monitor.check_all(
    vibration_g=4.5,        # High!
    hydraulic_temp_c=75.0,  # Warning
    motor_temp_c=85.0,
    pressure_bar=320.0,     # Warning
    resistance=150.0,
    depth_m=25.0
)

# Handle alerts
for alert in alerts:
    print(f"⚠️ {alert.level.value.upper()}: {alert.message}")
    print(f"   Action: {alert.recommended_action.value}")

# Check system status
status = monitor.get_status()
print(f"System Safe: {status.is_safe}")
print(f"Health Score: {status.system_health:.0f}%")
```

**Monitored Hazards:**
- Excessive vibration
- Overheat (hydraulic/motor)
- Pressure anomalies
- Ground instability
- Operator fatigue

### Analytics Engine (`analytics_engine.py`)

Advanced drilling analytics and ROI calculations.

```python
from analytics_engine import AnalyticsEngine

engine = AnalyticsEngine()

# Score a completed hole
score = engine.score_hole(
    hole_id="HOLE-001",
    target_depth_m=30.0,
    actual_depth_m=29.8,
    max_deviation_m=0.25,
    collar_offset_m=0.05,
    angle_deviation_deg=1.2
)
print(f"Hole Grade: {score.overall_grade.value}")
print(f"Score: {score.overall_score:.1f}/100")

# Calculate ROI
roi = engine.calculate_roi(years=10, discount_rate=0.08)
print(f"NPV: ${roi.npv:,.0f}")
print(f"IRR: {roi.irr_percent:.1f}%")
print(f"Payback: {roi.simple_payback_years:.1f} years")
```

**Analytics Features:**
- Material layer detection
- Geological anomaly detection
- Hole quality scoring (A-F grades)
- EHS vs conventional ROI/TCO analysis

### Dashboard API (`dashboard_api.py`)

FastAPI REST and WebSocket endpoints for real-time dashboard.

**Key Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | System status |
| `/predict` | POST | Material prediction |
| `/sensors/current` | GET | Current sensor readings |
| `/maintenance/health` | GET | Component health status |
| `/maintenance/schedule` | GET | Maintenance schedule |
| `/energy/metrics` | GET | Energy consumption metrics |
| `/energy/comparison` | GET | EHS vs pneumatic comparison |
| `/safety/status` | GET | Safety system status |
| `/safety/alerts` | GET | Active safety alerts |
| `/analytics/roi` | GET | ROI analysis |
| `/ws/live` | WebSocket | Live sensor streaming |

**Example API Usage:**

```bash
# Get material prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "rpm": 80,
    "current_a": 150,
    "vibration_g": 2.5,
    "depth_m": 15,
    "pressure_bar": 250
  }'

# Get safety status
curl http://localhost:8000/safety/status

# Get energy metrics (last 24 hours)
curl "http://localhost:8000/energy/metrics?hours=24"
```

## ⚙️ Configuration

Configuration is managed through environment variables or `.env` file:

```bash
# .env file
EHS_ENVIRONMENT=production
EHS_DEBUG=false
EHS_LOG_LEVEL=INFO

# API Settings
EHS_API_HOST=0.0.0.0
EHS_API_PORT=8000

# Database
EHS_DATABASE__URL=postgresql+asyncpg://user:pass@localhost/ehs_simba

# MQTT (for sensor integration)
EHS_MQTT__ENABLED=true
EHS_MQTT__BROKER_HOST=localhost
EHS_MQTT__BROKER_PORT=1883

# Alerts
EHS_ALERTS__EMAIL__ENABLED=true
EHS_ALERTS__EMAIL__SMTP_HOST=smtp.gmail.com
```

See `config.py` for all available options.

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_ml_predictor.py -v
```

## 📊 Key Performance Indicators (KPIs)

The system tracks these KPIs:

| KPI | Description | Target |
|-----|-------------|--------|
| Material Prediction Accuracy | ML model accuracy | >85% |
| Drill Utilization | Active drilling time | >75% |
| Quality Rate | Holes meeting standards | >95% |
| Energy Efficiency | Drilling vs idle energy | >80% |
| Safety Score | System health percentage | >90% |
| Maintenance Compliance | Completed on schedule | >95% |

## 🔧 Integration

### MQTT Sensor Integration

```python
# Sensor data format (JSON)
{
    "sensor_id": "vib_01",
    "sensor_type": "vibration",
    "value": 2.5,
    "unit": "g",
    "timestamp": "2024-01-15T10:30:00Z",
    "quality": 0.98
}
```

Topic structure: `ehs/simba/sensors/{sensor_type}/{sensor_id}`

### WebSocket Live Streaming

```javascript
// JavaScript client example
const ws = new WebSocket('ws://localhost:8000/ws/live');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'prediction') {
        console.log('Material:', data.data.material);
    } else if (data.type === 'safety_alert') {
        console.warn('Alert:', data.data.message);
    }
};
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Support

For support, please open an issue in the repository or contact the development team.

---

**Built with ❤️ for mining industry excellence**

# perpexcu-
