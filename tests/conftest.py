"""
Pytest configuration and fixtures for DDoSPoT tests.
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure pytest
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: integration tests requiring full stack"
    )
    config.addinivalue_line(
        "markers", "security: security-focused tests"
    )
    config.addinivalue_line(
        "markers", "slow: slow tests"
    )

@pytest.fixture(scope="session")
def test_config():
    """Session-level test configuration"""
    return {
        'test_dir': Path(__file__).parent,
        'project_root': project_root,
    }

# Markers for running specific test categories
# pytest -m security    - run security tests only
# pytest -m integration - run integration tests only
# pytest -m "not slow"  - skip slow tests

