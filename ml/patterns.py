"""
Pattern Learning System for DDoS Attack Detection
Uses K-means clustering to discover and learn attack patterns
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import sqlite3

try:
    from sklearn.cluster import KMeans  # type: ignore
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class AttackPattern:
    """Discovered attack pattern"""
    pattern_id: str
    cluster_center: List[float]
    cluster_label: int
    samples_in_cluster: int
    pattern_signature: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    first_seen: float
    last_seen: float
    detection_count: int
    confidence: float  # 0-1, how confident we are this is a pattern
    characteristics: Dict  # Key pattern characteristics
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'pattern_id': self.pattern_id,
            'cluster_center': self.cluster_center,
            'cluster_label': self.cluster_label,
            'samples_in_cluster': self.samples_in_cluster,
            'pattern_signature': self.pattern_signature,
            'severity': self.severity,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'detection_count': self.detection_count,
            'confidence': float(self.confidence),
            'characteristics': self.characteristics
        }

# ============================================================================
# PATTERN LEARNING ENGINE
# ============================================================================

class PatternLearningEngine:
    """
    K-means based attack pattern discovery and learning
    """
    
    def __init__(self, 
                 n_clusters: int = 10,
                 min_cluster_size: int = 5,
                 db_path: str = 'ddospot.db'):
        """
        Initialize pattern learning engine
        
        Args:
            n_clusters: Number of clusters for K-means
            min_cluster_size: Minimum samples per cluster to be valid pattern
            db_path: Path to database for persistence
        """
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn required for PatternLearningEngine")
        
        self.n_clusters = n_clusters
        self.min_cluster_size = min_cluster_size
        self.db_path = db_path
        self.kmeans = KMeans(  # type: ignore
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )
        self.is_fitted = False
        self.patterns = {}  # cluster_label -> AttackPattern
        self.feature_names = []
        self.cluster_counts = {}
        
        self._init_database()
        logger.info('[ML] Pattern Learning Engine initialized (clusters={0})'.format(n_clusters))
    
    def _init_database(self) -> None:
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Attack patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_patterns (
                    id INTEGER PRIMARY KEY,
                    pattern_id TEXT UNIQUE NOT NULL,
                    cluster_label INTEGER NOT NULL,
                    cluster_center TEXT NOT NULL,
                    samples_in_cluster INTEGER NOT NULL,
                    pattern_signature TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    detection_count INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    characteristics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ml_patterns_severity ON ml_patterns(severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ml_patterns_cluster ON ml_patterns(cluster_label)')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error('[ML] Database initialization error: {0}'.format(e))
    
    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None, feature_names: Optional[List[str]] = None) -> None:
        """
        Fit K-means clustering on attack data
        
        Args:
            X: Feature data (N, features)
            y: Optional labels for attack samples (for validation)
            feature_names: Optional feature names
        """
        if X.shape[0] == 0:
            logger.warning('[ML] No data to fit pattern learner')
            return
        
        # Fit K-means
        self.kmeans.fit(X)
        self.is_fitted = True
        self.feature_names = feature_names or [f'feature_{i}' for i in range(X.shape[1])]
        
        # Get cluster assignments
        labels = self.kmeans.labels_
        
        # Analyze clusters
        for cluster_id in range(self.n_clusters):
            mask = labels == cluster_id
            cluster_samples = X[mask]
            
            if len(cluster_samples) >= self.min_cluster_size:
                # Create pattern for this cluster
                pattern = self._create_pattern(
                    cluster_id,
                    cluster_samples,
                    self.kmeans.cluster_centers_[cluster_id]
                )
                self.patterns[cluster_id] = pattern
                self.cluster_counts[cluster_id] = len(cluster_samples)
                
                logger.info('[ML] Pattern {0} discovered with {1} samples'.format(
                    cluster_id, len(cluster_samples)
                ))
        
        logger.info('[ML] Pattern learning fitted on {0} samples, {1} patterns'.format(
            X.shape[0], len(self.patterns)
        ))
    
    def _create_pattern(self, 
                       cluster_id: int, 
                       cluster_samples: np.ndarray,
                       cluster_center: np.ndarray) -> AttackPattern:
        """Create AttackPattern from cluster data"""
        # Generate pattern signature
        pattern_sig = self._generate_signature(cluster_center)
        
        # Extract characteristics
        characteristics = self._extract_characteristics(cluster_samples, self.feature_names)
        
        # Determine severity based on characteristics
        severity = self._determine_severity(characteristics)
        
        # Calculate confidence
        distances = np.linalg.norm(cluster_samples - cluster_center, axis=1)
        avg_distance = np.mean(distances)
        max_distance = np.max(distances)
        
        # Confidence based on cluster cohesion (lower distance = higher confidence)
        confidence = 1.0 - min(avg_distance / max(max_distance, 1.0), 1.0)
        
        pattern = AttackPattern(
            pattern_id='pattern_{0}_{1}'.format(cluster_id, int(datetime.now().timestamp())),
            cluster_center=cluster_center.tolist(),
            cluster_label=cluster_id,
            samples_in_cluster=len(cluster_samples),
            pattern_signature=pattern_sig,
            severity=severity,
            first_seen=datetime.now().timestamp(),
            last_seen=datetime.now().timestamp(),
            detection_count=1,
            confidence=float(confidence),
            characteristics=characteristics
        )
        
        return pattern
    
    def _generate_signature(self, cluster_center: np.ndarray) -> str:
        """Generate unique signature for pattern"""
        # Use cluster center hash
        import hashlib
        center_str = ','.join([f'{x:.2f}' for x in cluster_center])
        signature = hashlib.md5(center_str.encode()).hexdigest()[:16]
        return signature
    
    def _extract_characteristics(self, cluster_samples: np.ndarray, 
                                feature_names: List[str]) -> Dict:
        """Extract key characteristics from cluster"""
        characteristics = {}
        
        for i, name in enumerate(feature_names[:5]):  # Top 5 features
            values = cluster_samples[:, i]
            characteristics[name] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values))
            }
        
        return characteristics
    
    def _determine_severity(self, characteristics: Dict) -> str:
        """Determine attack severity from characteristics"""
        # Simple heuristic: look at packet rate and packet count
        severity_score = 0
        
        for feature_name, stats in characteristics.items():
            if 'packet' in feature_name.lower():
                if stats['mean'] > 100:
                    severity_score += 2
                elif stats['mean'] > 50:
                    severity_score += 1
            
            if 'rate' in feature_name.lower():
                if stats['mean'] > 500:
                    severity_score += 2
                elif stats['mean'] > 100:
                    severity_score += 1
        
        if severity_score >= 4:
            return 'critical'
        elif severity_score >= 3:
            return 'high'
        elif severity_score >= 1:
            return 'medium'
        else:
            return 'low'
    
    def predict_pattern(self, sample: np.ndarray) -> Tuple[Optional[AttackPattern], float]:
        """
        Predict which pattern a sample belongs to
        
        Args:
            sample: Feature vector (28,)
        
        Returns:
            Tuple of (AttackPattern or None, distance to cluster center)
        """
        if not self.is_fitted:
            logger.warning('[ML] Pattern learner not fitted')
            return None, float('inf')
        
        if sample.ndim == 1:
            sample = sample.reshape(1, -1)
        
        # Predict cluster
        cluster_id = self.kmeans.predict(sample)[0]
        
        # Get distance to cluster center
        distance = np.linalg.norm(sample - self.kmeans.cluster_centers_[cluster_id])
        
        # Return pattern if exists
        pattern = self.patterns.get(cluster_id)
        
        if pattern:
            # Update detection info
            pattern.detection_count += 1
            pattern.last_seen = datetime.now().timestamp()
        
        return pattern, float(distance)
    
    def save_patterns(self) -> bool:
        """Save patterns to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for cluster_id, pattern in self.patterns.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO ml_patterns
                    (pattern_id, cluster_label, cluster_center, samples_in_cluster,
                     pattern_signature, severity, first_seen, last_seen,
                     detection_count, confidence, characteristics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pattern.pattern_id,
                    pattern.cluster_label,
                    json.dumps(pattern.cluster_center),
                    pattern.samples_in_cluster,
                    pattern.pattern_signature,
                    pattern.severity,
                    pattern.first_seen,
                    pattern.last_seen,
                    pattern.detection_count,
                    pattern.confidence,
                    json.dumps(pattern.characteristics)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info('[ML] Saved {0} patterns to database'.format(len(self.patterns)))
            return True
        except Exception as e:
            logger.error('[ML] Error saving patterns: {0}'.format(e))
            return False
    
    def load_patterns(self) -> bool:
        """Load patterns from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM ml_patterns ORDER BY cluster_label')
            rows = cursor.fetchall()
            
            self.patterns.clear()
            
            for row in rows:
                # Skip ID column (first element)
                pattern_id, cluster_label, cluster_center_json, samples, sig, severity, \
                first_seen, last_seen, detection_count, confidence, char_json = row[1:12]
                
                pattern = AttackPattern(
                    pattern_id=pattern_id,
                    cluster_center=json.loads(cluster_center_json),
                    cluster_label=cluster_label,
                    samples_in_cluster=samples,
                    pattern_signature=sig,
                    severity=severity,
                    first_seen=first_seen,
                    last_seen=last_seen,
                    detection_count=detection_count,
                    confidence=confidence,
                    characteristics=json.loads(char_json) if char_json else {}
                )
                
                self.patterns[cluster_label] = pattern
            
            conn.close()
            
            logger.info('[ML] Loaded {0} patterns from database'.format(len(self.patterns)))
            return True
        except Exception as e:
            logger.error('[ML] Error loading patterns: {0}'.format(e))
            return False
    
    def get_patterns(self, min_severity: Optional[str] = None) -> List[AttackPattern]:
        """Get all known patterns, optionally filtered by severity"""
        patterns = list(self.patterns.values())
        
        if min_severity:
            severity_levels = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
            min_level = severity_levels.get(min_severity, 0)
            
            patterns = [
                p for p in patterns
                if severity_levels.get(p.severity, 0) >= min_level
            ]
        
        return sorted(patterns, key=lambda p: -p.detection_count)
    
    def get_pattern_stats(self) -> Dict:
        """Get pattern statistics"""
        if not self.patterns:
            return {
                'total_patterns': 0,
                'critical_patterns': 0,
                'high_patterns': 0,
                'medium_patterns': 0,
                'low_patterns': 0,
                'total_detections': 0,
                'avg_confidence': 0.0
            }
        
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        total_detections = 0
        total_confidence = 0
        
        for pattern in self.patterns.values():
            severity_counts[pattern.severity] += 1
            total_detections += pattern.detection_count
            total_confidence += pattern.confidence
        
        return {
            'total_patterns': len(self.patterns),
            'critical_patterns': severity_counts['critical'],
            'high_patterns': severity_counts['high'],
            'medium_patterns': severity_counts['medium'],
            'low_patterns': severity_counts['low'],
            'total_detections': total_detections,
            'avg_confidence': total_confidence / len(self.patterns) if self.patterns else 0.0
        }

# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_pattern_engine = None

def get_pattern_engine(n_clusters: int = 10, 
                      min_cluster_size: int = 5,
                      db_path: str = 'ddospot.db') -> PatternLearningEngine:
    """Get singleton pattern learning engine"""
    global _pattern_engine
    
    if _pattern_engine is None:
        _pattern_engine = PatternLearningEngine(n_clusters, min_cluster_size, db_path)
    
    return _pattern_engine
