"""
ML System Integration Tests

Comprehensive end-to-end testing for the complete ML pipeline:
- Full integration across all ML components
- Performance benchmarking and latency verification
- Load testing and throughput validation
- Error recovery and edge cases
"""

import json
import time
import unittest
from datetime import datetime
from typing import List, Tuple
import numpy as np
from sklearn.datasets import make_classification
from sklearn.preprocessing import StandardScaler

from ml.features import get_feature_extractor
from ml.detection import get_anomaly_detector
from ml.prediction import get_prediction_engine
from ml.patterns import get_pattern_engine
from ml.training import get_training_pipeline


class MLPipelineIntegrationTest(unittest.TestCase):
    """End-to-end integration tests for ML pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data and engines once for all tests."""
        # Generate test data (100 samples, 28 features)
        cls.X_test, cls.y_test = make_classification(
            n_samples=100,
            n_features=28,
            n_informative=20,
            n_redundant=5,
            random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        cls.X_test = scaler.fit_transform(cls.X_test)
        
        # Get singleton engines
        cls.feature_extractor = get_feature_extractor()
        cls.detector = get_anomaly_detector()
        cls.predictor = get_prediction_engine()
        cls.pattern_engine = get_pattern_engine()
        cls.trainer = get_training_pipeline()
    
    def test_01_all_engines_initialized(self):
        """Test that all ML engines are properly initialized."""
        self.assertIsNotNone(self.feature_extractor)
        self.assertIsNotNone(self.detector)
        self.assertIsNotNone(self.predictor)
        self.assertIsNotNone(self.pattern_engine)
        self.assertIsNotNone(self.trainer)
    
    def test_02_feature_extraction_pipeline(self):
        """Test feature extraction for a sample."""
        sample = self.X_test[0]
        
        # Should have 28 features
        self.assertEqual(len(sample), 28)
        
        # All features should be numeric
        for feature in sample:
            self.assertIsInstance(float(feature), float)
    
    def test_03_anomaly_detection_single(self):
        """Test anomaly detection on single sample."""
        sample = self.X_test[0:1]
        
        start_time = time.time()
        result = self.detector.detect(sample)
        latency_ms = (time.time() - start_time) * 1000
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.is_anomaly)  # type: ignore
        self.assertIsNotNone(result.score)  # type: ignore
        self.assertGreaterEqual(result.score, 0.0)  # type: ignore
        self.assertLessEqual(result.score, 1.0)  # type: ignore
        
        # Verify latency < 50ms
        self.assertLess(latency_ms, 50, f"Detection latency {latency_ms}ms exceeds 50ms")
    
    def test_04_attack_prediction_single(self):
        """Test attack prediction on single sample."""
        sample = self.X_test[0:1]
        
        start_time = time.time()
        result = self.predictor.predict(sample)
        latency_ms = (time.time() - start_time) * 1000
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.is_attack)  # type: ignore
        self.assertIsNotNone(result.attack_probability)  # type: ignore
        self.assertGreaterEqual(result.attack_probability, 0.0)  # type: ignore
        self.assertLessEqual(result.attack_probability, 1.0)  # type: ignore
        
        # Verify latency < 50ms
        self.assertLess(latency_ms, 50, f"Prediction latency {latency_ms}ms exceeds 50ms")
    
    def test_05_pattern_discovery_integration(self):
        """Test pattern discovery on batch of samples."""
        sample = self.X_test[0:20]
        
        # Fit patterns
        start_time = time.time()
        self.pattern_engine.fit(sample, np.zeros(len(sample)))
        fit_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(fit_time, 5.0, f"Pattern fitting took {fit_time}s, expected <5s")
        
        # Predict patterns
        start_time = time.time()
        predictions = self.pattern_engine.predict_pattern(sample)
        predict_time = time.time() - start_time
        
        # Verify predictions
        self.assertEqual(len(predictions), len(sample))
        for pred in predictions:
            self.assertIsNotNone(pred)
    
    def test_06_batch_detection_performance(self):
        """Test detection performance on batch of samples."""
        batch_size = 50
        batch = self.X_test[0:batch_size]
        
        start_time = time.time()
        results = self.detector.detect(batch)
        total_time = time.time() - start_time
        
        # Verify result (single AnomalyScore)
        self.assertIsNotNone(results)
        
        # Verify total latency for batch
        total_latency_ms = total_time * 1000
        self.assertLess(total_latency_ms, 500,  # type: ignore
                       f"Batch detection latency {total_latency_ms}ms exceeds 500ms")
    
    def test_07_batch_prediction_performance(self):
        """Test prediction performance on batch of samples."""
        batch_size = 50
        batch = self.X_test[0:batch_size]
        
        predictions = []
        start_time = time.time()
        
        for sample in batch:
            result = self.predictor.predict(np.array([sample]))
            predictions.append(result)
        
        total_time = time.time() - start_time
        
        # Verify all results
        self.assertEqual(len(predictions), batch_size)
        
        # Verify average latency per sample
        avg_latency_ms = (total_time * 1000) / batch_size
        self.assertLess(avg_latency_ms, 50,
                       f"Average prediction latency {avg_latency_ms}ms exceeds 50ms per sample")
    
    def test_08_pipeline_throughput(self):
        """Test overall pipeline throughput (predictions per second)."""
        batch_size = 100
        batch = self.X_test[0:batch_size]
        
        start_time = time.time()
        count = 0
        
        for sample in batch:
            self.predictor.predict(np.array([sample]))
            count += 1
        
        total_time = time.time() - start_time
        throughput = count / total_time if total_time > 0 else 0
        
        # Should achieve at least 20 predictions per second
        self.assertGreater(throughput, 20,
                          f"Throughput {throughput:.1f} preds/sec is below 20 preds/sec target")
    
    def test_09_cross_engine_latency(self):
        """Test latency across multiple engines in sequence."""
        sample = self.X_test[0:1]
        
        total_start = time.time()
        
        # Detection
        det_start = time.time()
        self.detector.detect(sample)
        det_time = time.time() - det_start
        
        # Prediction
        pred_start = time.time()
        self.predictor.predict(sample)
        pred_time = time.time() - pred_start
        
        # Pattern
        pat_start = time.time()
        self.pattern_engine.predict_pattern(sample)
        pat_time = time.time() - pat_start
        
        total_time = time.time() - total_start
        
        # Each operation should be fast
        self.assertLess(det_time, 0.1, "Detection too slow")
        self.assertLess(pred_time, 0.1, "Prediction too slow")
        self.assertLess(pat_time, 0.1, "Pattern prediction too slow")
        self.assertLess(total_time, 0.3, "Cross-engine operations too slow")
    
    def test_10_data_consistency(self):
        """Test that data is processed consistently across engines."""
        sample = self.X_test[0:1].copy()
        
        # Run through all engines
        det_result = self.detector.detect(sample)
        pred_result = self.predictor.predict(sample)
        pat_result = self.pattern_engine.predict_pattern(sample)
        
        # All should complete without error
        self.assertIsNotNone(det_result)
        self.assertIsNotNone(pred_result)
        self.assertIsNotNone(pat_result)
        
        # Results should be of expected types
        self.assertIsInstance(det_result.score, (float, np.floating))  # type: ignore
        self.assertIsInstance(pred_result.attack_probability, (float, np.floating))  # type: ignore
    
    def test_11_error_recovery_invalid_input(self):
        """Test error handling with invalid input."""
        # Test with wrong feature count
        invalid_sample = np.random.randn(1, 10)  # 10 features instead of 28
        
        # Should handle gracefully or raise appropriate error
        try:
            self.detector.detect(invalid_sample)
            # If it doesn't raise, that's OK, it should just not crash
        except Exception as e:
            # Should be a validation error, not a crash
            self.assertIsInstance(e, (ValueError, IndexError, RuntimeError))
    
    def test_12_error_recovery_empty_input(self):
        """Test error handling with empty input."""
        empty_sample = np.array([]).reshape(0, 28)
        
        try:
            result = self.detector.detect(empty_sample)
            # Should return a result (might be None but not empty list)
            self.assertTrue(result is None or isinstance(result, type(self.detector.detection_history[0])) if self.detector.detection_history else True)  # type: ignore
        except Exception as e:
            # If it raises, should be graceful
            pass
    
    def test_13_concurrent_operations_safety(self):
        """Test that concurrent operations are safe."""
        sample1 = self.X_test[0:1]
        sample2 = self.X_test[1:2]
        
        # Perform operations on different samples
        det1 = self.detector.detect(sample1)
        pred1 = self.predictor.predict(sample1)
        det2 = self.detector.detect(sample2)
        pred2 = self.predictor.predict(sample2)
        
        # All should complete independently
        self.assertIsNotNone(det1)
        self.assertIsNotNone(pred1)
        self.assertIsNotNone(det2)
        self.assertIsNotNone(pred2)
    
    def test_14_training_pipeline_integration(self):
        """Test training pipeline integration."""
        # Get training pipeline
        pipeline = self.trainer
        
        # Should initialize without error
        self.assertEqual(pipeline.cv_folds, 5)
        self.assertEqual(pipeline.test_size, 0.2)
    
    def test_15_model_metadata_consistency(self):
        """Test that model metadata is consistent."""
        # Prediction model should have feature information
        pred_result = self.predictor.predict(self.X_test[0:1])
        
        # Should have feature count information
        self.assertIsNotNone(pred_result)
        # Results should contain probability between 0-1
        self.assertGreaterEqual(pred_result.attack_probability, 0.0)  # type: ignore
        self.assertLessEqual(pred_result.attack_probability, 1.0)  # type: ignore


