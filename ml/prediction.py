"""
Attack Prediction Model for DDoS Detection
Uses XGBoost/LightGBM for binary classification (attack vs normal)
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
import json
import sqlite3
import pickle
import os

try:
    import xgboost as xgb  # type: ignore
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb  # type: ignore
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PredictionResult:
    """Attack prediction result"""
    timestamp: float
    is_attack: bool
    attack_probability: float  # 0-1, probability of attack
    model_name: str
    prediction_time_ms: float
    feature_importance: List[Tuple[str, float]]  # [(feature_name, importance), ...]
    confidence: float  # 0-1 confidence in prediction
    top_risk_factors: List[str]  # Top contributing features
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'is_attack': self.is_attack,
            'attack_probability': float(self.attack_probability),
            'model_name': self.model_name,
            'prediction_time_ms': float(self.prediction_time_ms),
            'feature_importance': [(f, float(i)) for f, i in self.feature_importance],
            'confidence': float(self.confidence),
            'top_risk_factors': self.top_risk_factors
        }

# ============================================================================
# XGBOOST PREDICTOR
# ============================================================================

class XGBoostPredictor:
    """XGBoost-based attack prediction"""
    
    def __init__(self, 
                 n_estimators: int = 100,
                 learning_rate: float = 0.1,
                 max_depth: int = 6,
                 subsample: float = 0.8):
        """
        Initialize XGBoost predictor
        
        Args:
            n_estimators: Number of boosting rounds
            learning_rate: Learning rate (eta)
            max_depth: Maximum tree depth
            subsample: Subsample ratio of training instances
        """
        if not HAS_XGBOOST:
            raise ImportError("XGBoost required for XGBoostPredictor")
        
        self.params = {
            'objective': 'binary:logistic',
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'subsample': subsample,
            'eval_metric': 'logloss',
            'seed': 42,
            'n_jobs': -1
        }
        self.n_estimators = n_estimators
        self.model = None
        self.is_fitted = False
        self.feature_names = []
        self.threshold = 0.5  # Classification threshold
        
        logger.info('[ML] XGBoost predictor initialized (estimators={0})'.format(n_estimators))
    
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> None:
        """
        Fit XGBoost model
        
        Args:
            X: Training features (N, features)
            y: Training labels (N,) with 0 = normal, 1 = attack
            feature_names: Optional feature names
        """
        if X.shape[0] == 0:
            logger.warning('[ML] No data to fit XGBoost')
            return
        
        dtrain = xgb.DMatrix(X, label=y)  # type: ignore
        
        self.model = xgb.train(  # type: ignore
            self.params,
            dtrain,
            num_boost_round=self.n_estimators,
            verbose_eval=False
        )
        
        self.is_fitted = True
        self.feature_names = feature_names or [f'feature_{i}' for i in range(X.shape[1])]
        
        logger.info('[ML] XGBoost model fitted on {0} samples'.format(X.shape[0]))
    
    def predict(self, X: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Predict attack probability
        
        Returns:
            predictions: 0/1 (normal/attack based on threshold)
            probabilities: Attack probabilities (0-1)
        """
        if not self.is_fitted:
            logger.warning('[ML] XGBoost model not fitted')
            return None, None
        
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        dtest = xgb.DMatrix(X)  # type: ignore
        probabilities = self.model.predict(dtest)  # type: ignore
        predictions = (probabilities >= self.threshold).astype(int)
        
        return predictions, probabilities
    
    def get_feature_importance(self, top_n: int = 5) -> List[Tuple[str, float]]:
        """Get top N important features"""
        if not self.is_fitted:
            logger.warning('[ML] Model not fitted')
            return []
        
        importance_dict = self.model.get_score(importance_type='weight')  # type: ignore
        
        # Convert to feature names
        importance_tuples = []
        for feature_idx, importance in importance_dict.items():
            feature_name = self.feature_names[int(feature_idx.replace('f', ''))]
            importance_tuples.append((feature_name, float(importance)))  # type: ignore
        
        # Sort by importance
        importance_tuples.sort(key=lambda x: x[1], reverse=True)
        
        return importance_tuples[:top_n]
    
    def save(self, filepath: str) -> bool:
        """Save model to file"""
        try:
            if self.model:
                self.model.save_model(filepath)
                logger.info('[ML] XGBoost model saved to {0}'.format(filepath))
                return True
        except Exception as e:
            logger.error('[ML] Error saving XGBoost model: {0}'.format(e))
        
        return False
    
    def load(self, filepath: str) -> bool:
        """Load model from file"""
        try:
            self.model = xgb.Booster()  # type: ignore
            self.model.load_model(filepath)
            self.is_fitted = True
            logger.info('[ML] XGBoost model loaded from {0}'.format(filepath))
            return True
        except Exception as e:
            logger.error('[ML] Error loading XGBoost model: {0}'.format(e))
        
        return False

# ============================================================================
# LIGHTGBM PREDICTOR
# ============================================================================

