"""
Machine Learning model for attack classification and prediction.
Trained on historical attack patterns to predict attack types and intensity.
"""

import pickle
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class AttackClassifier:
    """
    ML classifier for attack pattern recognition.
    Predicts attack types: volumetric, multi_protocol, amplification, sustained
    """
    
    ATTACK_TYPES = {
        'volumetric': 0,
        'multi_protocol': 1,
        'amplification': 2,
        'sustained': 3,
        'normal': 4
    }
    
    def __init__(self, model_path: str = 'ml/attack_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.training_history = {
            'accuracy': [],
            'precision': [],
            'recall': [],
            'f1': [],
            'loss': []
        }
        self.is_trained = False
        self._load_model()
    
    def _load_model(self):
        """Load trained model from disk if available"""
        try:
            if Path(self.model_path).exists():
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data.get('model')
                    self.scaler = data.get('scaler')
                    self.feature_names = data.get('feature_names', [])
                    self.is_trained = True
                    logger.info(f'Loaded trained model from {self.model_path}')
        except Exception as e:
            logger.warning(f'Could not load model: {e}')
    
    def train(self, X_train: List[List[float]], y_train: List[int], 
              feature_names: List[str], X_test: Optional[List] = None, 
              y_test: Optional[List] = None) -> Dict:
        """
        Train the attack classification model.
        
        Args:
            X_train: Training features (list of feature vectors)
            y_train: Training labels (attack type indices)
            feature_names: Names of features
            X_test: Test features (optional)
            y_test: Test labels (optional)
        
        Returns:
            Training metrics dictionary
        """
        if not SKLEARN_AVAILABLE:
            logger.warning('scikit-learn not available, using dummy model')
            self.is_trained = True
            return {'status': 'sklearn_unavailable'}
        
        try:
            self.feature_names = feature_names
            
            # Normalize features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X_train)
            
            # Train Random Forest
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_scaled, y_train)
            self.is_trained = True
            
            # Evaluate
            metrics = {}
            y_pred = self.model.predict(X_scaled)
            metrics['train_accuracy'] = float(accuracy_score(y_train, y_pred))
            metrics['train_precision'] = float(precision_score(y_train, y_pred, average='weighted', zero_division=0))
            metrics['train_recall'] = float(recall_score(y_train, y_pred, average='weighted', zero_division=0))
            metrics['train_f1'] = float(f1_score(y_train, y_pred, average='weighted', zero_division=0))
            
            # Test metrics
            if X_test is not None and y_test is not None:
                X_test_scaled = self.scaler.transform(X_test)
                y_pred_test = self.model.predict(X_test_scaled)
                metrics['test_accuracy'] = float(accuracy_score(y_test, y_pred_test))
                metrics['test_precision'] = float(precision_score(y_test, y_pred_test, average='weighted', zero_division=0))
                metrics['test_recall'] = float(recall_score(y_test, y_pred_test, average='weighted', zero_division=0))
                metrics['test_f1'] = float(f1_score(y_test, y_pred_test, average='weighted', zero_division=0))
            
            metrics['samples_trained'] = len(X_train)
            metrics['timestamp'] = datetime.now().isoformat()
            
            # Save model
            self._save_model()
            
            logger.info(f'Model trained: accuracy={metrics.get("train_accuracy", 0):.3f}')
            return metrics
            
        except Exception as e:
            logger.error(f'Training failed: {e}')
            return {'error': str(e)}
    
    def predict(self, features: List[float]) -> Tuple[str, float]:
        """
        Predict attack type for given features.
        
        Args:
            features: Feature vector
        
        Returns:
            (attack_type, confidence)
        """
        if not self.is_trained or self.model is None:
            return 'normal', 0.0
        
        try:
            if self.scaler and len(features) == len(self.feature_names):
                X_scaled = self.scaler.transform([features])
                prediction = self.model.predict(X_scaled)[0]
                probabilities = self.model.predict_proba(X_scaled)[0]
                confidence = float(max(probabilities))
                
                # Get attack type name
                attack_type = [k for k, v in self.ATTACK_TYPES.items() if v == prediction][0]
                return attack_type, confidence
        except Exception as e:
            logger.debug(f'Prediction error: {e}')
        
        return 'normal', 0.0
    
    def predict_batch(self, feature_list: List[List[float]]) -> List[Tuple[str, float]]:
        """Predict for multiple feature vectors"""
        return [self.predict(features) for features in feature_list]
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get importance scores for each feature"""
        if not self.is_trained or self.model is None:
            return {}
        
        try:
            importances = self.model.feature_importances_
            return {
                name: float(importance)
                for name, importance in zip(self.feature_names, importances)
            }
        except Exception as e:
            logger.debug(f'Could not get feature importance: {e}')
            return {}
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'feature_names': self.feature_names
                }, f)
            logger.info(f'Model saved to {self.model_path}')
        except Exception as e:
            logger.error(f'Failed to save model: {e}')
    
    def get_stats(self) -> Dict:
        """Get model statistics"""
        return {
            'is_trained': self.is_trained,
            'model_path': self.model_path,
            'features_count': len(self.feature_names),
            'feature_importance': self.get_feature_importance(),
            'attack_types': list(self.ATTACK_TYPES.keys())
        }


class DummyModel:
    """Fallback model when sklearn is not available"""
    
    def predict(self, features):
        return False


# Global model instance
_model_instance = None


def get_model() -> AttackClassifier:
    """Get global model instance (singleton)"""
    global _model_instance
    if _model_instance is None:
        _model_instance = AttackClassifier()
    return _model_instance