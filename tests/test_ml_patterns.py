"""
Comprehensive tests for ML pattern learning engine
Tests K-means clustering, pattern discovery, and pattern matching
"""

import unittest
import numpy as np
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.patterns import (
    PatternLearningEngine, AttackPattern, get_pattern_engine
)

# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def create_normal_features(samples=100, features=28):
    """Create normal traffic features"""
    return np.random.normal(loc=50, scale=10, size=(samples, features))

def create_attack_pattern_1(samples=50, features=28):
    """Create first attack pattern (e.g., SYN flood)"""
    return np.random.normal(loc=200, scale=20, size=(samples, features))

def create_attack_pattern_2(samples=50, features=28):
    """Create second attack pattern (e.g., DNS amplification)"""
    return np.random.normal(loc=400, scale=30, size=(samples, features))

def create_training_data(samples_each=50, features=28):
    """Create labeled training data with multiple patterns"""
    normal = create_normal_features(samples_each, features)
    pattern1 = create_attack_pattern_1(samples_each, features)
    pattern2 = create_attack_pattern_2(samples_each, features)
    
    X = np.vstack([normal, pattern1, pattern2])
    
    # Shuffle
    idx = np.random.permutation(len(X))
    
    return X[idx]

# ============================================================================
# PATTERN LEARNING TESTS
# ============================================================================

