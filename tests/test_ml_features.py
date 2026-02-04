"""
Comprehensive tests for ML feature engineering module
Tests feature extraction, normalization, and data handling
"""

import unittest
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.features import (
    FeatureExtractor, FeatureNormalizer, 
    PacketFeatures, TrafficFeatures,
    get_feature_extractor, get_feature_normalizer
)

# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def create_sample_packet(
    src_ip='192.168.1.1',
    dst_ip='10.0.0.1',
    protocol='TCP',
    packet_size=100,
    payload_size=50,
    flags='',
    timestamp=None
):
    """Create sample packet data"""
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    
    return {
        'timestamp': timestamp,
        'src_ip': src_ip,
        'dst_ip': dst_ip,
        'src_port': 12345,
        'dst_port': 80,
        'protocol': protocol,
        'packet_size': packet_size,
        'flags': flags,
        'payload_size': payload_size
    }

def create_ddos_traffic(count=100, protocol='TCP'):
    """Create DDoS-like traffic pattern"""
    packets = []
    base_time = datetime.now().timestamp()
    
    for i in range(count):
        packets.append({
            'timestamp': base_time + i * 0.01,  # 10ms apart
            'src_ip': f'203.0.113.{i % 255}',
            'dst_ip': '10.0.0.1',
            'src_port': 1024 + i,
            'dst_port': 80,
            'protocol': protocol,
            'packet_size': 64,
            'flags': 'SYN' if protocol == 'TCP' else '',
            'payload_size': 0
        })
    
    return packets

def create_normal_traffic(count=100):
    """Create normal traffic pattern"""
    packets = []
    base_time = datetime.now().timestamp()
    
    for i in range(count):
        packets.append({
            'timestamp': base_time + i * 0.05,  # 50ms apart
            'src_ip': '192.168.1.' + str(2 + i % 10),
            'dst_ip': '10.0.0.1',
            'src_port': 1024 + i,
            'dst_port': 80 if i % 2 == 0 else 443,
            'protocol': 'TCP',
            'packet_size': 1500,
            'flags': 'SYN' if i % 3 == 0 else 'ACK',
            'payload_size': 1000
        })
    
    return packets

# ============================================================================
# FEATURE EXTRACTION TESTS
# ============================================================================

