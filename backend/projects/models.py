from django.conf import settings
from django.db import models

from core.models import TenantOwnedModel


class Project(TenantOwnedModel):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default="ACTIVE")  # PLANNING | ACTIVE | ON_HOLD | COMPLETED
    budget_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    deadline = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_projects")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_project_tenant_code"),
        ]


class Task(TenantOwnedModel):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="tasks")
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_tasks"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    column_status = models.CharField(max_length=20, default="TODO")  # TODO | IN_PROGRESS | IN_REVIEW | DONE
    position = models.PositiveIntegerField(default=0)
    priority = models.CharField(max_length=20, default="MEDIUM")  # LOW | MEDIUM | HIGH | URGENT
    tags = models.JSONField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["project", "column_status", "position"], name="task_proj_col_pos_idx"),
        ]
