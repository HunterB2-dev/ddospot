"""
Comprehensive tests for ML attack prediction model
Tests XGBoost, LightGBM, and ensemble prediction
"""

import unittest
import numpy as np
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.prediction import (
    PredictionEngine, XGBoostPredictor, LightGBMPredictor,
    PredictionResult, get_prediction_engine
)

# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def create_normal_features(samples=100, features=28):
    """Create normal traffic features"""
    return np.random.normal(loc=50, scale=10, size=(samples, features))

def create_attack_features(samples=50, features=28):
    """Create attack traffic features"""
    return np.random.normal(loc=500, scale=100, size=(samples, features))

def create_training_data(normal_samples=200, attack_samples=100, features=28):
    """Create labeled training data"""
    X_normal = np.random.normal(loc=50, scale=10, size=(normal_samples, features))
    X_attack = np.random.normal(loc=500, scale=100, size=(attack_samples, features))
    
    X = np.vstack([X_normal, X_attack])
    y = np.hstack([np.zeros(normal_samples), np.ones(attack_samples)])
    
    # Shuffle
    idx = np.random.permutation(len(y))
    
    return X[idx], y[idx]

# ============================================================================
# XGBOOST TESTS
# ============================================================================

class TestXGBoostPredictor(unittest.TestCase):
    """Test XGBoost predictor"""
    
    def setUp(self):
        """Setup test fixtures"""
        try:
            self.predictor = XGBoostPredictor(n_estimators=50)
            self.has_xgboost = True
        except ImportError:
            self.has_xgboost = False
    
    def test_initialization(self):
        """Test initialization"""
        if not self.has_xgboost:
            self.skipTest("XGBoost not available")
        
        self.assertFalse(self.predictor.is_fitted)
        self.assertEqual(self.predictor.n_estimators, 50)
    
    def test_fit(self):
        """Test model fitting"""
        if not self.has_xgboost:
            self.skipTest("XGBoost not available")
        
        X, y = create_training_data()
        self.predictor.fit(X, y)
        
        self.assertTrue(self.predictor.is_fitted)
    
    def test_predict(self):
        """Test predictions"""
        if not self.has_xgboost:
            self.skipTest("XGBoost not available")
        
        X, y = create_training_data()
        self.predictor.fit(X, y)
        
        test_X = create_normal_features(samples=10)
        preds, probs = self.predictor.predict(test_X)
        
        self.assertIsNotNone(preds)
        self.assertIsNotNone(probs)
        self.assertEqual(len(preds), 10)  # type: ignore
        self.assertEqual(len(probs), 10)  # type: ignore
    
    def test_attack_detection(self):
        """Test attack detection"""
        if not self.has_xgboost:
            self.skipTest("XGBoost not available")
        
        X, y = create_training_data()
        self.predictor.fit(X, y)
        
        # Predict on attacks
        attack_X = create_attack_features(samples=10)
        preds, probs = self.predictor.predict(attack_X)
        
        # Should detect as attacks
        attack_count = np.sum(preds == 1)
        self.assertGreater(attack_count, 5)
    
    def test_feature_importance(self):
        """Test feature importance extraction"""
        if not self.has_xgboost:
            self.skipTest("XGBoost not available")
        
        X, y = create_training_data()
        self.predictor.fit(X, y)
        
        importance = self.predictor.get_feature_importance(top_n=5)
        
        # Should have at least some features
        self.assertGreaterEqual(len(importance), 1)
        self.assertTrue(all(isinstance(f[0], str) for f in importance))
        self.assertTrue(all(isinstance(f[1], (int, float)) for f in importance))

# ============================================================================
# LIGHTGBM TESTS
# ============================================================================

class TestLightGBMPredictor(unittest.TestCase):
    """Test LightGBM predictor"""
    
    def setUp(self):
        """Setup test fixtures"""
        try:
            self.predictor = LightGBMPredictor(n_estimators=50)
            self.has_lightgbm = True
        except ImportError:
            self.has_lightgbm = False
    
    def test_initialization(self):
        """Test initialization"""
        if not self.has_lightgbm:
            self.skipTest("LightGBM not available")
        
        self.assertFalse(self.predictor.is_fitted)
    
    def test_fit(self):
        """Test model fitting"""
        if not self.has_lightgbm:
            self.skipTest("LightGBM not available")
        
        X, y = create_training_data()
        self.predictor.fit(X, y)
        
        self.assertTrue(self.predictor.is_fitted)
    
    def test_predict(self):
        """Test predictions"""
        if not self.has_lightgbm:
            self.skipTest("LightGBM not available")
        
        X, y = create_training_data()
        self.predictor.fit(X, y)
        
        test_X = create_normal_features(samples=10)
        preds, probs = self.predictor.predict(test_X)
        
        self.assertIsNotNone(preds)
        self.assertIsNotNone(probs)

# ============================================================================
# PREDICTION ENGINE TESTS
# ============================================================================

