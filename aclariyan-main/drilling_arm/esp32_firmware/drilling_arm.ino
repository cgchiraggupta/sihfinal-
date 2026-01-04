/*
 * ============================================================
 *  DRILLING ARM CONTROLLER - ESP32 Firmware v2.2
 *  Fixed UI + Compatible with ESPAsyncWebServer 3.x
 * ============================================================
 */

#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <EEPROM.h>
#include <ArduinoJson.h>

// WiFi AP settings
const char* AP_SSID = "DrillArm";
const char* AP_PASS = "drill1234";

// I2C & PCA9685
#define SDA_PI?≥cvxzsaDRTUYI[\
  ][5321Q234567890-]=[-098754321₹ ]"}]
#define CH_BASE    0
#define CH_MIDDLE  1
#define CH_TOP     2
#define SERVO_MIN_US  500
#define SERVO_MAX_US  2500
#define PWM_FREQ      50

// EEPROM
#define EEPROM_SIZE 64
#define ADDR_INIT     0
#define ADDR_LIMITS   1

Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40);
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

struct ServoData {
  float current;
  float target;
  uint8_t minLimit;
  uint8_t maxLimit;
  uint8_t speed;
  const char* name;
};

ServoData servos[3] = {
  {90.0, 90.0, 0, 180, 20, "BASE"},
  {45.0, 45.0, 0, 90,  25, "MIDDLE"},
  {75.0, 75.0, 0, 150, 25, "TOP"}
};

bool eStopActive = false;
unsigned long lastBroadcast = 0;

void setServoAngle(uint8_t channel, float angle) {
  angle = constrain(angle, 0, 180);
  uint16_t pulse = map(angle * 10, 0, 1800, SERVO_MIN_US, SERVO_MAX_US);
  uint16_t pwm = (uint16_t)((pulse * 4096L) / 20000L);
  pca.setPWM(channel, 0, pwm);
  // Uncomment for verbose debug:
  // Serial.printf("[PWM] CH%d: angle=%.1f, pulse=%dus, pwm=%d\n", channel, angle, pulse, pwm);
}

void updateServos() {
  if (eStopActive) return;
  for (int i = 0; i < 3; i++) {
    float diff = servos[i].target - servos[i].current;
    if (abs(diff) > 0.3) {
      // Still moving - calculate step based on speed
      float step = (diff > 0) ? 0.5 : -0.5;
      servos[i].current += step;
      servos[i].current = constrain(servos[i].current, servos[i].minLimit, servos[i].maxLimit);
      setServoAngle(i, servos[i].current);
    } else if (abs(diff) > 0.01) {
      // Very close to target (within 0.3° but not exact) - snap to target and STOP
      servos[i].current = servos[i].target;
      setServoAngle(i, servos[i].current);
      Serial.printf("[STOP] %s reached target: %.1f°\n", servos[i].name, servos[i].current);
    }
    // If abs(diff) <= 0.01, servo is at target - do nothing, movement stopped
  }
}

void sendConfig(AsyncWebSocketClient *client) {
  StaticJsonDocument<512> doc;
  JsonArray arr = doc.createNestedArray("servos");
  for (int i = 0; i < 3; i++) {
    JsonObject s = arr.createNestedObject();
    s["name"] = servos[i].name;
    s["min"] = servos[i].minLimit;
    s["max"] = servos[i].maxLimit;
    s["speed"] = servos[i].speed;
    s["angle"] = servos[i].current;
  }
  doc["estop"] = eStopActive;
  String json;
  serializeJson(doc, json);
  client->text(json);
}

