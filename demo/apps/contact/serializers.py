"""
Contact serializers.
"""

from rest_framework import serializers
from drf_recaptcha_enterprise import ReCaptchaEnterpriseSerializer
from .models import ContactSubmission


class ContactFormSerializer(ReCaptchaEnterpriseSerializer):
    """Serializer for contact form with reCAPTCHA Enterprise validation."""

    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    message = serializers.CharField()

    class Meta:
        fields = ["name", "email", "message", "recaptcha_token"]

    def create(self, validated_data):
        """Create a new contact submission."""
        # Get reCAPTCHA verification result
        recaptcha_result = self.get_recaptcha_verification_result()

        # Remove reCAPTCHA token from validated data
        validated_data.pop("recaptcha_token", None)

        # Create the contact submission
        contact = ContactSubmission.objects.create(
            name=validated_data["name"],
            email=validated_data["email"],
            message=validated_data["message"],
            recaptcha_score=recaptcha_result["score"] if recaptcha_result else None,
            recaptcha_action=recaptcha_result["action"] if recaptcha_result else None,
        )

        return contact


class ContactSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for contact submission model."""

    class Meta:
        model = ContactSubmission
        fields = [
            "id",
            "name",
            "email",
            "message",
            "submitted_at",
            "recaptcha_score",
            "recaptcha_action",
        ]
        read_only_fields = ["id", "submitted_at", "recaptcha_score", "recaptcha_action"]
