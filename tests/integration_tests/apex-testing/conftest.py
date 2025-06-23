"""
Pytest configuration for Superset Apex module testing
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the superset directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test configuration
TEST_CONFIG = {
    "BASE_URL": "http://localhost:8088",
    "TEST_USERNAME": "admin",
    "TEST_PASSWORD": "admin",
    "TEST_PROVIDER": "db",
    "SECRET_KEY": "test_secret_key_for_jwt",
    "JWT_ALGORITHM": "HS256"
}


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return TEST_CONFIG


@pytest.fixture(scope="session")
def mock_superset_app():
    """Mock Superset Flask application for testing"""
    app_mock = MagicMock()
    app_mock.config = {
        "SECRET_KEY": TEST_CONFIG["SECRET_KEY"],
        "APEX_JWT_HEADER_AUTH_ENABLED": True,
        "APEX_SWAGGER_ANONYMOUS_ENABLED": True,
        "APEX_API_ENABLED": True,
        "APEX_JWT_DEFAULT_EXPIRES_IN": 86400,
    }
    return app_mock


@pytest.fixture(scope="function")
def mock_user():
    """Mock Superset user for testing"""
    user_mock = MagicMock()
    user_mock.id = 1
    user_mock.username = "admin"
    user_mock.first_name = "Admin"
    user_mock.last_name = "User"
    user_mock.email = "admin@example.com"
    user_mock.is_active = True
    return user_mock


@pytest.fixture(scope="function")
def mock_security_manager():
    """Mock Superset security manager for testing"""
    sm_mock = MagicMock()
    sm_mock.find_user.return_value = mock_user()
    sm_mock.auth_user_db.return_value = mock_user()
    return sm_mock


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for each test"""
    # Mock Flask current_app
    with patch('flask.current_app') as mock_app:
        mock_app.config = TEST_CONFIG
        yield mock_app


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    ) 