void processMessage(uint8_t *data, size_t len) {
  if (len < 1) return;
  uint8_t cmd = data[0];
  
  switch (cmd) {
    case 0x01: // MOVE
      if (len >= 5) {
        uint8_t idx = data[1];
        uint16_t angleCenti = (data[2] << 8) | data[3];
        uint8_t speed = data[4];
        if (idx < 3) {
          float angle = angleCenti / 100.0;
          angle = constrain(angle, servos[idx].minLimit, servos[idx].maxLimit);
          
          // IMPORTANT: Start from current position, set new target
          // This ensures each instruction starts from where previous one ended
          Serial.printf("[CMD] MOVE %s: %.1f° -> %.1f° (speed:%d)\n", 
                       servos[idx].name, servos[idx].current, angle, speed);
          
          servos[idx].target = angle;
          servos[idx].speed = constrain(speed, 1, 100);
          
          // If servo was already at a different target, it will now move from current to new target
        }
      }
      break;
    case 0x02: // SET_LIMIT
      if (len >= 4 && data[1] < 3 && data[2] < data[3]) {
        servos[data[1]].minLimit = data[2];
        servos[data[1]].maxLimit = data[3];
        saveSettings();
      }
      break;
    case 0x04: // E-STOP
      eStopActive = !eStopActive;
      if (eStopActive) {
        for (int i = 0; i < 3; i++) servos[i].target = servos[i].current;
      }
      break;
    case 0x07: // SET_SPEED
      if (len >= 3 && data[1] < 3) {
        servos[data[1]].speed = constrain(data[2], 1, 100);
      }
      break;
    case 0x08: // HOME
      servos[0].target = constrain(90, servos[0].minLimit, servos[0].maxLimit);
      servos[1].target = constrain(45, servos[1].minLimit, servos[1].maxLimit);
      servos[2].target = constrain(75, servos[2].minLimit, servos[2].maxLimit);
      Serial.println("[CMD] HOME");
      break;
      
    case 0x09: // RESET - Stop at current position and clear state
      Serial.println("[CMD] RESET - Stop and clear state");
      eStopActive = false;
      
      // Stop all servos at their current positions (freeze movement)
      // Set target = current so no further movement occurs
      for (int i = 0; i < 3; i++) {
        servos[i].target = servos[i].current;
        Serial.printf("[RESET] %s stopped at %.1f° (target=current)\n", 
                      servos[i].name, servos[i].current);
      }
      
      // Clear any pending state/flags
      // Servos remain at their current physical positions
      // No movement occurs - just state cleared
      
      Serial.println("[RESET] All states cleared, servos frozen at current positions");
      break;
  }
}

void onWsEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, 
               AwsEventType type, void *arg, uint8_t *data, size_t len) {
  switch (type) {
    case WS_EVT_CONNECT:
      Serial.printf("[WS] Client #%u connected\n", client->id());
      sendConfig(client);
      break;
    case WS_EVT_DISCONNECT:
      Serial.printf("[WS] Client #%u disconnected\n", client->id());
      break;
    case WS_EVT_DATA:
      if (len > 0 && data != NULL) {
        processMessage(data, len);
      }
      break;
    default:
      break;
  }
}

void broadcastStatus() {
  if (ws.count() == 0) return;
  uint8_t packet[8];
  packet[0] = 0xAA;
  uint16_t a0 = (uint16_t)(servos[0].current * 100);
  uint16_t a1 = (uint16_t)(servos[1].current * 100);
  uint16_t a2 = (uint16_t)(servos[2].current * 100);
  packet[1] = a0 >> 8; packet[2] = a0 & 0xFF;
  packet[3] = a1 >> 8; packet[4] = a1 & 0xFF;
  packet[5] = a2 >> 8; packet[6] = a2 & 0xFF;
  packet[7] = eStopActive ? 1 : 0;
  ws.binaryAll(packet, 8);
}

void loadSettings() {
  if (EEPROM.read(ADDR_INIT) != 0xAB) {
    saveSettings();
    EEPROM.write(ADDR_INIT, 0xAB);
    EEPROM.commit();
    return;
  }
  servos[0].minLimit = EEPROM.read(ADDR_LIMITS);
  servos[0].maxLimit = EEPROM.read(ADDR_LIMITS + 1);
  servos[1].minLimit = EEPROM.read(ADDR_LIMITS + 2);
  servos[1].maxLimit = EEPROM.read(ADDR_LIMITS + 3);
  servos[2].minLimit = EEPROM.read(ADDR_LIMITS + 4);
  servos[2].maxLimit = EEPROM.read(ADDR_LIMITS + 5);
}

void saveSettings() {
  EEPROM.write(ADDR_LIMITS, servos[0].minLimit);
  EEPROM.write(ADDR_LIMITS + 1, servos[0].maxLimit);
  EEPROM.write(ADDR_LIMITS + 2, servos[1].minLimit);
  EEPROM.write(ADDR_LIMITS + 3, servos[1].maxLimit);
  EEPROM.write(ADDR_LIMITS + 4, servos[2].minLimit);
  EEPROM.write(ADDR_LIMITS + 5, servos[2].maxLimit);
  EEPROM.commit();
}