class TestPredictionEngine(unittest.TestCase):
    """Test ensemble prediction engine"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.temp_model_dir = tempfile.mkdtemp()
        self.engine = PredictionEngine(self.temp_db.name, self.temp_model_dir)
    
    def tearDown(self):
        """Cleanup"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
        
        try:
            import shutil
            shutil.rmtree(self.temp_model_dir)
        except:
            pass
    
    def test_initialization(self):
        """Test engine initialization"""
        self.assertGreater(len(self.engine.models), 0)
    
    def test_fit_engine(self):
        """Test fitting engine"""
        X, y = create_training_data()
        feature_names = [f'feature_{i}' for i in range(28)]
        
        self.engine.fit(X, y, feature_names)
        
        self.assertEqual(self.engine.feature_names, feature_names)
    
    def test_predict_normal(self):
        """Test prediction on normal traffic"""
        X, y = create_training_data()
        self.engine.fit(X, y)
        
        test_X = create_normal_features(samples=1)
        result = self.engine.predict(test_X)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, PredictionResult)
        self.assertGreaterEqual(result.attack_probability, 0)  # type: ignore
        self.assertLessEqual(result.attack_probability, 1)  # type: ignore
    
    def test_predict_attack(self):
        """Test prediction on attack traffic"""
        X, y = create_training_data()
        self.engine.fit(X, y)
        
        # Extreme attack features
        attack_X = np.ones((1, 28)) * 1000
        result = self.engine.predict(attack_X)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_attack)  # type: ignore
        self.assertGreater(result.attack_probability, 0.7)  # type: ignore
    
    def test_prediction_result(self):
        """Test PredictionResult data model"""
        result = PredictionResult(
            timestamp=1234567890.0,
            is_attack=True,
            attack_probability=0.95,
            model_name='ensemble',
            prediction_time_ms=2.5,
            feature_importance=[('feature_0', 0.3), ('feature_1', 0.2)],
            confidence=0.98,
            top_risk_factors=['feature_0', 'feature_1']
        )
        
        self.assertTrue(result.is_attack)
        self.assertEqual(result.attack_probability, 0.95)
        self.assertEqual(len(result.top_risk_factors), 2)
        
        # Test conversion to dict
        d = result.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn('attack_probability', d)
    
    def test_batch_prediction(self):
        """Test batch prediction"""
        X, y = create_training_data()
        self.engine.fit(X, y)
        
        batch = create_normal_features(samples=10)
        
        for sample in batch:
            result = self.engine.predict(sample.reshape(1, -1))
            self.assertIsNotNone(result)
    
    def test_prediction_history(self):
        """Test prediction history"""
        X, y = create_training_data()
        self.engine.fit(X, y)
        
        # Generate predictions
        for _ in range(5):
            sample = create_normal_features(samples=1)
            self.engine.predict(sample)
        
        history = self.engine.get_prediction_history(limit=10)
        self.assertEqual(len(history), 5)
    
    def test_prediction_stats(self):
        """Test prediction statistics"""
        X, y = create_training_data()
        self.engine.fit(X, y)
        
        # Generate predictions
        for _ in range(10):
            sample = create_normal_features(samples=1)
            self.engine.predict(sample)
        
        stats = self.engine.get_prediction_stats()
        
        self.assertIn('total_predictions', stats)
        self.assertIn('attacks_predicted', stats)
        self.assertIn('attack_rate', stats)
        self.assertEqual(stats['total_predictions'], 10)

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPredictionPerformance(unittest.TestCase):
    """Test prediction performance"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.temp_model_dir = tempfile.mkdtemp()
        self.engine = PredictionEngine(self.temp_db.name, self.temp_model_dir)
    
    def tearDown(self):
        """Cleanup"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
        
        try:
            import shutil
            shutil.rmtree(self.temp_model_dir)
        except:
            pass
    
    def test_prediction_speed(self):
        """Test prediction speed"""
        import time
        
        X, y = create_training_data()
        self.engine.fit(X, y)
        
        test_X = create_normal_features(samples=100)
        
        start = time.time()
        for sample in test_X:
            self.engine.predict(sample.reshape(1, -1))
        elapsed = time.time() - start
        
        # Should be <50ms per prediction
        avg_time = elapsed / 100
        self.assertLess(avg_time, 0.05)
    
    def test_throughput(self):
        """Test prediction throughput"""
        import time
        
        X, y = create_training_data()
        self.engine.fit(X, y)
        
        test_X = create_normal_features(samples=1000)
        
        start = time.time()
        for sample in test_X:
            self.engine.predict(sample.reshape(1, -1))
        elapsed = time.time() - start
        
        throughput = 1000 / elapsed
        
        # Should handle >20 predictions/sec
        self.assertGreater(throughput, 20)

# ============================================================================
# SINGLETON TESTS
# ============================================================================

class TestSingletonAccess(unittest.TestCase):
    """Test singleton pattern"""
    
    def test_get_singleton(self):
        """Test getting singleton engine"""
        engine1 = get_prediction_engine()
        engine2 = get_prediction_engine()
        
        self.assertIs(engine1, engine2)

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
