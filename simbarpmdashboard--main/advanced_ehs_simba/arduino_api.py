"""
Simple Arduino API for Drilling MVP
- Receives sensor data from Arduino via Serial/HTTP
- Predicts material using ML
- Stores to Supabase cloud
"""

import os
import serial
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Supabase connection
SUPABASE_URL = "https://ntxqedcyxsqdpauphunc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50eHFlZGN5eHNxZHBhdXBodW5jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5MzA3MjQsImV4cCI6MjA3NTUwNjcyNH0.WmL5Ly6utECuTt2qTWbKqltLP73V3hYPLUeylBELKTk"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Import ML predictor
from ml_predictor import MaterialPredictor

# Initialize predictor
predictor = MaterialPredictor()

# Try to load existing models or train new ones
try:
    predictor.load_models()
except:
    print("Training new models...")
    os.makedirs('models', exist_ok=True)
    predictor.train()


# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def home():
    """API info"""
    return jsonify({
        "name": "Arduino Drilling MVP API",
        "version": "1.0",
        "endpoints": {
            "/dashboard": "GET - Visual dashboard",
            "/predict": "POST - Predict material from sensor data",
            "/log": "POST - Log drilling data to Supabase",
            "/materials": "GET - List all materials",
            "/history": "GET - Get drilling history",
            "/stats": "GET - Get statistics"
        }
    })


@app.route('/dashboard')
def dashboard():
    """Visual dashboard for judges demo"""
    return render_template('dashboard.html')


