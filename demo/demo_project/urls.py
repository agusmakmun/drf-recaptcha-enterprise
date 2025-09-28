"""
URL configuration for demo project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.contact.views import api_info

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_info, name="api-info"),  # API information endpoint
    path("api/contact/", include("apps.contact.urls")),  # Contact API
]

# Serve media files during development (for file uploads if needed)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
