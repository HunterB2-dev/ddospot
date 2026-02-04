"""
ML Feature Engineering for DDoS Detection
Extracts and engineers features from network traffic for ML models
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PacketFeatures:
    """Features extracted from a single packet"""
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    packet_size: int
    flags: str
    payload_size: int
    is_syn: bool = False
    is_ack: bool = False
    is_fin: bool = False
    is_rst: bool = False

@dataclass
class TrafficFeatures:
    """Aggregated features from traffic window"""
    # Time window info
    timestamp: float
    window_duration: float
    
    # Volume features
    packet_count: int
    byte_count: int
    avg_packet_size: float
    packet_rate: float  # packets/sec
    byte_rate: float    # bytes/sec
    
    # Source IP features
    unique_src_ips: int
    src_ip_concentration: float  # entropy of source IPs
    top_src_ip: str
    top_src_ip_count: int
    
    # Destination port features
    unique_dst_ports: int
    port_concentration: float
    top_dst_port: int
    top_dst_port_count: int
    
    # Protocol features
    tcp_count: int
    udp_count: int
    icmp_count: int
    other_count: int
    tcp_ratio: float
    udp_ratio: float
    
    # TCP flag features
    syn_count: int
    ack_count: int
    fin_count: int
    rst_count: int
    syn_ack_ratio: float
    
    # Payload features
    avg_payload_size: float
    payload_entropy: float
    zero_payload_ratio: float
    
    # Temporal features
    packet_inter_arrival_mean: float
    packet_inter_arrival_std: float
    packet_inter_arrival_min: float
    packet_inter_arrival_max: float
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array for ML"""
        return np.array([
            self.packet_count,
            self.byte_count,
            self.avg_packet_size,
            self.packet_rate,
            self.byte_rate,
            self.unique_src_ips,
            self.src_ip_concentration,
            self.top_src_ip_count,
            self.unique_dst_ports,
            self.port_concentration,
            self.top_dst_port_count,
            self.tcp_count,
            self.udp_count,
            self.icmp_count,
            self.tcp_ratio,
            self.udp_ratio,
            self.syn_count,
            self.ack_count,
            self.fin_count,
            self.rst_count,
            self.syn_ack_ratio,
            self.avg_payload_size,
            self.payload_entropy,
            self.zero_payload_ratio,
            self.packet_inter_arrival_mean,
            self.packet_inter_arrival_std,
            self.packet_inter_arrival_min,
            self.packet_inter_arrival_max
        ], dtype=np.float32)

# ============================================================================
# FEATURE EXTRACTION
# ============================================================================