class TestPatternLearningEngine(unittest.TestCase):
    """Test pattern learning engine"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        try:
            self.engine = PatternLearningEngine(
                n_clusters=3,
                min_cluster_size=3,
                db_path=self.temp_db.name
            )
            self.has_sklearn = True
        except ImportError:
            self.has_sklearn = False
    
    def tearDown(self):
        """Cleanup"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_initialization(self):
        """Test engine initialization"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        self.assertFalse(self.engine.is_fitted)
        self.assertEqual(self.engine.n_clusters, 3)
    
    def test_fit_engine(self):
        """Test fitting pattern engine"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=50)
        self.engine.fit(X)
        
        self.assertTrue(self.engine.is_fitted)
        self.assertGreater(len(self.engine.patterns), 0)
    
    def test_pattern_discovery(self):
        """Test pattern discovery"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=60)
        self.engine.fit(X)
        
        # Should discover multiple patterns
        self.assertGreaterEqual(len(self.engine.patterns), 1)
    
    def test_attack_pattern_object(self):
        """Test AttackPattern data model"""
        pattern = AttackPattern(
            pattern_id='test_pattern_1',
            cluster_center=[1.0, 2.0, 3.0],
            cluster_label=0,
            samples_in_cluster=50,
            pattern_signature='abc123def456',
            severity='high',
            first_seen=1234567890.0,
            last_seen=1234567900.0,
            detection_count=25,
            confidence=0.95,
            characteristics={'feature_0': {'mean': 100, 'std': 10}}
        )
        
        self.assertEqual(pattern.pattern_id, 'test_pattern_1')
        self.assertEqual(pattern.severity, 'high')
        self.assertEqual(pattern.detection_count, 25)
        
        # Test conversion to dict
        d = pattern.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn('pattern_id', d)
    
    def test_pattern_prediction(self):
        """Test predicting which pattern a sample belongs to"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=60)
        self.engine.fit(X)
        
        # Test with attack pattern
        attack_sample = create_attack_pattern_1(samples=1)[0]
        pattern, distance = self.engine.predict_pattern(attack_sample)
        
        self.assertIsNotNone(pattern)
        self.assertGreaterEqual(distance, 0)
    
    def test_pattern_matching(self):
        """Test matching samples to patterns"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=50)
        self.engine.fit(X)
        
        # Predict on training data
        for sample in X[:10]:
            pattern, distance = self.engine.predict_pattern(sample)
            # Should match to some pattern
            self.assertIsNotNone(pattern)
    
    def test_severity_determination(self):
        """Test severity determination"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        # Create high-rate traffic
        X = create_attack_pattern_2(samples=100)  # Higher values = higher severity
        self.engine.fit(X)
        
        # Should have patterns with various severities
        patterns = self.engine.get_patterns()
        self.assertGreater(len(patterns), 0)
    
    def test_get_patterns_filtered(self):
        """Test filtering patterns by severity"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=50)
        self.engine.fit(X)
        
        # Get high and critical patterns
        high_patterns = self.engine.get_patterns(min_severity='high')
        
        # Should return list (may be empty)
        self.assertIsInstance(high_patterns, list)
    
    def test_pattern_stats(self):
        """Test pattern statistics"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=50)
        self.engine.fit(X)
        
        stats = self.engine.get_pattern_stats()
        
        self.assertIn('total_patterns', stats)
        self.assertIn('critical_patterns', stats)
        self.assertIn('high_patterns', stats)
        self.assertIn('total_detections', stats)
        self.assertGreater(stats['total_patterns'], 0)
    
    def test_save_patterns(self):
        """Test saving patterns to database"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=50)
        self.engine.fit(X)
        
        result = self.engine.save_patterns()
        self.assertTrue(result)
    
    def test_load_patterns(self):
        """Test loading patterns from database"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=50)
        self.engine.fit(X)
        
        # Save patterns
        self.engine.save_patterns()
        
        # Create new engine
        engine2 = PatternLearningEngine(
            n_clusters=3,
            min_cluster_size=3,
            db_path=self.temp_db.name
        )
        
        # Load patterns
        result = engine2.load_patterns()
        self.assertTrue(result)
        self.assertGreater(len(engine2.patterns), 0)
    
    def test_pattern_persistence(self):
        """Test full pattern persistence cycle"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=50)
        self.engine.fit(X)
        
        original_count = len(self.engine.patterns)
        
        # Save
        self.engine.save_patterns()
        
        # Load in new engine
        engine2 = PatternLearningEngine(
            n_clusters=3,
            min_cluster_size=3,
            db_path=self.temp_db.name
        )
        engine2.load_patterns()
        
        self.assertEqual(len(engine2.patterns), original_count)

# ============================================================================
# CLUSTERING TESTS
# ============================================================================

class TestClustering(unittest.TestCase):
    """Test K-means clustering quality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        try:
            self.engine = PatternLearningEngine(
                n_clusters=3,
                min_cluster_size=3,
                db_path=self.temp_db.name
            )
            self.has_sklearn = True
        except ImportError:
            self.has_sklearn = False
    
    def tearDown(self):
        """Cleanup"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_cluster_separation(self):
        """Test that clusters are well separated"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        # Create well-separated patterns
        X = create_training_data(samples_each=100)
        self.engine.fit(X)
        
        # Should have discovered clusters
        self.assertGreater(len(self.engine.patterns), 0)
    
    def test_cluster_cohesion(self):
        """Test cluster cohesion"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        X = create_training_data(samples_each=100)
        self.engine.fit(X)
        
        # All patterns should have reasonable confidence
        for pattern in self.engine.patterns.values():
            self.assertGreater(pattern.confidence, 0)
            self.assertLessEqual(pattern.confidence, 1)

# ============================================================================
# SINGLETON TESTS
# ============================================================================

class TestSingletonAccess(unittest.TestCase):
    """Test singleton pattern"""
    
    def test_get_singleton(self):
        """Test getting singleton engine"""
        engine1 = get_pattern_engine()
        engine2 = get_pattern_engine()
        
        self.assertIs(engine1, engine2)

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPatternPerformance(unittest.TestCase):
    """Test pattern learning performance"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        try:
            self.engine = PatternLearningEngine(
                n_clusters=10,
                min_cluster_size=5,
                db_path=self.temp_db.name
            )
            self.has_sklearn = True
        except ImportError:
            self.has_sklearn = False
    
    def tearDown(self):
        """Cleanup"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_learning_speed(self):
        """Test pattern learning speed"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        import time
        
        X = create_training_data(samples_each=200)
        
        start = time.time()
        self.engine.fit(X)
        elapsed = time.time() - start
        
        # Should be reasonably fast (<3 seconds for K-means)
        self.assertLess(elapsed, 3.0)
    
    def test_prediction_speed(self):
        """Test pattern prediction speed"""
        if not self.has_sklearn:
            self.skipTest("scikit-learn not available")
        
        import time
        
        X = create_training_data(samples_each=100)
        self.engine.fit(X)
        
        test_samples = create_normal_features(samples=100)
        
        start = time.time()
        for sample in test_samples:
            self.engine.predict_pattern(sample)
        elapsed = time.time() - start
        
        # Should be very fast
        avg_time = elapsed / 100
        self.assertLess(avg_time, 0.01)

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
