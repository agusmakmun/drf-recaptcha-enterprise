"""
Django REST Framework validators for reCAPTCHA Enterprise integration.
"""

from typing import Any, Dict, Optional

from rest_framework import serializers

from .client import ReCaptchaEnterpriseClient


class ReCaptchaEnterpriseValidator:
    """
    A Django REST Framework validator for reCAPTCHA Enterprise tokens.

    This validator can be used with any field to validate reCAPTCHA tokens.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        site_key: Optional[str] = None,
        min_score: float = 0.5,
        expected_action: Optional[str] = None,
        message: str = "reCAPTCHA validation failed.",
    ):
        """
        Initialize the reCAPTCHA Enterprise validator.

        Args:
            project_id: Google Cloud project ID. If not provided, will use
                       RECAPTCHA_ENTERPRISE_PROJECT_ID from Django settings.
            site_key: reCAPTCHA site key. If not provided, will use
                     RECAPTCHA_ENTERPRISE_SITE_KEY from Django settings.
            min_score: Minimum score threshold for validation (0.0 to 1.0)
            expected_action: The expected action name (if using action-based scoring)
            message: Custom error message for validation failures
        """
        self.project_id = project_id
        self.site_key = site_key
        self.min_score = min_score
        self.expected_action = expected_action
        self.message = message

    def __call__(self, value: str, serializer_field: Optional[Any] = None) -> None:
        """
        Validate the reCAPTCHA token.

        Args:
            value: The reCAPTCHA token string
            serializer_field: The serializer field instance (for context)

        Raises:
            serializers.ValidationError: If validation fails
        """
        if not value:
            raise serializers.ValidationError("reCAPTCHA token is required.")

        # Get request context for IP and user agent
        request = None
        if serializer_field and hasattr(serializer_field, "context"):
            request = serializer_field.context.get("request")

        user_ip = None
        user_agent = None

        if request:
            user_ip = self._get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Initialize the client and verify the token
        try:
            client = ReCaptchaEnterpriseClient(
                project_id=self.project_id, site_key=self.site_key
            )

            result = client.verify_token(
                token=value,
                user_ip=user_ip,
                user_agent=user_agent,
                expected_action=self.expected_action,
                min_score=self.min_score,
            )

            if not result["success"]:
                error_message = self._get_error_message(result)
                raise serializers.ValidationError(error_message)

        except Exception as e:
            raise serializers.ValidationError(
                f"reCAPTCHA verification failed: {str(e)}"
            )

    def _get_client_ip(self, request: Any) -> Optional[str]:
        """
        Get the client IP address from the request.

        Args:
            request: Django request object

        Returns:
            Client IP address or None
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return str(ip) if ip else None

    def _get_error_message(self, result: Dict[str, Any]) -> str:
        """
        Generate a user-friendly error message from the verification result.

        Args:
            result: The verification result dictionary

        Returns:
            Error message string
        """
        error_codes = result.get("error_codes", [])
        score = result.get("score", 0.0)

        if "VERIFICATION_FAILED" in error_codes:
            return "reCAPTCHA verification failed. Please try again."
        elif score < self.min_score:
            return (
                f"reCAPTCHA score too low ({score:.2f}). "
                f"Minimum required: {self.min_score}."
            )
        elif not result.get("valid", False):
            return "Invalid reCAPTCHA token."
        else:
            return self.message
