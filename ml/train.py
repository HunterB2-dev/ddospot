"""
Training pipeline for attack classification model.
Generates synthetic and real training data from honeypot events.
"""

import sys
import logging
from pathlib import Path
from typing import List, Tuple, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import honeypot modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.database import HoneypotDatabase
from ml.features import FeatureExtractor
from ml.model import get_model

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


def generate_synthetic_training_data(num_samples: int = 100) -> Tuple[List[List[float]], List[int], List[str]]:
    """
    Generate synthetic training data for model pre-training.
    
    Returns:
        (features_list, labels_list, feature_names)
    """
    if not NUMPY_AVAILABLE:
        logger.warning('NumPy not available, cannot generate synthetic data')
        return [], [], []
    
    import numpy as np
    
    logger.info(f'Generating {num_samples} synthetic training samples...')
    
    extractor = FeatureExtractor()
    feature_names = extractor.get_feature_names()
    
    X = []
    y = []
    
    # Attack type labels:
    # 0: volumetric, 1: multi_protocol, 2: amplification, 3: sustained, 4: normal
    
    for i in range(num_samples):
        attack_type = i % 5  # Cycle through attack types
        
        # Generate feature values based on attack type
        features = []
        
        if attack_type == 0:  # Volumetric
            event_count = np.random.randint(1000, 10000)
            events_per_sec = np.random.uniform(50, 200)
            protocol_div = np.random.randint(1, 3)
            features = [
                event_count,  # event_count
                np.random.randint(1, 50),  # unique_ips
                protocol_div,  # protocol_diversity
                np.random.uniform(0.3, 0.8),  # dominant_protocol_ratio
                event_count / events_per_sec,  # time_span_seconds
                events_per_sec,  # events_per_second
                np.random.uniform(100, 500),  # avg_payload_size
                np.random.uniform(500, 2000),  # max_payload_size
                np.random.uniform(50, 200),  # min_payload_size
                np.random.uniform(1000, 5000),  # payload_variance
                np.random.randint(1, 5),  # port_diversity
                np.random.uniform(1, 5),  # ports_per_ip_avg
                1, 0, 0, 0,  # has_high_rate, amplification, multi_protocol, port_scanning
                np.random.uniform(0.7, 1.0),  # http_ratio
                np.random.uniform(0, 0.1),  # dns_ratio
                np.random.uniform(0, 0.1),  # ssdp_ratio
                np.random.uniform(0, 0.1),  # ntp_ratio
            ]
        
        elif attack_type == 1:  # Multi-protocol
            features = [
                np.random.randint(500, 3000),  # event_count
                np.random.randint(3, 20),  # unique_ips
                np.random.randint(3, 6),  # protocol_diversity
                np.random.uniform(0.2, 0.4),  # dominant_protocol_ratio
                np.random.uniform(60, 300),  # time_span_seconds
                np.random.uniform(5, 30),  # events_per_second
                np.random.uniform(200, 800),  # avg_payload_size
                np.random.uniform(1000, 3000),  # max_payload_size
                np.random.uniform(50, 300),  # min_payload_size
                np.random.uniform(2000, 8000),  # payload_variance
                np.random.randint(5, 15),  # port_diversity
                np.random.uniform(5, 15),  # ports_per_ip_avg
                np.random.randint(0, 1), 0, 1, 0,  # flags
                np.random.uniform(0.2, 0.4),  # http_ratio
                np.random.uniform(0.2, 0.4),  # dns_ratio
                np.random.uniform(0.1, 0.3),  # ssdp_ratio
                np.random.uniform(0.1, 0.3),  # ntp_ratio
            ]
        
        elif attack_type == 2:  # Amplification
            features = [
                np.random.randint(500, 5000),  # event_count
                np.random.randint(5, 30),  # unique_ips
                np.random.randint(2, 4),  # protocol_diversity
                np.random.uniform(0.6, 0.9),  # dominant_protocol_ratio
                np.random.uniform(30, 180),  # time_span_seconds
                np.random.uniform(10, 50),  # events_per_second
                np.random.uniform(3000, 8000),  # avg_payload_size (large!)
                np.random.uniform(8000, 15000),  # max_payload_size
                np.random.uniform(1000, 5000),  # min_payload_size
                np.random.uniform(5000, 15000),  # payload_variance
                np.random.randint(3, 8),  # port_diversity
                np.random.uniform(3, 10),  # ports_per_ip_avg
                np.random.randint(0, 1), 1, 0, 0,  # has_high_rate, amplification flag
                np.random.uniform(0.1, 0.3),  # http_ratio
                np.random.uniform(0.2, 0.4),  # dns_ratio
                np.random.uniform(0.1, 0.3),  # ssdp_ratio
                np.random.uniform(0.2, 0.4),  # ntp_ratio
            ]
        
        elif attack_type == 3:  # Sustained
            features = [
                np.random.randint(5000, 20000),  # event_count (very high!)
                np.random.randint(10, 100),  # unique_ips
                np.random.randint(2, 5),  # protocol_diversity
                np.random.uniform(0.4, 0.7),  # dominant_protocol_ratio
                np.random.uniform(600, 3600),  # time_span_seconds (long!)
                np.random.uniform(5, 30),  # events_per_second
                np.random.uniform(200, 1000),  # avg_payload_size
                np.random.uniform(1000, 3000),  # max_payload_size
                np.random.uniform(50, 300),  # min_payload_size
                np.random.uniform(2000, 8000),  # payload_variance
                np.random.randint(5, 20),  # port_diversity
                np.random.uniform(5, 20),  # ports_per_ip_avg
                0, 0, 0, 0,  # flags
                np.random.uniform(0.2, 0.5),  # http_ratio
                np.random.uniform(0.1, 0.3),  # dns_ratio
                np.random.uniform(0.1, 0.3),  # ssdp_ratio
                np.random.uniform(0.1, 0.3),  # ntp_ratio
            ]
        
        else:  # Normal (label 4)
            features = [
                np.random.randint(1, 50),  # event_count (low)
                np.random.randint(1, 5),  # unique_ips
                1,  # protocol_diversity
                1.0,  # dominant_protocol_ratio
                np.random.uniform(1, 30),  # time_span_seconds
                np.random.uniform(0.1, 2),  # events_per_second (low)
                np.random.uniform(50, 200),  # avg_payload_size (small)
                np.random.uniform(100, 500),  # max_payload_size
                np.random.uniform(10, 100),  # min_payload_size
                np.random.uniform(100, 1000),  # payload_variance
                1,  # port_diversity (single port)
                1.0,  # ports_per_ip_avg
                0, 0, 0, 0,  # flags
                1.0,  # http_ratio (single protocol)
                0, 0, 0,  # other protocols
            ]
        
        X.append(features)
        y.append(attack_type)
    
    logger.info(f'Generated {len(X)} synthetic samples with {len(feature_names)} features')
    return X, y, feature_names


