"""
Pytest configuration and fixtures for unit tests.
"""

import json
import os
import tempfile
from typing import Any, Dict
from unittest.mock import Mock

import pytest
from google.cloud.recaptchaenterprise_v1 import (
    Assessment,
    RiskAnalysis,
    TokenProperties,
)

# Configure Django settings for testing
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test-secret-key",
        DEBUG=True,
        USE_I18N=True,
        USE_L10N=True,
        USE_TZ=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "rest_framework",
        ],
        REST_FRAMEWORK={
            "DEFAULT_RENDERER_CLASSES": [
                "rest_framework.renderers.JSONRenderer",
            ],
            "DEFAULT_PARSER_CLASSES": [
                "rest_framework.parsers.JSONParser",
            ],
        },
        RECAPTCHA_ENTERPRISE_PROJECT_ID="test-project-id",
        RECAPTCHA_ENTERPRISE_SITE_KEY="test-site-key",
    )
    django.setup()


@pytest.fixture
def mock_credentials():
    """Mock Google Cloud credentials."""
    credentials = Mock()
    credentials.project_id = "test-project-id"
    return credentials


@pytest.fixture
def mock_service_account_credentials():
    """Mock service account credentials."""
    credentials = Mock()
    credentials.project_id = "test-project-id"
    credentials.type = "service_account"
    return credentials


@pytest.fixture
def temp_credentials_file():
    """Create a temporary credentials file for testing."""
    credentials_data = {
        "type": "service_account",
        "project_id": "test-project-id",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project-id.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(credentials_data, f)
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def mock_assessment():
    """Mock reCAPTCHA Enterprise Assessment object."""
    assessment = Mock(spec=Assessment)

    # Mock risk analysis
    risk_analysis = Mock(spec=RiskAnalysis)
    risk_analysis.score = 0.8
    risk_analysis.reasons = []
    assessment.risk_analysis = risk_analysis

    # Mock token properties
    token_properties = Mock(spec=TokenProperties)
    token_properties.valid = True
    token_properties.action = "submit"
    token_properties.hostname = "example.com"
    assessment.token_properties = token_properties

    return assessment


@pytest.fixture
def mock_recaptcha_client():
    """Mock reCAPTCHA Enterprise client."""
    client = Mock()
    client.create_assessment.return_value = mock_assessment()
    return client


@pytest.fixture
def mock_django_settings():
    """Mock Django settings for testing."""
    settings = Mock()
    settings.RECAPTCHA_ENTERPRISE_PROJECT_ID = "test-project-id"
    settings.RECAPTCHA_ENTERPRISE_SITE_KEY = "test-site-key"
    return settings


@pytest.fixture
def mock_request():
    """Mock Django request object."""
    request = Mock()
    request.META = {
        "HTTP_X_FORWARDED_FOR": "192.168.1.1",
        "HTTP_USER_AGENT": "Mozilla/5.0 (Test Browser)",
        "REMOTE_ADDR": "127.0.0.1",
    }
    return request


@pytest.fixture
def mock_serializer_field(mock_request):
    """Mock DRF serializer field."""
    field = Mock()
    field.context = {"request": mock_request}
    return field


@pytest.fixture
def sample_verification_result():
    """Sample verification result dictionary."""
    return {
        "success": True,
        "score": 0.8,
        "action": "submit",
        "error_codes": [],
        "assessment": create_mock_assessment(),
        "valid": True,
        "hostname": "example.com",
    }


@pytest.fixture
def sample_failed_verification_result():
    """Sample failed verification result dictionary."""
    return {
        "success": False,
        "score": 0.2,
        "action": "submit",
        "error_codes": ["VERIFICATION_FAILED"],
        "assessment": None,
        "valid": False,
        "hostname": None,
        "error": "Token verification failed",
    }


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    env_vars = {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json",
        "RECAPTCHA_ENTERPRISE_PROJECT_ID": "test-project-id",
        "RECAPTCHA_ENTERPRISE_SITE_KEY": "test-site-key",
    }

    with pytest.MonkeyPatch().context() as m:
        for key, value in env_vars.items():
            m.setenv(key, value)
        yield env_vars


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for gcloud config testing."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "test-project-id\n"
    return mock_result


# Test data fixtures
@pytest.fixture
def valid_recaptcha_token():
    """Valid reCAPTCHA token for testing."""
    return "03AGdBq25SXTXT-mSkeTjhz2REIlidLhI3I3mCzFSJzAWuOVy1IvNd1gVYxJR_0kR8uA2HTT1HTi5MwUjlHDkUlamFREXucPpEd1va6J4D8dKf5aLmMgerX8DfK8lC6V8dbuhEDDUbbnyQeS4nltkO1WS8xKZ1-jUg6XoZ6m2AeXHTc7L0HU6p3O1L9mr4X1Xj2oK3L9p4R5s6T7u8V9w0X1Y2Z3A4B5C6D7E8F9G0H1I2J3K4L5M6N7O8P9Q0R1S2T3U4V5W6X7Y8Z9"


@pytest.fixture
def invalid_recaptcha_token():
    """Invalid reCAPTCHA token for testing."""
    return "invalid-token"


@pytest.fixture
def empty_recaptcha_token():
    """Empty reCAPTCHA token for testing."""
    return ""


# Utility functions for tests
def create_mock_assessment(
    score: float = 0.8, valid: bool = True, action: str = "submit"
) -> Mock:
    """Create a mock assessment with specified properties."""
    assessment = Mock(spec=Assessment)

    risk_analysis = Mock(spec=RiskAnalysis)
    risk_analysis.score = score
    risk_analysis.reasons = []
    assessment.risk_analysis = risk_analysis

    token_properties = Mock(spec=TokenProperties)
    token_properties.valid = valid
    token_properties.action = action
    token_properties.hostname = "example.com"
    assessment.token_properties = token_properties

    return assessment


def create_verification_result(
    success: bool = True,
    score: float = 0.8,
    valid: bool = True,
    action: str = "submit",
    error_codes: list = None,
    error: str = None,
) -> Dict[str, Any]:
    """Create a verification result dictionary with specified properties."""
    if error_codes is None:
        error_codes = []

    result = {
        "success": success,
        "score": score,
        "action": action,
        "error_codes": error_codes,
        "assessment": create_mock_assessment(score, valid, action) if success else None,
        "valid": valid,
        "hostname": "example.com" if valid else None,
    }

    if error:
        result["error"] = error

    return result
