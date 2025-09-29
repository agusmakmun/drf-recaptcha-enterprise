"""
Contact API URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "contact"

# Create router for ViewSet
router = DefaultRouter()
router.register(
    r"submissions",
    views.ContactSubmissionViewSet,
    basename="contact-submission",
)

urlpatterns = [
    # Template-based views
    path("", views.ContactFormView.as_view(), name="contact-form"),  # Root - GET form
    path("form/", views.ContactFormView.as_view(), name="contact-form-alt"),  # GET form
    path(
        "submit/", views.contact_form_submit_template, name="contact-submit"
    ),  # POST form
    path(
        "success/", views.ContactSuccessView.as_view(), name="success"
    ),  # Success page
    # API endpoints (these will be under /api/contact/)
    path("api/", views.contact_form_submit, name="contact-form-submit"),  # POST
    path("api/list/", views.contact_list, name="contact-list"),  # GET
    path(
        "api/<int:pk>/", views.contact_detail, name="contact-detail"
    ),  # GET specific contact
    # Include ViewSet routes
    path("api/", include(router.urls)),
]
