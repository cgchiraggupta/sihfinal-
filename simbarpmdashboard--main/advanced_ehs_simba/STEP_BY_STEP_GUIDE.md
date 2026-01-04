# 📋 Step-by-Step Integration Guide

## 🎯 What You Need to Do Now

---

## ✅ STEP 1: Check Your Current Setup (5 minutes)

### **1.1 Verify Flask API is Running**
```bash
cd /Users/apple/Downloads/perpexcu/advanced_ehs_simba
source venv/bin/activate
python arduino_api.py
```

**Expected**: Should see "Arduino Drilling MVP API" running on port 5001

### **1.2 Test the API**
Open new terminal:
```bash
curl http://localhost:5001/
```

**Expected**: JSON response with API info

### **1.3 Check Supabase Connection**
```bash
# Test if Supabase is accessible
curl -X POST http://localhost:5001/log \
  -H "Content-Type: application/json" \
  -d '{"rpm": 2300, "current": 14.5, "vibration_readings": [68,72,70], "depth": 45.5}'
```

**Expected**: `{"status": "logged", "log_id": "...", "prediction": {...}}`

---

## ✅ STEP 2: Modify ESP32 Arduino Code (30-60 minutes)

### **2.1 Open Your Friend's Arduino Code**
- Open the `.ino` file in Arduino IDE
- Make sure ESP32 board is selected

### **2.2 Add Vibration Buffer (Top of File)**
```cpp
// Add after #define statements
int vibBuffer[10] = {0};
int vibIndex = 0;
unsigned long lastSendTime = 0;
const unsigned long SEND_INTERVAL = 2000; // Send every 2 seconds
```

### **2.3 Modify loop() Function**
```cpp
void loop() {
  server.handleClient();
  
  // Collect vibration readings
  vibBuffer[vibIndex] = analogRead(VIB_AO_PIN);
  vibIndex = (vibIndex + 1) % 10;
  
  // Send to ML API every 2 seconds
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    sendToMLAPI();
    lastSendTime = millis();
  }
}
```

### **2.4 Add Function to Get RPM**
```cpp
// Add this function - modify based on your drill controller
float getRPMFromController() {
  // OPTION 1: If your drill controller has serial/I2C
  // return readRPMFromSerial();
  
  // OPTION 2: Calculate from pump speed (if related)
  float rpm = map(pumpSpeedPercent, 0, 100, 500, 3000);
  return rpm;
  
  // OPTION 3: If you have encoder
  // return calculateRPMFromEncoder();
  
  // OPTION 4: Estimate from current (temporary)
  // float currentA = readCurrentACS712();
  // return (currentA * 150.0) + 500;
}
```

### **2.5 Add Function to Get Depth**
```cpp
// Add this function
float getDepth() {
  // OPTION 1: If you have depth encoder
  // return readDepthFromEncoder();
  
  // OPTION 2: Estimate from time (if drilling started)
  static unsigned long drillingStartTime = 0;
  static bool drillingStarted = false;
  
  if (drillOn && !drillingStarted) {
    drillingStartTime = millis();
    drillingStarted = true;
  }
  
  if (!drillOn) {
    drillingStarted = false;
    return 0;
  }
  
  // Estimate: 0.1 m/s drilling rate (adjust based on your drill)
  float depth = (millis() - drillingStartTime) / 1000.0 * 0.1;
  return depth;
}
```

### **2.6 Add Function to Send to ML API**
```cpp
// Add this function
void sendToMLAPI() {
  // Get sensor data
  float rpm = getRPMFromController();
  float currentA = readCurrentACS712();
  float depth = getDepth();
  
  // Build vibration array string
  String vibArray = "[";
  for(int i = 0; i < 10; i++) {
    vibArray += String(vibBuffer[i]);
    if(i < 9) vibArray += ",";
  }
  vibArray += "]";
  
  // Build JSON payload
  String json = "{";
  json += "\"rpm\":" + String(rpm, 1) + ",";
  json += "\"current\":" + String(currentA, 3) + ",";
  json += "\"vibration_readings\":" + vibArray + ",";
  json += "\"depth\":" + String(depth, 2);
  json += "}";
  
  // Get your PC's IP address (replace with actual IP)
  // Find it: On Mac: System Preferences > Network
  const char* apiHost = "192.168.1.100"; // CHANGE THIS!
  int apiPort = 5001;
  
  WiFiClient client;
  if(client.connect(apiHost, apiPort)) {
    client.println("POST /log HTTP/1.1");
    client.println("Host: " + String(apiHost) + ":" + String(apiPort));
    client.println("Content-Type: application/json");
    client.print("Content-Length: ");
    client.println(json.length());
    client.println();
    client.print(json);
    
    // Wait for response
    unsigned long timeout = millis();
    while(client.available() == 0) {
      if(millis() - timeout > 5000) {
        Serial.println(">>> Client Timeout !");
        client.stop();
        return;
      }
    }
    
    // Read response
    String response = "";
    while(client.available()) {
      response += client.readStringUntil('\r');
    }
    
    Serial.println("API Response: " + response);
    
    // Parse prediction (optional - for future use)
    // You can extract material prediction and display it
    
    client.stop();
  } else {
    Serial.println("Connection to API failed!");
  }
}
```

