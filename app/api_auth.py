"""
API Authentication and Rate Limiting Module
Provides JWT-based authentication and rate limiting for the DDoSPot API
"""

import time
from datetime import datetime
from typing import Dict, Optional, Callable
from functools import wraps
import secrets

from flask import request, jsonify, g
from telemetry.logger import get_logger

logger = get_logger(__name__)

# In-memory rate limiting storage (use Redis for production)
RATE_LIMIT_STORE: Dict[str, list] = {}

# API Keys storage (in production, store in database)
API_KEYS: Dict[str, Dict] = {
    'demo-key-admin': {
        'name': 'Demo Admin Key',
        'permissions': ['read', 'write', 'admin'],
        'created_at': datetime.now(),
        'active': True
    }
}


class RateLimiter:
    """Rate limiting decorator for API endpoints"""
    
    def __init__(self, calls: int, period: int):
        """
        Initialize rate limiter
        
        Args:
            calls: Number of allowed calls
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get client identifier (IP or API key)
            client_id = get_client_identifier()
            key = f"{func.__name__}:{client_id}"
            
            # Get current time
            now = time.time()
            
            # Initialize or retrieve request history
            if key not in RATE_LIMIT_STORE:
                RATE_LIMIT_STORE[key] = []
            
            # Remove old requests outside the period
            RATE_LIMIT_STORE[key] = [
                req_time for req_time in RATE_LIMIT_STORE[key]
                if now - req_time < self.period
            ]
            
            # Check if limit exceeded
            if len(RATE_LIMIT_STORE[key]) >= self.calls:
                logger.warning(f"Rate limit exceeded for {client_id} on {func.__name__}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': self.calls,
                    'period': self.period,
                    'retry_after': self.period
                }), 429
            
            # Add current request
            RATE_LIMIT_STORE[key].append(now)
            
            # Add rate limit headers
            remaining = self.calls - len(RATE_LIMIT_STORE[key])
            g.rate_limit_remaining = remaining
            g.rate_limit_limit = self.calls
            g.rate_limit_reset = int(now + self.period)
            
            return func(*args, **kwargs)
        
        return wrapper


class APIKeyAuth:
    """API Key based authentication"""
    
    # Class attribute to access API_KEYS
    API_KEYS = API_KEYS
    
    @staticmethod
    def get_or_create_key(name: str, permissions: list = None) -> str:
        """Generate or retrieve API key"""
        if permissions is None:
            permissions = ['read']
        
        key = secrets.token_urlsafe(32)
        API_KEYS[key] = {
            'name': name,
            'permissions': permissions,
            'created_at': datetime.now(),
            'active': True
        }
        
        logger.info(f"Created new API key: {name}")
        return key
    
    @staticmethod
    def validate_key(key: str) -> Optional[Dict]:
        """Validate API key"""
        if key in API_KEYS:
            key_data = API_KEYS[key]
            if key_data.get('active'):
                return key_data
        return None
    
    @staticmethod
    def revoke_key(key: str) -> bool:
        """Revoke an API key"""
        if key in API_KEYS:
            API_KEYS[key]['active'] = False
            logger.info(f"Revoked API key: {API_KEYS[key].get('name')}")
            return True
        return False
    
    @staticmethod
    def has_permission(key_data: Dict, permission: str) -> bool:
        """Check if key has permission"""
        return permission in key_data.get('permissions', [])


def require_api_key(permission: str = 'read'):
    """
    Decorator to require API key for endpoint
    
    Args:
        permission: Required permission level ('read', 'write', 'admin')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get API key from header or query parameter
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if not api_key:
                logger.warning("API request without key")
                return jsonify({'error': 'API key required'}), 401
            
            # Validate key
            key_data = APIKeyAuth.validate_key(api_key)
            if not key_data:
                logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Check permission
            if not APIKeyAuth.has_permission(key_data, permission):
                logger.warning(f"Insufficient permissions for key: {key_data.get('name')}")
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Store key info in request context
            g.api_key = api_key
            g.api_key_data = key_data
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_client_identifier() -> str:
    """Get unique client identifier for rate limiting"""
    # Use API key if available, otherwise use IP address
    if hasattr(g, 'api_key'):
        return g.api_key
    
    # Get real IP (handles proxies)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    
    return request.remote_addr or 'unknown'


def add_rate_limit_headers(response):
    """Add rate limit headers to response"""
    if hasattr(g, 'rate_limit_remaining'):
        response.headers['X-RateLimit-Limit'] = str(g.rate_limit_limit)
        response.headers['X-RateLimit-Remaining'] = str(g.rate_limit_remaining)
        response.headers['X-RateLimit-Reset'] = str(g.rate_limit_reset)
    
    return response


def get_api_stats() -> Dict:
    """Get API usage statistics"""
    stats = {
        'total_rate_limit_entries': len(RATE_LIMIT_STORE),
        'active_api_keys': sum(1 for k in API_KEYS.values() if k.get('active')),
        'total_api_keys': len(API_KEYS),
        'rate_limit_store_keys': list(RATE_LIMIT_STORE.keys())[:10]  # Last 10
    }
    return stats


def cleanup_old_rate_limits():
    """Clean up old rate limit entries (call periodically)"""
    now = time.time()
    max_period = max(300, 3600)  # Keep records for at most 1 hour
    
    keys_to_remove = []
    for key, timestamps in RATE_LIMIT_STORE.items():
        RATE_LIMIT_STORE[key] = [
            ts for ts in timestamps
            if now - ts < max_period
        ]
        if not RATE_LIMIT_STORE[key]:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del RATE_LIMIT_STORE[key]
    
    logger.debug(f"Cleaned up {len(keys_to_remove)} rate limit entries")
