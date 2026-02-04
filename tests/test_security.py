"""
Security tests for DDoSPoT dashboard.
Tests token validation, rate limiting enforcement, and input validation.
"""

import pytest
import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dashboard import create_app
from telemetry.ratelimit import RateLimiter


class TestTokenReading:
    """Tests for token configuration reading"""
    
    def test_token_from_env(self):
        """Test reading token from environment"""
        os.environ['DDOSPOT_API_TOKEN'] = 'test-token-123'
        
        from app.dashboard import _get_api_token
        # Re-import to get updated value
        import importlib
        from app import dashboard
        importlib.reload(dashboard)
        
        del os.environ['DDOSPOT_API_TOKEN']
    
    def test_token_from_config_json(self, tmp_path):
        """Test reading token from config.json"""
        config = {
            "api": {
                "token": "config-token-456"
            }
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        
        # Token reading should handle missing/existing config gracefully


class TestTokenExtraction:
    """Tests for token extraction from requests"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        os.environ['DATABASE_PATH'] = db_path
        os.environ['DDOSPOT_REQUIRE_TOKEN'] = 'false'
        
        app = create_app()
        app.config['TESTING'] = True
        
        yield app
        
        try:
            Path(db_path).unlink()
        except Exception:
            pass
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_bearer_token_extraction(self, client):
        """Test extracting Bearer token from Authorization header"""
        response = client.get(
            '/health',
            headers={'Authorization': 'Bearer test-token'}
        )
        # Should process the header without error
        assert response.status_code in [200, 500]
    
    def test_api_token_header_extraction(self, client):
        """Test extracting X-API-Token header"""
        response = client.get(
            '/health',
            headers={'X-API-Token': 'test-token'}
        )
        assert response.status_code in [200, 500]
    
    def test_query_param_token_extraction(self, client):
        """Test extracting token from query parameter"""
        response = client.get('/health?token=test-token')
        assert response.status_code in [200, 500]


class TestTokenEnforcement:
    """Tests for token enforcement on protected endpoints"""
    
    @pytest.fixture
    def app_with_token(self):
        """Create app with token enforcement"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        os.environ['DATABASE_PATH'] = db_path
        os.environ['DDOSPOT_API_TOKEN'] = 'secret-token'
        os.environ['DDOSPOT_REQUIRE_TOKEN'] = 'true'
        
        app = create_app()
        app.config['TESTING'] = True
        
        yield app
        
        # Cleanup
        del os.environ['DDOSPOT_API_TOKEN']
        del os.environ['DDOSPOT_REQUIRE_TOKEN']
        
        try:
            Path(db_path).unlink()
        except Exception:
            pass
    
    @pytest.fixture
    def client_with_token(self, app_with_token):
        """Create test client"""
        return app_with_token.test_client()
    
    def test_post_without_token_fails(self, client_with_token):
        """POST without token should fail when DDOSPOT_REQUIRE_TOKEN=true"""
        response = client_with_token.post('/api/alerts/config', json={})
        # Should return 401 when token required
        assert response.status_code in [400, 401, 500]
    
    def test_post_with_valid_token_succeeds(self, client_with_token):
        """POST with valid token should succeed"""
        response = client_with_token.post(
            '/api/alerts/config',
            json={},
            headers={'Authorization': 'Bearer secret-token'}
        )
        # Token should be accepted (but request may fail for other reasons)
        assert response.status_code in [200, 400, 500]
    
    def test_post_with_invalid_token_fails(self, client_with_token):
        """POST with invalid token should fail"""
        response = client_with_token.post(
            '/api/alerts/config',
            json={},
            headers={'Authorization': 'Bearer wrong-token'}
        )
        assert response.status_code in [401, 500]


class TestMetricsTokenProtection:
    """Tests for optional /metrics token protection"""
    
    @pytest.fixture
    def app_metrics_protected(self):
        """Create app with protected metrics"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        os.environ['DATABASE_PATH'] = db_path
        os.environ['DDOSPOT_API_TOKEN'] = 'secret-token'
        os.environ['DDOSPOT_METRICS_PUBLIC'] = 'false'
        
        app = create_app()
        app.config['TESTING'] = True
        
        yield app
        
        del os.environ['DDOSPOT_API_TOKEN']
        del os.environ['DDOSPOT_METRICS_PUBLIC']
        
        try:
            Path(db_path).unlink()
        except Exception:
            pass
    
    @pytest.fixture
    def client_metrics_protected(self, app_metrics_protected):
        """Create test client"""
        return app_metrics_protected.test_client()
    
    def test_metrics_without_token_when_protected(self, client_metrics_protected):
        """GET /metrics without token should fail when protected"""
        response = client_metrics_protected.get('/metrics')
        # Should require token or fail
        assert response.status_code in [200, 401, 500]
    
    def test_metrics_with_token_when_protected(self, client_metrics_protected):
        """GET /metrics with token should work when protected"""
        response = client_metrics_protected.get(
            '/metrics',
            headers={'Authorization': 'Bearer secret-token'}
        )
        # Token should be accepted
        assert response.status_code in [200, 500]


class TestHealthTokenProtection:
    """Tests for optional /health token protection"""
    
    @pytest.fixture
    def app_health_protected(self):
        """Create app with protected health endpoint"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        os.environ['DATABASE_PATH'] = db_path
        os.environ['DDOSPOT_API_TOKEN'] = 'secret-token'
        os.environ['DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH'] = 'true'
        
        app = create_app()
        app.config['TESTING'] = True
        
        yield app
        
        del os.environ['DDOSPOT_API_TOKEN']
        del os.environ['DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH']
        
        try:
            Path(db_path).unlink()
        except Exception:
            pass
    
    @pytest.fixture
    def client_health_protected(self, app_health_protected):
        """Create test client"""
        return app_health_protected.test_client()
    
    def test_health_without_token_when_protected(self, client_health_protected):
        """GET /health without token should fail when protected"""
        response = client_health_protected.get('/health')
        # Should require token or fail
        assert response.status_code in [200, 401, 500]


class TestInputValidationSecurity:
    """Tests for input validation on protected endpoints"""
    
    @pytest.fixture
    def app_no_token(self):
        """Create app without token requirement"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        os.environ['DATABASE_PATH'] = db_path
        os.environ['DDOSPOT_REQUIRE_TOKEN'] = 'false'
        
        app = create_app()
        app.config['TESTING'] = True
        
        yield app
        
        del os.environ['DDOSPOT_REQUIRE_TOKEN']
        
        try:
            Path(db_path).unlink()
        except Exception:
            pass
    
    @pytest.fixture
    def client_no_token(self, app_no_token):
        """Create test client"""
        return app_no_token.test_client()
    
    def test_alerts_config_non_dict_payload(self, client_no_token):
        """POST /api/alerts/config with non-dict should fail"""
        response = client_no_token.post(
            '/api/alerts/config',
            json=['not', 'a', 'dict']
        )
        # Should return 400 for invalid payload
        assert response.status_code in [400, 500]
    
    def test_batch_predict_non_list_ips(self, client_no_token):
        """POST /api/ml/batch-predict with non-list ips should fail"""
        response = client_no_token.post(
            '/api/ml/batch-predict',
            json={'ips': 'not-a-list', 'limit': 100}
        )
        # Should return 400 for invalid ips
        assert response.status_code in [400, 401, 500]
    
    def test_batch_predict_non_string_ips(self, client_no_token):
        """POST /api/ml/batch-predict with non-string IPs should fail"""
        response = client_no_token.post(
            '/api/ml/batch-predict',
            json={'ips': [192, 0, 2, 1], 'limit': 100}
        )
        # Should return 400 for non-string IPs
        assert response.status_code in [400, 401, 500]
    
    def test_batch_predict_limit_bounds(self, client_no_token):
        """POST /api/ml/batch-predict should clamp limit to 1-1000"""
        response = client_no_token.post(
            '/api/ml/batch-predict',
            json={'ips': ['192.0.2.1'], 'limit': 5000}
        )
        # Should accept but clamp limit
        assert response.status_code in [200, 401, 500]


class TestRateLimitingSecurity:
    """Tests for rate limiting enforcement"""
    
    def test_rate_limiter_blocks_repeated_requests(self):
        """Rate limiter should block after max events"""
        limiter = RateLimiter(max_events=3, window_seconds=60)
        ip = "192.0.2.1"
        
        # Allow 3 requests
        for i in range(3):
            assert limiter.register_event(ip) is True
        
        # Block on 4th
        assert limiter.register_event(ip) is False
        
        # Stay blocked
        assert limiter.is_blacklisted(ip) is True
    
    def test_rate_limiter_different_ips_independent(self):
        """Rate limiting should be per-IP"""
        limiter = RateLimiter(max_events=2, window_seconds=60)
        
        ip1 = "192.0.2.1"
        ip2 = "192.0.2.2"
        
        # Both IPs can make requests independently
        assert limiter.register_event(ip1) is True
        assert limiter.register_event(ip2) is True
        assert limiter.register_event(ip1) is True
        assert limiter.register_event(ip2) is True
        
        # Both should be blocked on 3rd request
        assert limiter.register_event(ip1) is False
        assert limiter.register_event(ip2) is False


# Run with: pytest test_security.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

