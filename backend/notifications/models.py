from django.conf import settings
from django.db import models

from core.models import TenantOwnedModel


class Notification(TenantOwnedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    payload = models.JSONField(null=True, blank=True)