class FeatureExtractor:
    """
    Extracts ML features from network traffic
    """
    
    def __init__(self, window_size: int = 5):
        """
        Initialize feature extractor
        
        Args:
            window_size: Time window for feature aggregation (seconds)
        """
        self.window_size = window_size
        self.packet_buffer: deque = deque(maxlen=10000)
        self.feature_names = [
            'packet_count', 'byte_count', 'avg_packet_size', 'packet_rate', 'byte_rate',
            'unique_src_ips', 'src_ip_concentration', 'top_src_ip_count',
            'unique_dst_ports', 'port_concentration', 'top_dst_port_count',
            'tcp_count', 'udp_count', 'icmp_count', 'tcp_ratio', 'udp_ratio',
            'syn_count', 'ack_count', 'fin_count', 'rst_count', 'syn_ack_ratio',
            'avg_payload_size', 'payload_entropy', 'zero_payload_ratio',
            'packet_inter_arrival_mean', 'packet_inter_arrival_std',
            'packet_inter_arrival_min', 'packet_inter_arrival_max'
        ]
        
        logger.info('[ML] Feature extractor initialized with 28 features')
    
    def extract_packet_features(self, packet_data: Dict) -> PacketFeatures:
        """Extract features from a single packet"""
        features = PacketFeatures(
            timestamp=packet_data.get('timestamp', datetime.now().timestamp()),
            src_ip=packet_data.get('src_ip', '0.0.0.0'),
            dst_ip=packet_data.get('dst_ip', '0.0.0.0'),
            src_port=packet_data.get('src_port', 0),
            dst_port=packet_data.get('dst_port', 0),
            protocol=packet_data.get('protocol', 'unknown'),
            packet_size=packet_data.get('packet_size', 0),
            flags=packet_data.get('flags', ''),
            payload_size=packet_data.get('payload_size', 0)
        )
        
        # Parse TCP flags
        flags_str = packet_data.get('flags', '').upper()
        features.is_syn = 'S' in flags_str or 'SYN' in flags_str
        features.is_ack = 'A' in flags_str or 'ACK' in flags_str
        features.is_fin = 'F' in flags_str or 'FIN' in flags_str
        features.is_rst = 'R' in flags_str or 'RST' in flags_str
        
        return features
    
    def add_packet(self, packet_data: Dict) -> None:
        """Add packet to buffer"""
        features = self.extract_packet_features(packet_data)
        self.packet_buffer.append(features)
    
    def extract_window_features(self, window_start: float = None) -> Optional[TrafficFeatures]:
        """Extract aggregated features for time window"""
        if window_start is None:
            window_start = datetime.now().timestamp() - self.window_size
        
        window_end = window_start + self.window_size
        
        # Filter packets in window
        window_packets = [
            p for p in self.packet_buffer
            if window_start <= p.timestamp < window_end
        ]
        
        if len(window_packets) == 0:
            logger.debug('[ML] Empty window, returning None')
            return None
        
        # Volume features
        packet_count = len(window_packets)
        byte_count = sum(p.packet_size for p in window_packets)
        avg_packet_size = byte_count / packet_count if packet_count > 0 else 0
        packet_rate = packet_count / self.window_size
        byte_rate = byte_count / self.window_size
        
        # Source IP features
        src_ip_counts = defaultdict(int)
        for p in window_packets:
            src_ip_counts[p.src_ip] += 1
        
        unique_src_ips = len(src_ip_counts)
        src_ip_concentration = self._entropy(list(src_ip_counts.values()))
        top_src_ip, top_src_ip_count = max(src_ip_counts.items(), key=lambda x: x[1], default=('', 0))
        
        # Destination port features
        dst_port_counts = defaultdict(int)
        for p in window_packets:
            dst_port_counts[p.dst_port] += 1
        
        unique_dst_ports = len(dst_port_counts)
        port_concentration = self._entropy(list(dst_port_counts.values()))
        top_dst_port, top_dst_port_count = max(dst_port_counts.items(), key=lambda x: x[1], default=(0, 0))
        
        # Protocol features
        tcp_count = sum(1 for p in window_packets if p.protocol.upper() == 'TCP')
        udp_count = sum(1 for p in window_packets if p.protocol.upper() == 'UDP')
        icmp_count = sum(1 for p in window_packets if p.protocol.upper() == 'ICMP')
        other_count = packet_count - tcp_count - udp_count - icmp_count
        
        tcp_ratio = tcp_count / packet_count if packet_count > 0 else 0
        udp_ratio = udp_count / packet_count if packet_count > 0 else 0
        
        # TCP flag features
        syn_count = sum(1 for p in window_packets if p.is_syn)
        ack_count = sum(1 for p in window_packets if p.is_ack)
        fin_count = sum(1 for p in window_packets if p.is_fin)
        rst_count = sum(1 for p in window_packets if p.is_rst)
        syn_ack_ratio = syn_count / max(ack_count, 1)
        
        # Payload features
        payload_sizes = [p.payload_size for p in window_packets]
        avg_payload_size = np.mean(payload_sizes) if payload_sizes else 0
        payload_entropy = self._entropy(payload_sizes, bins=10)
        zero_payload_count = sum(1 for p in window_packets if p.payload_size == 0)
        zero_payload_ratio = zero_payload_count / packet_count if packet_count > 0 else 0
        
        # Temporal features
        timestamps = [p.timestamp for p in window_packets]
        if len(timestamps) > 1:
            inter_arrivals = np.diff(sorted(timestamps))
            packet_inter_arrival_mean = np.mean(inter_arrivals)
            packet_inter_arrival_std = np.std(inter_arrivals)
            packet_inter_arrival_min = np.min(inter_arrivals)
            packet_inter_arrival_max = np.max(inter_arrivals)
        else:
            packet_inter_arrival_mean = 0
            packet_inter_arrival_std = 0
            packet_inter_arrival_min = 0
            packet_inter_arrival_max = 0
        
        features = TrafficFeatures(
            timestamp=window_end,
            window_duration=self.window_size,
            packet_count=packet_count,
            byte_count=byte_count,
            avg_packet_size=avg_packet_size,
            packet_rate=packet_rate,
            byte_rate=byte_rate,
            unique_src_ips=unique_src_ips,
            src_ip_concentration=src_ip_concentration,
            top_src_ip=top_src_ip,
            top_src_ip_count=top_src_ip_count,
            unique_dst_ports=unique_dst_ports,
            port_concentration=port_concentration,
            top_dst_port=top_dst_port,
            top_dst_port_count=top_dst_port_count,
            tcp_count=tcp_count,
            udp_count=udp_count,
            icmp_count=icmp_count,
            other_count=other_count,
            tcp_ratio=tcp_ratio,
            udp_ratio=udp_ratio,
            syn_count=syn_count,
            ack_count=ack_count,
            fin_count=fin_count,
            rst_count=rst_count,
            syn_ack_ratio=syn_ack_ratio,
            avg_payload_size=avg_payload_size,
            payload_entropy=payload_entropy,
            zero_payload_ratio=zero_payload_ratio,
            packet_inter_arrival_mean=packet_inter_arrival_mean,
            packet_inter_arrival_std=packet_inter_arrival_std,
            packet_inter_arrival_min=packet_inter_arrival_min,
            packet_inter_arrival_max=packet_inter_arrival_max
        )
        
        return features
    
    def _entropy(self, values: List, bins: Optional[int] = None) -> float:
        """Calculate Shannon entropy of values"""
        if not values:
            return 0.0
        
        if bins is not None:
            # Histogram-based entropy for continuous values
            hist, _ = np.histogram(values, bins=bins)
            hist = hist[hist > 0]
        else:
            # Count-based entropy for discrete values
            unique, counts = np.unique(values, return_counts=True)
            hist = counts
        
        probabilities = hist / np.sum(hist)
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        
        return float(entropy)
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return self.feature_names.copy()

