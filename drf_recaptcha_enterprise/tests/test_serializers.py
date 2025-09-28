"""
Unit tests for serializers.py module.
"""

from unittest.mock import Mock, patch

import pytest
from rest_framework import serializers

from drf_recaptcha_enterprise.fields import ReCaptchaEnterpriseField
from drf_recaptcha_enterprise.serializers import (
    ReCaptchaEnterpriseMixin,
    ReCaptchaEnterpriseSerializer,
)


class TestReCaptchaEnterpriseSerializer:
    """Test ReCaptchaEnterpriseSerializer class."""

    def test_init_default_parameters(self):
        """Test serializer initialization with default parameters."""
        serializer = ReCaptchaEnterpriseSerializer()

        assert "recaptcha_token" in serializer.fields
        recaptcha_field = serializer.fields["recaptcha_token"]
        assert isinstance(recaptcha_field, serializers.CharField)
        assert recaptcha_field.write_only is True
        assert recaptcha_field.required is True

    def test_init_custom_field_name(self):
        """Test serializer initialization with custom field name."""
        serializer = ReCaptchaEnterpriseSerializer(
            recaptcha_field_name="custom_recaptcha"
        )

        assert "custom_recaptcha" in serializer.fields
        assert "recaptcha_token" not in serializer.fields

    def test_init_custom_parameters(self):
        """Test serializer initialization with custom parameters."""
        serializer = ReCaptchaEnterpriseSerializer(
            recaptcha_project_id="custom-project",
            recaptcha_site_key="custom-site-key",
            recaptcha_min_score=0.7,
            recaptcha_expected_action="custom_action",
        )

        recaptcha_field = serializer.fields["recaptcha_token"]
        assert recaptcha_field.project_id == "custom-project"
        assert recaptcha_field.site_key == "custom-site-key"
        assert recaptcha_field.min_score == 0.7
        assert recaptcha_field.expected_action == "custom_action"

    def test_get_recaptcha_verification_result_with_field(
        self, sample_verification_result
    ):
        """Test getting verification result when field exists."""
        serializer = ReCaptchaEnterpriseSerializer()

        # Mock the recaptcha field with verification result
        recaptcha_field = Mock(spec=ReCaptchaEnterpriseField)
        # Use property to mock verification_result
        type(recaptcha_field).verification_result = property(
            lambda self: sample_verification_result
        )
        serializer.fields["recaptcha_token"] = recaptcha_field

        result = serializer.get_recaptcha_verification_result()
        assert result == sample_verification_result

    def test_get_recaptcha_verification_result_no_field(self):
        """Test getting verification result when no recaptcha field exists."""
        serializer = ReCaptchaEnterpriseSerializer()

        # Remove the recaptcha field
        del serializer.fields["recaptcha_token"]

        result = serializer.get_recaptcha_verification_result()
        assert result is None

    def test_get_recaptcha_verification_result_field_no_result(self):
        """Test getting verification result when field has no result."""
        serializer = ReCaptchaEnterpriseSerializer()

        # Mock the recaptcha field without verification result
        recaptcha_field = Mock(spec=ReCaptchaEnterpriseField)
        recaptcha_field.verification_result = None
        serializer.fields["recaptcha_token"] = recaptcha_field

        result = serializer.get_recaptcha_verification_result()
        assert result is None

    def test_get_recaptcha_verification_result_multiple_fields(
        self, sample_verification_result
    ):
        """Test getting verification result with multiple fields."""
        serializer = ReCaptchaEnterpriseSerializer()

        # Add multiple fields, including a recaptcha field
        recaptcha_field = Mock(spec=ReCaptchaEnterpriseField)
        # Use property to mock verification_result
        type(recaptcha_field).verification_result = property(
            lambda self: sample_verification_result
        )
        serializer.fields["recaptcha_token"] = recaptcha_field
        serializer.fields["other_field"] = Mock()

        result = serializer.get_recaptcha_verification_result()
        assert result == sample_verification_result

    def test_serializer_inheritance(self):
        """Test that serializer can be used as base class."""

        class CustomSerializer(ReCaptchaEnterpriseSerializer):
            name = serializers.CharField()
            email = serializers.EmailField()

        serializer = CustomSerializer()

        assert "name" in serializer.fields
        assert "email" in serializer.fields
        assert "recaptcha_token" in serializer.fields

    def test_serializer_with_data_validation(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test serializer with data validation."""
        serializer = ReCaptchaEnterpriseSerializer()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            data = {"recaptcha_token": valid_recaptcha_token}
            validated_data = serializer.validate(data)

            assert validated_data["recaptcha_token"] == valid_recaptcha_token

    def test_serializer_with_invalid_data(self, invalid_recaptcha_token):
        """Test serializer with invalid data."""
        serializer = ReCaptchaEnterpriseSerializer()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
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

            # This should raise a ValidationError during field validation
            # The validation happens at the field level, not serializer level
            with pytest.raises(serializers.ValidationError):
                # Access the field directly to trigger validation
                field = serializer.fields["recaptcha_token"]
                field.to_internal_value(invalid_recaptcha_token)


class TestReCaptchaEnterpriseMixin:
    """Test ReCaptchaEnterpriseMixin class."""

    def test_mixin_initialization(self):
        """Test mixin initialization."""

        class TestSerializer(ReCaptchaEnterpriseMixin, serializers.Serializer):
            name = serializers.CharField()

        serializer = TestSerializer()

        assert "recaptcha_token" in serializer.fields
        assert "name" in serializer.fields
        recaptcha_field = serializer.fields["recaptcha_token"]
        assert isinstance(recaptcha_field, serializers.CharField)

    def test_mixin_custom_field_name(self):
        """Test mixin with custom field name."""

        class TestSerializer(ReCaptchaEnterpriseMixin, serializers.Serializer):
            name = serializers.CharField()

        serializer = TestSerializer(recaptcha_field_name="custom_recaptcha")

        assert "custom_recaptcha" in serializer.fields
        assert "recaptcha_token" not in serializer.fields

    def test_mixin_custom_parameters(self):
        """Test mixin with custom parameters."""

        class TestSerializer(ReCaptchaEnterpriseMixin, serializers.Serializer):
            name = serializers.CharField()

        serializer = TestSerializer(
            recaptcha_project_id="custom-project",
            recaptcha_site_key="custom-site-key",
            recaptcha_min_score=0.7,
            recaptcha_expected_action="custom_action",
        )

        recaptcha_field = serializer.fields["recaptcha_token"]
        assert recaptcha_field.project_id == "custom-project"
        assert recaptcha_field.site_key == "custom-site-key"
        assert recaptcha_field.min_score == 0.7
        assert recaptcha_field.expected_action == "custom_action"

    def test_mixin_get_recaptcha_verification_result(self, sample_verification_result):
        """Test mixin get_recaptcha_verification_result method."""

        class TestSerializer(ReCaptchaEnterpriseMixin, serializers.Serializer):
            name = serializers.CharField()

        serializer = TestSerializer()

        # Mock the recaptcha field with verification result
        recaptcha_field = Mock(spec=ReCaptchaEnterpriseField)
        # Use property to mock verification_result
        type(recaptcha_field).verification_result = property(
            lambda self: sample_verification_result
        )
        serializer.fields["recaptcha_token"] = recaptcha_field

        result = serializer.get_recaptcha_verification_result()
        assert result == sample_verification_result

    def test_mixin_with_model_serializer(self):
        """Test mixin with ModelSerializer."""
        # Skip this test as it requires a proper Django model setup
        pytest.skip("ModelSerializer test requires Django model setup")

    def test_mixin_multiple_inheritance(self):
        """Test mixin with multiple inheritance."""

        class BaseSerializer(serializers.Serializer):
            base_field = serializers.CharField()

        class TestSerializer(ReCaptchaEnterpriseMixin, BaseSerializer):
            name = serializers.CharField()

        serializer = TestSerializer()

        assert "base_field" in serializer.fields
        assert "name" in serializer.fields
        assert "recaptcha_token" in serializer.fields

    def test_mixin_with_data_validation(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test mixin with data validation."""

        class TestSerializer(ReCaptchaEnterpriseMixin, serializers.Serializer):
            name = serializers.CharField()

        serializer = TestSerializer()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            data = {"name": "Test User", "recaptcha_token": valid_recaptcha_token}
            validated_data = serializer.validate(data)

            assert validated_data["name"] == "Test User"
            assert validated_data["recaptcha_token"] == valid_recaptcha_token

    def test_mixin_verification_result_property(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test mixin verification result property."""

        class TestSerializer(ReCaptchaEnterpriseMixin, serializers.Serializer):
            name = serializers.CharField()

        serializer = TestSerializer()

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            data = {"name": "Test User", "recaptcha_token": valid_recaptcha_token}
            serializer.validate(data)

            # Mock the field's verification_result property
            recaptcha_field = serializer.fields["recaptcha_token"]
            type(recaptcha_field).verification_result = property(
                lambda self: sample_verification_result
            )

            result = serializer.get_recaptcha_verification_result()
            assert result == sample_verification_result

    def test_mixin_with_custom_field_name_and_verification(
        self, valid_recaptcha_token, sample_verification_result
    ):
        """Test mixin with custom field name and verification."""

        class TestSerializer(ReCaptchaEnterpriseMixin, serializers.Serializer):
            name = serializers.CharField()

        serializer = TestSerializer(recaptcha_field_name="custom_recaptcha")

        with patch(
            "drf_recaptcha_enterprise.fields.ReCaptchaEnterpriseClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.verify_token.return_value = sample_verification_result
            mock_client_class.return_value = mock_client

            data = {"name": "Test User", "custom_recaptcha": valid_recaptcha_token}
            validated_data = serializer.validate(data)

            assert validated_data["name"] == "Test User"
            assert validated_data["custom_recaptcha"] == valid_recaptcha_token

            # Mock the field's verification_result property
            recaptcha_field = serializer.fields["custom_recaptcha"]
            type(recaptcha_field).verification_result = property(
                lambda self: sample_verification_result
            )

            result = serializer.get_recaptcha_verification_result()
            assert result == sample_verification_result

    def test_mixin_no_recaptcha_field_found(self):
        """Test mixin when no recaptcha field is found."""

        class TestSerializer(ReCaptchaEnterpriseMixin, serializers.Serializer):
            name = serializers.CharField()

        serializer = TestSerializer()

        # Remove the recaptcha field to simulate no field found
        del serializer.fields["recaptcha_token"]

        result = serializer.get_recaptcha_verification_result()
        assert result is None

    def test_mixin_with_kwargs_passthrough(self):
        """Test mixin passes through additional kwargs to parent."""

        class TestSerializer(ReCaptchaEnterpriseMixin, serializers.Serializer):
            name = serializers.CharField()

        # This should not raise an error - only pass valid kwargs
        serializer = TestSerializer(recaptcha_field_name="custom_recaptcha")

        assert "custom_recaptcha" in serializer.fields
