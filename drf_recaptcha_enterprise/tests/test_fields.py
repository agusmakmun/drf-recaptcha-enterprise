"""
Unit tests for fields.py module.
"""

from unittest.mock import Mock, patch

import pytest
from rest_framework import serializers

from drf_recaptcha_enterprise.fields import ReCaptchaEnterpriseField


class TestReCaptchaEnterpriseField:
    """Test ReCaptchaEnterpriseField class."""

    def test_init_default_parameters(self):
        """Test field initialization with default parameters."""
        field = ReCaptchaEnterpriseField()

        assert field.project_id is None
        assert field.site_key is None
        assert field.min_score == 0.5
        assert field.expected_action is None
        assert field.write_only is True
        assert field.required is True

    def test_init_custom_parameters(self):
        """Test field initialization with custom parameters."""
        field = ReCaptchaEnterpriseField(
            project_id="custom-project",
            site_key="custom-site-key",
            min_score=0.7,
            expected_action="custom_action",
            write_only=False,
            required=False,
        )

        assert field.project_id == "custom-project"
        assert field.site_key == "custom-site-key"
        assert field.min_score == 0.7
        assert field.expected_action == "custom_action"
        assert field.write_only is False
        assert field.required is False

    def test_to_internal_value_empty_token(self):
        """Test validation with empty token."""
        field = ReCaptchaEnterpriseField()

        with pytest.raises(
            serializers.ValidationError,
            match="reCAPTCHA token is required",
        ):
            field.to_internal_value("")

    def test_to_internal_value_none_token(self):
        """Test validation with None token."""
        field = ReCaptchaEnterpriseField()

        with pytest.raises(serializers.ValidationError):
            field.to_internal_value(None)

    def test_to_internal_value_invalid_type(self):
        """Test validation with invalid token type."""
        field = ReCaptchaEnterpriseField()

        with pytest.raises(serializers.ValidationError):
            field.to_internal_value(123)

    def test_to_internal_value_success(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test successful token validation."""
        field = ReCaptchaEnterpriseField()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            result = field.to_internal_value(valid_recaptcha_token)

            assert result == valid_recaptcha_token
            assert field._verification_result == sample_verification_result
            mock_client.verify_token.assert_called_once()

    def test_to_internal_value_with_request_context(
        self, valid_recaptcha_token, sample_verification_result, mock_request
    ):
        """Test token validation with request context."""
        field = ReCaptchaEnterpriseField()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            # Mock the _get_client_ip method to return the expected IP
            with patch.object(field, "_get_client_ip", return_value="192.168.1.1"):
                # Mock the context property using property decorator
                with patch.object(
                    type(field),
                    "context",
                    property(lambda self: {"request": mock_request}),
                ):
                    result = field.to_internal_value(valid_recaptcha_token)

                    assert result == valid_recaptcha_token

                    # Verify that IP and user agent were passed to verify_token
                    call_args = mock_client.verify_token.call_args
                    assert call_args[1]["user_ip"] == "192.168.1.1"
                    assert call_args[1]["user_agent"] == "Mozilla/5.0 (Test Browser)"

    def test_to_internal_value_verification_failed(
        self, valid_recaptcha_token, sample_failed_verification_result
    ):
        """Test token validation with verification failure."""
        field = ReCaptchaEnterpriseField()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_failed_verification_result
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA verification failed"
            ):
                field.to_internal_value(valid_recaptcha_token)

    def test_to_internal_value_low_score(self, valid_recaptcha_token):
        """Test token validation with low score."""
        field = ReCaptchaEnterpriseField(min_score=0.8)

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
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = low_score_result
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA score too low"
            ):
                field.to_internal_value(valid_recaptcha_token)

    def test_to_internal_value_invalid_token(self, valid_recaptcha_token):
        """Test token validation with invalid token."""
        field = ReCaptchaEnterpriseField()

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
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = invalid_token_result
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="Invalid reCAPTCHA token"
            ):
                field.to_internal_value(valid_recaptcha_token)

    def test_to_internal_value_verification_failed_error_code(
        self, valid_recaptcha_token
    ):
        """Test token validation with VERIFICATION_FAILED error code."""
        field = ReCaptchaEnterpriseField()

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
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = verification_failed_result
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA verification failed"
            ):
                field.to_internal_value(valid_recaptcha_token)

    def test_to_internal_value_client_exception(self, valid_recaptcha_token):
        """Test token validation with client exception."""
        field = ReCaptchaEnterpriseField()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client_class.side_effect = Exception("Client initialization failed")

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA verification failed"
            ):
                field.to_internal_value(valid_recaptcha_token)

    def test_to_internal_value_verify_token_exception(self, valid_recaptcha_token):
        """Test token validation with verify_token exception."""
        field = ReCaptchaEnterpriseField()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.side_effect = Exception("API Error")
            mock_client_class.return_value = mock_client

            with pytest.raises(
                serializers.ValidationError, match="reCAPTCHA verification failed"
            ):
                field.to_internal_value(valid_recaptcha_token)

    def test_get_client_ip_x_forwarded_for(self, mock_request):
        """Test getting client IP from X-Forwarded-For header."""
        field = ReCaptchaEnterpriseField()

        ip = field._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_remote_addr(self):
        """Test getting client IP from REMOTE_ADDR."""
        field = ReCaptchaEnterpriseField()

        request = Mock()
        request.META = {"REMOTE_ADDR": "127.0.0.1"}

        ip = field._get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_get_client_ip_no_ip(self):
        """Test getting client IP when no IP is available."""
        field = ReCaptchaEnterpriseField()

        request = Mock()
        request.META = {}

        ip = field._get_client_ip(request)
        assert ip is None

    def test_get_client_ip_multiple_x_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For with multiple IPs."""
        field = ReCaptchaEnterpriseField()

        request = Mock()
        request.META = {"HTTP_X_FORWARDED_FOR": "192.168.1.1, 10.0.0.1, 172.16.0.1"}

        ip = field._get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_get_error_message_verification_failed(self):
        """Test error message generation for VERIFICATION_FAILED."""
        field = ReCaptchaEnterpriseField()

        result = {
            "error_codes": ["VERIFICATION_FAILED"],
            "score": 0.8,
            "valid": True,
        }

        message = field._get_error_message(result)
        assert message == "reCAPTCHA verification failed. Please try again."

    def test_get_error_message_low_score(self):
        """Test error message generation for low score."""
        field = ReCaptchaEnterpriseField(min_score=0.8)

        result = {
            "error_codes": [],
            "score": 0.3,
            "valid": True,
        }

        message = field._get_error_message(result)
        assert "reCAPTCHA score too low (0.30)" in message
        assert "Minimum required: 0.8" in message

    def test_get_error_message_invalid_token(self):
        """Test error message generation for invalid token."""
        field = ReCaptchaEnterpriseField()

        result = {
            "error_codes": [],
            "score": 0.8,
            "valid": False,
        }

        message = field._get_error_message(result)
        assert message == "Invalid reCAPTCHA token."

    def test_get_error_message_generic(self):
        """Test error message generation for generic failure."""
        field = ReCaptchaEnterpriseField()

        result = {
            "error_codes": ["SOME_OTHER_ERROR"],
            "score": 0.8,
            "valid": True,
        }

        message = field._get_error_message(result)
        assert message == "reCAPTCHA validation failed. Please try again."

    def test_verification_result_property(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test verification_result property."""
        field = ReCaptchaEnterpriseField()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            field.to_internal_value(valid_recaptcha_token)

            assert field.verification_result == sample_verification_result

    def test_verification_result_property_no_verification(self):
        """Test verification_result property when no verification has been performed."""
        field = ReCaptchaEnterpriseField()

        assert field.verification_result is None

    def test_to_internal_value_with_custom_parameters(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test token validation with custom field parameters."""
        field = ReCaptchaEnterpriseField(
            project_id="custom-project",
            site_key="custom-site-key",
            min_score=0.7,
            expected_action="custom_action",
        )

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            field.to_internal_value(valid_recaptcha_token)

            # Verify that custom parameters were passed to the client
            mock_client_class.assert_called_once_with(
                project_id="custom-project", site_key="custom-site-key"
            )

            # Verify that custom parameters were passed to verify_token
            call_args = mock_client.verify_token.call_args
            assert call_args[1]["expected_action"] == "custom_action"
            assert call_args[1]["min_score"] == 0.7

    def test_to_internal_value_without_request_context(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test token validation without request context."""
        field = ReCaptchaEnterpriseField()
        # No context set

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            result = field.to_internal_value(valid_recaptcha_token)

            assert result == valid_recaptcha_token

            # Verify that no IP or user agent were passed
            call_args = mock_client.verify_token.call_args
            assert call_args[1]["user_ip"] is None
            assert call_args[1]["user_agent"] is None

    def test_to_internal_value_with_context_but_no_request(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test token validation with context but no request."""
        field = ReCaptchaEnterpriseField()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            # Mock the context property using property decorator
            with patch.object(type(field), "context", property(lambda self: {})):
                result = field.to_internal_value(valid_recaptcha_token)

                assert result == valid_recaptcha_token

                # Verify that no IP or user agent were passed
                call_args = mock_client.verify_token.call_args
                assert call_args[1]["user_ip"] is None
                assert call_args[1]["user_agent"] is None