# ============================================================================
# FEATURE NORMALIZATION
# ============================================================================

class FeatureNormalizer:
    """
    Normalizes ML features for training and prediction
    """
    
    def __init__(self):
        """Initialize normalizer"""
        self.feature_means = None
        self.feature_stds = None
        self.is_fitted = False
        
        logger.info('[ML] Feature normalizer initialized')
    
    def fit(self, features: np.ndarray) -> None:
        """Fit normalizer on training data"""
        if features.shape[0] == 0:
            logger.warning('[ML] No features to fit')
            return
        
        self.feature_means = np.mean(features, axis=0)
        self.feature_stds = np.std(features, axis=0)
        
        # Avoid division by zero
        self.feature_stds[self.feature_stds == 0] = 1.0
        
        self.is_fitted = True
        logger.info('[ML] Normalizer fitted on {0} samples'.format(features.shape[0]))
    
    def transform(self, features: np.ndarray) -> np.ndarray:
        """Normalize features"""
        if not self.is_fitted:
            logger.warning('[ML] Normalizer not fitted, returning raw features')
            return features
        
        return (features - self.feature_means) / self.feature_stds
    
    def fit_transform(self, features: np.ndarray) -> np.ndarray:
        """Fit and transform in one step"""
        self.fit(features)
        return self.transform(features)
    
    def get_params(self) -> Dict:
        """Get normalizer parameters"""
        if not self.is_fitted:
            return {}
        
        return {
            'means': self.feature_means.tolist(),
            'stds': self.feature_stds.tolist()
        }
    
    def set_params(self, params: Dict) -> None:
        """Set normalizer parameters"""
        if 'means' in params and 'stds' in params:
            self.feature_means = np.array(params['means'])
            self.feature_stds = np.array(params['stds'])
            self.is_fitted = True
            logger.info('[ML] Normalizer parameters restored')

# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_extractor = None
_normalizer = None

def get_feature_extractor(window_size: int = 5) -> FeatureExtractor:
    """Get singleton feature extractor"""
    global _extractor
    
    if _extractor is None:
        _extractor = FeatureExtractor(window_size)
    
    return _extractor

def get_feature_normalizer() -> FeatureNormalizer:
    """Get singleton feature normalizer"""
    global _normalizer
    
    if _normalizer is None:
        _normalizer = FeatureNormalizer()
    
    return _normalizer