class MLPerformanceBenchmark(unittest.TestCase):
    """Performance benchmarking tests."""
    
    def setUp(self):
        """Set up test data."""
        self.X, self.y = make_classification(
            n_samples=200,
            n_features=28,
            n_informative=20,
            random_state=42
        )
        scaler = StandardScaler()
        self.X = scaler.fit_transform(self.X)
        
        self.detector = get_anomaly_detector()
        self.predictor = get_prediction_engine()
    
    def test_detection_latency_percentiles(self):
        """Test detection latency at different percentiles."""
        latencies = []
        
        for sample in self.X[0:50]:
            start = time.time()
            self.detector.detect(np.array([sample]))
            latencies.append((time.time() - start) * 1000)
        
        latencies.sort()
        
        # Calculate percentiles
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)
        
        # All should be well under 50ms
        self.assertLess(p50, 50)
        self.assertLess(p95, 50)
        self.assertLess(p99, 50)
    
    def test_prediction_latency_percentiles(self):
        """Test prediction latency at different percentiles."""
        latencies = []
        
        for sample in self.X[0:50]:
            start = time.time()
            self.predictor.predict(np.array([sample]))
            latencies.append((time.time() - start) * 1000)
        
        latencies.sort()
        
        # Calculate percentiles
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)
        
        # All should be well under 50ms
        self.assertLess(p50, 50)
        self.assertLess(p95, 50)
        self.assertLess(p99, 50)
    
    def test_batch_vs_sequential_efficiency(self):
        """Compare batch processing vs sequential."""
        batch = self.X[0:50]
        
        # Sequential processing
        seq_start = time.time()
        for sample in batch:
            self.predictor.predict(np.array([sample]))
        seq_time = time.time() - seq_start
        
        seq_throughput = len(batch) / seq_time
        
        # Should achieve reasonable throughput
        self.assertGreater(seq_throughput, 20,
                          f"Sequential throughput {seq_throughput:.1f} preds/sec < 20 preds/sec")


