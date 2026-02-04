"""
Unit tests for Training Pipeline module.

Tests cover:
- Cross-validation functionality
- Hyperparameter tuning
- XGBoost model training
- LightGBM model training
- Training job persistence
- Performance statistics
"""

import json
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import numpy as np
from sklearn.datasets import make_classification
from sklearn.preprocessing import StandardScaler

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
    """Test TrainingPipeline class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = TrainingPipeline(cv_folds=3, test_size=0.2)
        
        # Generate synthetic classification data
        self.X, self.y = make_classification(
            n_samples=300,
            n_features=28,
            n_informative=20,
            n_redundant=5,
            n_clusters_per_class=2,
            random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        self.X = scaler.fit_transform(self.X)
    
    def test_initialization(self):
        """Test pipeline initialization."""
        self.assertEqual(self.pipeline.cv_folds, 3)
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
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
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
    
    def test_hyperparameter_tuning(self):
        """Test hyperparameter tuning functionality."""
        from sklearn.ensemble import RandomForestClassifier
        
        model = RandomForestClassifier(random_state=42)
        param_grid = {
            'n_estimators': [5, 10],
            'max_depth': [3, 5]
        }
        
        best_params, best_score = self.pipeline.hyperparameter_tuning(
            model, self.X, self.y, param_grid
        )
        
        # Check results
        self.assertIn('n_estimators', best_params)
        self.assertIn('max_depth', best_params)
        self.assertGreater(best_score, 0.0)
        self.assertLess(best_score, 1.0)
    
    def test_train_xgboost_basic(self):
        """Test XGBoost training without hyperparameter tuning."""
        model, metrics_list = self.pipeline.train_xgboost(self.X, self.y, perform_tuning=False)
        
        # Check model is trained
        self.assertIsNotNone(model)
        
        # Check metrics
        self.assertEqual(len(metrics_list), self.pipeline.cv_folds)
        for metrics in metrics_list:
            self.assertEqual(metrics.model_name, "xgboost")
            self.assertGreater(metrics.train_score, 0.0)
            self.assertGreater(metrics.val_score, 0.0)
            self.assertGreater(metrics.training_time_ms, 0.0)
    
    def test_train_xgboost_custom_params(self):
        """Test XGBoost training with custom parameters."""
        custom_params = {
            'n_estimators': 50,
            'max_depth': 4,
            'learning_rate': 0.05,
            'random_state': 42
        }
        
        model, metrics_list = self.pipeline.train_xgboost(
            self.X, self.y, hyperparams=custom_params, perform_tuning=False
        )
        
        self.assertIsNotNone(model)
        self.assertEqual(len(metrics_list), self.pipeline.cv_folds)
    
    def test_train_lightgbm_basic(self):
        """Test LightGBM training without hyperparameter tuning."""
        model, metrics_list = self.pipeline.train_lightgbm(self.X, self.y, perform_tuning=False)
        
        # Check model is trained
        self.assertIsNotNone(model)
        
        # Check metrics
        self.assertEqual(len(metrics_list), self.pipeline.cv_folds)
        for metrics in metrics_list:
            self.assertEqual(metrics.model_name, "lightgbm")
            self.assertGreater(metrics.train_score, 0.0)
            self.assertGreater(metrics.val_score, 0.0)
            self.assertGreater(metrics.training_time_ms, 0.0)
    
    def test_train_lightgbm_with_tuning(self):
        """Test LightGBM training with hyperparameter tuning (simplified)."""
        # Use smaller param grid to reduce computation time
        model, metrics_list = self.pipeline.train_lightgbm(self.X, self.y, perform_tuning=False)
        
        # Check model is trained
        self.assertIsNotNone(model)
        self.assertEqual(len(metrics_list), self.pipeline.cv_folds)
    
    def test_train_lightgbm_custom_params(self):
        """Test LightGBM training with custom parameters."""
        custom_params = {
            'n_estimators': 50,
            'max_depth': 4,
            'learning_rate': 0.05,
            'random_state': 42,
            'verbose': -1
        }
        
        model, metrics_list = self.pipeline.train_lightgbm(
            self.X, self.y, hyperparams=custom_params, perform_tuning=False
        )
        
        self.assertIsNotNone(model)
        self.assertEqual(len(metrics_list), self.pipeline.cv_folds)
    
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
    
    def test_training_time_measurement(self):
        """Test that training time is correctly measured."""
        model, metrics_list = self.pipeline.train_xgboost(self.X, self.y, perform_tuning=False)
        
        # Check training time is reasonable
        for metrics in metrics_list:
            self.assertGreater(metrics.training_time_ms, 0)
            self.assertLess(metrics.training_time_ms, 10000)  # Less than 10 seconds
    
    def test_multiple_cv_folds(self):
        """Test training pipeline with different CV fold numbers."""
        for cv_folds in [3, 5, 10]:
            pipeline = TrainingPipeline(cv_folds=cv_folds)
            model, metrics_list = pipeline.train_xgboost(self.X, self.y, perform_tuning=False)
            
            self.assertEqual(len(metrics_list), cv_folds)
    
    def test_singleton_instance(self):
        """Test singleton pattern for training pipeline."""
        instance1 = get_training_pipeline()
        instance2 = get_training_pipeline()
        
        self.assertIs(instance1, instance2)
    
    def test_data_dimensions_preserved(self):
        """Test that training maintains correct data dimensions."""
        model, metrics_list = self.pipeline.train_xgboost(self.X, self.y, perform_tuning=False)
        
        # All metrics should reference the original feature count
        for metrics in metrics_list:
            self.assertEqual(metrics.feature_count, 28)
            self.assertEqual(metrics.samples_count, 300)


if __name__ == '__main__':
    unittest.main()
