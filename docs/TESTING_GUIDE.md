# DDoSPoT Testing Guide

## Overview

DDoSPoT includes a comprehensive test suite covering:
- **Core Modules**: Database, geolocation, rate limiting, ML features
- **API Endpoints**: Stats, events, alerts, ML endpoints
- **Security**: Token authentication, rate limiting enforcement, input validation
- **CLI**: Token reading, health checks, log rotation

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_core_modules.py     # Database, rate limiter tests
├── test_api_endpoints.py    # Dashboard endpoint tests
├── test_security.py         # Token auth and rate limiting tests
├── test_cli.py              # CLI functionality tests
└── __pycache__/             # Python cache (auto-generated)
```

## Installation

### Install test dependencies

```bash
pip install pytest pytest-cov
```

### Optional: Install additional testing tools

```bash
pip install pytest-xdist pytest-timeout pytest-mock
```

## Running Tests

### Using the test runner script

```bash
# Run all tests
./run_tests.py all

# Run specific test category
./run_tests.py core       # Core modules
./run_tests.py api        # API endpoints
./run_tests.py security   # Security tests
./run_tests.py cli        # CLI tests

# Run fast tests only (skip slow/integration tests)
./run_tests.py quick

# Run with coverage report
./run_tests.py coverage

# Run with verbose output
./run_tests.py verbose

# Run specific test with extra pytest options
./run_tests.py api -v -s
./run_tests.py security -k token --tb=short
```

### Using pytest directly

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_core_modules.py -v

# Run specific test class
pytest tests/test_core_modules.py::TestHoneypotDatabase -v

# Run specific test function
pytest tests/test_core_modules.py::TestHoneypotDatabase::test_add_event -v

# Run tests matching pattern
pytest -k "test_token" -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run with markers (skip slow tests)
pytest -m "not slow" tests/

# Run with short output
pytest tests/ --tb=short

# Exit on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -s
```

## Test Categories

### Core Modules Tests (`test_core_modules.py`)

Tests for database operations and rate limiting:

```
TestHoneypotDatabase
  ✓ test_database_init           - Database initialization
  ✓ test_add_event               - Adding single event
  ✓ test_add_multiple_events     - Adding multiple events
  ✓ test_get_events_by_ip        - Querying events by IP
  ✓ test_get_recent_events_filtered - Filtering events
  ✓ test_count_recent_events_filtered - Counting filtered events
  ✓ test_get_top_attackers       - Top attacker ranking
  ✓ test_cleanup_old_events      - Old event cleanup
  ✓ test_get_database_size       - Database size info

TestRateLimiter
  ✓ test_rate_limiter_init       - Rate limiter setup
  ✓ test_register_event_within_limit - Events within limit
  ✓ test_register_event_exceeds_limit - Limit enforcement
  ✓ test_ip_blacklist            - IP blacklisting
  ✓ test_multiple_ips            - Per-IP tracking
  ✓ test_sliding_window          - Sliding window behavior

TestEventStatistics
  ✓ test_statistics_consistency  - Stats accuracy
```

### API Endpoint Tests (`test_api_endpoints.py`)

Tests for Flask API endpoints:

```
TestStatsEndpoint
  ✓ test_stats_without_auth      - GET /api/stats
  ✓ test_stats_pagination        - Hours parameter

TestRecentEventsEndpoint
  ✓ test_recent_events_default   - Default pagination
  ✓ test_recent_events_pagination - Page controls
  ✓ test_recent_events_filter_by_ip - IP filtering
  ✓ test_recent_events_filter_by_protocol - Protocol filtering

TestAuthorizationEndpoints
  ✓ test_alerts_config_post_no_token - Token enforcement

TestInputValidation
  ✓ test_alerts_config_invalid_payload - Payload validation
  ✓ test_batch_predict_invalid_ips - IPs validation
  ✓ test_batch_predict_invalid_limit - Limit validation

TestHealthEndpoint
  ✓ test_health_check - GET /health

TestMetricsEndpoint
  ✓ test_metrics_returns_data - GET /metrics format

TestErrorHandling
  ✓ test_404_not_found - 404 responses
  ✓ test_invalid_json - JSON parsing errors

TestRateLimitingIntegration
  ✓ test_rate_limit_429_response - Rate limit response code

TestProxyHeaders
  ✓ test_forwarded_for_header - Proxy support
```

### Security Tests (`test_security.py`)

Tests for authentication and input validation:

