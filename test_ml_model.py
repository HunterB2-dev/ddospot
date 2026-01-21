#!/usr/bin/env python3
"""
Test script for ML model training and attack classification.
Demonstrates feature extraction, model training, and prediction.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ml.features import FeatureExtractor
from ml.train import train_from_database, generate_synthetic_training_data
from ml.model import get_model


def test_feature_extraction():
    """Test feature extraction from events"""
    print("\n" + "=" * 60)
    print("TEST 1: Feature Extraction")
    print("=" * 60)
    
    extractor = FeatureExtractor()
    
    # Create mock events
    events = [
        {
            'source_ip': '192.0.2.1',
            'protocol': 'HTTP',
            'payload_size': 500,
            'timestamp': 1000.0,
            'port': 80
        },
        {
            'source_ip': '192.0.2.1',
            'protocol': 'HTTP',
            'payload_size': 520,
            'timestamp': 1001.0,
            'port': 80
        },
        {
            'source_ip': '192.0.2.1',
            'protocol': 'DNS',
            'payload_size': 200,
            'timestamp': 1002.0,
            'port': 53
        },
        {
            'source_ip': '192.0.2.1',
            'protocol': 'SSDP',
            'payload_size': 5000,
            'timestamp': 1003.0,
            'port': 1900
        },
    ]
    
    features = extractor.extract_from_events(events)
    
    print(f"\n✓ Extracted {len(features)} features from {len(events)} events")
    print("\nTop features:")
    for key, value in list(features.items())[:10]:
        if isinstance(value, float):
            print(f"  {key:30} = {value:12.3f}")
        else:
            print(f"  {key:30} = {value}")


def test_synthetic_training():
    """Test synthetic data generation and model training"""
    print("\n" + "=" * 60)
    print("TEST 2: Synthetic Data & Model Training")
    print("=" * 60)
    
    # Generate synthetic data
    print("\nGenerating synthetic training data...")
    X, y, feature_names = generate_synthetic_training_data(200)
    
    if not X:
        print("⚠ Synthetic data generation failed (NumPy not installed)")
        return
    
    print(f"✓ Generated {len(X)} training samples with {len(feature_names)} features")
    
    # Show class distribution
    from collections import Counter
    class_names = {0: 'volumetric', 1: 'multi_protocol', 2: 'amplification', 3: 'sustained', 4: 'normal'}
    class_dist = Counter(y)
    print("\nClass distribution:")
    for class_id, count in sorted(class_dist.items()):
        print(f"  {class_names[class_id]:15} : {count:3d} samples")
    
    # Train model
    print("\nTraining model...")
    model = get_model()
    metrics = model.train(X, y, feature_names)
    
    if 'error' in metrics:
        print(f"⚠ Training error: {metrics.get('error')}")
        return
    
    print("\n✓ Model trained successfully")
    print("\nTraining metrics:")
    for key, value in metrics.items():
        if key not in ['timestamp']:
            if isinstance(value, float):
                print(f"  {key:25} = {value:.4f}")
            else:
                print(f"  {key:25} = {value}")


def test_prediction():
    """Test attack classification prediction"""
    print("\n" + "=" * 60)
    print("TEST 3: Attack Classification & Prediction")
    print("=" * 60)
    
    extractor = FeatureExtractor()
    model = get_model()
    feature_names = extractor.get_feature_names()
    
    # Create test cases
    test_cases = {
        'Volumetric Attack': {
            'event_count': 5000,
            'unique_ips': 20,
            'protocol_diversity': 1,
            'dominant_protocol_ratio': 0.95,
            'time_span_seconds': 30,
            'events_per_second': 150,
            'avg_payload_size': 200,
            'max_payload_size': 500,
            'min_payload_size': 100,
            'payload_variance': 500,
            'port_diversity': 1,
            'ports_per_ip_avg': 1,
            'has_high_rate': 1,
            'has_amplification': 0,
            'has_multi_protocol': 0,
            'has_port_scanning': 0,
            'http_ratio': 0.95,
            'dns_ratio': 0.05,
            'ssdp_ratio': 0,
            'ntp_ratio': 0,
        },
        'Multi-Protocol Attack': {
            'event_count': 1000,
            'unique_ips': 15,
            'protocol_diversity': 4,
            'dominant_protocol_ratio': 0.35,
            'time_span_seconds': 60,
            'events_per_second': 16,
            'avg_payload_size': 400,
            'max_payload_size': 1000,
            'min_payload_size': 100,
            'payload_variance': 3000,
            'port_diversity': 10,
            'ports_per_ip_avg': 8,
            'has_high_rate': 0,
            'has_amplification': 0,
            'has_multi_protocol': 1,
            'has_port_scanning': 0,
            'http_ratio': 0.25,
            'dns_ratio': 0.30,
            'ssdp_ratio': 0.25,
            'ntp_ratio': 0.20,
        },
        'Amplification Attack': {
            'event_count': 2000,
            'unique_ips': 25,
            'protocol_diversity': 2,
            'dominant_protocol_ratio': 0.8,
            'time_span_seconds': 45,
            'events_per_second': 45,
            'avg_payload_size': 6000,
            'max_payload_size': 10000,
            'min_payload_size': 4000,
            'payload_variance': 8000,
            'port_diversity': 3,
            'ports_per_ip_avg': 2,
            'has_high_rate': 0,
            'has_amplification': 1,
            'has_multi_protocol': 0,
            'has_port_scanning': 0,
            'http_ratio': 0.1,
            'dns_ratio': 0.40,
            'ssdp_ratio': 0.30,
            'ntp_ratio': 0.20,
        },
        'Sustained Attack': {
            'event_count': 8000,
            'unique_ips': 50,
            'protocol_diversity': 3,
            'dominant_protocol_ratio': 0.45,
            'time_span_seconds': 600,
            'events_per_second': 13,
            'avg_payload_size': 500,
            'max_payload_size': 1500,
            'min_payload_size': 200,
            'payload_variance': 4000,
            'port_diversity': 15,
            'ports_per_ip_avg': 12,
            'has_high_rate': 0,
            'has_amplification': 0,
            'has_multi_protocol': 0,
            'has_port_scanning': 0,
            'http_ratio': 0.30,
            'dns_ratio': 0.25,
            'ssdp_ratio': 0.20,
            'ntp_ratio': 0.25,
        },
        'Normal Traffic': {
            'event_count': 20,
            'unique_ips': 2,
            'protocol_diversity': 1,
            'dominant_protocol_ratio': 1.0,
            'time_span_seconds': 10,
            'events_per_second': 2,
            'avg_payload_size': 100,
            'max_payload_size': 150,
            'min_payload_size': 50,
            'payload_variance': 200,
            'port_diversity': 1,
            'ports_per_ip_avg': 1,
            'has_high_rate': 0,
            'has_amplification': 0,
            'has_multi_protocol': 0,
            'has_port_scanning': 0,
            'http_ratio': 1.0,
            'dns_ratio': 0,
            'ssdp_ratio': 0,
            'ntp_ratio': 0,
        }
    }
    
    print(f"\n✓ Testing predictions on {len(test_cases)} scenarios\n")
    
    for test_name, feature_dict in test_cases.items():
        # Convert feature dict to vector
        feature_vector = [feature_dict.get(name, 0) for name in feature_names]
        
        # Predict
        attack_type, confidence = model.predict(feature_vector)
        
        print(f"{test_name:25} -> {attack_type:15} (confidence: {confidence:.2%})")


def test_feature_importance():
    """Test feature importance analysis"""
    print("\n" + "=" * 60)
    print("TEST 4: Feature Importance Analysis")
    print("=" * 60)
    
    model = get_model()
    
    if not model.is_trained:
        print("\n⚠ Model not trained yet. Train model first.")
        return
    
    importance = model.get_feature_importance()
    
    if not importance:
        print("\n⚠ Could not get feature importance (model not available)")
        return
    
    print("\n✓ Top 10 most important features:\n")
    sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    for i, (feature, score) in enumerate(sorted_features[:10], 1):
        print(f"  {i:2}. {feature:30} : {score:.4f}")


def main():
    """Run all tests"""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  ML MODEL TESTING & TRAINING PIPELINE".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)
    
    test_feature_extraction()
    test_synthetic_training()
    test_prediction()
    test_feature_importance()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
✓ ML Model System Ready

Available Features:
  - Advanced feature extraction (20+ features)
  - Synthetic training data generation
  - Random Forest classifier training
  - Attack type classification (5 classes)
  - Feature importance analysis
  - Model persistence (pickle)
  
Attack Types Supported:
  1. Volumetric   - High rate attacks (floods)
  2. Multi-Protocol - Coordinated multi-protocol attacks
  3. Amplification - Large payload attacks (reflection)
  4. Sustained    - Long-duration attacks
  5. Normal       - Benign traffic
  
Next Steps:
  1. Train on real honeypot data: python3 ml/train.py
  2. Integrate into server: core/server.py
  3. Add to dashboard: dashboard.py
  4. Monitor predictions: Real-time attack classification
    """)
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