### **2.7 Find Your PC's IP Address**
**On Mac**:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```
Look for something like `192.168.1.100` or `10.0.0.5`

**Update in code**:
```cpp
const char* apiHost = "YOUR_PC_IP_HERE"; // e.g., "192.168.1.100"
```

---

## ✅ STEP 3: Upload & Test ESP32 (15 minutes)

### **3.1 Upload Code**
1. Connect ESP32 via USB
2. Select correct port in Arduino IDE
3. Click Upload
4. Wait for "Done uploading"

### **3.2 Open Serial Monitor**
- Set baud rate to 115200
- You should see:
  - WiFi connection status
  - IP address
  - "Connection to API failed!" or "API Response: ..."

### **3.3 Test Connection**
1. ESP32 should connect to WiFi
2. Every 2 seconds, it should send data to your API
3. Check Serial Monitor for responses

---

## ✅ STEP 4: Verify Data Flow (10 minutes)

### **4.1 Check Flask API Logs**
In terminal where `arduino_api.py` is running:
- You should see POST requests coming in
- Check for any errors

### **4.2 Test Prediction**
```bash
curl http://localhost:5001/history | python3 -m json.tool
```

**Expected**: See your ESP32 data in the response

### **4.3 Check Supabase Dashboard**
1. Go to: https://supabase.com/dashboard
2. Navigate to your project
3. Go to Table Editor > `ehs_drill_logs`
4. You should see new rows appearing every 2 seconds!

---

## ✅ STEP 5: Fix Common Issues (If Needed)

### **Issue 1: "Connection to API failed"**
**Solution**:
- Check PC and ESP32 are on same WiFi network
- Verify PC's IP address is correct
- Check firewall isn't blocking port 5001
- Make sure Flask API is running

### **Issue 2: "Missing rpm or current"**
**Solution**:
- Check `getRPMFromController()` returns valid value
- Verify `readCurrentACS712()` works
- Add Serial.println() to debug values

### **Issue 3: No data in Supabase**
**Solution**:
- Check Flask API logs for errors
- Verify Supabase credentials in `arduino_api.py`
- Test API manually with curl

### **Issue 4: RPM is always 0 or wrong**
**Solution**:
- Modify `getRPMFromController()` based on your drill controller
- If using encoder, implement encoder reading
- If using PWM, map PWM to RPM correctly

---

## ✅ STEP 6: Optimize & Enhance (Optional)

### **6.1 Display ML Prediction on ESP32 Dashboard**
Modify ESP32's HTML to show:
- Predicted material
- Confidence score
- Recommended RPM

### **6.2 Use ML Prediction to Optimize Drill**
```cpp
void optimizeDrillFromML(String material) {
  // Get optimal RPM from material
  if (material == "Granite") {
    pumpSpeedPercent = 75; // Optimal for granite
  } else if (material == "Coal") {
    pumpSpeedPercent = 30; // Optimal for coal
  }
  // ... etc
}
```

### **6.3 Add More Sensors**
- Pressure sensor (improves prediction)
- Temperature sensor (already have DHT11)
- GPS module (for location tracking)

---

## 📋 Quick Checklist

- [ ] **Step 1**: Flask API running and tested
- [ ] **Step 2**: Modified Arduino code with:
  - [ ] Vibration buffer
  - [ ] RPM function
  - [ ] Depth function
  - [ ] sendToMLAPI() function
- [ ] **Step 3**: Uploaded to ESP32
- [ ] **Step 4**: Data flowing to Supabase
- [ ] **Step 5**: Fixed any issues
- [ ] **Step 6**: Optional enhancements

---

## 🎯 Expected Result

After completing these steps:
- ✅ ESP32 sends sensor data every 2 seconds
- ✅ Flask API receives data and makes ML predictions
- ✅ Data stored in Supabase cloud database
- ✅ You can view data in Supabase dashboard
- ✅ Material predictions happening in real-time

---

## 🆘 Need Help?

**If stuck on any step**:
1. Check Serial Monitor output
2. Check Flask API terminal output
3. Test API manually with curl
4. Check Supabase dashboard for errors

**Common Questions**:
- **"How do I get RPM from my drill controller?"** → Depends on your controller. Tell me what controller you use!
- **"What if I don't have depth encoder?"** → Use time-based estimate (already in code)
- **"Can I test without real drill?"** → Yes! Use fake data in `sendToMLAPI()`

---

## 🚀 Next Steps After Integration

1. **Monitor for 24 hours** - Collect real data
2. **Analyze patterns** - Check Supabase for trends
3. **Optimize ML model** - Retrain with real data
4. **Add features** - Safety alerts, energy tracking
5. **Build dashboard** - Visualize data

---

**Ready to start? Begin with Step 1!** 🎯