```
TestTokenReading
  ✓ test_token_from_env - Env var reading
  ✓ test_token_from_config_json - Config file reading

TestTokenExtraction
  ✓ test_bearer_token_extraction - Bearer header
  ✓ test_api_token_header_extraction - X-API-Token header
  ✓ test_query_param_token_extraction - Query parameter

TestTokenEnforcement
  ✓ test_post_without_token_fails - Auth enforcement
  ✓ test_post_with_valid_token_succeeds - Valid token
  ✓ test_post_with_invalid_token_fails - Invalid token

TestMetricsTokenProtection
  ✓ test_metrics_without_token_when_protected - Protected /metrics
  ✓ test_metrics_with_token_when_protected - Token access

TestHealthTokenProtection
  ✓ test_health_without_token_when_protected - Protected /health

TestInputValidationSecurity
  ✓ test_alerts_config_non_dict_payload - Dict validation
  ✓ test_batch_predict_non_list_ips - List validation
  ✓ test_batch_predict_non_string_ips - String validation
  ✓ test_batch_predict_limit_bounds - Limit clamping

TestRateLimitingSecurity
  ✓ test_rate_limiter_blocks_repeated_requests - Rate limit enforcement
  ✓ test_rate_limiter_different_ips_independent - Per-IP tracking
```

### CLI Tests (`test_cli.py`)

Tests for command-line interface:

```
TestTokenReading
  ✓ test_get_api_token_from_env - Read from env
  ✓ test_get_api_token_from_config - Read from config
  ✓ test_get_api_token_env_priority - Env precedence

TestLogRotationSettings
  ✓ test_default_log_rotation_settings - Default config
  ✓ test_log_rotation_from_env - Env config
  ✓ test_log_rotation_invalid_values - Invalid handling

TestLogRotation
  ✓ test_rotate_log_creates_file - File creation
  ✓ test_rotate_log_respects_max_bytes - Size enforcement
  ✓ test_rotate_log_keeps_backups - Backup management

TestHealthCheckIntegration
  ✓ test_health_check_with_token - Token support
  ✓ test_health_check_without_token - No auth mode
```

## Test Coverage

Generate coverage report:

```bash
./run_tests.py coverage

# Or with pytest directly:
pytest tests/ --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

Target coverage:
- Core modules: 80%+
- API endpoints: 70%+
- Security: 90%+
- CLI: 75%+

## Continuous Integration

### Run tests in CI pipeline

```bash
# Install dependencies
pip install -r requerements.txt
pip install pytest pytest-cov

# Run all tests with coverage
pytest tests/ --cov=. --cov-report=xml --cov-report=term

# Generate XML report for CI tools
pytest tests/ --junit-xml=test-results.xml
```

## Debugging Tests

### Run with verbose output and print statements

```bash
pytest tests/ -vvs
```

### Run single test with detailed traceback

```bash
pytest tests/test_security.py::TestTokenEnforcement::test_post_without_token_fails -vvs --tb=long
```

### Run with pdb debugger

```bash
pytest tests/ --pdb
```

### Skip certain tests

```bash
pytest -k "not slow" tests/
pytest -m "not integration" tests/
```

## Common Issues

### ModuleNotFoundError when importing test

**Solution**: Make sure project root is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

### Tests fail with "Database not initialized"

**Solution**: Tests use temporary in-memory databases. This error indicates database fixture not set up. Check conftest.py.

### Rate limiter tests fail intermittently

**Solution**: Sliding window tests may be timing-sensitive. Add a small sleep or use `pytest-timeout`:
```bash
pytest tests/test_core_modules.py -v --timeout=10
```

### Token tests fail with environ issues

**Solution**: Clean up environment variables between tests:
```bash
# In test_security.py, fixtures should clean up os.environ
del os.environ['DDOSPOT_API_TOKEN']
```

## Writing New Tests

### Test naming convention

```python
# File: tests/test_feature.py
class TestFeatureName:
    def test_specific_behavior(self):
        """Test description"""
        # Arrange
        setup_data = ...
        
        # Act
        result = function_under_test()
        
        # Assert
        assert result == expected
```

### Using fixtures

```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### Parametrized tests

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_calculation(input, expected):
    assert input * 2 == expected
```

## Test Markers

Add markers to tests:

```python
@pytest.mark.slow
def test_large_dataset():
    # Long-running test
    pass

@pytest.mark.security
def test_token_validation():
    # Security-focused test
    pass

@pytest.mark.integration
def test_full_workflow():
    # End-to-end test
    pass
```

Run by marker:

```bash
pytest -m security
pytest -m "not slow"
pytest -m "security or integration"
```

## Performance Testing

```bash
# Run tests and show timing
pytest tests/ --durations=10

# Run with timeout for each test
pytest tests/ --timeout=30
```

## Next Steps

1. **Run verification**: `./run_tests.py all`
2. **Check coverage**: `./run_tests.py coverage`
3. **Review failures**: Fix any broken tests
4. **Add more tests**: Cover additional edge cases
5. **Set up CI**: Configure automated testing in your workflow

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [Test Coverage](https://en.wikipedia.org/wiki/Code_coverage)

