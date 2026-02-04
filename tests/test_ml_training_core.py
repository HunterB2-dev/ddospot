"""
Quick validation tests for Training Pipeline module.

Focused on verifying core functionality without expensive computations.
"""

import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from ml.training import (
    TrainingPipeline,
    TrainingMetrics,
    TrainingJob,
    get_training_pipeline
)


class TestTrainingPipelineBasic(unittest.TestCase):
    """Test TrainingPipeline basic functionality."""
    
    def test_metrics_dataclass(self):
        """Test TrainingMetrics creation."""
        metrics = TrainingMetrics(
            timestamp="2026-02-03T12:00:00",
            model_name="xgboost",
            fold=0,
            train_score=0.95,
            val_score=0.92,
            training_time_ms=150.5,
            feature_count=28,
            samples_count=1000
        )
        self.assertEqual(metrics.model_name, "xgboost")
        self.assertEqual(metrics.fold, 0)
    
    def test_job_dataclass(self):
        """Test TrainingJob creation."""
        job = TrainingJob(
            job_id="job_123",
            model_name="xgboost",
            scheduled_time="2026-02-03T12:00:00",
            status="completed"
        )
        self.assertEqual(job.job_id, "job_123")
    
    def test_pipeline_init(self):
        """Test pipeline initialization."""
        pipeline = TrainingPipeline(cv_folds=3, test_size=0.2)
        self.assertEqual(pipeline.cv_folds, 3)
        self.assertEqual(pipeline.test_size, 0.2)
    
    def test_singleton_pattern(self):
        """Test singleton returns same instance."""
        p1 = get_training_pipeline()
        p2 = get_training_pipeline()
        self.assertIs(p1, p2)
    
    def test_data_split(self):
        """Test data splitting logic."""
        pipeline = TrainingPipeline(cv_folds=2, test_size=0.25)
        
        import numpy as np
        X = np.random.randn(100, 28)
        y = np.random.randint(0, 2, 100)
        
        X_train, X_test, y_train, y_test = pipeline._split_data(X, y)
        
        # Test 75/25 split
        self.assertEqual(len(X_train), 75)
        self.assertEqual(len(X_test), 25)
        self.assertEqual(X_train.shape[1], 28)
    
    @patch('sqlite3.connect')
    def test_store_job_mocked(self, mock_connect):
        """Test storing training job with mocked DB."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        pipeline = TrainingPipeline()
        job = TrainingJob(
            job_id="test_123",
            model_name="xgboost",
            scheduled_time="2026-02-03T12:00:00",
            status="completed"
        )
        
        result = pipeline.store_training_job(job)
        self.assertTrue(result)
        self.assertTrue(mock_cursor.execute.called)
    
    @patch('sqlite3.connect')
    def test_get_history_mocked(self, mock_connect):
        """Test retrieving history with mocked DB."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Mock empty response
        mock_cursor.fetchall.return_value = []
        
        pipeline = TrainingPipeline()
        history = pipeline.get_training_history(model_name="xgboost", limit=5)
        
        self.assertEqual(len(history), 0)
        self.assertTrue(mock_cursor.execute.called)
    
    @patch('sqlite3.connect')
    def test_get_stats_mocked(self, mock_connect):
        """Test getting stats with mocked DB."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Mock response with stats
        mock_cursor.fetchall.return_value = [
            ("xgboost", 3, 0.92, 0.95, 0.89)
        ]
        
        pipeline = TrainingPipeline()
        stats = pipeline.get_model_performance_stats()
        
        self.assertIn("xgboost", stats)
        self.assertEqual(stats["xgboost"]["training_runs"], 3)


if __name__ == '__main__':
    # Run with minimal verbosity for speed
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTrainingPipelineBasic)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70)
