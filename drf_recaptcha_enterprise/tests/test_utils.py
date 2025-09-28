"""
Utility functions and helpers for testing.
"""

import json
import tempfile
from typing import Any, Dict
from unittest.mock import Mock

from google.cloud.recaptchaenterprise_v1 import (
    Assessment,
    RiskAnalysis,
    TokenProperties,
)


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


def create_temp_credentials_file(project_id: str = "test-project-id") -> str:
    """Create a temporary credentials file for testing."""
    credentials_data = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
        "client_email": f"test@{project_id}.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(credentials_data, f)
        return f.name


def create_mock_request(
    ip: str = "192.168.1.1", user_agent: str = "Mozilla/5.0 (Test Browser)"
):
    """Create a mock Django request object."""
    request = Mock()
    request.META = {
        "HTTP_X_FORWARDED_FOR": ip,
        "HTTP_USER_AGENT": user_agent,
        "REMOTE_ADDR": "127.0.0.1",
    }
    return request


def create_mock_serializer_field(request=None):
    """Create a mock DRF serializer field with context."""
    field = Mock()
    field.context = {"request": request} if request else {}
    return field


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_mock_assessment_default(self):
        """Test create_mock_assessment with default parameters."""
        assessment = create_mock_assessment()

        assert assessment.risk_analysis.score == 0.8
        assert assessment.token_properties.valid is True
        assert assessment.token_properties.action == "submit"
        assert assessment.token_properties.hostname == "example.com"

    def test_create_mock_assessment_custom(self):
        """Test create_mock_assessment with custom parameters."""
        assessment = create_mock_assessment(score=0.3, valid=False, action="login")

        assert assessment.risk_analysis.score == 0.3
        assert assessment.token_properties.valid is False
        assert assessment.token_properties.action == "login"

    def test_create_verification_result_success(self):
        """Test create_verification_result for success case."""
        result = create_verification_result()

        assert result["success"] is True
        assert result["score"] == 0.8
        assert result["valid"] is True
        assert result["action"] == "submit"
        assert result["error_codes"] == []
        assert result["assessment"] is not None
        assert result["hostname"] == "example.com"

    def test_create_verification_result_failure(self):
        """Test create_verification_result for failure case."""
        result = create_verification_result(
            success=False,
            score=0.2,
            valid=False,
            error_codes=["VERIFICATION_FAILED"],
            error="Test error",
        )

        assert result["success"] is False
        assert result["score"] == 0.2
        assert result["valid"] is False
        assert result["error_codes"] == ["VERIFICATION_FAILED"]
        assert result["assessment"] is None
        assert result["hostname"] is None
        assert result["error"] == "Test error"

    def test_create_temp_credentials_file(self):
        """Test create_temp_credentials_file."""
        import os

        temp_file = create_temp_credentials_file("custom-project")

        try:
            assert os.path.exists(temp_file)

            with open(temp_file, "r") as f:
                data = json.load(f)

            assert data["type"] == "service_account"
            assert data["project_id"] == "custom-project"
            assert data["client_email"] == "test@custom-project.iam.gserviceaccount.com"
        finally:
            os.unlink(temp_file)

    def test_create_mock_request_default(self):
        """Test create_mock_request with default parameters."""
        request = create_mock_request()

        assert request.META["HTTP_X_FORWARDED_FOR"] == "192.168.1.1"
        assert request.META["HTTP_USER_AGENT"] == "Mozilla/5.0 (Test Browser)"
        assert request.META["REMOTE_ADDR"] == "127.0.0.1"

    def test_create_mock_request_custom(self):
        """Test create_mock_request with custom parameters."""
        request = create_mock_request(ip="10.0.0.1", user_agent="Custom Agent")

        assert request.META["HTTP_X_FORWARDED_FOR"] == "10.0.0.1"
        assert request.META["HTTP_USER_AGENT"] == "Custom Agent"

    def test_create_mock_serializer_field_with_request(self):
        """Test create_mock_serializer_field with request."""
        request = create_mock_request()
        field = create_mock_serializer_field(request)

        assert field.context["request"] == request

    def test_create_mock_serializer_field_without_request(self):
        """Test create_mock_serializer_field without request."""
        field = create_mock_serializer_field()

        assert field.context == {}
