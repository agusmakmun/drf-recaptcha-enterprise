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
    # API endpoints
    path("", views.contact_form_submit, name="contact-form-submit"),  # POST
    path("list/", views.contact_list, name="contact-list"),  # GET
    path(
        "<int:pk>/", views.contact_detail, name="contact-detail"
    ),  # GET specific contact
    # Include ViewSet routes
    path("", include(router.urls)),
]