void clearEEPROM() {
  Serial.println("\n[RESET] Clearing EEPROM...");
  for (int i = 0; i < EEPROM_SIZE; i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
  Serial.println("[RESET] EEPROM cleared!");
  Serial.println("[RESET] Resetting to defaults...");
  
  // Reset to defaults
  servos[0] = {90.0, 90.0, 0, 180, 20, "BASE"};
  servos[1] = {45.0, 45.0, 0, 90,  25, "MIDDLE"};
  servos[2] = {75.0, 75.0, 0, 150, 25, "TOP"};
  
  saveSettings();
  Serial.println("[RESET] Done! Defaults restored.");
}

// ==================== HTML PAGE ====================

const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Drill Arm</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#fff;min-height:100vh}
.hdr{background:#14141e;padding:10px 15px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #00d4ff33}
.logo{font-weight:600;display:flex;align-items:center;gap:8px}
.logo span{background:linear-gradient(135deg,#00d4ff,#00ff88);width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center}
.status{font-size:12px;color:#666}
.status.on{color:#00ff88}
.main{padding:15px;max-width:800px;margin:0 auto}

.servo-card{background:#16161f;border-radius:12px;padding:15px;margin-bottom:12px;border:1px solid #ffffff08}
.servo-header{display:flex;justify-content:space-between;margin-bottom:12px}
.servo-name{color:#00d4ff;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:1px}
.servo-range{color:#666;font-size:11px}

.slider-container{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.slider-container input[type="range"]{flex:1;height:8px;-webkit-appearance:none;background:#1a1a24;border-radius:4px;outline:none}
.slider-container input[type="range"]::-webkit-slider-thumb{-webkit-appearance:none;width:22px;height:22px;background:linear-gradient(135deg,#00d4ff,#00ff88);border-radius:50%;cursor:pointer;box-shadow:0 2px 8px #00d4ff66}
.angle-display{background:#0a0a0f;padding:8px 12px;border-radius:6px;min-width:60px;text-align:center;font-weight:700;font-size:16px}

.speed-row{display:flex;align-items:center;gap:10px;margin-top:8px}
.speed-row label{color:#666;font-size:11px}
.speed-row input{width:80px;height:4px;-webkit-appearance:none;background:#1a1a24;border-radius:2px}
.speed-row input::-webkit-slider-thumb{-webkit-appearance:none;width:12px;height:12px;background:#00d4ff;border-radius:50%;cursor:pointer}
.speed-val{color:#666;font-size:11px;min-width:24px}

.btns{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:15px}
.btn{flex:1;min-width:70px;padding:12px 8px;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:4px;transition:all 0.15s}
.btn-home{background:#16161f;color:#fff;border:1px solid #ffffff15}
.btn-home:active{background:#00d4ff;color:#000}
.btn-stop{background:#ff3860;color:#fff}
.btn-stop.active{animation:pulse 0.4s infinite alternate}
@keyframes pulse{to{box-shadow:0 0 20px #ff386088}}

.preview{background:#16161f;border-radius:12px;padding:12px;border:1px solid #ffffff08}
.preview-title{color:#666;font-size:11px;margin-bottom:8px}
#canvas{width:100%;height:140px;background:#0a0a0f;border-radius:8px;display:block}

.modal-bg{display:none;position:fixed;inset:0;background:#000c;z-index:100;align-items:center;justify-content:center;padding:15px}
.modal-bg.open{display:flex}
.modal{background:#16161f;border-radius:12px;width:100%;max-width:380px;max-height:80vh;overflow:auto}
.modal-head{padding:15px;border-bottom:1px solid #ffffff10;display:flex;justify-content:space-between;align-items:center}
.modal-head h3{font-size:16px}
.modal-close{background:none;border:none;color:#666;font-size:24px;cursor:pointer}
.modal-body{padding:15px}
.setting-group{margin-bottom:20px}
.setting-title{color:#00d4ff;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px}
.setting-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.setting-row label{color:#888;font-size:13px}
.setting-row input{width:55px;padding:6px;background:#0a0a0f;border:1px solid #ffffff15;border-radius:4px;color:#fff;text-align:center}
.modal-foot{padding:15px;border-top:1px solid #ffffff10;display:flex;gap:10px}
.modal-foot button{flex:1;padding:10px;border:none;border-radius:6px;font-weight:600;cursor:pointer}
.btn-cancel{background:#1a1a24;color:#fff}
.btn-save{background:#00d4ff;color:#000}
</style>
</head>
<body>

<header class="hdr">
  <div class="logo"><span>⚙</span> Drill Arm</div>
  <div class="status" id="status">● Offline</div>
</header>

<main class="main">
  <!-- SERVO 0: BASE -->
  <div class="servo-card">
    <div class="servo-header">
      <span class="servo-name">BASE</span>
      <span class="servo-range" id="range0">0° - 180°</span>
    </div>
    <div class="slider-container">
      <input type="range" id="servo0" min="0" max="180" value="90" oninput="moveServo(0,this.value)">
      <div class="angle-display" id="angle0">90°</div>
    </div>
    <div class="speed-row">
      <label>Speed:</label>
      <input type="range" id="speed0" min="1" max="100" value="20" oninput="setSpeed(0,this.value)">
      <span class="speed-val" id="spdval0">20</span>
    </div>
  </div>

  <!-- SERVO 1: MIDDLE -->
  <div class="servo-card">
    <div class="servo-header">
      <span class="servo-name">MIDDLE</span>
      <span class="servo-range" id="range1">0° - 90°</span>
    </div>
    <div class="slider-container">
      <input type="range" id="servo1" min="0" max="90" value="45" oninput="moveServo(1,this.value)">
      <div class="angle-display" id="angle1">45°</div>
    </div>
    <div class="speed-row">
      <label>Speed:</label>
      <input type="range" id="speed1" min="1" max="100" value="25" oninput="setSpeed(1,this.value)">
      <span class="speed-val" id="spdval1">25</span>
    </div>
  </div>

  <!-- SERVO 2: TOP -->
  <div class="servo-card">
    <div class="servo-header">
      <span class="servo-name">TOP</span>
      <span class="servo-range" id="range2">0° - 150°</span>
    </div>
    <div class="slider-container">
      <input type="range" id="servo2" min="0" max="150" value="75" oninput="moveServo(2,this.value)">
      <div class="angle-display" id="angle2">75°</div>
    </div>
    <div class="speed-row">
      <label>Speed:</label>
      <input type="range" id="speed2" min="1" max="100" value="25" oninput="setSpeed(2,this.value)">
      <span class="speed-val" id="spdval2">25</span>
    </div>
  </div>

  <!-- BUTTONS -->
  <div class="btns">
    <button class="btn btn-home" onclick="goHome()">🏠 Home</button>
    <button class="btn btn-home" onclick="resetESP()">🔄 Reset</button>
    <button class="btn btn-home" onclick="openSettings()">⚙️ Settings</button>
    <button class="btn btn-stop" id="stopBtn" onclick="toggleStop()">🛑 STOP</button>
  </div>

  <!-- ARM PREVIEW -->
  <div class="preview">
    <div class="preview-title">Arm Preview</div>
    <canvas id="canvas"></canvas>
  </div>
</main>

<!-- SETTINGS MODAL -->
<div class="modal-bg" id="modal">
  <div class="modal">
    <div class="modal-head">
      <h3>⚙️ Settings</h3>
      <button class="modal-close" onclick="closeSettings()">×</button>
    </div>
    <div class="modal-body">
      <div class="setting-group">
        <div class="setting-title">Servo Limits</div>
        <div class="setting-row"><label>BASE Min:</label><input type="number" id="min0" value="0"></div>
        <div class="setting-row"><label>BASE Max:</label><input type="number" id="max0" value="180"></div>
        <div class="setting-row"><label>MIDDLE Min:</label><input type="number" id="min1" value="0"></div>
        <div class="setting-row"><label>MIDDLE Max:</label><input type="number" id="max1" value="90"></div>
        <div class="setting-row"><label>TOP Min:</label><input type="number" id="min2" value="0"></div>
        <div class="setting-row"><label>TOP Max:</label><input type="number" id="max2" value="150"></div>
      </div>
    </div>
    <div class="modal-foot">
      <button class="btn-cancel" onclick="closeSettings()">Cancel</button>
      <button class="btn-save" onclick="saveSettings()">Save</button>
    </div>
  </div>
</div>

<script>
var ws;
var connected = false;
var estop = false;
var servos = [
  {min:0, max:180, speed:20, angle:90},
  {min:0, max:90, speed:25, angle:45},
  {min:0, max:150, speed:25, angle:75}
];

function connect() {
  ws = new WebSocket('ws://' + location.hostname + '/ws');
  ws.binaryType = 'arraybuffer';
  
  ws.onopen = function() {
    connected = true;
    document.getElementById('status').className = 'status on';
    document.getElementById('status').textContent = '● Online';
    console.log('Connected!');
  };
  
  ws.onclose = function() {
    connected = false;
    document.getElementById('status').className = 'status';
    document.getElementById('status').textContent = '● Offline';
    console.log('Disconnected, reconnecting...');
    setTimeout(connect, 2000);
  };
  
  ws.onerror = function(e) {
    console.log('WS Error', e);
  };
  
  ws.onmessage = function(e) {
    if (typeof e.data === 'string') {
      // Config JSON
      var cfg = JSON.parse(e.data);
      if (cfg.servos) {
        for (var i = 0; i < 3; i++) {
          servos[i].min = cfg.servos[i].min;
          servos[i].max = cfg.servos[i].max;
          servos[i].speed = cfg.servos[i].speed;
          servos[i].angle = cfg.servos[i].angle;
          updateSlider(i);
        }
      }
      if (cfg.estop !== undefined) {
        estop = cfg.estop;
        updateStopBtn();
      }
    } else {
      // Binary status
      var d = new Uint8Array(e.data);
      if (d[0] === 0xAA && d.length >= 8) {
        servos[0].angle = ((d[1] << 8) | d[2]) / 100;
        servos[1].angle = ((d[3] << 8) | d[4]) / 100;
        servos[2].angle = ((d[5] << 8) | d[6]) / 100;
        estop = d[7] === 1;
        for (var i = 0; i < 3; i++) {
          document.getElementById('servo' + i).value = servos[i].angle;
          document.getElementById('angle' + i).textContent = Math.round(servos[i].angle) + '°';
        }
        updateStopBtn();
        drawArm();
      }
    }
  };
}

function updateSlider(i) {
  var slider = document.getElementById('servo' + i);
  slider.min = servos[i].min;
  slider.max = servos[i].max;
  slider.value = servos[i].angle;
  document.getElementById('angle' + i).textContent = Math.round(servos[i].angle) + '°';
  document.getElementById('range' + i).textContent = servos[i].min + '° - ' + servos[i].max + '°';
  document.getElementById('speed' + i).value = servos[i].speed;
  document.getElementById('spdval' + i).textContent = servos[i].speed;
}

function send(data) {
  if (connected && ws.readyState === 1) {
    ws.send(new Uint8Array(data).buffer);
  }
}

function moveServo(i, val) {
  val = parseInt(val);
  document.getElementById('angle' + i).textContent = val + '°';
  servos[i].angle = val;
  var a = Math.round(val * 100);
  send([0x01, i, (a >> 8) & 0xFF, a & 0xFF, servos[i].speed]);
  drawArm();
}

function setSpeed(i, val) {
  servos[i].speed = parseInt(val);
  document.getElementById('spdval' + i).textContent = val;
  send([0x07, i, parseInt(val)]);
}

function goHome() {
  send([0x08]);
}

function toggleStop() {
  send([0x04]);
}

function resetESP() {
  if (confirm('Reset ESP32? This will stop all movement at current positions and clear all state.')) {
    send([0x09]);  // Reset command - stops at current positions, clears state
    // Keep current positions in UI - don't reset to home
    // The servos will stop where they are, state will be cleared
    estop = false;
    updateStopBtn();
    // UI positions remain unchanged - servos stay at current angles
    drawArm();
    console.log('ESP32 Reset sent - Servos will stop at current positions');
  }
}

function updateStopBtn() {
  var btn = document.getElementById('stopBtn');
  if (estop) {
    btn.className = 'btn btn-stop active';
    btn.textContent = '🛑 RELEASE';
  } else {
    btn.className = 'btn btn-stop';
    btn.textContent = '🛑 STOP';
  }
}

function openSettings() {
  for (var i = 0; i < 3; i++) {
    document.getElementById('min' + i).value = servos[i].min;
    document.getElementById('max' + i).value = servos[i].max;
  }
  document.getElementById('modal').className = 'modal-bg open';
}

function closeSettings() {
  document.getElementById('modal').className = 'modal-bg';
}

function saveSettings() {
  for (var i = 0; i < 3; i++) {
    var min = parseInt(document.getElementById('min' + i).value);
    var max = parseInt(document.getElementById('max' + i).value);
    if (min < max) {
      servos[i].min = min;
      servos[i].max = max;
      send([0x02, i, min, max]);
      updateSlider(i);
    }
  }
  closeSettings();
}

function drawArm() {
  var c = document.getElementById('canvas');
  var ctx = c.getContext('2d');
  c.width = c.offsetWidth * 2;
  c.height = c.offsetHeight * 2;
  ctx.scale(2, 2);
  
  var w = c.offsetWidth, h = c.offsetHeight;
  ctx.fillStyle = '#0a0a0f';
  ctx.fillRect(0, 0, w, h);
  
  var bx = w / 2, by = h - 15;
  var l1 = 45, l2 = 35;
  
  var a0 = (servos[0].angle - 90) * Math.PI / 180;
  var a1 = (180 - servos[1].angle) * Math.PI / 180;
  var a2 = (180 - servos[2].angle) * Math.PI / 180;
  
  var j1x = bx + Math.sin(a0) * 12;
  var j1y = by - 12;
  var j2x = j1x + Math.cos(a1) * l1;
  var j2y = j1y - Math.sin(a1) * l1;
  var ex = j2x + Math.cos(a1 + a2 - Math.PI) * l2;
  var ey = j2y - Math.sin(a1 + a2 - Math.PI) * l2;
  
  // Base
  ctx.fillStyle = '#00d4ff';
  ctx.beginPath();
  ctx.arc(bx, by, 15, Math.PI, 0);
  ctx.fill();
  
  // Arm 1
  ctx.strokeStyle = '#00ff88';
  ctx.lineWidth = 5;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(j1x, j1y);
  ctx.lineTo(j2x, j2y);
  ctx.stroke();
  
  // Arm 2
  ctx.strokeStyle = '#00d4ff';
  ctx.beginPath();
  ctx.moveTo(j2x, j2y);
  ctx.lineTo(ex, ey);
  ctx.stroke();
  
  // Joints
  ctx.fillStyle = '#fff';
  ctx.beginPath();
  ctx.arc(j1x, j1y, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(j2x, j2y, 4, 0, Math.PI * 2);
  ctx.fill();
  
  // Drill tip
  ctx.fillStyle = '#ff3860';
  ctx.beginPath();
  ctx.arc(ex, ey, 3, 0, Math.PI * 2);
  ctx.fill();
}

// Initialize
window.onload = function() {
  drawArm();
  connect();
};
</script>
</body>
</html>
)rawliteral";

void testServo(int channel, const char* name) {
  Serial.printf("[TEST] %s (CH%d): Moving to 90°...\n", name, channel);
  setServoAngle(channel, 90);
  delay(500);
  Serial.printf("[TEST] %s (CH%d): Moving to 45°...\n", name, channel);
  setServoAngle(channel, 45);
  delay(500);
  Serial.printf("[TEST] %s (CH%d): Moving to 135°...\n", name, channel);
  setServoAngle(channel, 135);
  delay(500);
  Serial.printf("[TEST] %s (CH%d): Back to 90°\n", name, channel);
  setServoAngle(channel, 90);
  delay(300);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=====================================");
  Serial.println("  DRILLING ARM CONTROLLER v2.2");
  Serial.println("        DIAGNOSTIC MODE");
  Serial.println("=====================================\n");
  
  EEPROM.begin(EEPROM_SIZE);
  loadSettings();
  
  // I2C Setup
  Serial.println("[I2C] Initializing I2C on SDA=21, SCL=22...");
  Wire.begin(SDA_PIN, SCL_PIN);
  
  // Scan for I2C devices
  Serial.println("[I2C] Scanning for devices...");
  byte count = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("[I2C] Found device at 0x%02X\n", addr);
      count++;
    }
  }
  if (count == 0) {
    Serial.println("[I2C] ERROR: No devices found! Check wiring:");
    Serial.println("      - ESP32 GPIO21 -> PCA9685 SDA");
    Serial.println("      - ESP32 GPIO22 -> PCA9685 SCL");
    Serial.println("      - ESP32 GND -> PCA9685 GND");
    Serial.println("      - ESP32 3.3V -> PCA9685 VCC");
  }
  
  // PCA9685 Setup
  Serial.println("\n[PCA9685] Initializing...");
  pca.begin();
  pca.setOscillatorFrequency(25000000);
  pca.setPWMFreq(PWM_FREQ);
  delay(10);
  Serial.println("[PCA9685] Ready");
  
  // Test each servo
  Serial.println("\n[SERVO TEST] Testing all servos...");
  Serial.println("[SERVO TEST] If servos don't move, check:");
  Serial.println("             - V+ on PCA9685 needs 5-6V external power!");
  Serial.println("             - Servo signal wires on CH0, CH1, CH2");
  Serial.println("             - Servo power (red) to V+, ground (brown) to GND\n");
  
  testServo(CH_BASE, "BASE");
  testServo(CH_MIDDLE, "MIDDLE");
  testServo(CH_TOP, "TOP");
  
  Serial.println("\n[SERVO TEST] Complete!");
  
  // Set initial positions
  for (int i = 0; i < 3; i++) {
    setServoAngle(i, servos[i].current);
  }
  Serial.println("[OK] Servos initialized");
  
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.print("[OK] WiFi AP: ");
  Serial.println(AP_SSID);
  Serial.print("    IP: ");
  Serial.println(WiFi.softAPIP());
  
  ws.onEvent(onWsEvent);
  server.addHandler(&ws);
  
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send_P(200, "text/html", INDEX_HTML);
  });
  
  server.begin();
  Serial.println("[OK] Server started");
  Serial.println("\n>>> Connect to WiFi 'DrillArm' (pass: drill1234)");
  Serial.println(">>> Open http://192.168.4.1\n");
}

void loop() {
  static unsigned long lastUpdate = 0;
  unsigned long now = millis();
  
  // Check for Serial commands
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();
    
    if (cmd == "RESET" || cmd == "CLEAR") {
      clearEEPROM();
    }
    else if (cmd == "TEST") {
      Serial.println("\n[MANUAL TEST] Testing servos...");
      testServo(CH_BASE, "BASE");
      testServo(CH_MIDDLE, "MIDDLE");
      testServo(CH_TOP, "TOP");
    }
    else if (cmd == "STATUS") {
      Serial.println("\n[STATUS]");
      for (int i = 0; i < 3; i++) {
        Serial.printf("  %s: current=%.1f°, target=%.1f°, limits=%d-%d°, speed=%d\n",
          servos[i].name, servos[i].current, servos[i].target,
          servos[i].minLimit, servos[i].maxLimit, servos[i].speed);
      }
    }
    else if (cmd == "HELP") {
      Serial.println("\n[COMMANDS]");
      Serial.println("  RESET  - Clear EEPROM and restore defaults");
      Serial.println("  TEST   - Test all servos");
      Serial.println("  STATUS - Show current servo positions");
      Serial.println("  HELP   - Show this help");
    }
    else if (cmd.length() > 0) {
      Serial.println("[?] Unknown command. Type HELP for commands.");
    }
  }
  
  uint8_t minSpeed = 100;
  for (int i = 0; i < 3; i++) {
    if (abs(servos[i].target - servos[i].current) > 0.3) {
      if (servos[i].speed < minSpeed) minSpeed = servos[i].speed;
    }
  }
  unsigned long interval = map(minSpeed, 1, 100, 2, 40);
  
  if (now - lastUpdate >= interval) {
    updateServos();
    lastUpdate = now;
  }
  
  if (now - lastBroadcast >= 80) {
    broadcastStatus();
    lastBroadcast = now;
  }
  
  ws.cleanupClients();
}
