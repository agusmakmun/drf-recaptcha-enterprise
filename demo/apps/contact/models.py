"""
Contact models.
"""

from django.db import models
from django.utils import timezone


class ContactSubmission(models.Model):
    """Model for storing contact form submissions."""

    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(default=timezone.now)
    recaptcha_score = models.FloatField(null=True, blank=True)
    recaptcha_action = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Contact Submission"
        verbose_name_plural = "Contact Submissions"

    def __str__(self):
        return f"Contact from {self.name} ({self.email})"