class TestFeatureExtraction(unittest.TestCase):
    """Test basic feature extraction functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.extractor = FeatureExtractor(window_size=5)
    
    def test_packet_feature_extraction(self):
        """Test extracting features from a single packet"""
        packet = create_sample_packet()
        features = self.extractor.extract_packet_features(packet)
        
        self.assertIsInstance(features, PacketFeatures)
        self.assertEqual(features.src_ip, '192.168.1.1')
        self.assertEqual(features.protocol, 'TCP')
        self.assertEqual(features.packet_size, 100)
    
    def test_tcp_flag_parsing(self):
        """Test TCP flag parsing"""
        packet = create_sample_packet(flags='SYN')
        features = self.extractor.extract_packet_features(packet)
        
        self.assertTrue(features.is_syn)
        self.assertFalse(features.is_ack)
        
        packet2 = create_sample_packet(flags='ACK')
        features2 = self.extractor.extract_packet_features(packet2)
        
        self.assertTrue(features2.is_ack)
        self.assertFalse(features2.is_syn)
    
    def test_add_packet_to_buffer(self):
        """Test adding packets to buffer"""
        self.assertEqual(len(self.extractor.packet_buffer), 0)
        
        packet = create_sample_packet()
        self.extractor.add_packet(packet)
        
        self.assertEqual(len(self.extractor.packet_buffer), 1)
    
    def test_window_features_empty(self):
        """Test extracting features from empty window"""
        features = self.extractor.extract_window_features()
        
        self.assertIsNone(features)
    
    def test_window_features_single_packet(self):
        """Test extracting features from single packet"""
        packet = create_sample_packet()
        self.extractor.add_packet(packet)
        
        features = self.extractor.extract_window_features()
        
        self.assertIsNotNone(features)
        self.assertEqual(features.packet_count, 1)  # type: ignore
        self.assertEqual(features.byte_count, 100)  # type: ignore
        self.assertEqual(features.unique_src_ips, 1)  # type: ignore
    
    def test_window_features_multiple_packets(self):
        """Test extracting features from multiple packets"""
        packets = create_normal_traffic(count=50)
        
        for packet in packets:
            self.extractor.add_packet(packet)
        
        # Get the latest window (most packets will be in this window)
        window_start = min(p['timestamp'] for p in packets)
        features = self.extractor.extract_window_features(window_start)
        
        self.assertIsNotNone(features)
        self.assertGreaterEqual(features.packet_count, 1)  # type: ignore
        self.assertGreater(features.byte_count, 0)  # type: ignore
        self.assertGreater(features.unique_src_ips, 0)  # type: ignore
    
    def test_ddos_traffic_detection(self):
        """Test feature extraction on DDoS traffic"""
        packets = create_ddos_traffic(count=200)
        
        for packet in packets:
            self.extractor.add_packet(packet)
        
        window_start = min(p['timestamp'] for p in packets)
        features = self.extractor.extract_window_features(window_start)
        
        self.assertIsNotNone(features)
        self.assertGreater(features.packet_rate, 1)  # type: ignore  # Higher packet rate
        self.assertGreater(features.syn_count, 0)    # type: ignore  # Many SYN packets
    
    def test_feature_array_conversion(self):
        """Test converting features to numpy array"""
        packets = create_normal_traffic(count=50)
        
        for packet in packets:
            self.extractor.add_packet(packet)
        
        features = self.extractor.extract_window_features()
        array = features.to_array()  # type: ignore
        
        self.assertIsInstance(array, np.ndarray)
        self.assertEqual(len(array), 28)  # 28 features
        self.assertEqual(array.dtype, np.float32)
    
    def test_feature_names(self):
        """Test retrieving feature names"""
        names = self.extractor.get_feature_names()
        
        self.assertIsInstance(names, list)
        self.assertEqual(len(names), 28)
        self.assertIn('packet_count', names)
        self.assertIn('packet_rate', names)

# ============================================================================
# FEATURE NORMALIZATION TESTS
# ============================================================================

class TestFeatureNormalization(unittest.TestCase):
    """Test feature normalization functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.normalizer = FeatureNormalizer()
        # Create sample training data
        self.training_data = np.random.randn(100, 28) * 100 + 50
    
    def test_normalizer_initialization(self):
        """Test normalizer initializes correctly"""
        self.assertFalse(self.normalizer.is_fitted)
        self.assertIsNone(self.normalizer.feature_means)
        self.assertIsNone(self.normalizer.feature_stds)
    
    def test_fit_normalizer(self):
        """Test fitting normalizer on training data"""
        self.normalizer.fit(self.training_data)
        
        self.assertTrue(self.normalizer.is_fitted)
        self.assertIsNotNone(self.normalizer.feature_means)
        self.assertIsNotNone(self.normalizer.feature_stds)
        self.assertEqual(len(self.normalizer.feature_means), 28)  # type: ignore
    
    def test_transform_unfitted(self):
        """Test transform on unfitted normalizer returns data as-is"""
        data = np.random.randn(10, 28)
        result = self.normalizer.transform(data)
        
        np.testing.assert_array_equal(result, data)
    
    def test_transform_fitted(self):
        """Test transform on fitted normalizer"""
        self.normalizer.fit(self.training_data)
        result = self.normalizer.transform(self.training_data)
        
        # Check that result has been normalized
        self.assertAlmostEqual(np.mean(result), 0, places=1)
        self.assertAlmostEqual(np.std(result), 1, places=1)
    
    def test_fit_transform(self):
        """Test fit_transform in one operation"""
        result = self.normalizer.fit_transform(self.training_data)
        
        self.assertTrue(self.normalizer.is_fitted)
        self.assertAlmostEqual(np.mean(result), 0, places=1)
    
    def test_get_params(self):
        """Test retrieving normalizer parameters"""
        self.normalizer.fit(self.training_data)
        params = self.normalizer.get_params()
        
        self.assertIn('means', params)
        self.assertIn('stds', params)
        self.assertEqual(len(params['means']), 28)
        self.assertEqual(len(params['stds']), 28)
    
    def test_set_params(self):
        """Test setting normalizer parameters"""
        self.normalizer.fit(self.training_data)
        params = self.normalizer.get_params()
        
        # Create new normalizer and set params
        normalizer2 = FeatureNormalizer()
        normalizer2.set_params(params)
        
        self.assertTrue(normalizer2.is_fitted)
        np.testing.assert_array_almost_equal(
            normalizer2.feature_means,  # type: ignore
            self.normalizer.feature_means  # type: ignore
        )

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFeatureIntegration(unittest.TestCase):
    """Test integrated feature extraction and normalization"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.extractor = FeatureExtractor()
        self.normalizer = FeatureNormalizer()
    
    def test_end_to_end_pipeline(self):
        """Test complete extraction and normalization pipeline"""
        # Create traffic and extract features
        packets = create_normal_traffic(count=100)
        for packet in packets:
            self.extractor.add_packet(packet)
        
        features = self.extractor.extract_window_features()
        array1 = features.to_array()  # type: ignore
        
        # Prepare training data
        arrays = []
        for _ in range(10):
            packets = create_normal_traffic(count=100)
            for packet in packets:
                self.extractor.add_packet(packet)
            features = self.extractor.extract_window_features()
            arrays.append(features.to_array())  # type: ignore
        
        training_data = np.vstack(arrays)
        
        # Fit normalizer and transform
        self.normalizer.fit(training_data)
        normalized = self.normalizer.transform(array1.reshape(1, -1))
        
        # Verify normalization
        self.assertEqual(normalized.shape, (1, 28))
        self.assertTrue(np.all(np.isfinite(normalized)))
    
    def test_batch_feature_extraction(self):
        """Test extracting features from batch of packets"""
        extractor = FeatureExtractor()
        packets = create_ddos_traffic(count=500)
        
        # Add all packets
        for packet in packets:
            extractor.add_packet(packet)
        
        # Extract features with specific window
        window_start = min(p['timestamp'] for p in packets)
        features = extractor.extract_window_features(window_start)
        array = features.to_array()  # type: ignore
        
        # Verify
        self.assertEqual(array.shape, (28,))
        self.assertGreater(features.packet_rate, 1)  # type: ignore  # Significant packet rate
        self.assertTrue(np.all(np.isfinite(array)))

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestFeaturePerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def test_feature_extraction_speed(self):
        """Test feature extraction speed"""
        import time
        
        extractor = FeatureExtractor()
        packets = create_ddos_traffic(count=1000)
        
        # Add all packets
        start = time.time()
        for packet in packets:
            extractor.add_packet(packet)
        add_time = time.time() - start
        
        # Extract features
        start = time.time()
        features = extractor.extract_window_features()
        extract_time = time.time() - start
        
        # Should be very fast
        self.assertLess(add_time, 1.0)  # < 1 second for 1000 packets
        self.assertLess(extract_time, 0.1)  # < 100ms for extraction
    
    def test_normalization_speed(self):
        """Test normalization speed"""
        import time
        
        normalizer = FeatureNormalizer()
        data = np.random.randn(10000, 28)
        
        # Fit
        start = time.time()
        normalizer.fit(data)
        fit_time = time.time() - start
        
        # Transform
        start = time.time()
        result = normalizer.transform(data)
        transform_time = time.time() - start
        
        # Should be very fast
        self.assertLess(fit_time, 0.5)  # < 500ms
        self.assertLess(transform_time, 0.5)

# ============================================================================
# SINGLETON TESTS
# ============================================================================

class TestSingletonAccess(unittest.TestCase):
    """Test singleton pattern access"""
    
    def test_get_singleton_extractor(self):
        """Test getting singleton extractor"""
        extractor1 = get_feature_extractor()
        extractor2 = get_feature_extractor()
        
        self.assertIs(extractor1, extractor2)
    
    def test_get_singleton_normalizer(self):
        """Test getting singleton normalizer"""
        normalizer1 = get_feature_normalizer()
        normalizer2 = get_feature_normalizer()
        
        self.assertIs(normalizer1, normalizer2)

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
