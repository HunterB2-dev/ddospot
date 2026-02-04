"""
Tests for ML API endpoints.

Tests cover:
- Prediction endpoint
- Anomaly detection endpoint
- Model management endpoints
- Metrics and statistics endpoints
- Attack patterns endpoints
- Health check
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from ml.api import ml_bp


class MLAPITestCase(unittest.TestCase):
    """Base test case for ML API."""
    
    def setUp(self):
        """Set up Flask test client."""
        from flask import Flask
        
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.register_blueprint(ml_bp)
        self.client = self.app.test_client()
    
    def test_api_blueprint_registered(self):
        """Test that ML API blueprint is registered."""
        self.assertIsNotNone(ml_bp)
        self.assertEqual(ml_bp.name, 'ml')
        self.assertEqual(ml_bp.url_prefix, '/api/ml')


class TestPredictionEndpoint(MLAPITestCase):
    """Test prediction endpoint."""
    
    @patch('ml.api.get_prediction_engine')
    def test_predict_success(self, mock_engine):
        """Test successful prediction."""
        # Mock prediction result
        mock_result = MagicMock()
        mock_result.is_attack = True
        mock_result.attack_probability = 0.85
        mock_result.confidence = 0.92
        mock_result.top_risk_factors = ['high_packet_rate', 'low_entropy']
        
        mock_pred_engine = MagicMock()
        mock_pred_engine.predict.return_value = mock_result
        mock_engine.return_value = mock_pred_engine
        
        # Make request
        response = self.client.post(
            '/api/ml/predict',
            data=json.dumps({
                'features': [0.1] * 28,
                'sample_id': 'test_123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['is_attack'])
        self.assertEqual(data['sample_id'], 'test_123')
        self.assertIn('probability', data)
    
    def test_predict_missing_features(self):
        """Test prediction with missing features."""
        response = self.client.post(
            '/api/ml/predict',
            data=json.dumps({'sample_id': 'test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_predict_wrong_feature_count(self):
        """Test prediction with wrong feature count."""
        response = self.client.post(
            '/api/ml/predict',
            data=json.dumps({
                'features': [0.1] * 10,  # Wrong count
                'sample_id': 'test'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)


class TestAnomalyDetectionEndpoint(MLAPITestCase):
    """Test anomaly detection endpoint."""
    
    @patch('ml.api.get_anomaly_detection_engine')
    def test_detect_anomaly_success(self, mock_engine):
        """Test successful anomaly detection."""
        # Mock detection result
        mock_result = MagicMock()
        mock_result.is_anomaly = True
        mock_result.score = 0.75
        mock_result.confidence = 0.88
        mock_result.detection_method = 'isolation_forest'
        mock_result.top_anomalous_features = [('packet_rate', 0.9), ('byte_rate', 0.85)]
        
        mock_det_engine = MagicMock()
        mock_det_engine.detect.return_value = [mock_result]
        mock_engine.return_value = mock_det_engine
        
        # Make request
        response = self.client.post(
            '/api/ml/detect-anomaly',
            data=json.dumps({
                'features': [0.1] * 28,
                'sample_id': 'test_456'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['is_anomaly'])
        self.assertEqual(data['sample_id'], 'test_456')
        self.assertIn('score', data)


class TestModelManagementEndpoints(MLAPITestCase):
    """Test model management endpoints."""
    
    @patch('ml.api.get_prediction_engine')
    @patch('ml.api.get_anomaly_detection_engine')
    @patch('ml.api.get_pattern_learning_engine')
    def test_get_models(self, mock_pattern, mock_detection, mock_prediction):
        """Test getting available models."""
        mock_prediction.return_value = MagicMock()
        mock_detection.return_value = MagicMock()
        mock_pattern.return_value = MagicMock()
        
        response = self.client.get('/api/ml/models')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('models', data)
        self.assertEqual(len(data['models']), 3)
        
        model_names = [m['name'] for m in data['models']]
        self.assertIn('prediction', model_names)
        self.assertIn('anomaly_detection', model_names)
        self.assertIn('pattern_learning', model_names)
    
    @patch('ml.api.get_training_pipeline')
    def test_retrain_valid_model(self, mock_training):
        """Test retraining with valid model."""
        mock_pipeline = MagicMock()
        mock_pipeline.store_training_job.return_value = True
        mock_training.return_value = mock_pipeline
        
        response = self.client.post(
            '/api/ml/retrain',
            data=json.dumps({
                'model_name': 'prediction',
                'use_hyperparameter_tuning': False
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 202)
        data = json.loads(response.data)
        self.assertEqual(data['model_name'], 'prediction')
        self.assertEqual(data['status'], 'pending')
        self.assertIn('job_id', data)
    
    def test_retrain_invalid_model(self):
        """Test retraining with invalid model."""
        response = self.client.post(
            '/api/ml/retrain',
            data=json.dumps({'model_name': 'invalid_model'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)


class TestMetricsEndpoints(MLAPITestCase):
    """Test metrics and statistics endpoints."""
    
    @patch('ml.api.get_training_pipeline')
    def test_get_metrics(self, mock_training):
        """Test getting model metrics."""
        mock_stats = {
            'xgboost': {
                'training_runs': 5,
                'avg_cv_score': 0.92,
                'best_cv_score': 0.95,
                'worst_cv_score': 0.88
            }
        }
        
        mock_pipeline = MagicMock()
        mock_pipeline.get_model_performance_stats.return_value = mock_stats
        mock_training.return_value = mock_pipeline
        
        response = self.client.get('/api/ml/metrics')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('metrics', data)
        self.assertIn('xgboost', data['metrics'])
    
    @patch('ml.api.get_training_pipeline')
    def test_get_training_history(self, mock_training):
        """Test getting training history."""
        mock_job = MagicMock()
        mock_job.job_id = 'job_123'
        mock_job.model_name = 'xgboost'
        mock_job.status = 'completed'
        mock_job.start_time = '2026-02-03T12:00:00'
        mock_job.end_time = '2026-02-03T12:05:00'
        mock_job.metrics = [MagicMock(), MagicMock()]
        
        mock_pipeline = MagicMock()
        mock_pipeline.get_training_history.return_value = [mock_job]
        mock_training.return_value = mock_pipeline
        
        response = self.client.get('/api/ml/training-history')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('history', data)
        self.assertEqual(len(data['history']), 1)
        self.assertEqual(data['history'][0]['job_id'], 'job_123')


class TestPatternEndpoints(MLAPITestCase):
    """Test attack pattern endpoints."""
    
    @patch('ml.api.get_pattern_learning_engine')
    def test_get_patterns(self, mock_engine):
        """Test getting attack patterns."""
        mock_pattern = MagicMock()
        mock_pattern.pattern_id = 'pat_001'
        mock_pattern.severity = 'high'
        mock_pattern.confidence = 0.85
        mock_pattern.detection_count = 42
        mock_pattern.characteristics = {'packet_rate': 1000}
        
        mock_pat_engine = MagicMock()
        mock_pat_engine.get_patterns.return_value = [mock_pattern]
        mock_engine.return_value = mock_pat_engine
        
        response = self.client.get('/api/ml/patterns')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('patterns', data)
        self.assertEqual(len(data['patterns']), 1)
        self.assertEqual(data['patterns'][0]['pattern_id'], 'pat_001')
    
    @patch('ml.api.get_pattern_learning_engine')
    def test_get_pattern_stats(self, mock_engine):
        """Test getting pattern statistics."""
        mock_patterns = [
            MagicMock(severity='high', detection_count=10, confidence=0.9),
            MagicMock(severity='medium', detection_count=5, confidence=0.8),
            MagicMock(severity='critical', detection_count=20, confidence=0.95),
        ]
        
        mock_pat_engine = MagicMock()
        mock_pat_engine.get_patterns.return_value = mock_patterns
        mock_engine.return_value = mock_pat_engine
        
        response = self.client.get('/api/ml/pattern-stats')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_patterns'], 3)
        self.assertIn('by_severity', data)
        self.assertGreater(data['avg_detection_count'], 0)


class TestHealthCheckEndpoint(MLAPITestCase):
    """Test health check endpoint."""
    
    @patch('ml.api.get_prediction_engine')
    @patch('ml.api.get_anomaly_detection_engine')
    @patch('ml.api.get_pattern_learning_engine')
    @patch('ml.api.get_training_pipeline')
    def test_health_check_healthy(self, mock_training, mock_pattern, mock_detection, mock_prediction):
        """Test health check when all components are healthy."""
        mock_prediction.return_value = MagicMock()
        mock_detection.return_value = MagicMock()
        mock_pattern.return_value = MagicMock()
        mock_training.return_value = MagicMock()
        
        response = self.client.get('/api/ml/health')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('components', data)
        self.assertTrue(data['components']['prediction_engine'])
    
    @patch('ml.api.get_prediction_engine', side_effect=Exception('Test error'))
    @patch('ml.api.get_anomaly_detection_engine')
    @patch('ml.api.get_pattern_learning_engine')
    @patch('ml.api.get_training_pipeline')
    def test_health_check_degraded(self, mock_training, mock_pattern, mock_detection, mock_prediction):
        """Test health check when some components fail."""
        mock_detection.return_value = MagicMock()
        mock_pattern.return_value = MagicMock()
        mock_training.return_value = MagicMock()
        
        response = self.client.get('/api/ml/health')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'degraded')


if __name__ == '__main__':
    unittest.main()
