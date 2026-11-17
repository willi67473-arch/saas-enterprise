from rest_framework import serializers

from accounts.models import User
from core.fields import TenantRelatedField
from projects.models import Project, Task
from timetracking.models import TimeEntry


class EntryProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "code", "name", "hourly_rate")
        read_only_fields = fields


class EntryTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "title")
        read_only_fields = fields


class EntryUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "nom", "prenom")
        read_only_fields = fields


class TimeEntrySerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    project_id = serializers.IntegerField(read_only=True)
    task_id = serializers.IntegerField(read_only=True)
    project = EntryProjectSerializer(read_only=True)
    task = EntryTaskSerializer(read_only=True)
    user = EntryUserSerializer(read_only=True)

    class Meta:
        model = TimeEntry
        fields = ("id", "tenant_id", "user_id", "project_id", "task_id", "project", "task", "user",
                  "description", "started_at", "ended_at", "duration_seconds", "is_billable", "is_running",
                  "created_at", "updated_at")
        read_only_fields = fields


class StartTimerSerializer(serializers.Serializer):
    # Seuls les projets/tâches du tenant courant sont acceptés (sinon 422).
    project_id = TenantRelatedField(Project, source="project")
    task_id = TenantRelatedField(Task, source="task", required=False, allow_null=True)
    description = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    is_billable = serializers.BooleanField(default=True)

    def validate(self, attrs):
        task = attrs.get("task")
        if task is not None and task.project_id != attrs["project"].pk:
            raise serializers.ValidationError({"task_id": ["Cette tâche n'appartient pas au projet sélectionné."]})
        return attrs