@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict material from Arduino sensor data
    
    Expected JSON:
    {
        "rpm": 2300,
        "current": 14.5,
        "vibration_readings": [68, 72, 70, 69, 71],
        "depth": 45.5
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        if 'rpm' not in data or 'current' not in data:
            return jsonify({"error": "Missing rpm or current"}), 400
        
        # Add default values if missing
        sensor_data = {
            'rpm': data['rpm'],
            'current': data['current'],
            'vibration_readings': data.get('vibration_readings', [50]),
            'depth': data.get('depth', 0),
            'rpm_history': data.get('rpm_history', [data['rpm']]),
            'current_history': data.get('current_history', [data['current']])
        }
        
        # Get prediction
        result = predictor.predict(sensor_data)
        
        # Convert numpy types to Python types for JSON
        return jsonify({
            'material': str(result['predicted_material']),
            'predicted_material': str(result['predicted_material']),
            'confidence': float(result['confidence']),
            'category': str(result['category']),
            'recommended_rpm': int(result.get('recommended_rpm', data['rpm'])),
            'is_anomaly': bool(result['is_anomaly']),
            'top_3_predictions': [
                {
                    'material': str(p['material']),
                    'confidence': float(p['confidence'])
                }
                for p in result['top_3_predictions']
            ],
            'timestamp': result['timestamp']
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/log', methods=['POST'])
def log_to_supabase():
    """
    Log drilling data to Supabase
    
    Expected JSON:
    {
        "rpm": 2300,
        "current": 14.5,
        "vibration_readings": [68, 72, 70],
        "depth": 45.5,
        "latitude": 28.6139,
        "longitude": 77.2090
    }
    """
    try:
        data = request.json
        
        # Get prediction first
        sensor_data = {
            'rpm': data['rpm'],
            'current': data['current'],
            'vibration_readings': data.get('vibration_readings', [50]),
            'depth': data.get('depth', 0),
            'rpm_history': data.get('rpm_history', [data['rpm']]),
            'current_history': data.get('current_history', [data['current']])
        }
        
        prediction = predictor.predict(sensor_data)
        
        # Calculate vibration stats
        vib = data.get('vibration_readings', [50])
        import numpy as np
        vib_arr = np.array(vib)
        
        # Prepare log entry
        log_entry = {
            "rpm": float(data['rpm']),
            "current_a": float(data['current']),
            "vibration_mean": float(np.mean(vib_arr)),
            "vibration_std": float(np.std(vib_arr)),
            "vibration_max": float(np.max(vib_arr)),
            "depth_m": float(data.get('depth', 0)),
            "latitude": float(data.get('latitude')) if data.get('latitude') else None,
            "longitude": float(data.get('longitude')) if data.get('longitude') else None,
            "predicted_material": str(prediction['predicted_material']),
            "confidence": float(prediction['confidence']),
            "category": str(prediction['category']),
            "is_anomaly": bool(prediction['is_anomaly']),
            "binary_search_iterations": int(data.get('iterations')) if data.get('iterations') else None,
            "final_rpm": int(data.get('final_rpm')) if data.get('final_rpm') else None
        }
        
        # Insert to Supabase
        result = supabase.table('ehs_drill_logs').insert(log_entry).execute()
        
        return jsonify({
            "status": "logged",
            "prediction": {
                'material': str(prediction['predicted_material']),
                'confidence': float(prediction['confidence']),
                'category': str(prediction['category']),
                'recommended_rpm': int(prediction.get('recommended_rpm', data['rpm']))
            },
            "log_id": result.data[0]['id'] if result.data else None
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/materials', methods=['GET'])
def get_materials():
    """Get all materials from database"""
    try:
        result = supabase.table('ehs_materials').select('*').execute()
        return jsonify({"materials": result.data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/history', methods=['GET'])
def get_history():
    """Get drilling history (last 100 logs)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        result = (
            supabase.table('ehs_drill_logs')
            .select('*')
            .order('timestamp', desc=True)
            .limit(limit)
            .execute()
        )
        
        return jsonify({
            "count": len(result.data),
            "logs": result.data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get drilling statistics"""
    try:
        # Get all logs
        result = supabase.table('ehs_drill_logs').select('*').execute()
        logs = result.data
        
        if not logs:
            return jsonify({
                "total_logs": 0,
                "materials_found": {},
                "avg_confidence": 0
            })
        
        # Calculate stats
        import numpy as np
        from collections import Counter
        
        materials = [log['predicted_material'] for log in logs if log['predicted_material']]
        confidences = [log['confidence'] for log in logs if log['confidence']]
        
        return jsonify({
            "total_logs": len(logs),
            "materials_found": dict(Counter(materials)),
            "avg_confidence": float(np.mean(confidences)) if confidences else 0,
            "anomalies": sum(1 for log in logs if log.get('is_anomaly')),
            "depth_range": {
                "min": min((log['depth_m'] for log in logs if log.get('depth_m')), default=0),
                "max": max((log['depth_m'] for log in logs if log.get('depth_m')), default=0)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# ARDUINO SERIAL BRIDGE (Optional)
# ============================================

def run_serial_bridge(port='/dev/tty.usbmodem14201', baud=115200):
    """
    Bridge between Arduino Serial and API
    Run this if Arduino sends data via USB Serial
    """
    print(f"Connecting to Arduino on {port}...")
    
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print("Connected! Listening for data...")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                
                try:
                    # Expect JSON from Arduino
                    data = json.loads(line)
                    print(f"Received: {data}")
                    
                    # Predict and log
                    sensor_data = {
                        'rpm': data.get('rpm', 0),
                        'current': data.get('current', 0),
                        'vibration_readings': data.get('vibration', [50]),
                        'depth': data.get('depth', 0)
                    }
                    
                    prediction = predictor.predict(sensor_data)
                    print(f"Prediction: {prediction['predicted_material']} ({prediction['confidence']:.1f}%)")
                    
                    # Send result back to Arduino
                    response = {
                        'material': prediction['predicted_material'],
                        'confidence': round(prediction['confidence'], 1),
                        'category': prediction['category']
                    }
                    ser.write((json.dumps(response) + '\n').encode())
                    
                except json.JSONDecodeError:
                    print(f"Raw data: {line}")
                    
            time.sleep(0.1)
            
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("\nStopping serial bridge...")
        ser.close()


# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--serial':
        # Run serial bridge mode
        port = sys.argv[2] if len(sys.argv) > 2 else '/dev/tty.usbmodem14201'
        run_serial_bridge(port)
    else:
        # Run HTTP API mode
        print("="*50)
        print("🔧 SmartDrill Pro - Arduino Drilling MVP API")
        print("="*50)
        print("\n📊 DASHBOARD: http://localhost:5001/dashboard")
        print("\nEndpoints:")
        print("  GET  /dashboard - Visual dashboard")
        print("  POST /predict   - Get material prediction")
        print("  POST /log       - Log data to Supabase")
        print("  GET  /materials - List all materials")
        print("  GET  /history   - Get drilling history")
        print("  GET  /stats     - Get statistics")
        print("\n" + "="*50)
        
        app.run(host='0.0.0.0', port=5001, debug=True)

