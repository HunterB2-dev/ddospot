"""
Training Pipeline for ML Models

Handles automated model retraining, cross-validation, hyperparameter tuning,
and performance monitoring.
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from sklearn.model_selection import cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb


logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """Training performance metrics."""
    timestamp: str
    model_name: str
    fold: int
    train_score: float
    val_score: float
    test_score: Optional[float] = None
    training_time_ms: float = 0.0
    best_params: Optional[Dict[str, Any]] = None
    feature_count: int = 0
    samples_count: int = 0


@dataclass
class TrainingJob:
    """Scheduled training job record."""
    job_id: str
    model_name: str
    scheduled_time: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    metrics: Optional[List[TrainingMetrics]] = None
    error_message: Optional[str] = None


class TrainingPipeline:
    """
    Automated training pipeline for ML models.
    
    Features:
    - Cross-validation for robust model evaluation
    - Hyperparameter tuning via grid search
    - Automatic model selection based on performance
    - Training history persistence
    - Performance metrics tracking
    """
    
    def __init__(self, cv_folds: int = 5, test_size: float = 0.2):
        """
        Initialize training pipeline.
        
        Args:
            cv_folds: Number of cross-validation folds
            test_size: Fraction of data reserved for testing
        """
        self.cv_folds = cv_folds
        self.test_size = test_size
        self.training_history: List[TrainingJob] = []
        self._initialize_db()
        
    def _initialize_db(self) -> None:
        """Initialize database tables for training history."""
        db = sqlite3.connect('ddospot.db')
        cursor = db.cursor()
        
        # Training history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_training_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                model_name TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                status TEXT NOT NULL,
                metrics TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Model versions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                version INTEGER NOT NULL,
                training_job_id TEXT NOT NULL,
                cv_score_mean REAL NOT NULL,
                cv_score_std REAL NOT NULL,
                best_params TEXT,
                model_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_name, version)
            )
        ''')
        
        db.commit()
        cursor.close()
    
    def _split_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[
        np.ndarray, np.ndarray, np.ndarray, np.ndarray
    ]:
        """
        Split data into train and test sets.
        
        Args:
            X: Feature matrix
            y: Target labels
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        split_idx = int(len(X) * (1 - self.test_size))
        
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        return X_train, X_test, y_train, y_test
    
    def cross_validate(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        scoring: str = "accuracy"
    ) -> Tuple[float, float, List[float]]:
        """
        Perform k-fold cross-validation.
        
        Args:
            model: Sklearn-compatible model
            X: Feature matrix
            y: Target labels
            scoring: Scoring metric
            
        Returns:
            Tuple of (mean_score, std_score, fold_scores)
        """
        cv = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=42)
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring, n_jobs=-1)
        
        return float(scores.mean()), float(scores.std()), scores.tolist()
    
    def hyperparameter_tuning(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: Dict[str, List[Any]],
        scoring: str = "accuracy"
    ) -> Tuple[Dict[str, Any], float]:
        """
        Perform grid search for hyperparameter tuning.
        
        Args:
            model: Sklearn-compatible model
            X: Feature matrix
            y: Target labels
            param_grid: Parameter grid for grid search
            scoring: Scoring metric
            
        Returns:
            Tuple of (best_params, best_score)
        """
        cv = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=42)
        
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=cv,
            scoring=scoring,
            n_jobs=-1,
            verbose=0
        )
        
        grid_search.fit(X, y)
        
        return grid_search.best_params_, float(grid_search.best_score_)
    
    def train_xgboost(
        self,
        X: np.ndarray,
        y: np.ndarray,
        hyperparams: Optional[Dict[str, Any]] = None,
        perform_tuning: bool = False
    ) -> Tuple[xgb.XGBClassifier, List[TrainingMetrics]]:
        """
        Train XGBoost model with cross-validation.
        
        Args:
            X: Feature matrix
            y: Target labels
            hyperparams: Custom hyperparameters (optional)
            perform_tuning: Whether to perform hyperparameter tuning
            
        Returns:
            Tuple of (trained_model, metrics_list)
        """
        metrics_list = []
        
        if hyperparams is None:
            hyperparams = {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42
            }
        
        if perform_tuning:
            param_grid = {
                'n_estimators': [100, 150],
                'max_depth': [4, 6, 8],
                'learning_rate': [0.01, 0.05, 0.1]
            }
            
            base_model = xgb.XGBClassifier(**hyperparams)
            best_params, best_score = self.hyperparameter_tuning(
                base_model, X, y, param_grid
            )
            hyperparams.update(best_params)
            logger.info(f"XGBoost best params: {best_params}, score: {best_score:.4f}")
        
        model = xgb.XGBClassifier(**hyperparams)
        cv_mean, cv_std, fold_scores = self.cross_validate(model, X, y)
        
        # Train final model on all data
        start_time = time.time()
        model.fit(X, y)
        training_time = (time.time() - start_time) * 1000
        
        for fold_idx, fold_score in enumerate(fold_scores):
            metrics = TrainingMetrics(
                timestamp=datetime.now().isoformat(),
                model_name="xgboost",
                fold=fold_idx,
                train_score=fold_score,
                val_score=cv_mean,
                training_time_ms=training_time,
                best_params=hyperparams,
                feature_count=X.shape[1],
                samples_count=X.shape[0]
            )
            metrics_list.append(metrics)
        
        logger.info(f"XGBoost CV - Mean: {cv_mean:.4f}, Std: {cv_std:.4f}")
        return model, metrics_list
    
    def train_lightgbm(
        self,
        X: np.ndarray,
        y: np.ndarray,
        hyperparams: Optional[Dict[str, Any]] = None,
        perform_tuning: bool = False
    ) -> Tuple[lgb.LGBMClassifier, List[TrainingMetrics]]:
        """
        Train LightGBM model with cross-validation.
        
        Args:
            X: Feature matrix
            y: Target labels
            hyperparams: Custom hyperparameters (optional)
            perform_tuning: Whether to perform hyperparameter tuning
            
        Returns:
            Tuple of (trained_model, metrics_list)
        """
        metrics_list = []
        
        if hyperparams is None:
            hyperparams = {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42,
                'verbose': -1
            }
        
        if perform_tuning:
            param_grid = {
                'n_estimators': [100, 150],
                'max_depth': [4, 6, 8],
                'learning_rate': [0.01, 0.05, 0.1]
            }
            
            base_model = lgb.LGBMClassifier(**hyperparams)
            best_params, best_score = self.hyperparameter_tuning(
                base_model, X, y, param_grid
            )
            hyperparams.update(best_params)
            logger.info(f"LightGBM best params: {best_params}, score: {best_score:.4f}")
        
        model = lgb.LGBMClassifier(**hyperparams)
        cv_mean, cv_std, fold_scores = self.cross_validate(model, X, y)
        
        # Train final model on all data
        start_time = time.time()
        model.fit(X, y)
        training_time = (time.time() - start_time) * 1000
        
        for fold_idx, fold_score in enumerate(fold_scores):
            metrics = TrainingMetrics(
                timestamp=datetime.now().isoformat(),
                model_name="lightgbm",
                fold=fold_idx,
                train_score=fold_score,
                val_score=cv_mean,
                training_time_ms=training_time,
                best_params=hyperparams,
                feature_count=X.shape[1],
                samples_count=X.shape[0]
            )
            metrics_list.append(metrics)
        
        logger.info(f"LightGBM CV - Mean: {cv_mean:.4f}, Std: {cv_std:.4f}")
        return model, metrics_list
    
    def store_training_job(self, job: TrainingJob) -> bool:
        """
        Store training job record in database.
        
        Args:
            job: Training job record
            
        Returns:
            True if successful
        """
        try:
            db = sqlite3.connect('ddospot.db')
            cursor = db.cursor()
            
            metrics_json = json.dumps([asdict(m) for m in job.metrics]) if job.metrics else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO ml_training_history
                (job_id, model_name, scheduled_time, start_time, end_time, status, metrics, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.job_id,
                job.model_name,
                job.scheduled_time,
                job.start_time,
                job.end_time,
                job.status,
                metrics_json,
                job.error_message
            ))
            
            db.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error storing training job: {e}")
            return False
    
    def get_training_history(self, model_name: Optional[str] = None, limit: int = 10) -> List[TrainingJob]:
        """
        Retrieve training history from database.
        
        Args:
            model_name: Filter by model name (optional)
            limit: Maximum number of records to retrieve
            
        Returns:
            List of training jobs
        """
        try:
            db = sqlite3.connect('ddospot.db')
            cursor = db.cursor()
            
            if model_name:
                cursor.execute('''
                    SELECT job_id, model_name, scheduled_time, start_time, end_time, status, metrics, error_message
                    FROM ml_training_history
                    WHERE model_name = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (model_name, limit))
            else:
                cursor.execute('''
                    SELECT job_id, model_name, scheduled_time, start_time, end_time, status, metrics, error_message
                    FROM ml_training_history
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            jobs = []
            for row in cursor.fetchall():
                metrics = None
                if row[6]:  # metrics field
                    metrics = [TrainingMetrics(**m) for m in json.loads(row[6])]
                
                job = TrainingJob(
                    job_id=row[0],
                    model_name=row[1],
                    scheduled_time=row[2],
                    start_time=row[3],
                    end_time=row[4],
                    status=row[5],
                    metrics=metrics,
                    error_message=row[7]
                )
                jobs.append(job)
            
            cursor.close()
            return jobs
        except Exception as e:
            logger.error(f"Error retrieving training history: {e}")
            return []
    
    def get_model_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for all models.
        
        Returns:
            Dictionary with model performance stats
        """
        try:
            db = sqlite3.connect('ddospot.db')
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT model_name, 
                       COUNT(*) as training_runs,
                       AVG(cv_score_mean) as avg_cv_score,
                       MAX(cv_score_mean) as best_cv_score,
                       MIN(cv_score_mean) as worst_cv_score
                FROM ml_model_versions
                GROUP BY model_name
            ''')
            
            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = {
                    'training_runs': row[1],
                    'avg_cv_score': float(row[2]) if row[2] else 0.0,
                    'best_cv_score': float(row[3]) if row[3] else 0.0,
                    'worst_cv_score': float(row[4]) if row[4] else 0.0
                }
            
            cursor.close()
            return stats
        except Exception as e:
            logger.error(f"Error getting model performance stats: {e}")
            return {}


# Singleton instance
_training_pipeline_instance: Optional[TrainingPipeline] = None


def get_training_pipeline() -> TrainingPipeline:
    """Get or create training pipeline singleton."""
    global _training_pipeline_instance
    if _training_pipeline_instance is None:
        _training_pipeline_instance = TrainingPipeline()
    return _training_pipeline_instance
