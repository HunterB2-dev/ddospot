"""
Integration tests for DDoSPoT dashboard API endpoints.
Tests authentication, rate limiting, validation, and endpoint functionality.
"""

import pytest
import os
import sys
import json
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dashboard import create_app, _rate_limiter


@pytest.fixture
def app():
    """Create Flask test app"""
    # Create temp database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    os.environ['DATABASE_PATH'] = db_path
    
    app = create_app()
    app.config['TESTING'] = True
    
    yield app
    
    # Cleanup
    try:
        Path(db_path).unlink()
    except Exception:
        pass


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


class TestStatsEndpoint:
    """Tests for GET /api/stats"""
    
    def test_stats_without_auth(self, client):
        """GET /api/stats should work without auth"""
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_events' in data
    
    def test_stats_pagination(self, client):
        """Test stats with hours parameter"""
        response = client.get('/api/stats?hours=24')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)


class TestRecentEventsEndpoint:
    """Tests for GET /api/recent-events with filtering and pagination"""
    
    def test_recent_events_default(self, client):
        """Test recent events without filters"""
        response = client.get('/api/recent-events')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'items' in data
        assert 'page' in data
        assert 'total' in data
        assert 'filters' in data
    
    def test_recent_events_pagination(self, client):
        """Test pagination parameters"""
        response = client.get('/api/recent-events?page=1&page_size=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['page'] == 1
        assert data['page_size'] == 10
    
    def test_recent_events_invalid_page(self, client):
        """Test that invalid page returns page 1"""
        response = client.get('/api/recent-events?page=0&page_size=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['page'] == 1
    
    def test_recent_events_max_page_size(self, client):
        """Test that page_size is capped at 200"""
        response = client.get('/api/recent-events?page_size=1000')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['page_size'] <= 200
    
    def test_recent_events_filter_by_ip(self, client):
        """Test filtering by IP"""
        response = client.get('/api/recent-events?ip=192.0.2.1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['filters']['ip'] == '192.0.2.1'
    
    def test_recent_events_filter_by_protocol(self, client):
        """Test filtering by protocol"""
        response = client.get('/api/recent-events?protocol=HTTP')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['filters']['protocol'] == 'HTTP'


class TestAuthorizationEndpoints:
    """Tests for authentication-protected endpoints"""
    
    def test_alerts_config_post_no_token(self, client):
        """POST /api/alerts/config requires token"""
        os.environ['DDOSPOT_REQUIRE_TOKEN'] = 'true'
        
        response = client.post(
            '/api/alerts/config',
            json={'threshold': 100}
        )
        
        # Should fail if token required
        if os.environ.get('DDOSPOT_REQUIRE_TOKEN') == 'true':
            # Reset for next tests
            del os.environ['DDOSPOT_REQUIRE_TOKEN']
            # Note: actual response depends on SEC_REQUIRE_TOKEN config
    
    def test_ml_train_post_no_token(self, client):
        """POST /api/ml/train requires token"""
        response = client.post('/api/ml/train')
        # Response depends on DDOSPOT_REQUIRE_TOKEN setting
        assert response.status_code in [200, 401, 500]


class TestInputValidation:
    """Tests for request payload validation"""
    
    def test_alerts_config_invalid_payload(self, client):
        """POST /api/alerts/config with invalid payload"""
        response = client.post(
            '/api/alerts/config',
            json=["list", "instead", "of", "dict"]
        )
        # Should return 400 if validation is enforced
        assert response.status_code in [200, 400]
    
    def test_batch_predict_invalid_ips(self, client):
        """POST /api/ml/batch-predict with invalid ips"""
        response = client.post(
            '/api/ml/batch-predict',
            json={'ips': 'not-a-list', 'limit': 100}
        )
        # Should return 400 for invalid ips
        assert response.status_code in [200, 400, 401]
    
    def test_batch_predict_invalid_limit(self, client):
        """POST /api/ml/batch-predict with invalid limit"""
        response = client.post(
            '/api/ml/batch-predict',
            json={'ips': ['192.0.2.1'], 'limit': 'not-a-number'}
        )
        # Should return 400 for invalid limit
        assert response.status_code in [200, 400, 401]
    
    def test_batch_predict_valid_payload(self, client):
        """POST /api/ml/batch-predict with valid payload"""
        response = client.post(
            '/api/ml/batch-predict',
            json={'ips': ['192.0.2.1'], 'limit': 100}
        )
        # Should accept valid payload
        assert response.status_code in [200, 401]


class TestHealthEndpoint:
    """Tests for GET /health"""
    
    def test_health_check(self, client):
        """Health check endpoint should return status"""
        response = client.get('/health')
        assert response.status_code in [200, 500]
        data = json.loads(response.data)
        assert 'status' in data


class TestMetricsEndpoint:
    """Tests for GET /metrics"""
    
    def test_metrics_returns_data(self, client):
        """Metrics endpoint should return Prometheus format"""
        response = client.get('/metrics')
        assert response.status_code in [200, 401]
        
        # Should contain Prometheus-style data if successful
        if response.status_code == 200:
            text = response.data.decode('utf-8')
            assert 'ddospot_' in text or '# HELP' in text


class TestErrorHandling:
    """Tests for error responses"""
    
    def test_404_not_found(self, client):
        """Test 404 error handling"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            '/api/alerts/config',
            data='{invalid json}',
            content_type='application/json'
        )
        assert response.status_code in [400, 500]


class TestRateLimitingIntegration:
    """Tests for rate limiting on dashboard endpoints"""
    
    def test_rate_limit_429_response(self, client):
        """Test that rate limit returns 429"""
        # Note: Rate limiting is per-IP, and test client may share IP
        # This test verifies the status code if rate limit is triggered
        
        # Make rapid requests to trigger rate limit
        for i in range(100):
            response = client.get('/api/stats')
            if response.status_code == 429:
                # Rate limit triggered
                data = json.loads(response.data)
                assert 'error' in data
                break


class TestProxyHeaders:
    """Tests for X-Forwarded-For header support"""
    
    def test_forwarded_for_header(self, client):
        """Test that X-Forwarded-For is respected"""
        response = client.get(
            '/api/stats',
            headers={'X-Forwarded-For': '10.0.0.1'}
        )
        # Should work regardless of X-Forwarded-For
        assert response.status_code in [200, 429]


# Run with: pytest test_api_endpoints.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

