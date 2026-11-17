from django.conf import settings
from django.db import models

from core.models import TenantOwnedModel


class TimeEntry(TenantOwnedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="time_entries")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="time_entries")
    task = models.ForeignKey("projects.Task", null=True, blank=True, on_delete=models.SET_NULL, related_name="time_entries")
    description = models.CharField(max_length=255, null=True, blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    is_billable = models.BooleanField(default=True)
    is_running = models.BooleanField(default=False)

    class Meta:
        constraints = [
            # Au plus UN chronomètre actif par utilisateur, garanti par la base (même en concurrence).
            models.UniqueConstraint(
                fields=["user"], condition=models.Q(is_running=True), name="uniq_running_timer_per_user"
            ),
        ]
