"""
Comprehensive tests for ML anomaly detection engine
Tests Isolation Forest, LOF, statistical methods, and ensemble detection
"""

import unittest
import numpy as np
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.detection import (
    AnomalyDetectionEngine, IsolationForestDetector,
    LocalOutlierFactorDetector, StatisticalDetector,
    AnomalyScore, get_anomaly_detector
)

# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def create_normal_data(samples=100, features=28):
    """Create normal (non-anomalous) data"""
    return np.random.normal(loc=50, scale=10, size=(samples, features))

def create_anomalous_data(samples=10, features=28):
    """Create anomalous data (extreme values)"""
    return np.random.normal(loc=500, scale=100, size=(samples, features))

def create_mixed_data(normal_samples=90, anomaly_samples=10, features=28):
    """Create mixed normal and anomalous data"""
    normal = np.random.normal(loc=50, scale=10, size=(normal_samples, features))
    anomaly = np.random.normal(loc=500, scale=100, size=(anomaly_samples, features))
    return np.vstack([normal, anomaly])

# ============================================================================
# ISOLATION FOREST TESTS
# ============================================================================

class TestIsolationForest(unittest.TestCase):
    """Test Isolation Forest detector"""
    
    def setUp(self):
        """Setup test fixtures"""
        try:
            self.detector = IsolationForestDetector(contamination=0.1)
            self.has_sklearn = True
        except ImportError:
            self.has_sklearn = False
    
    def test_initialization(self):
        """Test detector initialization"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        self.assertFalse(self.detector.is_fitted)
        self.assertEqual(self.detector.contamination, 0.1)
    
    def test_fit(self):
        """Test fitting detector"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        data = create_mixed_data(normal_samples=90, anomaly_samples=10)
        self.detector.fit(data)
        
        self.assertTrue(self.detector.is_fitted)
    
    def test_predict(self):
        """Test anomaly prediction"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        data = create_mixed_data(normal_samples=90, anomaly_samples=10)
        self.detector.fit(data)
        
        predictions, scores = self.detector.predict(data)
        
        self.assertIsNotNone(predictions)
        self.assertIsNotNone(scores)
        self.assertEqual(len(predictions), 100)  # type: ignore
        self.assertEqual(len(scores), 100)  # type: ignore
    
    def test_anomaly_detection(self):
        """Test that anomalies are detected"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        # Train on normal data
        normal_data = create_normal_data(samples=100)
        self.detector.fit(normal_data)
        
        # Test on anomalies
        anomaly_data = create_anomalous_data(samples=10)
        predictions, scores = self.detector.predict(anomaly_data)
        
        # Most should be detected as anomalies (-1)
        anomaly_count = np.sum(predictions == -1)
        self.assertGreater(anomaly_count, 5)

# ============================================================================
# LOCAL OUTLIER FACTOR TESTS
# ============================================================================

class TestLocalOutlierFactor(unittest.TestCase):
    """Test LOF detector"""
    
    def setUp(self):
        """Setup test fixtures"""
        try:
            self.detector = LocalOutlierFactorDetector(n_neighbors=20, contamination=0.1)
            self.has_sklearn = True
        except ImportError:
            self.has_sklearn = False
    
    def test_initialization(self):
        """Test detector initialization"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        self.assertFalse(self.detector.is_fitted)
    
    def test_fit_insufficient_data(self):
        """Test fitting with insufficient data"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        data = np.random.randn(5, 28)  # Less than n_neighbors
        self.detector.fit(data)
        
        self.assertFalse(self.detector.is_fitted)
    
    def test_fit_sufficient_data(self):
        """Test fitting with sufficient data"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        data = create_mixed_data()
        self.detector.fit(data)
        
        self.assertTrue(self.detector.is_fitted)

# ============================================================================
# STATISTICAL DETECTOR TESTS
# ============================================================================

class TestStatisticalDetector(unittest.TestCase):
    """Test statistical Z-score detector"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.detector = StatisticalDetector(z_threshold=3.0)
    
    def test_initialization(self):
        """Test detector initialization"""
        self.assertFalse(self.detector.is_fitted)
        self.assertEqual(self.detector.z_threshold, 3.0)
    
    def test_fit(self):
        """Test fitting detector"""
        data = create_normal_data()
        self.detector.fit(data)
        
        self.assertTrue(self.detector.is_fitted)
        self.assertIsNotNone(self.detector.means)
        self.assertIsNotNone(self.detector.stds)
    
    def test_predict_unfitted(self):
        """Test prediction on unfitted detector"""
        data = create_normal_data()
        preds, scores = self.detector.predict(data)
        
        self.assertIsNone(preds)
        self.assertIsNone(scores)
    
    def test_detect_normal(self):
        """Test detection on normal data"""
        train_data = create_normal_data(samples=100)
        self.detector.fit(train_data)
        
        test_data = create_normal_data(samples=20)
        predictions, scores = self.detector.predict(test_data)
        
        # Most should be normal (1)
        normal_count = np.sum(predictions == 1)
        self.assertGreater(normal_count, 15)
    
    def test_detect_anomalies(self):
        """Test detection on anomalous data"""
        train_data = create_normal_data(samples=100)
        self.detector.fit(train_data)
        
        anomaly_data = create_anomalous_data(samples=20)
        predictions, scores = self.detector.predict(anomaly_data)
        
        # Most should be anomalies (-1)
        anomaly_count = np.sum(predictions == -1)
        self.assertGreater(anomaly_count, 15)

