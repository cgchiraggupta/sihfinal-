# 🦾 Drilling Arm Controller

Real-time robotic arm control system with ESP32, PCA9685, and WebSocket dashboard.

![Dashboard Preview](dashboard_preview.png)

## 🎯 Features

- **Real-time Control**: ~10-30ms latency via WebSocket
- **3 Servo Motors**: Base, Middle Arm, Top Arm (with drill)
- **Circular Knobs**: Intuitive angle control
- **Speed Control**: Individual speed for each servo
- **Configurable Limits**: Set min/max angles per servo
- **Safety Features**: E-STOP, limit alerts
- **Position Presets**: Save and recall positions
- **Live Visualization**: 2D arm preview

## 📦 Hardware Requirements

| Component | Quantity | Notes |
|-----------|----------|-------|
| ESP32 DevKit | 1 | Any variant |
| PCA9685 PWM Driver | 1 | 16-channel I2C |
| MG996R Servo | 3 | Or similar high-torque |
| 5V Power Supply | 1 | 3A+ for servos |
| Drill Motor | 1 | For top arm |

## 🔌 Wiring Diagram

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

## 📚 Required Libraries

Install these via Arduino IDE Library Manager:

1. **Adafruit PWM Servo Driver Library**
   - Search: "Adafruit PWM Servo"
   - Also installs: Adafruit BusIO

2. **WebSockets by Markus Sattler**
   - Search: "WebSockets"

3. **ArduinoJson by Benoit Blanchon**
   - Search: "ArduinoJson"

## 🚀 Installation

### 1. Install Arduino IDE + ESP32 Board

```
Arduino IDE → Preferences → Additional Board Manager URLs:
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

Tools → Board → Boards Manager → Search "ESP32" → Install
```

### 2. Install Libraries

```
Sketch → Include Library → Manage Libraries
- Search and install: "Adafruit PWM Servo Driver"
- Search and install: "WebSockets"
- Search and install: "ArduinoJson"
```

### 3. Upload Code

1. Open `esp32_firmware/drilling_arm.ino`
2. Select Board: `Tools → Board → ESP32 Dev Module`
3. Select Port: `Tools → Port → (your ESP32 port)`
4. Click Upload

### 4. Connect to Dashboard

1. Connect your phone/laptop to WiFi:
   - **SSID**: `DrillArm`
   - **Password**: `drill1234`

2. Open browser:
   - **URL**: `http://192.168.4.1`

## 🎮 Dashboard Controls

### Servo Knobs
- **Drag** the circular knob to set angle
- Real-time movement with minimal latency
- Color indicates position within limits

### Speed Sliders
- **1** = Fastest (1ms per step)
- **100** = Slowest (50ms per step)

### Action Buttons
| Button | Function |
|--------|----------|
| 🏠 Home | Move all servos to center |
| 💾 Save | Save current position to Preset 1 |
| ▶️ P1/P2 | Load saved preset |
| 🛑 E-STOP | Emergency stop all movement |

### Settings Panel
- Click ⚙️ Settings to configure:
  - Min/Max limits per servo
  - Default speeds

## 📡 Communication Protocol

### Binary Commands (5 bytes)

| Byte | Content | Description |
|------|---------|-------------|
| 0 | CMD | Command code |
| 1 | SERVO | Servo index (0-2) |
| 2 | ANGLE_HI | Angle × 100, high byte |
| 3 | ANGLE_LO | Angle × 100, low byte |
| 4 | SPEED | Speed value (1-100) |

### Command Codes

| Code | Name | Description |
|------|------|-------------|
| 0x01 | MOVE | Move servo to angle |
| 0x02 | SET_LIMIT | Set min/max limits |
| 0x03 | GET_STATUS | Request status |
| 0x04 | ESTOP | Toggle emergency stop |
| 0x05 | SAVE_POS | Save position to preset |
| 0x06 | LOAD_POS | Load preset |
| 0x07 | SET_SPEED | Set default speed |
| 0x08 | HOME | Go to home position |

### Status Packet (8 bytes)

| Byte | Content |
|------|---------|
| 0 | 0xAA (marker) |
| 1-2 | Base angle × 100 |
| 3-4 | Middle angle × 100 |
| 5-6 | Top angle × 100 |
| 7 | E-STOP status |

## ⚙️ Configuration

### WiFi Settings (in code)

```cpp
const char* AP_SSID = "DrillArm";      // Change WiFi name
const char* AP_PASS = "drill1234";      // Change password
```

### Servo Limits (default)

| Servo | Min | Max | Home |
|-------|-----|-----|------|
| BASE | 0° | 180° | 90° |
| MIDDLE | 0° | 90° | 45° |
| TOP | 0° | 150° | 75° |

### Servo Pulse Calibration

```cpp
#define SERVO_MIN_US  500   // 0° pulse width (microseconds)
#define SERVO_MAX_US  2500  // 180° pulse width
```

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect to WiFi | Check SSID/password, restart ESP32 |
| Dashboard won't load | Clear browser cache, try incognito mode |
| Servos don't move | Check PCA9685 power (V+ needs 5-6V) |
| Servos jitter | Add 100-1000µF capacitor on power rail |
| High latency | Move closer to ESP32, reduce interference |
| WebSocket disconnects | Check Serial Monitor for errors |

## 📊 Performance

| Metric | Value |
|--------|-------|
| WebSocket Latency | 10-30ms |
| Update Rate | 60 FPS max |
| Packet Size | 5 bytes (command) |
| Status Broadcast | Every 100ms |

## 🛡️ Safety Features

1. **Angle Limits**: Prevents over-rotation
2. **E-STOP**: Instantly stops all movement
3. **Client-side Validation**: Checks limits before sending
4. **Smooth Movement**: Prevents sudden jerks
5. **Auto-reconnect**: Dashboard reconnects if disconnected

## 📝 License

MIT License - Feel free to modify and use for your projects!

---

Made with ❤️ for robotics enthusiasts

