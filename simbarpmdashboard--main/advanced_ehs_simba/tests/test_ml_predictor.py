"""
Unit tests for ML Predictor module.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_predictor import (
    MaterialType,
    SensorInput,
    PredictionResult,
    FeatureEngineer,
    MaterialPredictor,
)


class TestMaterialType:
    """Tests for MaterialType enum."""
    
    def test_hardness_values(self):
        """Test hardness values for different materials."""
        assert MaterialType.get_hardness("soft_soil") == 1.0
        assert MaterialType.get_hardness("granite") == 8.0
        assert MaterialType.get_hardness("basalt") == 9.0
        assert MaterialType.get_hardness("void") == 0.0
    
    def test_unknown_material_hardness(self):
        """Test default hardness for unknown material."""
        assert MaterialType.get_hardness("unknown_material") == 5.0


class TestSensorInput:
    """Tests for SensorInput dataclass."""
    
    def test_basic_creation(self):
        """Test basic sensor input creation."""
        sensor = SensorInput(
            rpm=80.0,
            current_a=120.0,
            vibration_g=2.5,
            depth_m=15.0,
        )
        
        assert sensor.rpm == 80.0
        assert sensor.current_a == 120.0
        assert sensor.vibration_g == 2.5
        assert sensor.depth_m == 15.0
        assert sensor.pressure_bar is None
    
    def test_with_optional_values(self):
        """Test sensor input with optional values."""
        sensor = SensorInput(
            rpm=80.0,
            current_a=120.0,
            vibration_g=2.5,
            depth_m=15.0,
            pressure_bar=250.0,
            temperature_c=65.0,
            acoustic_db=75.0,
        )
        
        assert sensor.pressure_bar == 250.0
        assert sensor.temperature_c == 65.0
        assert sensor.acoustic_db == 75.0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        sensor = SensorInput(
            rpm=80.0,
            current_a=120.0,
            vibration_g=2.5,
            depth_m=15.0,
        )
        
        result = sensor.to_dict()
        
        assert result["rpm"] == 80.0
        assert result["current_a"] == 120.0
        assert "timestamp" in result
    
    def test_to_feature_vector(self):
        """Test conversion to feature vector."""
        sensor = SensorInput(
            rpm=80.0,
            current_a=120.0,
            vibration_g=2.5,
            depth_m=15.0,
            pressure_bar=250.0,
            temperature_c=65.0,
            acoustic_db=75.0,
        )
        
        features = sensor.to_feature_vector()
        
        assert isinstance(features, np.ndarray)
        assert len(features) == 7
        assert features[0] == 80.0  # rpm
        assert features[1] == 120.0  # current
        assert features[4] == 250.0  # pressure
    
    def test_to_feature_vector_with_defaults(self):
        """Test feature vector fills defaults for missing values."""
        sensor = SensorInput(
            rpm=80.0,
            current_a=120.0,
            vibration_g=2.5,
            depth_m=15.0,
        )
        
        features = sensor.to_feature_vector()
        
        # Check defaults are used
        assert features[4] == 200.0  # default pressure
        assert features[5] == 45.0   # default temperature
        assert features[6] == 70.0   # default acoustic


class TestFeatureEngineer:
    """Tests for FeatureEngineer class."""
    
    def test_initialization(self):
        """Test feature engineer initialization."""
        fe = FeatureEngineer()
        
        assert fe._is_fitted == False
        assert len(fe.feature_names) > 0
    
    def test_extend_features(self):
        """Test feature extension."""
        fe = FeatureEngineer()
        
        # Create sample input
        X = np.array([[80, 120, 2.5, 15, 250, 65, 75]])
        
        X_extended = fe._extend_features(X)
        
        # Should have more features than input
        assert X_extended.shape[1] > X.shape[1]
    
    def test_fit_transform(self):
        """Test fit_transform operation."""
        fe = FeatureEngineer()
        
        # Create sample data
        X = np.random.rand(100, 7) * 100
        
        X_transformed = fe.fit_transform(X)
        
        assert fe._is_fitted == True
        assert X_transformed.shape[0] == X.shape[0]
    
    def test_extract_frequency_features_short_signal(self):
        """Test frequency feature extraction with short signal."""
        fe = FeatureEngineer()
        
        # Short signal
        signal = np.array([1.0, 2.0, 3.0])
        
        features = fe.extract_frequency_features(signal)
        
        assert features["dominant_freq"] == 0.0
    
    def test_extract_frequency_features_normal_signal(self):
        """Test frequency feature extraction with normal signal."""
        fe = FeatureEngineer()
        
        # Generate sinusoidal signal
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 50 * t) + np.sin(2 * np.pi * 100 * t)
        
        features = fe.extract_frequency_features(signal, sampling_rate=1000)
        
        assert "dominant_freq" in features
        assert "freq_energy_low" in features
        assert "freq_energy_mid" in features
        assert "freq_energy_high" in features


class TestMaterialPredictor:
    """Tests for MaterialPredictor class."""
    
    @pytest.fixture
    def predictor(self):
        """Create a predictor instance for testing."""
        pred = MaterialPredictor()
        pred.load_or_train()
        return pred
    
    def test_initialization(self):
        """Test predictor initialization."""
        pred = MaterialPredictor()
        
        assert pred.is_trained == False
        assert len(pred.classes) > 0
    
    def test_load_or_train(self):
        """Test loading or training model."""
        pred = MaterialPredictor()
        
        result = pred.load_or_train()
        
        assert result == True
        assert pred.is_trained == True
    
    def test_predict(self, predictor):
        """Test material prediction."""
        sensor_input = SensorInput(
            rpm=80.0,
            current_a=180.0,  # High current suggests hard material
            vibration_g=3.0,
            depth_m=15.0,
            pressure_bar=280.0,
        )
        
        result = predictor.predict(sensor_input)
        
        assert isinstance(result, PredictionResult)
        assert result.material in predictor.classes
        assert 0 <= result.confidence <= 1
        assert result.recommended_rpm is not None
    
    def test_predict_soft_material(self, predictor):
        """Test prediction for soft material characteristics."""
        sensor_input = SensorInput(
            rpm=120.0,
            current_a=50.0,  # Low current
            vibration_g=0.5,  # Low vibration
            depth_m=5.0,
            pressure_bar=150.0,  # Low pressure
        )
        
        result = predictor.predict(sensor_input)
        
        # Should predict softer material
        assert result.confidence > 0.5
    
    def test_predict_hard_material(self, predictor):
        """Test prediction for hard material characteristics."""
        sensor_input = SensorInput(
            rpm=50.0,
            current_a=200.0,  # High current
            vibration_g=4.0,  # High vibration
            depth_m=20.0,
            pressure_bar=320.0,  # High pressure
        )
        
        result = predictor.predict(sensor_input)
        
        # Should predict harder material
        assert result.confidence > 0.5
    
    def test_predict_batch(self, predictor):
        """Test batch prediction."""
        inputs = [
            SensorInput(rpm=80, current_a=120, vibration_g=2.0, depth_m=10),
            SensorInput(rpm=60, current_a=180, vibration_g=3.5, depth_m=15),
            SensorInput(rpm=100, current_a=80, vibration_g=1.0, depth_m=5),
        ]
        
        results = predictor.predict_batch(inputs)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, PredictionResult)
    
    def test_get_feature_importance(self, predictor):
        """Test getting feature importance."""
        importance = predictor.get_feature_importance()
        
        assert isinstance(importance, dict)
        assert len(importance) > 0
        assert all(isinstance(v, float) for v in importance.values())
    
    def test_prediction_result_to_dict(self, predictor):
        """Test prediction result serialization."""
        sensor_input = SensorInput(
            rpm=80.0,
            current_a=120.0,
            vibration_g=2.5,
            depth_m=15.0,
        )
        
        result = predictor.predict(sensor_input)
        result_dict = result.to_dict()
        
        assert "material" in result_dict
        assert "confidence" in result_dict
        assert "probabilities" in result_dict
        assert "timestamp" in result_dict
    
    def test_generate_synthetic_data(self):
        """Test synthetic data generation."""
        pred = MaterialPredictor()
        
        data = pred._generate_synthetic_data(n_samples=100)
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) >= 100
        assert "material" in data.columns
        assert "rpm" in data.columns


class TestMaterialPredictorEdgeCases:
    """Edge case tests for MaterialPredictor."""
    
    def test_predict_without_training(self):
        """Test that prediction fails without training."""
        pred = MaterialPredictor()
        
        sensor_input = SensorInput(
            rpm=80.0,
            current_a=120.0,
            vibration_g=2.5,
            depth_m=15.0,
        )
        
        with pytest.raises(RuntimeError):
            pred.predict(sensor_input)
    
    def test_predict_with_extreme_values(self):
        """Test prediction with extreme sensor values."""
        pred = MaterialPredictor()
        pred.load_or_train()
        
        # Very high values
        sensor_input = SensorInput(
            rpm=300.0,
            current_a=500.0,
            vibration_g=15.0,
            depth_m=100.0,
        )
        
        result = pred.predict(sensor_input)
        
        # Should still produce valid output
        assert result.material in pred.classes
        assert 0 <= result.confidence <= 1
    
    def test_predict_with_zero_values(self):
        """Test prediction with zero values."""
        pred = MaterialPredictor()
        pred.load_or_train()
        
        sensor_input = SensorInput(
            rpm=0.0,
            current_a=0.0,
            vibration_g=0.0,
            depth_m=0.0,
        )
        
        result = pred.predict(sensor_input)
        
        # Should handle zeros gracefully
        assert result.material in pred.classes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

