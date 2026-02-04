"""
Anomaly Detection Engine for DDoS Detection
Uses Isolation Forest, LOF, and statistical methods for attack detection
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import sqlite3

try:
    from sklearn.ensemble import IsolationForest  # type: ignore
    from sklearn.neighbors import LocalOutlierFactor  # type: ignore
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class AnomalyScore:
    """Anomaly detection result"""
    timestamp: float
    is_anomaly: bool
    score: float  # 0-1, where 1 is maximum anomaly
    detection_method: str  # 'isolation_forest', 'lof', 'zscore', 'ensemble'
    feature_count: int
    top_anomalous_features: List[Tuple[str, float]]  # [(feature_name, importance), ...]
    confidence: float  # 0-1 confidence in detection
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'is_anomaly': self.is_anomaly,
            'score': float(self.score),
            'detection_method': self.detection_method,
            'feature_count': self.feature_count,
            'top_anomalous_features': [(f, float(s)) for f, s in self.top_anomalous_features],
            'confidence': float(self.confidence)
        }

# ============================================================================
# ANOMALY DETECTION ENGINES
# ============================================================================

class IsolationForestDetector:
    """
    Isolation Forest anomaly detection
    Fast, effective for high-dimensional data
    """
    
    def __init__(self, contamination: float = 0.05, n_estimators: int = 100):
        """
        Initialize Isolation Forest detector
        
        Args:
            contamination: Expected proportion of anomalies (0-1)
            n_estimators: Number of trees
        """
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn required for Isolation Forest")
        
        self.contamination = contamination
        self.model = IsolationForest(  # type: ignore
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42,
            n_jobs=-1
        )
        self.is_fitted = False
        self.feature_names = []
        
        logger.info('[ML] Isolation Forest detector initialized (contamination={0})'.format(contamination))
    
    def fit(self, data: np.ndarray, feature_names: Optional[List[str]] = None) -> None:
        """Fit detector on training data"""
        if data.shape[0] == 0:
            logger.warning('[ML] No data to fit Isolation Forest')
            return
        
        self.model.fit(data)
        self.is_fitted = True
        self.feature_names = feature_names or [f'feature_{i}' for i in range(data.shape[1])]
        
        logger.info('[ML] Isolation Forest fitted on {0} samples'.format(data.shape[0]))
    
    def predict(self, data: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Predict anomalies
        
        Returns:
            predictions: -1 for anomaly, 1 for normal
            scores: Anomaly scores (higher = more anomalous)
        """
        if not self.is_fitted:
            logger.warning('[ML] Isolation Forest not fitted')
            return None, None
        
        predictions = self.model.predict(data)
        scores = self.model.score_samples(data)
        
        # Normalize scores to 0-1
        min_score = np.min(scores)
        max_score = np.max(scores)
        if max_score > min_score:
            normalized_scores = (scores - min_score) / (max_score - min_score)
        else:
            normalized_scores = np.zeros_like(scores)
        
        return predictions, normalized_scores

