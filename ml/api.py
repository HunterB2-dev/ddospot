"""
ML API Blueprint for DDoS Detection Honeypot

Provides REST endpoints for:
- Model inference and predictions
- Model management and retraining
- Performance metrics and statistics
- Attack pattern information
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from flask import Blueprint, request, jsonify

from ml.prediction import get_prediction_engine
from ml.detection import get_anomaly_detector
from ml.patterns import get_pattern_engine
from ml.training import get_training_pipeline, TrainingJob
from ml.features import get_feature_extractor


logger = logging.getLogger(__name__)

# Create blueprint
ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@ml_bp.route('/predict', methods=['POST'])
def predict():
    """
    Make a prediction on network traffic sample.
    
    Request JSON:
    {
        "features": [float, ...],  # 28 feature values
        "sample_id": "optional_id"
    }
    
    Response:
    {
        "is_attack": bool,
        "probability": float,
        "confidence": float,
        "risk_factors": [str, ...],
        "sample_id": str,
        "timestamp": str
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'features' not in data:
            return jsonify({'error': 'Missing features in request'}), 400
        
        features = data.get('features')
        sample_id = data.get('sample_id', 'unknown')
        
        # Validate feature count
        if len(features) != 28:
            return jsonify({'error': f'Expected 28 features, got {len(features)}'}), 400
        
        # Make prediction
        import numpy as np
        X = np.array([features])
        
        engine = get_prediction_engine()
        result = engine.predict(X)
        
        if result is None:
            return jsonify({'error': 'Prediction failed'}), 400
        
        # Format response
        response = {
            'is_attack': bool(result.is_attack),  # type: ignore
            'probability': float(result.attack_probability),  # type: ignore
            'confidence': float(result.confidence),  # type: ignore
            'risk_factors': result.top_risk_factors,  # type: ignore
            'sample_id': sample_id,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f'Prediction for {sample_id}: attack={result.is_attack}, prob={result.attack_probability:.3f}')  # type: ignore
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f'Prediction error: {e}')
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/detect-anomaly', methods=['POST'])
def detect_anomaly():
    """
    Detect anomalies in network traffic sample.
    
    Request JSON:
    {
        "features": [float, ...],  # 28 feature values
        "sample_id": "optional_id"
    }
    
    Response:
    {
        "is_anomaly": bool,
        "score": float,
        "confidence": float,
        "detection_method": str,
        "top_features": [[name, score], ...],
        "sample_id": str,
        "timestamp": str
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'features' not in data:
            return jsonify({'error': 'Missing features in request'}), 400
        
        features = data.get('features')
        sample_id = data.get('sample_id', 'unknown')
        
        # Validate feature count
        if len(features) != 28:
            return jsonify({'error': f'Expected 28 features, got {len(features)}'}), 400
        
        # Detect anomaly
        import numpy as np
        X = np.array([features])
        
        detector = get_anomaly_detector()
        result = detector.detect(X)
        
        if result is None:
            return jsonify({'error': 'Detection failed'}), 400
        
        # Format response
        response = {
            'is_anomaly': bool(result.is_anomaly),  # type: ignore
            'score': float(result.score),  # type: ignore
            'confidence': float(result.confidence),  # type: ignore
            'detection_method': result.detection_method,  # type: ignore
            'top_features': [[name, float(score)] for name, score in result.top_anomalous_features],  # type: ignore
            'sample_id': sample_id,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f'Anomaly detection for {sample_id}: anomaly={result.is_anomaly}, score={result.score:.3f}')  # type: ignore
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f'Anomaly detection error: {e}')
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MODEL MANAGEMENT ENDPOINTS
# ============================================================================

@ml_bp.route('/models', methods=['GET'])
def get_models():
    """
    Get information about available ML models.
    
    Response:
    {
        "models": [
            {
                "name": str,
                "type": str,
                "version": int,
                "trained": bool,
                "accuracy": float or null,
                "timestamp": str
            },
            ...
        ]
    }
    """
    try:
        prediction_engine = get_prediction_engine()
        detector = get_anomaly_detector()
        pattern_engine = get_pattern_engine()
        
        models = [
            {
                'name': 'prediction',
                'type': 'XGBoost/LightGBM Ensemble',
                'version': 1,
                'trained': True,
                'accuracy': None,
                'timestamp': datetime.now().isoformat()
            },
            {
                'name': 'anomaly_detection',
                'type': 'Isolation Forest/LOF/Z-score Ensemble',
                'version': 1,
                'trained': True,
                'accuracy': None,
                'timestamp': datetime.now().isoformat()
            },
            {
                'name': 'pattern_learning',
                'type': 'K-means Clustering',
                'version': 1,
                'trained': True,
                'accuracy': None,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        return jsonify({'models': models}), 200
    
    except Exception as e:
        logger.error(f'Get models error: {e}')
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/retrain', methods=['POST'])
def retrain():
    """
    Trigger model retraining.
    
    Request JSON:
    {
        "model_name": "prediction" | "anomaly_detection" | "pattern_learning",
        "use_hyperparameter_tuning": bool (optional, default: false)
    }
    
    Response:
    {
        "job_id": str,
        "model_name": str,
        "status": "pending",
        "message": str
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'model_name' not in data:
            return jsonify({'error': 'Missing model_name in request'}), 400
        
        model_name = data.get('model_name')
        perform_tuning = data.get('use_hyperparameter_tuning', False)
        
        valid_models = ['prediction', 'anomaly_detection', 'pattern_learning']
        if model_name not in valid_models:
            return jsonify({'error': f'Invalid model_name. Must be one of {valid_models}'}), 400
        
        # Create training job
        job_id = f"job_{datetime.now().timestamp():.0f}"
        job = TrainingJob(
            job_id=job_id,
            model_name=model_name,
            scheduled_time=datetime.now().isoformat(),
            status='pending'
        )
        
        # Store job
        training_pipeline = get_training_pipeline()
        training_pipeline.store_training_job(job)
        
        logger.info(f'Retraining job created: {job_id} for {model_name}')
        
        return jsonify({
            'job_id': job_id,
            'model_name': model_name,
            'status': 'pending',
            'message': f'Retraining job {job_id} scheduled for {model_name}'
        }), 202
    
    except Exception as e:
        logger.error(f'Retrain error: {e}')
        return jsonify({'error': str(e)}), 500


# ============================================================================
# METRICS AND STATISTICS ENDPOINTS
# ============================================================================

@ml_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Get performance metrics for all models.
    
    Query Parameters:
    - model_name: Filter by specific model (optional)
    
    Response:
    {
        "metrics": {
            "model_name": {
                "training_runs": int,
                "avg_cv_score": float,
                "best_cv_score": float,
                "worst_cv_score": float
            },
            ...
        }
    }
    """
    try:
        model_name = request.args.get('model_name')
        
        training_pipeline = get_training_pipeline()
        stats = training_pipeline.get_model_performance_stats()
        
        # Filter if model_name provided
        if model_name:
            stats = {k: v for k, v in stats.items() if k == model_name}
        
        return jsonify({'metrics': stats}), 200
    
    except Exception as e:
        logger.error(f'Get metrics error: {e}')
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/training-history', methods=['GET'])
def get_training_history():
    """
    Get training history for models.
    
    Query Parameters:
    - model_name: Filter by model name (optional)
    - limit: Maximum number of records (default: 10)
    
    Response:
    {
        "history": [
            {
                "job_id": str,
                "model_name": str,
                "status": str,
                "start_time": str or null,
                "end_time": str or null,
                "metrics_count": int
            },
            ...
        ]
    }
    """
    try:
        model_name = request.args.get('model_name')
        limit = int(request.args.get('limit', 10))
        
        training_pipeline = get_training_pipeline()
        jobs = training_pipeline.get_training_history(model_name=model_name, limit=limit)
        
        history = []
        for job in jobs:
            history.append({
                'job_id': job.job_id,
                'model_name': job.model_name,
                'status': job.status,
                'start_time': job.start_time,
                'end_time': job.end_time,
                'metrics_count': len(job.metrics) if job.metrics else 0
            })
        
        return jsonify({'history': history}), 200
    
    except ValueError:
        return jsonify({'error': 'Invalid limit parameter'}), 400
    except Exception as e:
        logger.error(f'Get training history error: {e}')
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ATTACK PATTERNS ENDPOINTS
# ============================================================================

@ml_bp.route('/patterns', methods=['GET'])
def get_patterns():
    """
    Get discovered attack patterns.
    
    Query Parameters:
    - min_severity: Filter by minimum severity (low|medium|high|critical)
    
    Response:
    {
        "patterns": [
            {
                "pattern_id": str,
                "severity": str,
                "confidence": float,
                "detection_count": int,
                "characteristics": {
                    "feature1": value,
                    ...
                }
            },
            ...
        ]
    }
    """
    try:
        min_severity = request.args.get('min_severity')
        
        pattern_engine = get_pattern_engine()
        patterns = pattern_engine.get_patterns(min_severity=min_severity)
        
        response_patterns = []
        for pattern in patterns:
            response_patterns.append({
                'pattern_id': pattern.pattern_id,
                'severity': pattern.severity,
                'confidence': float(pattern.confidence),
                'detection_count': pattern.detection_count,
                'characteristics': pattern.characteristics if isinstance(pattern.characteristics, dict) else {}
            })
        
        return jsonify({'patterns': response_patterns}), 200
    
    except Exception as e:
        logger.error(f'Get patterns error: {e}')
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/pattern-stats', methods=['GET'])
def get_pattern_stats():
    """
    Get statistics about discovered attack patterns.
    
    Response:
    {
        "total_patterns": int,
        "by_severity": {
            "low": int,
            "medium": int,
            "high": int,
            "critical": int
        },
        "avg_detection_count": float,
        "avg_confidence": float
    }
    """
    try:
        pattern_engine = get_pattern_engine()
        patterns = pattern_engine.get_patterns()
        
        if not patterns:
            return jsonify({
                'total_patterns': 0,
                'by_severity': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
                'avg_detection_count': 0.0,
                'avg_confidence': 0.0
            }), 200
        
        # Calculate statistics
        by_severity = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        total_detection = 0
        total_confidence = 0.0
        
        for pattern in patterns:
            severity = pattern.severity.lower()
            if severity in by_severity:
                by_severity[severity] += 1
            total_detection += pattern.detection_count
            total_confidence += pattern.confidence
        
        return jsonify({
            'total_patterns': len(patterns),
            'by_severity': by_severity,
            'avg_detection_count': total_detection / len(patterns) if patterns else 0,
            'avg_confidence': total_confidence / len(patterns) if patterns else 0
        }), 200
    
    except Exception as e:
        logger.error(f'Get pattern stats error: {e}')
        return jsonify({'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@ml_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for ML API.
    
    Response:
    {
        "status": "healthy" | "degraded" | "unhealthy",
        "timestamp": str,
        "components": {
            "prediction_engine": bool,
            "detection_engine": bool,
            "pattern_engine": bool,
            "training_pipeline": bool
        }
    }
    """
    try:
        components = {}
        
        try:
            prediction_engine = get_prediction_engine()
            components['prediction_engine'] = prediction_engine is not None
        except:
            components['prediction_engine'] = False
        
        try:
            detector = get_anomaly_detector()
            components['anomaly_detection'] = detector is not None
        except:
            components['anomaly_detection'] = False
        
        try:
            pattern_engine = get_pattern_engine()
            components['pattern_learning'] = pattern_engine is not None
        except:
            components['pattern_learning'] = False
        
        try:
            training_pipeline = get_training_pipeline()
            components['training_pipeline'] = training_pipeline is not None
        except:
            components['training_pipeline'] = False
        
        # Determine overall status
        all_healthy = all(components.values())
        status = 'healthy' if all_healthy else ('degraded' if any(components.values()) else 'unhealthy')
        
        return jsonify({
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'components': components
        }), 200
    
    except Exception as e:
        logger.error(f'Health check error: {e}')
        return jsonify({'error': str(e)}), 500
