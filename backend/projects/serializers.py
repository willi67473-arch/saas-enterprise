from rest_framework import serializers

from accounts.models import User
from core.constants import PROJECT_STATUSES, TASK_COLUMNS, TASK_PRIORITIES
from core.fields import TenantUserField
from core.serializers import TenantUniqueSerializerMixin
from projects.models import Project, Task


class AssigneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "nom", "prenom", "avatar")
        read_only_fields = fields


class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "nom", "prenom")
        read_only_fields = fields


class TaskSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(read_only=True)
    project_id = serializers.IntegerField(read_only=True)
    assignee_id = serializers.IntegerField(read_only=True)
    assignee = AssigneeSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ("id", "tenant_id", "project_id", "assignee_id", "assignee", "title", "description",
                  "column_status", "position", "priority", "tags", "due_date", "created_at", "updated_at")
        read_only_fields = fields


class ProjectSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(read_only=True)
    owner = OwnerSerializer(read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ("id", "tenant_id", "code", "name", "description", "status", "budget_hours", "hourly_rate",
                  "deadline", "owner", "tasks", "created_at", "updated_at")
        read_only_fields = fields


class ProjectCreateSerializer(TenantUniqueSerializerMixin, serializers.ModelSerializer):
    budget_hours = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0, required=False, allow_null=True)
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, allow_null=True)
    tenant_unique_fields = ("code",)

    class Meta:
        model = Project
        fields = ("code", "name", "description", "budget_hours", "hourly_rate", "deadline")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get("budget_hours") is None:
            attrs["budget_hours"] = 0
        if attrs.get("hourly_rate") is None:
            attrs["hourly_rate"] = 100
        return attrs


class ProjectUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=PROJECT_STATUSES, required=False)
    budget_hours = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0, required=False)
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)

    class Meta:
        model = Project
        fields = ("name", "description", "status", "budget_hours", "hourly_rate", "deadline")


class TaskWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    column_status = serializers.ChoiceField(choices=TASK_COLUMNS)
    priority = serializers.ChoiceField(choices=TASK_PRIORITIES)
    # N'accepte que des utilisateurs du tenant courant
    assignee_id = TenantUserField(source="assignee", required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=30), required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)


class TaskUpdateSerializer(TaskWriteSerializer):
    column_status = None  # le changement de colonne passe uniquement par /tasks/{id}/move


class TaskMoveSerializer(serializers.Serializer):
    column_status = serializers.ChoiceField(choices=TASK_COLUMNS)
    position = serializers.IntegerField(min_value=0)
