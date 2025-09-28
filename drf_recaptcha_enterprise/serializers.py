"""
Django REST Framework serializers for reCAPTCHA Enterprise integration.
"""

from typing import Any, Dict, Optional

from rest_framework import serializers

from .fields import ReCaptchaEnterpriseField


class ReCaptchaEnterpriseSerializer(serializers.Serializer):
    """
    A base serializer that includes reCAPTCHA Enterprise validation.

    This serializer can be used as a mixin or base class for other serializers
    that need reCAPTCHA validation.
    """

    def __init__(
        self,
        *args: Any,
        recaptcha_field_name: str = "recaptcha_token",
        recaptcha_project_id: Optional[str] = None,
        recaptcha_site_key: Optional[str] = None,
        recaptcha_min_score: float = 0.5,
        recaptcha_expected_action: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize the reCAPTCHA Enterprise serializer.

        Args:
            recaptcha_field_name: Name of the reCAPTCHA field in the serializer
            recaptcha_project_id: Google Cloud project ID
            recaptcha_site_key: reCAPTCHA site key
            recaptcha_min_score: Minimum score threshold for validation
            recaptcha_expected_action: Expected action name for action-based scoring
            **kwargs: Additional arguments passed to Serializer
        """
        super().__init__(*args, **kwargs)

        # Add the reCAPTCHA field
        self.fields[recaptcha_field_name] = ReCaptchaEnterpriseField(
            project_id=recaptcha_project_id,
            site_key=recaptcha_site_key,
            min_score=recaptcha_min_score,
            expected_action=recaptcha_expected_action,
            help_text="reCAPTCHA token for verification",
        )

    def get_recaptcha_verification_result(self) -> Optional[Dict[str, Any]]:
        """
        Get the reCAPTCHA verification result from the field.

        Returns:
            The verification result dictionary or None
        """
        recaptcha_field = None
        for field_name, field in self.fields.items():
            if isinstance(field, ReCaptchaEnterpriseField):
                recaptcha_field = field
                break

        if recaptcha_field:
            return recaptcha_field.verification_result

        return None


class ReCaptchaEnterpriseMixin:
    """
    A mixin class that adds reCAPTCHA Enterprise validation to any serializer.

    Usage:
        class MySerializer(ReCaptchaEnterpriseMixin, serializers.ModelSerializer):
            pass
    """

    def __init__(
        self,
        *args: Any,
        recaptcha_field_name: str = "recaptcha_token",
        recaptcha_project_id: Optional[str] = None,
        recaptcha_site_key: Optional[str] = None,
        recaptcha_min_score: float = 0.5,
        recaptcha_expected_action: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize the mixin with reCAPTCHA configuration.

        Args:
            recaptcha_field_name: Name of the reCAPTCHA field
            recaptcha_project_id: Google Cloud project ID
            recaptcha_site_key: reCAPTCHA site key
            recaptcha_min_score: Minimum score threshold
            recaptcha_expected_action: Expected action name
            **kwargs: Additional arguments
        """
        super().__init__(*args, **kwargs)

        # Add the reCAPTCHA field
        self.fields[recaptcha_field_name] = ReCaptchaEnterpriseField(
            project_id=recaptcha_project_id,
            site_key=recaptcha_site_key,
            min_score=recaptcha_min_score,
            expected_action=recaptcha_expected_action,
            help_text="reCAPTCHA token for verification",
        )

    def get_recaptcha_verification_result(self) -> Optional[Dict[str, Any]]:
        """
        Get the reCAPTCHA verification result from the field.

        Returns:
            The verification result dictionary or None
        """
        recaptcha_field = None
        for field_name, field in self.fields.items():
            if isinstance(field, ReCaptchaEnterpriseField):
                recaptcha_field = field
                break

        if recaptcha_field:
            return recaptcha_field.verification_result

        return None
