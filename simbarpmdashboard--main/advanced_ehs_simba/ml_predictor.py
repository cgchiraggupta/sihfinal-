"""
Advanced ML Material Predictor
Features:
- Vibration pattern analysis
- Multi-sensor fusion
- Real-time prediction confidence
- Anomaly detection for unknown materials
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import json
from datetime import datetime

class MaterialPredictor:
    def __init__(self):
        self.rf_model = None
        self.gb_model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'rpm', 'current', 'vibration_mean', 'vibration_std', 
            'vibration_max', 'rpm_stability', 'current_spike', 
            'depth', 'hardness_estimate', 'ucs_estimate'
        ]
        
        # Material properties database
        self.material_db = {
            'Coal': {'hardness': 1.5, 'ucs': 12.5, 'rpm': 450, 'density': 1.3, 'category': 'A'},
            'Shale': {'hardness': 3, 'ucs': 30, 'rpm': 680, 'density': 2.4, 'category': 'A'},
            'Limestone': {'hardness': 3.5, 'ucs': 55, 'rpm': 850, 'density': 2.7, 'category': 'A'},
            'Dolomite': {'hardness': 4, 'ucs': 115, 'rpm': 1100, 'density': 2.8, 'category': 'B'},
            'Sandstone': {'hardness': 6.5, 'ucs': 125, 'rpm': 1350, 'density': 2.3, 'category': 'B'},
            'Hematite': {'hardness': 5.5, 'ucs': 200, 'rpm': 1800, 'density': 5.3, 'category': 'B'},
            'Magnetite': {'hardness': 6, 'ucs': 225, 'rpm': 2100, 'density': 5.2, 'category': 'C'},
            'Granite': {'hardness': 6.5, 'ucs': 200, 'rpm': 2300, 'density': 2.7, 'category': 'C'},
            'Gneiss': {'hardness': 6.5, 'ucs': 200, 'rpm': 2400, 'density': 2.7, 'category': 'C'},
            'Quartzite': {'hardness': 7, 'ucs': 175, 'rpm': 2800, 'density': 2.6, 'category': 'C'},
            'Schist': {'hardness': 4.5, 'ucs': 125, 'rpm': 1500, 'density': 2.7, 'category': 'B'},
            'Quartz_Veins': {'hardness': 7, 'ucs': 200, 'rpm': 3200, 'density': 2.65, 'category': 'C'},
            'Copper': {'hardness': 3.5, 'ucs': 75, 'rpm': 950, 'density': 2.8, 'category': 'B'}
        }
    
    def generate_synthetic_data(self, samples_per_material=100):
        """Generate synthetic training data with realistic variations"""
        X = []
        y = []
        
        for material, props in self.material_db.items():
            base_rpm = props['rpm']
            base_hardness = props['hardness']
            base_ucs = props['ucs']
            
            for _ in range(samples_per_material):
                # Add realistic noise and variations
                rpm = base_rpm + np.random.normal(0, base_rpm * 0.1)
                current = (rpm / 200) + np.random.normal(0, 1.5)
                
                # Vibration patterns vary with material hardness
                vib_mean = base_hardness * 10 + np.random.normal(0, 5)
                vib_std = base_hardness * 2 + np.random.normal(0, 2)
                vib_max = vib_mean + vib_std * 2
                
                # RPM stability (harder materials = more stable)
                rpm_stability = 100 - (base_hardness * 5) + np.random.normal(0, 10)
                
                # Current spike during material break
                current_spike = base_ucs / 20 + np.random.normal(0, 2)
                
                # Depth (random underground position)
                depth = np.random.uniform(10, 200)
                
                # Estimated properties from sensor readings
                hardness_est = (rpm / 500) + 1 + np.random.normal(0, 0.5)
                ucs_est = rpm / 15 + np.random.normal(0, 10)
                
                features = [
                    rpm, current, vib_mean, vib_std, vib_max,
                    rpm_stability, current_spike, depth,
                    hardness_est, ucs_est
                ]
                
                X.append(features)
                y.append(material)
        
        return np.array(X), np.array(y)
    
    def train(self, X=None, y=None, save_model=True):
        """Train the ML models"""
        if X is None or y is None:
            print("Generating synthetic training data...")
            X, y = self.generate_synthetic_data(samples_per_material=100)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        print("\nTraining Random Forest...")
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        self.rf_model.fit(X_train_scaled, y_train)
        
        # Train Gradient Boosting
        print("Training Gradient Boosting...")
        self.gb_model = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=7,
            random_state=42
        )
        self.gb_model.fit(X_train_scaled, y_train)
        
        # Evaluate
        rf_score = self.rf_model.score(X_test_scaled, y_test)
        gb_score = self.gb_model.score(X_test_scaled, y_test)
        
        print(f"\nRandom Forest Accuracy: {rf_score:.3f}")
        print(f"Gradient Boosting Accuracy: {gb_score:.3f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 5 Most Important Features:")
        print(feature_importance.head())
        
        # Save models
        if save_model:
            joblib.dump(self.rf_model, 'models/rf_material_model.pkl')
            joblib.dump(self.gb_model, 'models/gb_material_model.pkl')
            joblib.dump(self.scaler, 'models/scaler.pkl')
            print("\nModels saved successfully!")
        
        return rf_score, gb_score
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            self.rf_model = joblib.load('models/rf_material_model.pkl')
            self.gb_model = joblib.load('models/gb_material_model.pkl')
            self.scaler = joblib.load('models/scaler.pkl')
            print("Models loaded successfully!")
            return True
        except FileNotFoundError:
            print("Models not found. Training new models...")
            self.train()
            return True
    
    def predict(self, sensor_data, ensemble=True):
        """
        Predict material from sensor data
        
        sensor_data should contain:
        - rpm: current RPM
        - current: motor current (A)
        - vibration_readings: list of vibration sensor readings
        - depth: current depth (m)
        """
        # Extract features
        features = self._extract_features(sensor_data)
        features_scaled = self.scaler.transform([features])
        
        if ensemble:
            # Ensemble prediction (average of both models)
            rf_proba = self.rf_model.predict_proba(features_scaled)[0]
            gb_proba = self.gb_model.predict_proba(features_scaled)[0]
            
            # Weighted average (RF gets more weight due to better performance)
            ensemble_proba = 0.6 * rf_proba + 0.4 * gb_proba
            
            predicted_idx = np.argmax(ensemble_proba)
            predicted_material = self.rf_model.classes_[predicted_idx]
            confidence = ensemble_proba[predicted_idx] * 100
            
            # Get top 3 predictions
            top_3_idx = np.argsort(ensemble_proba)[-3:][::-1]
            top_3 = [
                {
                    'material': self.rf_model.classes_[idx],
                    'confidence': ensemble_proba[idx] * 100,
                    'properties': self.material_db[self.rf_model.classes_[idx]]
                }
                for idx in top_3_idx
            ]
        else:
            # Single model prediction
            predicted_material = self.rf_model.predict(features_scaled)[0]
            proba = self.rf_model.predict_proba(features_scaled)[0]
            confidence = max(proba) * 100
            
            top_3_idx = np.argsort(proba)[-3:][::-1]
            top_3 = [
                {
                    'material': self.rf_model.classes_[idx],
                    'confidence': proba[idx] * 100,
                    'properties': self.material_db[self.rf_model.classes_[idx]]
                }
                for idx in top_3_idx
            ]
        
        # Anomaly detection (low confidence = unknown material)
        is_anomaly = confidence < 60
        
        return {
            'predicted_material': predicted_material,
            'confidence': confidence,
            'top_3_predictions': top_3,
            'is_anomaly': is_anomaly,
            'category': self.material_db[predicted_material]['category'],
            'recommended_rpm': self.material_db[predicted_material]['rpm'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_features(self, sensor_data):
        """Extract features from raw sensor data"""
        rpm = sensor_data['rpm']
        current = sensor_data['current']
        vibration = np.array(sensor_data.get('vibration_readings', [50]))
        depth = sensor_data.get('depth', 0)
        
        # Vibration statistics
        vib_mean = np.mean(vibration)
        vib_std = np.std(vibration)
        vib_max = np.max(vibration)
        
        # RPM stability (lower std = more stable)
        rpm_history = sensor_data.get('rpm_history', [rpm])
        rpm_stability = 100 - np.std(rpm_history)
        
        # Current spike detection
        current_history = sensor_data.get('current_history', [current])
        current_spike = max(current_history) - np.mean(current_history)
        
        # Estimated material properties
        hardness_estimate = (rpm / 500) + 1
        ucs_estimate = rpm / 15
        
        return [
            rpm, current, vib_mean, vib_std, vib_max,
            rpm_stability, current_spike, depth,
            hardness_estimate, ucs_estimate
        ]
    
    def analyze_drilling_pattern(self, time_series_data):
        """
        Analyze drilling pattern over time
        Detects material transitions and layers
        """
        df = pd.DataFrame(time_series_data)
        
        # Detect sudden changes in RPM/current (material boundaries)
        rpm_diff = df['rpm'].diff().abs()
        current_diff = df['current'].diff().abs()
        
        # Find peaks (potential material transitions)
        rpm_threshold = rpm_diff.mean() + 2 * rpm_diff.std()
        current_threshold = current_diff.mean() + 2 * current_diff.std()
        
        transitions = df[
            (rpm_diff > rpm_threshold) | 
            (current_diff > current_threshold)
        ]
        
        return {
            'num_transitions': len(transitions),
            'transition_depths': transitions['depth'].tolist(),
            'transition_times': transitions['timestamp'].tolist(),
            'materials_encountered': len(df['material'].unique()),
            'dominant_material': df['material'].mode()[0] if len(df) > 0 else 'Unknown'
        }
    
    def export_prediction_report(self, predictions, filename='prediction_report.json'):
        """Export predictions to JSON report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_predictions': len(predictions),
            'predictions': predictions,
            'material_distribution': pd.DataFrame(predictions)['predicted_material'].value_counts().to_dict(),
            'average_confidence': np.mean([p['confidence'] for p in predictions])
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report exported to {filename}")
        return report


