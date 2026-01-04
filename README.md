# 🏗️ Smart India Hackathon Finals - Mining Intelligence System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-red.svg)](https://www.espressif.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **An integrated mining intelligence platform combining real-time underground vehicle tracking, AI-powered drill monitoring with predictive maintenance, and robotic drilling arm control - built for Smart India Hackathon 2024 Finals.**

---

## ⚠️ Important Notice

**🚧 Repository Status: Partial Upload**

> **Note:** Some repositories and components are still not added to this repository. This is a work in progress and additional modules, documentation, and code will be uploaded soon. The complete system includes additional components that are currently being prepared for upload.

**Currently Included:**
- ✅ GPS Tracker - Underground Vehicle Tracking System
- ✅ Advanced EHS Simba Drill Monitoring System
- ✅ Robotic Drilling Arm Controller
- ✅ Comprehensive Documentation

**Coming Soon:**
- 🔄 Additional frontend dashboards
- 🔄 Mobile applications
- 🔄 Additional ML models and datasets
- 🔄 Deployment configurations
- 🔄 Demo videos and screenshots

---

## 📹 Demo Videos & Screenshots

### System Overview Video

<!-- Option 1: YouTube Video (Recommended) -->
<!-- Replace YOUR_VIDEO_ID with your actual YouTube video ID -->
[![Watch the Full System Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)

*🎬 Click the image above to watch the complete system demonstration*

---

### Component Demos

#### 1. GPS Tracker - 3D Underground Visualization

<!-- Replace with your actual video link after uploading -->
<!-- GitHub supports direct .mp4 upload - just drag and drop here -->

**Features Shown:**
- Real-time 3D mine tunnel rendering
- Vehicle tracking across multiple levels
- Playback controls and timeline
- Emergency alert system

<!-- Alternatively, use a GIF for quick preview -->
<!-- ![GPS Tracker Demo](./assets/gps-tracker-demo.gif) -->

---

#### 2. EHS Simba - AI Drill Monitoring

<!-- Add your video here -->

**Features Shown:**
- Material prediction in real-time
- Predictive maintenance dashboard
- Energy optimization metrics
- Safety monitoring alerts

---

#### 3. Robotic Drilling Arm Control

<!-- Add your video here -->

**Features Shown:**
- WebSocket real-time control
- 3-servo arm movement
- Live 2D visualization
- Emergency stop functionality

---

### 📸 Screenshots

<details>
<summary>Click to view screenshots</summary>

#### GPS Tracker - 3D View
<!-- ![3D Mine View](./assets/screenshots/gps-3d-view.png) -->
*Coming soon*

#### GPS Tracker - 2D Map View
<!-- ![2D Map View](./assets/screenshots/gps-2d-view.png) -->
*Coming soon*

#### EHS Simba - Dashboard
<!-- ![EHS Dashboard](./assets/screenshots/ehs-dashboard.png) -->
*Coming soon*

#### Drilling Arm - Control Interface
<!-- ![Drilling Arm UI](./assets/screenshots/drilling-arm-ui.png) -->
*Coming soon*

</details>

---

### 🎥 How to Add Your Videos

**Option 1: YouTube (Recommended for large videos)**
1. Upload your video to YouTube
2. Get the video ID from the URL (e.g., `https://youtube.com/watch?v=ABC123` → ID is `ABC123`)
3. Replace `YOUR_VIDEO_ID` in the markdown above

**Option 2: Direct Upload to GitHub**
1. Edit this README on GitHub.com
2. Drag and drop your `.mp4` or `.mov` file (max 10MB)
3. GitHub will automatically generate the embed code

**Option 3: GIF Animation**
1. Convert your video to GIF using [ezgif.com](https://ezgif.com/video-to-gif)
2. Create an `assets` folder in the repository
3. Upload the GIF and reference it: `![Demo](./assets/demo.gif)`

---

## 📋 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Project Components](#-project-components)
  - [1. GPS Tracker - Underground Vehicle Tracking](#1-gps-tracker---underground-vehicle-tracking)
  - [2. Advanced EHS Simba Drill Monitoring](#2-advanced-ehs-simba-drill-monitoring)
  - [3. Robotic Drilling Arm Controller](#3-robotic-drilling-arm-controller)
- [Technology Stack](#-technology-stack)
- [Installation & Setup](#-installation--setup)
- [Features Showcase](#-features-showcase)
- [API Documentation](#-api-documentation)
- [Hardware Requirements](#-hardware-requirements)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

This comprehensive mining intelligence system addresses critical challenges in modern underground mining operations through three integrated subsystems:

1. **Real-time Underground Vehicle Tracking** - 3D visualization of mining vehicles in complex tunnel networks
2. **AI-Powered Drill Monitoring** - Predictive maintenance, material detection, and energy optimization
3. **Robotic Drilling Arm Control** - Precision control system for automated drilling operations

### Key Achievements

- ✅ **Real-time 3D Visualization** of underground mine layouts with live vehicle tracking
- ✅ **Machine Learning Material Prediction** with 85%+ accuracy across 12 material types
- ✅ **Predictive Maintenance Engine** reducing downtime by up to 40%
- ✅ **Energy Optimization** with cost savings tracking and EHS vs pneumatic comparison
- ✅ **WebSocket-based Robotic Control** with ~10-30ms latency
- ✅ **Cloud-integrated** with Supabase for real-time data synchronization
- ✅ **IoT Sensor Fusion** supporting MQTT, Serial, and HTTP protocols

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MINING INTELLIGENCE PLATFORM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  GPS Tracker     │  │  EHS Simba       │  │  Drill Arm   │  │
│  │  (React/TS)      │  │  (Python/ML)     │  │  (ESP32)     │  │
│  │                  │  │                  │  │              │  │
│  │  • 3D Mine View  │  │  • ML Predictor  │  │  • 3-DOF     │  │
│  │  • Live Tracking │  │  • Maintenance   │  │  • WebSocket │  │
│  │  • Playback      │  │  • Energy Opt.   │  │  • Real-time │  │
│  │  • Alerts        │  │  • Safety Mon.   │  │              │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                     │                    │          │
│           └─────────────────────┼────────────────────┘          │
│                                 │                                │
│                    ┌────────────▼──────────────┐                │
│                    │   Supabase Cloud DB       │                │
│                    │   (PostgreSQL + Realtime) │                │
│                    └───────────────────────────┘                │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  IoT Integration Layer                                    │  │
│  │  • MQTT Broker  • Serial/USB  • HTTP/REST  • WebSockets  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Project Components

### 1. GPS Tracker - Underground Vehicle Tracking

**Location:** `/gps-tracker--main`

A sophisticated React-based 3D visualization system for tracking mining vehicles in underground tunnel networks.

#### Features

- 🗺️ **Interactive 3D Mine Visualization**
  - Multi-level tunnel network rendering (4 levels: -50m, -100m, -150m, -200m)
  - Real-time vehicle position tracking
  - Tunnel type differentiation (Main, Access, Extraction, Ventilation)
  - Workstation and refuge chamber markers

- 📍 **Dual View Modes**
  - **3D View**: Full underground mine visualization with React Three Fiber
  - **2D View**: Traditional map view with Leaflet integration

- 🎮 **Playback Controls**
  - Historical track playback with timeline scrubbing
  - Variable speed control (0.5x, 1x, 2x, 4x)
  - Skip forward/backward through track history

- 🚨 **Safety Features**
  - Real-time alert system (Critical, High, Normal priority)
  - Emergency button integration
  - Breakdown reporting
  - Geofence violation detection

- 📊 **Live Telemetry**
  - Speed, heading, depth monitoring
  - Signal strength and battery level
  - GPS accuracy tracking
  - Underground/Surface status indication

#### Tech Stack

- **Frontend**: React 18.3, TypeScript 5.8
- **3D Rendering**: React Three Fiber, Three.js
- **Mapping**: React Leaflet, Leaflet
- **UI Components**: Radix UI, shadcn/ui
- **State Management**: TanStack Query
- **Backend**: Supabase (PostgreSQL + Realtime)
- **Build Tool**: Vite 5.4

#### Quick Start

```bash
cd gps-tracker--main
npm install
npm run dev
# Open http://localhost:5173
```

#### Database Schema

**Tables:**
- `tracking_devices` - Vehicle/equipment registry
- `tracking_positions` - GPS position history
- `tracking_alerts` - Safety alerts and notifications
- `tracking_geofences` - Virtual boundary definitions

---

### 2. Advanced EHS Simba Drill Monitoring

**Location:** `/simbarpmdashboard--main/advanced_ehs_simba`

A comprehensive Python-based AI/ML system for Electric Hydraulic System (EHS) drill monitoring, predictive maintenance, and real-time analytics.

#### Core Modules

##### 🤖 Material Predictor (`ml_predictor.py`)
- **Algorithm**: Ensemble (Random Forest + Gradient Boosting)
- **Materials Supported**: 12 types (Coal, Granite, Quartzite, Limestone, etc.)
- **Accuracy**: 85%+ on test data
- **Features**: Real-time prediction, anomaly detection, confidence scoring
- **Output**: Material type, category (A/B/C), recommended RPM

##### 🔧 Predictive Maintenance (`maintenance_predictor.py`)
- **RUL Prediction**: Remaining Useful Life calculation using Weibull distribution
- **Components Monitored**: Drill bits, bearings, hydraulic seals, pumps, filters
- **Health Scoring**: 0-100% health score per component
- **Scheduling**: Automated maintenance task generation

##### ⚡ Energy Optimizer (`energy_optimizer.py`)
- **Real-time Power Monitoring**: kW, voltage, current, power factor
- **Cost Calculation**: Energy cost tracking with time-of-use rates
- **Efficiency Analysis**: Drilling vs idle energy consumption
- **Comparison**: EHS vs conventional pneumatic drill ROI

##### 🛡️ Safety Monitor (`safety_monitor.py`)
- **Multi-threshold Monitoring**: Vibration, temperature, pressure, depth
- **Alert Levels**: Info, Warning, Critical, Emergency
- **Auto-shutdown**: Emergency stop on critical conditions
- **Operator Safety**: Fatigue monitoring, void detection

##### 📊 Analytics Engine (`analytics_engine.py`)
- **Hole Quality Scoring**: A-F grading system
- **Geological Analysis**: Material layer detection, anomaly identification
- **ROI Calculations**: NPV, IRR, payback period analysis
- **Performance KPIs**: Drill utilization, quality rate, efficiency metrics

##### 🌐 Sensor Fusion (`sensor_fusion.py`)
- **Multi-sensor Integration**: Vibration, temperature, pressure, acoustic, power
- **Data Preprocessing**: Outlier detection, noise filtering, rolling statistics
- **MQTT Support**: IoT device connectivity
- **Health Monitoring**: Sensor diagnostics and quality tracking

#### API Endpoints

**FastAPI Server** (`dashboard_api.py`) - Port 8000

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | System status overview |
| `/predict` | POST | Material prediction from sensor data |
| `/sensors/current` | GET | Current sensor readings |
| `/maintenance/health` | GET | Component health status |
| `/maintenance/schedule` | GET | Upcoming maintenance tasks |
| `/energy/metrics` | GET | Energy consumption metrics |
| `/safety/status` | GET | Safety system status |
| `/safety/alerts` | GET | Active safety alerts |
| `/analytics/roi` | GET | ROI analysis |
| `/ws/live` | WebSocket | Live sensor streaming |

**Flask Arduino API** (`arduino_api.py`) - Port 5001

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Material prediction (Arduino compatible) |
| `/log` | POST | Log drilling data to Supabase |
| `/materials` | GET | List all material types |
| `/history` | GET | Drilling history |
| `/stats` | GET | Statistics dashboard |

#### Tech Stack

- **Backend**: FastAPI, Flask, Uvicorn
- **ML/AI**: scikit-learn, pandas, numpy, scipy
- **Database**: Supabase (PostgreSQL), SQLAlchemy ORM
- **IoT**: MQTT (paho-mqtt), Serial (pyserial)
- **Validation**: Pydantic, Pydantic Settings
- **Testing**: pytest, pytest-asyncio, pytest-cov

#### Quick Start

```bash
cd simbarpmdashboard--main/advanced_ehs_simba

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Start FastAPI server
uvicorn dashboard_api:app --host 0.0.0.0 --port 8000 --reload

# Or start Flask Arduino API
python arduino_api.py
```

#### Configuration

Create a `.env` file:

```bash
# Environment
EHS_ENVIRONMENT=production
EHS_DEBUG=false
EHS_LOG_LEVEL=INFO

# API Settings
EHS_API_HOST=0.0.0.0
EHS_API_PORT=8000

# Supabase
EHS_DATABASE__URL=postgresql+asyncpg://user:pass@host/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# MQTT (optional)
EHS_MQTT__ENABLED=true
EHS_MQTT__BROKER_HOST=localhost
EHS_MQTT__BROKER_PORT=1883

# Alerts (optional)
EHS_ALERTS__EMAIL__ENABLED=true
EHS_ALERTS__EMAIL__SMTP_HOST=smtp.gmail.com
```

#### Machine Learning Model

**Training Data:**
- 100 samples per material type (1,200 total)
- Synthetic data generation with realistic noise
- 80/20 train/test split

**Features Used:**
1. RPM (rotations per minute)
2. Current (amperage)
3. Vibration mean, std, max
4. RPM stability
5. Current spike
6. Depth
7. Hardness estimate
8. UCS (Unconfined Compressive Strength)

**Model Persistence:**
- `models/rf_material_model.pkl` - Random Forest
- `models/gb_material_model.pkl` - Gradient Boosting
- `models/scaler.pkl` - Feature scaler
- `models/material_classifier.joblib` - Combined ensemble

---

### 3. Robotic Drilling Arm Controller

**Location:** `/aclariyan-main/drilling_arm`

A real-time ESP32-based control system for a 3-DOF robotic drilling arm with WebSocket dashboard.

#### Features

- 🎮 **Real-time Control**
  - WebSocket communication (~10-30ms latency)
  - Binary protocol for efficient data transfer
  - Auto-reconnect on disconnect

- 🦾 **3-Servo System**
  - **BASE**: 0-180° rotation (horizontal)
  - **MIDDLE**: 0-90° arm elevation
  - **TOP**: 0-150° drill angle

- 🎛️ **Dashboard Controls**
  - Circular knob sliders for angle control
  - Individual speed control per servo (1-100)
  - Real-time 2D arm visualization
  - Live position feedback

- ⚙️ **Configuration**
  - Adjustable min/max limits per servo
  - EEPROM persistence of settings
  - Preset position save/load
  - Emergency stop (E-STOP)

- 🔒 **Safety Features**
  - Angle limit enforcement
  - Smooth movement interpolation
  - Client-side validation
  - Emergency stop button

#### Hardware Requirements

| Component | Quantity | Notes |
|-----------|----------|-------|
| ESP32 DevKit | 1 | Any variant |
| PCA9685 PWM Driver | 1 | 16-channel I2C |
| MG996R Servo | 3 | Or similar high-torque |
| 5V Power Supply | 1 | 3A+ for servos |
| Drill Motor | 1 | For top arm |

#### Wiring Diagram

```
                    ┌─────────────────┐
                    │      ESP32      │
                    │                 │
                    │  GPIO 21 (SDA) ─┼──────► PCA9685 SDA
                    │  GPIO 22 (SCL) ─┼──────► PCA9685 SCL
                    │  3.3V ──────────┼──────► PCA9685 VCC
                    │  GND ───────────┼──────► PCA9685 GND
                    └─────────────────┘

                    ┌─────────────────┐
                    │    PCA9685      │
                    │                 │
                    │  Channel 0 ─────┼──────► BASE Servo (Signal)
                    │  Channel 1 ─────┼──────► MIDDLE Servo (Signal)
                    │  Channel 2 ─────┼──────► TOP Servo (Signal)
                    │                 │
 5V Power Supply ──►│  V+ ────────────┼──────► All Servo VCC
 (3A minimum)    ──►│  GND ───────────┼──────► All Servo GND
                    └─────────────────┘
```

#### Required Libraries

Install via Arduino IDE Library Manager:

1. **Adafruit PWM Servo Driver Library**
2. **ESPAsyncWebServer** (v3.x compatible)
3. **AsyncTCP**
4. **ArduinoJson**

#### Quick Start

```bash
# 1. Install Arduino IDE and ESP32 board support
# Add to Board Manager URLs:
# https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

# 2. Install required libraries (see above)

# 3. Open drilling_arm.ino in Arduino IDE

# 4. Select Board: Tools → Board → ESP32 Dev Module

# 5. Upload to ESP32

# 6. Connect to WiFi:
#    SSID: DrillArm
#    Password: drill1234

# 7. Open browser:
#    http://192.168.4.1
```

#### Communication Protocol

**Binary Commands** (5 bytes):

| Byte | Content | Description |
|------|---------|-------------|
| 0 | CMD | Command code |
| 1 | SERVO | Servo index (0-2) |
| 2 | ANGLE_HI | Angle × 100, high byte |
| 3 | ANGLE_LO | Angle × 100, low byte |
| 4 | SPEED | Speed value (1-100) |

**Command Codes:**

| Code | Name | Description |
|------|------|-------------|
| 0x01 | MOVE | Move servo to angle |
| 0x02 | SET_LIMIT | Set min/max limits |
| 0x04 | ESTOP | Toggle emergency stop |
| 0x07 | SET_SPEED | Set default speed |
| 0x08 | HOME | Go to home position |
| 0x09 | RESET | Stop and clear state |

**Status Packet** (8 bytes):

| Byte | Content |
|------|---------|
| 0 | 0xAA (marker) |
| 1-2 | Base angle × 100 |
| 3-4 | Middle angle × 100 |
| 5-6 | Top angle × 100 |
| 7 | E-STOP status |

#### Serial Commands

Available via Serial Monitor (115200 baud):

- `RESET` - Clear EEPROM and restore defaults
- `TEST` - Test all servos
- `STATUS` - Show current positions
- `HELP` - Show command list

---

## 🛠️ Technology Stack

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3+ | UI framework |
| TypeScript | 5.8+ | Type safety |
| Vite | 5.4+ | Build tool |
| React Three Fiber | 8.18+ | 3D rendering |
| Three.js | 0.159+ | 3D graphics |
| React Leaflet | 5.0+ | 2D mapping |
| Radix UI | Latest | UI components |
| TailwindCSS | 3.4+ | Styling |
| TanStack Query | 5.83+ | Data fetching |

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Backend language |
| FastAPI | 0.104+ | Modern web framework |
| Flask | 3.0+ | Arduino API |
| Uvicorn | 0.24+ | ASGI server |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.5+ | Data validation |

### Machine Learning

| Technology | Version | Purpose |
|------------|---------|---------|
| scikit-learn | 1.3+ | ML algorithms |
| pandas | 2.1+ | Data manipulation |
| numpy | 1.26+ | Numerical computing |
| scipy | 1.11+ | Scientific computing |
| joblib | 1.3+ | Model persistence |

### Database & Cloud

| Technology | Version | Purpose |
|------------|---------|---------|
| Supabase | 2.0+ | Cloud PostgreSQL |
| PostgreSQL | 15+ | Database |
| SQLite | 3+ | Local storage |

### IoT & Hardware

| Technology | Version | Purpose |
|------------|---------|---------|
| ESP32 | Arduino | Microcontroller |
| PCA9685 | - | PWM servo driver |
| MQTT | 1.6+ | IoT messaging |
| WebSocket | - | Real-time comms |
| Serial/USB | - | Arduino comms |

---

## 🚀 Installation & Setup

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Arduino IDE** (for ESP32 firmware)
- **Git**
- **Supabase Account** (free tier works)

### Complete Setup

#### 1. Clone Repository

```bash
git clone <repository-url>
cd sihfinals
```

#### 2. GPS Tracker Setup

```bash
cd gps-tracker--main

# Install dependencies
npm install

# Configure Supabase
cp .env.example .env
# Edit .env with your Supabase credentials:
# VITE_SUPABASE_URL=https://your-project.supabase.co
# VITE_SUPABASE_ANON_KEY=your-anon-key

# Start development server
npm run dev
# Open http://localhost:5173
```

#### 3. EHS Simba Drill Monitoring Setup

```bash
cd ../simbarpmdashboard--main/advanced_ehs_simba

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database (if using local SQLite)
python -c "from database import get_db_manager; import asyncio; asyncio.run(get_db_manager())"

# Start FastAPI server
uvicorn dashboard_api:app --host 0.0.0.0 --port 8000 --reload
# API docs: http://localhost:8000/docs

# Or start Flask Arduino API
python arduino_api.py
# API: http://localhost:5001
```

#### 4. Drilling Arm Controller Setup

```bash
cd ../aclariyan-main/drilling_arm/esp32_firmware

# 1. Install Arduino IDE from https://www.arduino.cc/

# 2. Add ESP32 board support:
#    File → Preferences → Additional Board Manager URLs:
#    https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

# 3. Install ESP32 boards:
#    Tools → Board → Boards Manager → Search "ESP32" → Install

# 4. Install libraries:
#    Sketch → Include Library → Manage Libraries
#    - Adafruit PWM Servo Driver
#    - ESPAsyncWebServer (v3.x)
#    - AsyncTCP
#    - ArduinoJson

# 5. Open drilling_arm.ino

# 6. Configure:
#    Tools → Board → ESP32 Dev Module
#    Tools → Port → (select your ESP32 port)

# 7. Upload to ESP32

# 8. Connect to WiFi:
#    SSID: DrillArm
#    Password: drill1234

# 9. Open browser:
#    http://192.168.4.1
```

### Supabase Database Setup

#### Create Tables

Run these SQL commands in Supabase SQL Editor:

```sql
-- GPS Tracker Tables
CREATE TABLE tracking_devices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  status TEXT DEFAULT 'operational',
  is_online BOOLEAN DEFAULT false,
  last_seen_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tracking_positions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  device_id UUID REFERENCES tracking_devices(id),
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  altitude DOUBLE PRECISION,
  depth DOUBLE PRECISION,
  speed DOUBLE PRECISION,
  heading DOUBLE PRECISION,
  accuracy DOUBLE PRECISION,
  signal_strength INTEGER,
  battery INTEGER,
  zone TEXT,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tracking_alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  device_id UUID REFERENCES tracking_devices(id),
  type TEXT NOT NULL,
  priority TEXT NOT NULL,
  message TEXT NOT NULL,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  acknowledged BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tracking_geofences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  coordinates JSONB NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- EHS Simba Tables
CREATE TABLE ehs_drill_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  rpm DOUBLE PRECISION,
  current DOUBLE PRECISION,
  vibration_mean DOUBLE PRECISION,
  vibration_std DOUBLE PRECISION,
  vibration_max DOUBLE PRECISION,
  depth DOUBLE PRECISION,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  predicted_material TEXT,
  confidence DOUBLE PRECISION,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ehs_materials (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL,
  hardness DOUBLE PRECISION,
  ucs DOUBLE PRECISION,
  optimal_rpm DOUBLE PRECISION,
  density DOUBLE PRECISION,
  category TEXT
);

-- Add indexes for performance
CREATE INDEX idx_positions_device_time ON tracking_positions(device_id, timestamp DESC);
CREATE INDEX idx_alerts_device ON tracking_alerts(device_id);
CREATE INDEX idx_drill_logs_time ON ehs_drill_logs(timestamp DESC);
```

---

## ✨ Features Showcase

### GPS Tracker Features

#### 3D Mine Visualization
- **Multi-level Rendering**: 4 underground levels (-50m to -200m)
- **Tunnel Network**: Main tunnels, access tunnels, extraction zones, ventilation shafts
- **Workstations**: Loading bays, refuge chambers, emergency exits, pump stations
- **Real-time Updates**: Live vehicle position tracking with smooth animations

#### Playback System
- **Timeline Scrubbing**: Navigate through historical track data
- **Speed Control**: 0.5x, 1x, 2x, 4x playback speeds
- **Frame-by-frame**: Skip forward/backward through positions
- **Visual Timeline**: Progress bar with timestamps

#### Safety & Alerts
- **Priority Levels**: Critical (red), High (amber), Normal (cyan)
- **Emergency Button**: Instant emergency alert trigger
- **Breakdown Reporting**: Quick breakdown notification
- **Alert Dismissal**: Acknowledge and clear alerts

### EHS Simba Features

#### Material Prediction
- **12 Material Types**: Coal, Shale, Limestone, Dolomite, Sandstone, Hematite, Schist, Magnetite, Granite, Gneiss, Quartzite, Quartz Veins
- **Real-time Classification**: <100ms prediction time
- **Confidence Scoring**: 0-100% confidence with top-3 predictions
- **Anomaly Detection**: Identifies unknown materials

#### Predictive Maintenance
- **Component Monitoring**: 7 critical components tracked
- **RUL Calculation**: Hours until failure prediction
- **Health Scoring**: 0-100% health per component
- **Maintenance Scheduling**: Automated task generation with due dates

#### Energy Optimization
- **Real-time Monitoring**: Power, voltage, current, power factor
- **Cost Tracking**: kWh consumption and cost calculation
- **Efficiency Analysis**: Drilling vs idle energy breakdown
- **ROI Comparison**: EHS vs conventional drill economics

#### Safety Monitoring
- **Multi-parameter Tracking**: Vibration, temperature, pressure, depth
- **Threshold Alerts**: Info, Warning, Critical, Emergency levels
- **Auto-shutdown**: Emergency stop on critical conditions
- **Operator Safety**: Fatigue monitoring integration

### Drilling Arm Features

#### Control System
- **Real-time WebSocket**: 10-30ms latency
- **Binary Protocol**: Efficient 5-byte commands
- **Smooth Movement**: Interpolated servo motion
- **Position Feedback**: Live angle display

#### User Interface
- **Circular Knobs**: Intuitive angle control
- **Speed Sliders**: Individual servo speed adjustment
- **2D Preview**: Real-time arm visualization
- **Settings Panel**: Configurable limits per servo

---

## 📚 API Documentation

### GPS Tracker API

**Base URL**: Supabase Realtime API

**Subscriptions**:
```typescript
// Subscribe to position updates
supabase
  .channel('positions')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'tracking_positions'
  }, (payload) => {
    console.log('New position:', payload.new);
  })
  .subscribe();
```

### EHS Simba FastAPI

**Base URL**: `http://localhost:8000`

**Interactive Docs**: `http://localhost:8000/docs`

#### Example Requests

**Material Prediction**:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "rpm": 2300,
    "current_a": 14.5,
    "vibration_g": 2.5,
    "depth_m": 45.5,
    "pressure_bar": 250,
    "temperature_c": 55
  }'
```

**Response**:
```json
{
  "material": "Granite",
  "confidence": 0.92,
  "category": "C",
  "is_anomaly": false,
  "recommended_rpm": 1800,
  "top_predictions": [
    {"material": "Granite", "confidence": 0.92},
    {"material": "Gneiss", "confidence": 0.05},
    {"material": "Quartzite", "confidence": 0.02}
  ]
}
```

**Safety Status**:
```bash
curl http://localhost:8000/safety/status
```

**Response**:
```json
{
  "is_safe": true,
  "system_health": 95.5,
  "active_alerts": 0,
  "last_check": "2024-01-15T10:30:00Z"
}
```

### EHS Simba Flask API (Arduino)

**Base URL**: `http://localhost:5001`

**Log Drilling Data**:
```bash
curl -X POST http://localhost:5001/log \
  -H "Content-Type: application/json" \
  -d '{
    "rpm": 2300,
    "current": 14.5,
    "vibration_readings": [68, 72, 70, 69, 71],
    "depth": 45.5,
    "latitude": 22.292675,
    "longitude": 73.366018
  }'
```

### Drilling Arm WebSocket

**URL**: `ws://192.168.4.1/ws`

**Send Move Command** (JavaScript):
```javascript
const ws = new WebSocket('ws://192.168.4.1/ws');
ws.binaryType = 'arraybuffer';

// Move BASE servo to 120° at speed 50
const angle = 120 * 100; // Convert to centidegrees
const command = new Uint8Array([
  0x01,                    // MOVE command
  0,                       // Servo 0 (BASE)
  (angle >> 8) & 0xFF,     // Angle high byte
  angle & 0xFF,            // Angle low byte
  50                       // Speed
]);
ws.send(command.buffer);
```

---

## 🔧 Hardware Requirements

### GPS Tracker System

- **Server**: Any modern PC/laptop or cloud instance
- **Clients**: Web browsers (Chrome, Firefox, Safari, Edge)
- **Network**: WiFi or LAN connection
- **Optional**: GPS modules for actual vehicle tracking

### EHS Simba Drill Monitoring

- **Server**: 
  - CPU: 2+ cores
  - RAM: 4GB+ (8GB recommended)
  - Storage: 10GB+ SSD
  - OS: Linux, Windows, macOS

- **Sensors** (for production):
  - Vibration sensors (accelerometers)
  - Current sensors (hall effect)
  - Temperature sensors (thermocouples)
  - Pressure transducers
  - RPM sensors (hall effect/optical)

- **Optional**:
  - MQTT broker (Mosquitto)
  - Arduino/ESP32 for sensor integration

### Drilling Arm Controller

- **ESP32 DevKit**: Any variant (ESP32-WROOM, ESP32-WROVER)
- **PCA9685**: 16-channel I2C PWM driver
- **Servos**: 3x MG996R or similar (torque: 10kg·cm+)
- **Power Supply**: 5-6V, 3A+ (for servos)
- **Drill Motor**: 12V DC motor (optional)
- **Wiring**: Jumper wires, breadboard or PCB
- **Enclosure**: Protective case (recommended)

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Code Standards

- **TypeScript**: Follow ESLint configuration
- **Python**: Follow PEP 8, use type hints
- **Arduino**: Follow Arduino style guide
- **Commits**: Use conventional commits format

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**Smart India Hackathon 2024 Finals Team**

- Project Lead & Full-stack Development
- ML/AI Engineering
- IoT & Hardware Integration
- UI/UX Design
- Database Architecture
- DevOps & Deployment

---

## 🙏 Acknowledgments

- **Smart India Hackathon** for the opportunity
- **Supabase** for cloud database infrastructure
- **Adafruit** for excellent hardware libraries
- **React Three Fiber** community for 3D rendering support
- **FastAPI** team for the amazing framework

---

## 📞 Support

For issues, questions, or support:

- **GitHub Issues**: [Create an issue](../../issues)
- **Documentation**: See individual component READMEs
- **API Docs**: FastAPI auto-generated docs at `/docs`

---

## 🗺️ Roadmap

### Phase 1 (Current - SIH Finals)
- ✅ GPS tracking with 3D visualization
- ✅ Material prediction ML model
- ✅ Predictive maintenance engine
- ✅ Robotic arm control system
- ✅ Cloud integration with Supabase

### Phase 2 (Post-SIH)
- 🔲 Mobile app (React Native)
- 🔲 Advanced ML models (deep learning)
- 🔲 Multi-mine support
- 🔲 Offline mode with sync
- 🔲 Enhanced analytics dashboard

### Phase 3 (Future)
- 🔲 AR/VR mine visualization
- 🔲 Autonomous drilling integration
- 🔲 Blockchain for audit trails
- 🔲 Edge AI deployment
- 🔲 Multi-language support

---

**Built with ❤️ for Smart India Hackathon 2024 Finals**

**Total Lines of Code**: 15,000+  
**Components**: 3 major subsystems  
**Technologies**: 25+ frameworks and libraries  
**Development Time**: 6+ months  

---

*Last Updated: January 2026*
# sihfinal-
