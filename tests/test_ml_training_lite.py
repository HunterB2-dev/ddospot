"""
Lightweight tests for Training Pipeline module.

Tests cover core functionality without expensive model training.
"""

import json
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import numpy as np
from sklearn.datasets import make_classification

from ml.training import (
    TrainingPipeline,
    TrainingMetrics,
    TrainingJob,
    get_training_pipeline
)


class TestTrainingMetrics(unittest.TestCase):
    """Test TrainingMetrics dataclass."""
    
    def test_training_metrics_creation(self):
        """Test creating TrainingMetrics object."""
        metrics = TrainingMetrics(
            timestamp=datetime.now().isoformat(),
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
        self.assertEqual(metrics.train_score, 0.95)
        self.assertEqual(metrics.val_score, 0.92)
        self.assertIsNone(metrics.test_score)


class TestTrainingJob(unittest.TestCase):
    """Test TrainingJob dataclass."""
    
    def test_training_job_creation(self):
        """Test creating TrainingJob object."""
        job = TrainingJob(
            job_id="job_123",
            model_name="xgboost",
            scheduled_time=datetime.now().isoformat(),
            status="completed"
        )
        
        self.assertEqual(job.job_id, "job_123")
        self.assertEqual(job.model_name, "xgboost")
        self.assertEqual(job.status, "completed")
        self.assertIsNone(job.start_time)
        self.assertIsNone(job.end_time)


class TestTrainingPipeline(unittest.TestCase):
    """Test TrainingPipeline class - core functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = TrainingPipeline(cv_folds=2, test_size=0.2)
        
        # Generate smaller synthetic data for faster tests
        self.X, self.y = make_classification(
            n_samples=100,
            n_features=28,
            n_informative=20,
            n_redundant=5,
            n_clusters_per_class=2,
            random_state=42
        )
    
    def test_initialization(self):
        """Test pipeline initialization."""
        self.assertEqual(self.pipeline.cv_folds, 2)
        self.assertEqual(self.pipeline.test_size, 0.2)
        self.assertIsInstance(self.pipeline.training_history, list)
    
    def test_data_split(self):
        """Test data splitting into train/test sets."""
        X_train, X_test, y_train, y_test = self.pipeline._split_data(self.X, self.y)
        
        # Check split ratio
        expected_train_size = int(len(self.X) * 0.8)
        self.assertEqual(len(X_train), expected_train_size)
        self.assertEqual(len(X_test), len(self.X) - expected_train_size)
        
        # Check no overlap
        self.assertEqual(len(y_train) + len(y_test), len(self.y))
    
    def test_cross_validation(self):
        """Test cross-validation functionality."""
        from sklearn.ensemble import RandomForestClassifier
        
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        cv_mean, cv_std, fold_scores = self.pipeline.cross_validate(model, self.X, self.y)
        
        # Check results are valid
        self.assertGreater(cv_mean, 0.0)
        self.assertLess(cv_mean, 1.0)
        self.assertGreaterEqual(cv_std, 0.0)
        self.assertEqual(len(fold_scores), self.pipeline.cv_folds)
        
        # Check all fold scores are between 0 and 1
        for score in fold_scores:
            self.assertGreater(score, 0.0)
            self.assertLess(score, 1.0)
    
    def test_hyperparameter_tuning_small_grid(self):
        """Test hyperparameter tuning with small grid for fast execution."""
        from sklearn.ensemble import RandomForestClassifier
        
        model = RandomForestClassifier(random_state=42)
        param_grid = {
            'n_estimators': [5, 10],
            'max_depth': [3, 4]
        }
        
        best_params, best_score = self.pipeline.hyperparameter_tuning(
            model, self.X, self.y, param_grid
        )
        
        # Check results
        self.assertIn('n_estimators', best_params)
        self.assertIn('max_depth', best_params)
        self.assertGreater(best_score, 0.0)
        self.assertLess(best_score, 1.0)
    
    @patch('sqlite3.connect')
    def test_store_training_job(self, mock_connect):
        """Test storing training job in database."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        metrics = [TrainingMetrics(
            timestamp=datetime.now().isoformat(),
            model_name="xgboost",
            fold=0,
            train_score=0.95,
            val_score=0.92
        )]
        
        job = TrainingJob(
            job_id="test_job_123",
            model_name="xgboost",
            scheduled_time=datetime.now().isoformat(),
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            status="completed",
            metrics=metrics
        )
        
        result = self.pipeline.store_training_job(job)
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()
    
    @patch('sqlite3.connect')
    def test_get_training_history(self, mock_connect):
        """Test retrieving training history from database."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Mock database response
        mock_cursor.fetchall.return_value = [
            (
                "job_123",
                "xgboost",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                "completed",
                json.dumps([{
                    'timestamp': datetime.now().isoformat(),
                    'model_name': 'xgboost',
                    'fold': 0,
                    'train_score': 0.95,
                    'val_score': 0.92,
                    'test_score': None,
                    'training_time_ms': 100.0,
                    'best_params': None,
                    'feature_count': 28,
                    'samples_count': 1000
                }]),
                None
            )
        ]
        
        history = self.pipeline.get_training_history(model_name="xgboost")
        
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].job_id, "job_123")
        self.assertEqual(history[0].model_name, "xgboost")
    
    @patch('sqlite3.connect')
    def test_get_model_performance_stats(self, mock_connect):
        """Test getting model performance statistics."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Mock database response
        mock_cursor.fetchall.return_value = [
            ("xgboost", 5, 0.92, 0.95, 0.88),
            ("lightgbm", 5, 0.91, 0.94, 0.87)
        ]
        
        stats = self.pipeline.get_model_performance_stats()
        
        self.assertEqual(len(stats), 2)
        self.assertIn("xgboost", stats)
        self.assertIn("lightgbm", stats)
        self.assertEqual(stats["xgboost"]["training_runs"], 5)
        self.assertAlmostEqual(stats["xgboost"]["avg_cv_score"], 0.92)
    
    def test_data_dimensions_preserved(self):
        """Test that data dimensions are correct."""
        X_train, X_test, y_train, y_test = self.pipeline._split_data(self.X, self.y)
        
        self.assertEqual(X_train.shape[1], 28)
        self.assertEqual(X_test.shape[1], 28)
        self.assertEqual(len(y_train) + len(y_test), len(self.y))
    
    def test_singleton_instance(self):
        """Test singleton pattern for training pipeline."""
        instance1 = get_training_pipeline()
        instance2 = get_training_pipeline()
        
        self.assertIs(instance1, instance2)
    
    def test_cv_folds_configuration(self):
        """Test cross-validation folds configuration."""
        for cv_folds in [2, 3, 5]:
            pipeline = TrainingPipeline(cv_folds=cv_folds)
            self.assertEqual(pipeline.cv_folds, cv_folds)


if __name__ == '__main__':
    unittest.main()
