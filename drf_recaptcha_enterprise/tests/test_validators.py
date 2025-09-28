"""
Unit tests for validators.py module.
"""

from unittest.mock import Mock, patch

import pytest
from rest_framework import serializers

from drf_recaptcha_enterprise.validators import ReCaptchaEnterpriseValidator


class TestReCaptchaEnterpriseValidator:
    """Test ReCaptchaEnterpriseValidator class."""

    def test_init_default_parameters(self):
        """Test validator initialization with default parameters."""
        validator = ReCaptchaEnterpriseValidator()

        assert validator.project_id is None
        assert validator.site_key is None
        assert validator.min_score == 0.5
        assert validator.expected_action is None
        assert validator.message == "reCAPTCHA validation failed."

    def test_init_custom_parameters(self):
        """Test validator initialization with custom parameters."""
        validator = ReCaptchaEnterpriseValidator(
            project_id="custom-project",
            site_key="custom-site-key",
            min_score=0.7,
            expected_action="custom_action",
            message="Custom validation message",
        )

        assert validator.project_id == "custom-project"
        assert validator.site_key == "custom-site-key"
        assert validator.min_score == 0.7
        assert validator.expected_action == "custom_action"
        assert validator.message == "Custom validation message"

    def test_call_empty_token(self):
        """Test validator with empty token."""
        validator = ReCaptchaEnterpriseValidator()

        with pytest.raises(
            serializers.ValidationError, match="reCAPTCHA token is required"
        ):
            validator("")

    def test_call_none_token(self):
        """Test validator with None token."""
        validator = ReCaptchaEnterpriseValidator()

        with pytest.raises(
            serializers.ValidationError, match="reCAPTCHA token is required"
        ):
            validator(None)

    def test_call_success(self, valid_recaptcha_token, sample_verification_result):
        """Test successful token validation."""
        validator = ReCaptchaEnterpriseValidator()

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            # Should not raise an exception
            validator(valid_recaptcha_token)

            mock_client.verify_token.assert_called_once()

    def test_call_with_serializer_field_context(
        self, valid_recaptcha_token, sample_verification_result, mock_serializer_field
    ):
        """Test validator with serializer field context."""
        validator = ReCaptchaEnterpriseValidator()

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            validator(valid_recaptcha_token, serializer_field=mock_serializer_field)

            # Verify that IP and user agent were passed to verify_token
            call_args = mock_client.verify_token.call_args
            assert call_args[1]["user_ip"] == "192.168.1.1"
            assert call_args[1]["user_agent"] == "Mozilla/5.0 (Test Browser)"

    def test_call_verification_failed(
        self, valid_recaptcha_token, sample_failed_verification_result
    ):
        """Test validator with verification failure."""
        validator = ReCaptchaEnterpriseValidator()

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_failed_verification_result
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA verification failed"
            ):
                validator(valid_recaptcha_token)

    def test_call_low_score(self, valid_recaptcha_token):
        """Test validator with low score."""
        validator = ReCaptchaEnterpriseValidator(min_score=0.8)

        low_score_result = {
            "success": False,
            "score": 0.3,
            "action": "submit",
            "error_codes": [],
            "assessment": None,
            "valid": True,
            "hostname": "example.com",
        }

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = low_score_result
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA score too low"
            ):
                validator(valid_recaptcha_token)

    def test_call_invalid_token(self, valid_recaptcha_token):
        """Test validator with invalid token."""
        validator = ReCaptchaEnterpriseValidator()

        invalid_token_result = {
            "success": False,
            "score": 0.8,
            "action": "submit",
            "error_codes": [],
            "assessment": None,
            "valid": False,
            "hostname": "example.com",
        }

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = invalid_token_result
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="Invalid reCAPTCHA token"
            ):
                validator(valid_recaptcha_token)

    def test_call_verification_failed_error_code(self, valid_recaptcha_token):
        """Test validator with VERIFICATION_FAILED error code."""
        validator = ReCaptchaEnterpriseValidator()

        verification_failed_result = {
            "success": False,
            "score": 0.8,
            "action": "submit",
            "error_codes": ["VERIFICATION_FAILED"],
            "assessment": None,
            "valid": True,
            "hostname": "example.com",
        }

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = verification_failed_result
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA verification failed"
            ):
                validator(valid_recaptcha_token)

    def test_call_generic_error(self, valid_recaptcha_token):
        """Test validator with generic error."""
        validator = ReCaptchaEnterpriseValidator(message="Custom error message")

        generic_error_result = {
            "success": False,
            "score": 0.8,
            "action": "submit",
            "error_codes": ["SOME_OTHER_ERROR"],
            "assessment": None,
            "valid": True,
            "hostname": "example.com",
        }

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = generic_error_result
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="Custom error message"
            ):
                validator(valid_recaptcha_token)

    def test_call_client_exception(self, valid_recaptcha_token):
        """Test validator with client exception."""
        validator = ReCaptchaEnterpriseValidator()

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client_class.side_effect = Exception("Client initialization failed")

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA verification failed"
            ):
                validator(valid_recaptcha_token)

    def test_call_verify_token_exception(self, valid_recaptcha_token):
        """Test validator with verify_token exception."""
        validator = ReCaptchaEnterpriseValidator()

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.side_effect = Exception("API Error")
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA verification failed"
            ):
                validator(valid_recaptcha_token)

    def test_get_client_ip_x_forwarded_for(self, mock_request):
        """Test getting client IP from X-Forwarded-For header."""
        validator = ReCaptchaEnterpriseValidator()

        ip = validator._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_remote_addr(self):
        """Test getting client IP from REMOTE_ADDR."""
        validator = ReCaptchaEnterpriseValidator()

        request = Mock()
        request.META = {"REMOTE_ADDR": "127.0.0.1"}

        ip = validator._get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_get_client_ip_no_ip(self):
        """Test getting client IP when no IP is available."""
        validator = ReCaptchaEnterpriseValidator()

        request = Mock()
        request.META = {}

        ip = validator._get_client_ip(request)
        assert ip is None

    def test_get_client_ip_multiple_x_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For with multiple IPs."""
        validator = ReCaptchaEnterpriseValidator()

        request = Mock()
        request.META = {"HTTP_X_FORWARDED_FOR": "192.168.1.1, 10.0.0.1, 172.16.0.1"}

        ip = validator._get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_get_error_message_verification_failed(self):
        """Test error message generation for VERIFICATION_FAILED."""
        validator = ReCaptchaEnterpriseValidator()

        result = {
            "error_codes": ["VERIFICATION_FAILED"],
            "score": 0.8,
            "valid": True,
        }

        message = validator._get_error_message(result)
        assert message == "reCAPTCHA verification failed. Please try again."

    def test_get_error_message_low_score(self):
        """Test error message generation for low score."""
        validator = ReCaptchaEnterpriseValidator(min_score=0.8)

        result = {
            "error_codes": [],
            "score": 0.3,
            "valid": True,
        }

        message = validator._get_error_message(result)
        assert "reCAPTCHA score too low (0.30)" in message
        assert "Minimum required: 0.8" in message

    def test_get_error_message_invalid_token(self):
        """Test error message generation for invalid token."""
        validator = ReCaptchaEnterpriseValidator()

        result = {
            "error_codes": [],
            "score": 0.8,
            "valid": False,
        }

        message = validator._get_error_message(result)
        assert message == "Invalid reCAPTCHA token."

    def test_get_error_message_custom_message(self):
        """Test error message generation with custom message."""
        validator = ReCaptchaEnterpriseValidator(message="Custom validation failed")

        result = {
            "error_codes": ["SOME_OTHER_ERROR"],
            "score": 0.8,
            "valid": True,
        }

        message = validator._get_error_message(result)
        assert message == "Custom validation failed"

    def test_call_with_custom_parameters(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test validator with custom parameters."""
        validator = ReCaptchaEnterpriseValidator(
            project_id="custom-project",
            site_key="custom-site-key",
            min_score=0.7,
            expected_action="custom_action",
        )

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            validator(valid_recaptcha_token)

            # Verify that custom parameters were passed to the client
            mock_client_class.assert_called_once_with(
                project_id="custom-project", site_key="custom-site-key"
            )

            # Verify that custom parameters were passed to verify_token
            call_args = mock_client.verify_token.call_args
            assert call_args[1]["expected_action"] == "custom_action"
            assert call_args[1]["min_score"] == 0.7

    def test_call_without_serializer_field(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test validator without serializer field context."""
        validator = ReCaptchaEnterpriseValidator()

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            validator(valid_recaptcha_token)

            # Verify that no IP or user agent were passed
            call_args = mock_client.verify_token.call_args
            assert call_args[1]["user_ip"] is None
            assert call_args[1]["user_agent"] is None

    def test_call_with_serializer_field_no_context(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test validator with serializer field but no context."""
        validator = ReCaptchaEnterpriseValidator()

        serializer_field = Mock()
        serializer_field.context = {}

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            validator(valid_recaptcha_token, serializer_field=serializer_field)

            # Verify that no IP or user agent were passed
            call_args = mock_client.verify_token.call_args
            assert call_args[1]["user_ip"] is None
            assert call_args[1]["user_agent"] is None

    def test_call_with_serializer_field_no_request(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test validator with serializer field but no request in context."""
        validator = ReCaptchaEnterpriseValidator()

        serializer_field = Mock()
        serializer_field.context = {}

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            validator(valid_recaptcha_token, serializer_field=serializer_field)

            # Verify that no IP or user agent were passed
            call_args = mock_client.verify_token.call_args
            assert call_args[1]["user_ip"] is None
            assert call_args[1]["user_agent"] is None

    def test_validator_usage_in_serializer_field(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test validator usage in a DRF serializer field."""
        validator = ReCaptchaEnterpriseValidator()

        field = serializers.CharField(validators=[validator])

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            # Should not raise an exception
            field.run_validators(valid_recaptcha_token)

    def test_validator_usage_in_serializer_field_failure(self, invalid_recaptcha_token):
        """Test validator usage in a DRF serializer field with failure."""
        validator = ReCaptchaEnterpriseValidator()

        field = serializers.CharField(validators=[validator])

        with patch(
            "drf_recaptcha_enterprise.validators.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = {
                "success": False,
                "score": 0.2,
                "action": "submit",
                "error_codes": ["VERIFICATION_FAILED"],
                "assessment": None,
                "valid": False,
                "hostname": None,
            }
            mock_client_class.return_value = mock_client

            with pytest.raises(serializers.ValidationError):
                field.run_validators(invalid_recaptcha_token)
