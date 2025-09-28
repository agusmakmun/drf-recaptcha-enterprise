"""
Contact API views.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from .models import ContactSubmission
from .serializers import ContactFormSerializer, ContactSubmissionSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def contact_form_submit(request):
    """Handle contact form submission with reCAPTCHA validation."""
    serializer = ContactFormSerializer(data=request.data)

    if serializer.is_valid():
        # Get reCAPTCHA verification result
        recaptcha_result = serializer.get_recaptcha_verification_result()

        # Create the contact submission
        contact = serializer.save()

        # Return success response with reCAPTCHA info
        return Response(
            {
                "message": "Contact form submitted successfully",
                "contact_id": contact.id,
                "recaptcha_score": (
                    recaptcha_result["score"] if recaptcha_result else None
                ),
                "recaptcha_action": (
                    recaptcha_result["action"] if recaptcha_result else None
                ),
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def contact_list(request):
    """List all contact submissions."""
    contacts = ContactSubmission.objects.all()
    serializer = ContactSubmissionSerializer(contacts, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def contact_detail(request, pk):
    """Get a specific contact submission."""
    try:
        contact = ContactSubmission.objects.get(pk=pk)
        serializer = ContactSubmissionSerializer(contact)
        return Response(serializer.data)
    except ContactSubmission.DoesNotExist:
        return Response(
            {"error": "Contact submission not found"}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def api_info(request):
    """Get API information and configuration."""
    return Response(
        {
            "api_name": "Django reCAPTCHA Enterprise Demo API",
            "version": "1.0.0",
            "endpoints": {
                "contact": {
                    "submit": {
                        "method": "POST",
                        "url": "/api/contact/",
                        "description": "Submit a contact form with reCAPTCHA validation",
                        "required_fields": [
                            "name",
                            "email",
                            "message",
                            "recaptcha_token",
                        ],
                    },
                    "list": {
                        "method": "GET",
                        "url": "/api/contact/list/",
                        "description": "List all contact submissions",
                    },
                    "detail": {
                        "method": "GET",
                        "url": "/api/contact/{id}/",
                        "description": "Get a specific contact submission",
                    },
                },
            },
            "recaptcha_config": {
                "site_key": settings.RECAPTCHA_ENTERPRISE_SITE_KEY,
                "min_score": settings.RECAPTCHA_ENTERPRISE_MIN_SCORE,
                "expected_action": settings.RECAPTCHA_ENTERPRISE_EXPECTED_ACTION,
            },
        }
    )


class ContactSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading contact submissions."""

    queryset = ContactSubmission.objects.all()
    serializer_class = ContactSubmissionSerializer
    permission_classes = [AllowAny]