class LocalOutlierFactorDetector:
    """
    Local Outlier Factor (LOF) anomaly detection
    Good for local density-based anomalies
    """
    
    def __init__(self, n_neighbors: int = 20, contamination: float = 0.05):
        """
        Initialize LOF detector
        
        Args:
            n_neighbors: Number of neighbors for density estimation
            contamination: Expected proportion of anomalies
        """
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn required for LOF")
        
        self.n_neighbors = n_neighbors
        self.contamination = contamination
        self.model = LocalOutlierFactor(  # type: ignore
            n_neighbors=n_neighbors,
            contamination=contamination,
            novelty=True  # For predicting on new data
        )
        self.is_fitted = False
        self.feature_names = []
        
        logger.info('[ML] LOF detector initialized (n_neighbors={0})'.format(n_neighbors))
    
    def fit(self, data: np.ndarray, feature_names: Optional[List[str]] = None) -> None:
        """Fit detector on training data"""
        if data.shape[0] < self.n_neighbors:
            logger.warning('[ML] Insufficient data for LOF (need >= {0} samples)'.format(self.n_neighbors))
            return
        
        self.model.fit(data)
        self.is_fitted = True
        self.feature_names = feature_names or [f'feature_{i}' for i in range(data.shape[1])]
        
        logger.info('[ML] LOF fitted on {0} samples'.format(data.shape[0]))
    
    def predict(self, data: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Predict anomalies
        
        Returns:
            predictions: -1 for anomaly, 1 for normal
            scores: Anomaly scores (higher = more anomalous)
        """
        if not self.is_fitted:
            logger.warning('[ML] LOF not fitted')
            return None, None
        
        predictions = self.model.predict(data)
        scores = -self.model.score_samples(data)  # Negate for consistency
        
        # Normalize scores to 0-1
        min_score = np.min(scores)
        max_score = np.max(scores)
        if max_score > min_score:
            normalized_scores = (scores - min_score) / (max_score - min_score)
        else:
            normalized_scores = np.zeros_like(scores)
        
        return predictions, normalized_scores

class StatisticalDetector:
    """
    Statistical anomaly detection using Z-score
    Simple baseline for comparison
    """
    
    def __init__(self, z_threshold: float = 3.0):
        """
        Initialize statistical detector
        
        Args:
            z_threshold: Z-score threshold for anomaly
        """
        self.z_threshold = z_threshold
        self.means = None
        self.stds = None
        self.is_fitted = False
        self.feature_names = []
        
        logger.info('[ML] Statistical detector initialized (z_threshold={0})'.format(z_threshold))
    
    def fit(self, data: np.ndarray, feature_names: Optional[List[str]] = None) -> None:
        """Fit detector on training data"""
        self.means = np.mean(data, axis=0)
        self.stds = np.std(data, axis=0)
        self.stds[self.stds == 0] = 1.0  # Avoid division by zero
        
        self.is_fitted = True
        self.feature_names = feature_names or [f'feature_{i}' for i in range(data.shape[1])]
        
        logger.info('[ML] Statistical detector fitted on {0} samples'.format(data.shape[0]))
    
    def predict(self, data: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Predict anomalies using Z-score
        
        Returns:
            predictions: -1 for anomaly, 1 for normal
            scores: Z-score based anomaly scores
        """
        if not self.is_fitted:
            logger.warning('[ML] Statistical detector not fitted')
            return None, None
        
        # Calculate Z-scores
        z_scores = np.abs((data - self.means) / self.stds)
        
        # Check if any feature exceeds threshold
        predictions = np.where(np.any(z_scores > self.z_threshold, axis=1), -1, 1)
        
        # Use max Z-score as anomaly score
        scores = np.max(z_scores, axis=1)
        
        # Normalize to 0-1
        if np.max(scores) > 0:
            normalized_scores = np.minimum(scores / self.z_threshold, 1.0)
        else:
            normalized_scores = np.zeros_like(scores)
        
        return predictions, normalized_scores

# ============================================================================
# ENSEMBLE ANOMALY DETECTOR
# ============================================================================

class AnomalyDetectionEngine:
    """
    Ensemble anomaly detection using multiple algorithms
    Combines Isolation Forest, LOF, and statistical methods
    """
    
    def __init__(self, db_path: str = 'ddospot.db'):
        """
        Initialize anomaly detection engine
        
        Args:
            db_path: Path to database for persistence
        """
        self.db_path = db_path
        self.detectors = {}
        self.feature_names = []
        self.is_fitted = False
        self.detection_history = []
        
        # Initialize detectors if sklearn is available
        if HAS_SKLEARN:
            try:
                self.detectors['isolation_forest'] = IsolationForestDetector(contamination=0.05)
                self.detectors['lof'] = LocalOutlierFactorDetector(n_neighbors=20, contamination=0.05)
            except ImportError:
                logger.warning('[ML] scikit-learn detectors unavailable')
        
        self.detectors['zscore'] = StatisticalDetector(z_threshold=3.0)
        
        self._init_database()
        logger.info('[ML] Anomaly Detection Engine initialized with {0} detectors'.format(len(self.detectors)))
    
    def _init_database(self) -> None:
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Anomaly detections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_anomalies (
                    id INTEGER PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    is_anomaly INTEGER NOT NULL,
                    anomaly_score REAL NOT NULL,
                    detection_method TEXT NOT NULL,
                    feature_count INTEGER NOT NULL,
                    top_features TEXT,
                    confidence REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ml_anomalies_timestamp ON ml_anomalies(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ml_anomalies_is_anomaly ON ml_anomalies(is_anomaly)')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error('[ML] Database initialization error: {0}'.format(e))
    
    def fit(self, data: np.ndarray, feature_names: Optional[List[str]] = None) -> None:
        """Fit all detectors on training data"""
        if data.shape[0] == 0:
            logger.warning('[ML] No training data for anomaly detection')
            return
        
        self.feature_names = feature_names or [f'feature_{i}' for i in range(data.shape[1])]
        
        for name, detector in self.detectors.items():
            try:
                detector.fit(data, self.feature_names)
            except Exception as e:
                logger.error('[ML] Error fitting {0}: {1}'.format(name, e))
        
        self.is_fitted = True
        logger.info('[ML] All anomaly detectors fitted')
    
    def detect(self, data: np.ndarray) -> Optional[AnomalyScore]:
        """
        Detect anomalies in feature data
        
        Args:
            data: Single sample or batch (N, 28)
        
        Returns:
            AnomalyScore with ensemble result
        """
        if not self.is_fitted:
            logger.warning('[ML] Anomaly detectors not fitted')
            return None
        
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        # Run all detectors
        results = {}
        for name, detector in self.detectors.items():
            try:
                preds, scores = detector.predict(data)
                if preds is not None:
                    results[name] = {
                        'prediction': preds[0],
                        'score': scores[0]
                    }
            except Exception as e:
                logger.error('[ML] Error in {0} detection: {1}'.format(name, e))
        
        if not results:
            logger.error('[ML] No detectors produced results')
            return None
        
        # Ensemble: majority vote + average score
        anomaly_votes = sum(1 for r in results.values() if r['prediction'] == -1)
        is_anomaly = anomaly_votes > len(results) / 2
        
        # Average scores
        avg_score = np.mean([r['score'] for r in results.values()])
        
        # Weighted confidence
        confidence = min(abs(anomaly_votes - len(results) / 2) / len(results) * 2, 1.0)
        
        # Find top anomalous features
        top_features = self._get_top_anomalous_features(data[0], results)
        
        # Determine primary method
        primary_method = 'ensemble'
        if anomaly_votes > 0:
            for name, result in results.items():
                if result['prediction'] == -1:
                    primary_method = name
                    break
        
        score = AnomalyScore(
            timestamp=datetime.now().timestamp(),
            is_anomaly=is_anomaly,
            score=float(avg_score),  # type: ignore
            detection_method=primary_method,
            feature_count=len(self.feature_names),
            top_anomalous_features=top_features,
            confidence=float(confidence)  # type: ignore
        )
        
        # Store in history and database
        self.detection_history.append(score)
        if len(self.detection_history) > 10000:  # Keep last 10k in memory
            self.detection_history = self.detection_history[-10000:]
        
        self._store_detection(score)
        
        return score
    
    def _get_top_anomalous_features(self, sample: np.ndarray, results: Dict) -> List[Tuple[str, float]]:
        """Get top anomalous features"""
        feature_scores = np.zeros(len(self.feature_names))
        
        for name, result in results.items():
            if result['prediction'] == -1:
                # Contribution based on deviation and score
                feature_scores += np.abs(sample) * result['score']
        
        # Get top 5 features
        top_indices = np.argsort(-feature_scores)[:5]
        top_features = [
            (self.feature_names[i], float(feature_scores[i]))
            for i in top_indices if feature_scores[i] > 0
        ]
        
        return top_features
    
    def _store_detection(self, score: AnomalyScore) -> None:
        """Store detection result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            top_features_json = json.dumps(score.to_dict()['top_anomalous_features'])
            
            cursor.execute('''
                INSERT INTO ml_anomalies 
                (timestamp, is_anomaly, anomaly_score, detection_method, feature_count, top_features, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                score.timestamp,
                1 if score.is_anomaly else 0,
                score.score,
                score.detection_method,
                score.feature_count,
                top_features_json,
                score.confidence
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error('[ML] Error storing detection: {0}'.format(e))
    
    def get_detection_stats(self) -> Dict:
        """Get detection statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM ml_anomalies WHERE is_anomaly = 1')
            anomaly_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM ml_anomalies')
            total_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(anomaly_score), MAX(anomaly_score) FROM ml_anomalies')
            avg_score, max_score = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_detections': total_count,
                'anomalies_detected': anomaly_count,
                'anomaly_rate': anomaly_count / total_count if total_count > 0 else 0,
                'avg_score': avg_score or 0.0,
                'max_score': max_score or 0.0
            }
        except Exception as e:
            logger.error('[ML] Error getting stats: {0}'.format(e))
            return {}
    
    def get_detection_history(self, limit: int = 100) -> List[Dict]:
        """Get recent detection history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, is_anomaly, anomaly_score, detection_method, confidence
                FROM ml_anomalies
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'timestamp': row[0],
                    'is_anomaly': bool(row[1]),
                    'score': row[2],
                    'method': row[3],
                    'confidence': row[4]
                })
            
            conn.close()
            return results
        except Exception as e:
            logger.error('[ML] Error getting history: {0}'.format(e))
            return []

# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_detector = None

def get_anomaly_detector(db_path: str = 'ddospot.db') -> AnomalyDetectionEngine:
    """Get singleton anomaly detector"""
    global _detector
    
    if _detector is None:
        _detector = AnomalyDetectionEngine(db_path)
    
    return _detector
