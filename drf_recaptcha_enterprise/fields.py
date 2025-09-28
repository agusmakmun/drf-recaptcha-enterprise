"""
Django REST Framework fields for reCAPTCHA Enterprise integration.
"""

from typing import Any, Dict, Optional

from rest_framework import serializers

from .client import ReCaptchaEnterpriseClient


class ReCaptchaEnterpriseField(serializers.CharField):
    """
    A Django REST Framework field for reCAPTCHA Enterprise validation.

    This field validates reCAPTCHA tokens using Google's reCAPTCHA Enterprise API.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        site_key: Optional[str] = None,
        min_score: float = 0.5,
        expected_action: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize the reCAPTCHA Enterprise field.

        Args:
            project_id: Google Cloud project ID. If not provided, will use
                       RECAPTCHA_ENTERPRISE_PROJECT_ID from Django settings.
            site_key: reCAPTCHA site key. If not provided, will use
                     RECAPTCHA_ENTERPRISE_SITE_KEY from Django settings.
            min_score: Minimum score threshold for validation (0.0 to 1.0)
            expected_action: The expected action name (if using action-based scoring)
            **kwargs: Additional arguments passed to CharField
        """
        self.project_id = project_id
        self.site_key = site_key
        self.min_score = min_score
        self.expected_action = expected_action

        # Set default field properties
        kwargs.setdefault("write_only", True)
        kwargs.setdefault("required", True)

        super().__init__(**kwargs)

    def to_internal_value(self, data: str) -> str:
        """
        Validate the reCAPTCHA token and return the original token.

        Args:
            data: The reCAPTCHA token string

        Returns:
            The original token string if validation passes

        Raises:
            serializers.ValidationError: If validation fails
        """
        # First, validate that it's a string
        token = super().to_internal_value(data)

        if not token:
            raise serializers.ValidationError("reCAPTCHA token is required.")

        # Get request context for IP and user agent
        request = self.context.get("request") if hasattr(self, "context") else None
        user_ip = None
        user_agent = None

        if request:
            user_ip = self._get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Initialize the client and verify the token
        try:
            client = ReCaptchaEnterpriseClient(
                project_id=self.project_id,
                site_key=self.site_key,
            )

            result = client.verify_token(
                token=token,
                user_ip=user_ip,
                user_agent=user_agent,
                expected_action=self.expected_action,
                min_score=self.min_score,
            )

            if not result["success"]:
                error_message = self._get_error_message(result)
                raise serializers.ValidationError(error_message)

            # Store the verification result in the field for potential use
            self._verification_result = result

            return str(token)

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
            return "reCAPTCHA validation failed. Please try again."

    @property
    def verification_result(self) -> Optional[Dict[str, Any]]:
        """
        Get the verification result from the last validation.

        Returns:
            The verification result dictionary or None
        """
        return getattr(self, "_verification_result", None)