# ============================================================================
# ENSEMBLE DETECTOR TESTS
# ============================================================================

class TestAnomalyDetectionEngine(unittest.TestCase):
    """Test ensemble anomaly detection engine"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.engine = AnomalyDetectionEngine(self.temp_db.name)
    
    def tearDown(self):
        """Cleanup"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_initialization(self):
        """Test engine initialization"""
        self.assertFalse(self.engine.is_fitted)
        self.assertGreater(len(self.engine.detectors), 0)
    
    def test_fit_engine(self):
        """Test fitting ensemble engine"""
        data = create_mixed_data()
        feature_names = [f'feature_{i}' for i in range(28)]
        
        self.engine.fit(data, feature_names)
        
        self.assertTrue(self.engine.is_fitted)
        self.assertEqual(self.engine.feature_names, feature_names)
    
    def test_detect_normal(self):
        """Test detection on normal data"""
        train_data = create_normal_data(samples=100)
        self.engine.fit(train_data)
        
        test_sample = create_normal_data(samples=1)
        result = self.engine.detect(test_sample)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, AnomalyScore)
        # Most likely normal, but ensemble might flag some
        self.assertIsNotNone(result.timestamp)  # type: ignore
        self.assertGreaterEqual(result.score, 0)  # type: ignore
        self.assertLessEqual(result.score, 1)  # type: ignore
    
    def test_detect_anomaly(self):
        """Test detection on anomalous data"""
        train_data = create_normal_data(samples=100)
        self.engine.fit(train_data)
        
        # Create extreme anomaly
        anomaly_sample = np.ones((1, 28)) * 1000
        result = self.engine.detect(anomaly_sample)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_anomaly)  # type: ignore
        self.assertGreater(result.score, 0.2)  # type: ignore
    
    def test_batch_detection(self):
        """Test detection on batch"""
        train_data = create_normal_data(samples=100)
        self.engine.fit(train_data)
        
        batch_data = create_normal_data(samples=10)
        
        for sample in batch_data:
            result = self.engine.detect(sample.reshape(1, -1))
            self.assertIsNotNone(result)
    
    def test_anomaly_score(self):
        """Test AnomalyScore data model"""
        score = AnomalyScore(
            timestamp=1234567890.0,
            is_anomaly=True,
            score=0.85,
            detection_method='isolation_forest',
            feature_count=28,
            top_anomalous_features=[('feature_0', 0.9), ('feature_1', 0.8)],
            confidence=0.95
        )
        
        self.assertTrue(score.is_anomaly)
        self.assertEqual(score.score, 0.85)
        self.assertEqual(len(score.top_anomalous_features), 2)
        
        # Test conversion to dict
        d = score.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn('timestamp', d)
        self.assertIn('is_anomaly', d)
    
    def test_detection_history(self):
        """Test detection history storage"""
        train_data = create_normal_data(samples=100)
        self.engine.fit(train_data)
        
        # Generate detections
        for _ in range(5):
            sample = create_normal_data(samples=1)
            self.engine.detect(sample)
        
        history = self.engine.get_detection_history(limit=10)
        self.assertEqual(len(history), 5)
    
    def test_detection_stats(self):
        """Test detection statistics"""
        train_data = create_normal_data(samples=100)
        self.engine.fit(train_data)
        
        # Generate detections
        for _ in range(10):
            sample = create_normal_data(samples=1)
            self.engine.detect(sample)
        
        stats = self.engine.get_detection_stats()
        
        self.assertIn('total_detections', stats)
        self.assertIn('anomalies_detected', stats)
        self.assertIn('anomaly_rate', stats)
        self.assertEqual(stats['total_detections'], 10)

# ============================================================================
# SINGLETON TESTS
# ============================================================================

class TestSingletonAccess(unittest.TestCase):
    """Test singleton pattern"""
    
    def test_get_singleton(self):
        """Test getting singleton detector"""
        detector1 = get_anomaly_detector()
        detector2 = get_anomaly_detector()
        
        self.assertIs(detector1, detector2)

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestDetectionPerformance(unittest.TestCase):
    """Test detection performance"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.engine = AnomalyDetectionEngine(self.temp_db.name)
    
    def tearDown(self):
        """Cleanup"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_detection_speed(self):
        """Test detection speed"""
        import time
        
        train_data = create_mixed_data()
        self.engine.fit(train_data)
        
        test_data = create_normal_data(samples=100)
        
        start = time.time()
        for sample in test_data:
            self.engine.detect(sample.reshape(1, -1))
        elapsed = time.time() - start
        
        # Should be reasonably fast (<50ms per detection on average)
        avg_time = elapsed / 100
        self.assertLess(avg_time, 0.05)

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