def train_from_database(db_path: str = 'honeypot.db', use_synthetic: bool = True) -> Dict:
    """
    Train model using data from honeypot database.
    
    Args:
        db_path: Path to honeypot database
        use_synthetic: Whether to use synthetic data for initial training
    
    Returns:
        Training metrics
    """
    logger.info('Starting model training...')
    
    model = get_model()
    extractor = FeatureExtractor()
    feature_names = extractor.get_feature_names()
    
    X_train = []
    y_train = []
    
    # Start with synthetic data for quick training
    if use_synthetic:
        X_synthetic, y_synthetic, _ = generate_synthetic_training_data(100)
        X_train.extend(X_synthetic)
        y_train.extend(y_synthetic)
    
    # Try to load real data from database
    try:
        db = HoneypotDatabase(db_path)
        
        # Get all events
        cursor = db.conn.cursor()
        cursor.execute('SELECT id, source_ip, port, protocol, payload_size, timestamp FROM events LIMIT 10000')
        events = [dict(row) for row in cursor.fetchall()]
        
        if events:
            logger.info(f'Loaded {len(events)} events from database')
            
            # Group events by IP
            ip_events = {}
            for event in events:
                ip = event.get('source_ip', '')
                if ip not in ip_events:
                    ip_events[ip] = []
                ip_events[ip].append(event)
            
            # Extract features for each IP's events
            for ip, ip_event_list in ip_events.items():
                features_dict = extractor.extract_from_events(ip_event_list)
                feature_vector = [features_dict.get(name, 0) for name in feature_names]
                X_train.append(feature_vector)
                
                # Simple labeling based on patterns
                if features_dict.get('events_per_second', 0) > 50:
                    y_train.append(0)  # volumetric
                elif features_dict.get('protocol_diversity', 0) >= 3:
                    y_train.append(1)  # multi_protocol
                elif features_dict.get('max_payload_size', 0) > 5000:
                    y_train.append(2)  # amplification
                elif features_dict.get('event_count', 0) > 1000:
                    y_train.append(3)  # sustained
                else:
                    y_train.append(4)  # normal
        
        db.conn.close()
    
    except Exception as e:
        logger.warning(f'Could not load database: {e}')
    
    if not X_train:
        logger.error('No training data available')
        return {'error': 'No training data'}
    
    logger.info(f'Training on {len(X_train)} samples')
    
    # Train model
    metrics = model.train(X_train, y_train, feature_names)
    
    logger.info(f'Training complete: {metrics}')
    return metrics


def train():
    """Main training function"""
    return train_from_database()


if __name__ == '__main__':
    metrics = train()
    print('\n=== Training Results ===')
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f'{key}: {value:.4f}')
        else:
            print(f'{key}: {value}')