# Example usage and testing
if __name__ == '__main__':
    print("="*60)
    print("Material Prediction ML System - Training & Demo")
    print("="*60)
    
    # Initialize predictor
    predictor = MaterialPredictor()
    
    # Train models
    predictor.train()
    
    # Demo predictions
    print("\n" + "="*60)
    print("DEMO: Material Predictions")
    print("="*60)
    
    # Test case 1: Coal (soft material)
    print("\n[Test 1] Simulating Coal drilling:")
    sensor_data_coal = {
        'rpm': 470,
        'current': 6.5,
        'vibration_readings': [12, 15, 14, 16, 13],
        'rpm_history': [465, 468, 470, 472, 469],
        'current_history': [6.2, 6.4, 6.5, 6.6, 6.3],
        'depth': 25.5
    }
    result = predictor.predict(sensor_data_coal)
    print(f"Predicted: {result['predicted_material']}")
    print(f"Confidence: {result['confidence']:.1f}%")
    print(f"Category: {result['category']}")
    print("Top 3 predictions:")
    for i, pred in enumerate(result['top_3_predictions'], 1):
        print(f"  {i}. {pred['material']}: {pred['confidence']:.1f}%")
    
    # Test case 2: Granite (hard material)
    print("\n[Test 2] Simulating Granite drilling:")
    sensor_data_granite = {
        'rpm': 2320,
        'current': 14.8,
        'vibration_readings': [68, 72, 70, 69, 71],
        'rpm_history': [2310, 2315, 2320, 2318, 2322],
        'current_history': [14.5, 14.7, 14.8, 14.9, 14.6],
        'depth': 82.3
    }
    result = predictor.predict(sensor_data_granite)
    print(f"Predicted: {result['predicted_material']}")
    print(f"Confidence: {result['confidence']:.1f}%")
    print(f"Category: {result['category']}")
    
    # Test case 3: Quartzite (very hard material)
    print("\n[Test 3] Simulating Quartzite drilling:")
    sensor_data_quartzite = {
        'rpm': 2850,
        'current': 16.2,
        'vibration_readings': [78, 82, 80, 79, 81],
        'rpm_history': [2840, 2845, 2850, 2848, 2852],
        'current_history': [16.0, 16.1, 16.2, 16.3, 16.1],
        'depth': 145.7
    }
    result = predictor.predict(sensor_data_quartzite)
    print(f"Predicted: {result['predicted_material']}")
    print(f"Confidence: {result['confidence']:.1f}%")
    print(f"Category: {result['category']}")
    
    print("\n" + "="*60)
    print("Demo complete! Models are ready for real-time predictions.")
    print("="*60)