class LightGBMPredictor:
    """LightGBM-based attack prediction"""
    
    def __init__(self,
                 n_estimators: int = 100,
                 learning_rate: float = 0.1,
                 num_leaves: int = 31,
                 feature_fraction: float = 0.8):
        """
        Initialize LightGBM predictor
        
        Args:
            n_estimators: Number of boosting rounds
            learning_rate: Learning rate
            num_leaves: Number of leaves in tree
            feature_fraction: Feature sampling fraction
        """
        if not HAS_LIGHTGBM:
            raise ImportError("LightGBM required for LightGBMPredictor")
        
        self.params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'num_leaves': num_leaves,
            'learning_rate': learning_rate,
            'feature_fraction': feature_fraction,
            'seed': 42,
            'n_jobs': -1,
            'verbose': -1
        }
        self.n_estimators = n_estimators
        self.model = None
        self.is_fitted = False
        self.feature_names = []
        self.threshold = 0.5
        
        logger.info('[ML] LightGBM predictor initialized (estimators={0})'.format(n_estimators))
    
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> None:
        """
        Fit LightGBM model
        
        Args:
            X: Training features (N, features)
            y: Training labels (N,) with 0 = normal, 1 = attack
            feature_names: Optional feature names
        """
        if X.shape[0] == 0:
            logger.warning('[ML] No data to fit LightGBM')
            return
        
        train_data = lgb.Dataset(X, label=y)  # type: ignore
        
        self.model = lgb.train(  # type: ignore
            self.params,
            train_data,
            num_boost_round=self.n_estimators
        )
        
        self.is_fitted = True
        self.feature_names = feature_names or [f'feature_{i}' for i in range(X.shape[1])]
        
        logger.info('[ML] LightGBM model fitted on {0} samples'.format(X.shape[0]))
    
    def predict(self, X: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Predict attack probability
        
        Returns:
            predictions: 0/1 (normal/attack based on threshold)
            probabilities: Attack probabilities (0-1)
        """
        if not self.is_fitted:
            logger.warning('[ML] LightGBM model not fitted')
            return None, None
        
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        probabilities = self.model.predict(X)  # type: ignore
        predictions = (probabilities >= self.threshold).astype(int)  # type: ignore
        
        return predictions, probabilities  # type: ignore
    
    def get_feature_importance(self, top_n: int = 5) -> List[Tuple[str, float]]:
        """Get top N important features"""
        if not self.is_fitted:
            logger.warning('[ML] Model not fitted')
            return []
        
        importance = self.model.feature_importance(importance_type='gain')  # type: ignore
        
        # Create tuples
        importance_tuples = [
            (self.feature_names[i], float(importance[i]))
            for i in range(len(self.feature_names))
        ]
        
        # Sort by importance
        importance_tuples.sort(key=lambda x: x[1], reverse=True)
        
        return importance_tuples[:top_n]
    
    def save(self, filepath: str) -> bool:
        """Save model to file"""
        try:
            self.model.save_model(filepath)  # type: ignore
            logger.info('[ML] LightGBM model saved to {0}'.format(filepath))
            return True
        except Exception as e:
            logger.error('[ML] Error saving LightGBM model: {0}'.format(e))
        
        return False
    
    def load(self, filepath: str) -> bool:
        """Load model from file"""
        try:
            self.model = lgb.Booster(model_file=filepath)  # type: ignore
            self.is_fitted = True
            logger.info('[ML] LightGBM model loaded from {0}'.format(filepath))
            return True
        except Exception as e:
            logger.error('[ML] Error loading LightGBM model: {0}'.format(e))
        
        return False

# ============================================================================
# PREDICTION ENGINE
# ============================================================================

class PredictionEngine:
    """
    Attack prediction engine combining multiple models
    """
    
    def __init__(self, db_path: str = 'ddospot.db', model_dir: str = 'models'):
        """
        Initialize prediction engine
        
        Args:
            db_path: Path to database
            model_dir: Directory for model persistence
        """
        self.db_path = db_path
        self.model_dir = model_dir
        self.models = {}
        self.feature_names = []
        self.prediction_history = []
        
        # Create model directory if needed
        os.makedirs(model_dir, exist_ok=True)
        
        # Initialize predictors
        if HAS_XGBOOST:
            try:
                self.models['xgboost'] = XGBoostPredictor()
            except ImportError:
                logger.warning('[ML] XGBoost not available')
        
        if HAS_LIGHTGBM:
            try:
                self.models['lightgbm'] = LightGBMPredictor()
            except ImportError:
                logger.warning('[ML] LightGBM not available')
        
        self._init_database()
        logger.info('[ML] Prediction Engine initialized with {0} models'.format(len(self.models)))
    
    def _init_database(self) -> None:
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Predictions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_predictions (
                    id INTEGER PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    is_attack INTEGER NOT NULL,
                    attack_probability REAL NOT NULL,
                    model_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    top_features TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ml_predictions_timestamp ON ml_predictions(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ml_predictions_is_attack ON ml_predictions(is_attack)')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error('[ML] Database initialization error: {0}'.format(e))
    
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> None:
        """Fit all prediction models"""
        if X.shape[0] == 0:
            logger.warning('[ML] No training data for predictions')
            return
        
        self.feature_names = feature_names or [f'feature_{i}' for i in range(X.shape[1])]
        
        for name, model in self.models.items():
            try:
                model.fit(X, y, self.feature_names)
            except Exception as e:
                logger.error('[ML] Error fitting {0}: {1}'.format(name, e))
        
        logger.info('[ML] All prediction models fitted')
    
    def predict(self, data: np.ndarray) -> Optional[PredictionResult]:
        """
        Predict attack probability
        
        Args:
            data: Feature vector (28,) or batch (N, 28)
        
        Returns:
            PredictionResult with ensemble prediction
        """
        import time
        
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        start_time = time.time()
        
        # Get predictions from all models
        predictions = {}
        for name, model in self.models.items():
            try:
                preds, probs = model.predict(data)
                if preds is not None:
                    predictions[name] = {
                        'prediction': preds[0],
                        'probability': probs[0],
                        'model': model
                    }
            except Exception as e:
                logger.error('[ML] Error in {0} prediction: {1}'.format(name, e))
        
        if not predictions:
            logger.error('[ML] No predictions generated')
            return None
        
        # Ensemble: average probability
        avg_probability = np.mean([p['probability'] for p in predictions.values()])
        is_attack = avg_probability >= 0.5
        
        # Confidence: agreement among models
        agreement = sum(1 for p in predictions.values() if p['prediction'] == (1 if is_attack else 0))
        confidence = agreement / len(predictions)
        
        # Get feature importance from primary model
        primary_model = list(predictions.values())[0]['model']
        top_features = primary_model.get_feature_importance(top_n=5)
        top_feature_names = [f[0] for f in top_features]
        
        prediction_time_ms = (time.time() - start_time) * 1000
        
        result = PredictionResult(
            timestamp=datetime.now().timestamp(),
            is_attack=bool(is_attack),  # type: ignore
            attack_probability=float(avg_probability),
            model_name='ensemble',
            prediction_time_ms=prediction_time_ms,
            feature_importance=top_features,
            confidence=float(confidence),
            top_risk_factors=top_feature_names
        )
        
        # Store prediction
        self.prediction_history.append(result)
        if len(self.prediction_history) > 10000:
            self.prediction_history = self.prediction_history[-10000:]
        
        self._store_prediction(result)
        
        return result
    
    def _store_prediction(self, result: PredictionResult) -> None:
        """Store prediction in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            top_features_json = json.dumps(result.to_dict()['feature_importance'])
            
            cursor.execute('''
                INSERT INTO ml_predictions
                (timestamp, is_attack, attack_probability, model_name, confidence, top_features)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                result.timestamp,
                1 if result.is_attack else 0,
                result.attack_probability,
                result.model_name,
                result.confidence,
                top_features_json
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error('[ML] Error storing prediction: {0}'.format(e))
    
    def get_prediction_stats(self) -> Dict:
        """Get prediction statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM ml_predictions WHERE is_attack = 1')
            attack_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM ml_predictions')
            total_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(attack_probability), MAX(attack_probability) FROM ml_predictions')
            avg_prob, max_prob = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_predictions': total_count,
                'attacks_predicted': attack_count,
                'attack_rate': attack_count / total_count if total_count > 0 else 0,
                'avg_probability': avg_prob or 0.0,
                'max_probability': max_prob or 0.0
            }
        except Exception as e:
            logger.error('[ML] Error getting stats: {0}'.format(e))
            return {}
    
    def get_prediction_history(self, limit: int = 100) -> List[Dict]:
        """Get recent prediction history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, is_attack, attack_probability, model_name, confidence
                FROM ml_predictions
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'timestamp': row[0],
                    'is_attack': bool(row[1]),
                    'probability': row[2],
                    'model': row[3],
                    'confidence': row[4]
                })
            
            conn.close()
            return results
        except Exception as e:
            logger.error('[ML] Error getting history: {0}'.format(e))
            return []
    
    def save_models(self) -> bool:
        """Save all models"""
        all_saved = True
        
        for name, model in self.models.items():
            filepath = os.path.join(self.model_dir, f'{name}_model.bin')
            if not model.save(filepath):
                all_saved = False
        
        return all_saved
    
    def load_models(self) -> bool:
        """Load all saved models"""
        all_loaded = True
        
        for name, model in self.models.items():
            filepath = os.path.join(self.model_dir, f'{name}_model.bin')
            if os.path.exists(filepath):
                if not model.load(filepath):
                    all_loaded = False
        
        return all_loaded

# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_predictor = None

def get_prediction_engine(db_path: str = 'ddospot.db', model_dir: str = 'models') -> PredictionEngine:
    """Get singleton prediction engine"""
    global _predictor
    
    if _predictor is None:
        _predictor = PredictionEngine(db_path, model_dir)
    
    return _predictor