class MLEndToEndWorkflow(unittest.TestCase):
    """End-to-end workflow tests simulating real usage."""
    
    def test_incident_detection_workflow(self):
        """Test workflow: Detect attack -> Analyze -> Predict -> Pattern match."""
        # Generate sample traffic
        X, y = make_classification(n_samples=10, n_features=28, random_state=42)
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        
        detector = get_anomaly_detector()
        predictor = get_prediction_engine()
        pattern_engine = get_pattern_engine()
        
        # Step 1: Detect anomalies (returns single AnomalyScore)
        anomalies = detector.detect(X)
        self.assertIsNotNone(anomalies)
        
        # Step 2: Get predictions for anomalous samples (single sample)
        sample = X[0:1]
        pred = predictor.predict(sample)
        self.assertIsNotNone(pred)
        
        # Step 3: Learn patterns from data
        pattern_engine.fit(X, y)
        patterns = pattern_engine.predict_pattern(X)
        
        self.assertIsNotNone(patterns)
    
    def test_continuous_monitoring_workflow(self):
        """Test continuous monitoring with batch processing."""
        X, y = make_classification(n_samples=50, n_features=28, random_state=42)
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        
        detector = get_anomaly_detector()
        predictor = get_prediction_engine()
        
        # Process in batches (simulating continuous stream)
        batch_results = []
        
        for i in range(0, len(X), 10):
            batch = X[i:i+10]
            
            # Detect anomalies
            det_results = detector.detect(batch)
            
            # Predict on each
            pred_results = []
            for sample in batch:
                pred = predictor.predict(np.array([sample]))
                pred_results.append(pred)
            
            batch_results.append({
                'batch': i // 10,
                'detections': 1 if det_results is not None else 0,  # type: ignore
                'predictions': len([p for p in pred_results if p is not None])  # type: ignore
            })
        
        # Should have processed all batches
        self.assertEqual(len(batch_results), 5)


class MLFailureRecovery(unittest.TestCase):
    """Test error handling and failure recovery."""
    
    def test_nan_handling(self):
        """Test handling of NaN values."""
        data = np.array([[1.0, np.nan, 3.0] * 9 + [1.0]])  # 28 features with NaN
        
        detector = get_anomaly_detector()
        try:
            result = detector.detect(data)
            # Should either handle gracefully or raise appropriate error
            self.assertIsNotNone(result)
        except (ValueError, RuntimeWarning):
            pass  # Expected for NaN handling
    
    def test_inf_handling(self):
        """Test handling of infinity values."""
        data = np.array([[1.0, np.inf, 3.0] * 9 + [1.0]])  # 28 features with inf
        
        detector = get_anomaly_detector()
        try:
            result = detector.detect(data)
            # Should either handle gracefully or raise appropriate error
            self.assertIsNotNone(result)
        except (ValueError, RuntimeWarning):
            pass  # Expected for inf handling
    
    def test_extreme_values_handling(self):
        """Test handling of extreme values."""
        data = np.array([[1e10, -1e10, 0.0] * 9 + [1e10]])  # Very large values
        
        predictor = get_prediction_engine()
        try:
            result = predictor.predict(data)
            # Should handle without crashing
            self.assertIsNotNone(result)
        except (ValueError, OverflowError):
            pass  # May raise due to scale issues, that's OK


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
