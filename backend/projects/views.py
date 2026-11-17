from django.db import transaction
from django.db.models import Max, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsManagerRole
from core.views import TenantAPIView
from notifications.models import Notification
from projects.models import Project, Task
from projects.serializers import (
    ProjectCreateSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
    TaskMoveSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
    TaskWriteSerializer,
)


def projects_queryset():
    """Projets du tenant courant avec leurs tâches triées, sans requêtes N+1."""
    tasks = Task.objects.select_related("assignee").order_by("position", "id")
    return Project.objects.select_related("owner").prefetch_related(Prefetch("tasks", queryset=tasks))


class ProjectListCreateView(TenantAPIView):
    def get(self, request):
        return Response(ProjectSerializer(projects_queryset().order_by("-id"), many=True).data)

    def post(self, request):
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = request.user.tenant.plan
        if plan and Project.objects.count() >= plan.max_projects:
            raise PermissionDenied(f"Limite de {plan.max_projects} projets atteinte pour votre plan {plan.name}.")

        project = serializer.save(owner=request.user, status="ACTIVE")
        return Response(ProjectSerializer(projects_queryset().get(pk=project.pk)).data, status=201)


class ProjectDetailView(TenantAPIView):
    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsManagerRole()]
        return [IsAuthenticated()]

    def patch(self, request, pk):
        project = get_object_or_404(Project.objects.all(), pk=pk)  # 404 hors tenant
        serializer = ProjectUpdateSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProjectSerializer(projects_queryset().get(pk=project.pk)).data)

    def delete(self, request, pk):
        get_object_or_404(Project.objects.all(), pk=pk).delete()
        return Response({"message": "Projet supprimé"})


class TaskCreateView(TenantAPIView):
    def post(self, request, pk):
        project = get_object_or_404(Project.objects.all(), pk=pk)
        serializer = TaskWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        last = Task.objects.filter(project=project, column_status=data["column_status"]).aggregate(m=Max("position"))["m"]
        task = Task.objects.create(
            project=project,
            position=0 if last is None else last + 1,  # en fin de colonne
            **data,
        )

        assignee = task.assignee
        if assignee is not None and assignee.pk != request.user.pk:
            Notification.objects.create(
                user=assignee,
                type="TASK_ASSIGNED",
                title="Nouvelle tâche assignée",
                message=f"La tâche « {task.title} » vous a été attribuée sur {project.name}.",
                payload={"task_id": task.pk, "project_id": project.pk},
            )
        task = Task.objects.select_related("assignee").get(pk=task.pk)
        return Response(TaskSerializer(task).data, status=201)


class TaskDetailView(TenantAPIView):
    def patch(self, request, pk):
        task = get_object_or_404(Task.objects.all(), pk=pk)
        serializer = TaskUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(task, field, value)
        task.save()
        task = Task.objects.select_related("assignee").get(pk=task.pk)
        return Response(TaskSerializer(task).data)

    def delete(self, request, pk):
        get_object_or_404(Task.objects.all(), pk=pk).delete()
        return Response({"message": "Tâche supprimée"})


def _apply_order(task_ids, column):
    """Affecte positions 0..n-1 (et la colonne) aux tâches, dans l'ordre fourni."""
    tasks = {task.pk: task for task in Task.objects.filter(pk__in=task_ids)}
    now = timezone.now()
    changed = []
    for index, task_id in enumerate(task_ids):
        task = tasks[task_id]
        task.position = index
        task.column_status = column
        task.updated_at = now
        changed.append(task)
    Task.objects.bulk_update(changed, ["position", "column_status", "updated_at"])


class TaskMoveView(TenantAPIView):
    """Glisser-déposer : change de colonne ET de position, puis réindexe colonne cible et colonne d'origine."""

    def patch(self, request, pk):
        task = get_object_or_404(Task.objects.select_related("project"), pk=pk)
        serializer = TaskMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        column = serializer.validated_data["column_status"]
        position = serializer.validated_data["position"]
        origin = task.column_status

        with transaction.atomic():
            target_ids = list(
                Task.objects.filter(project_id=task.project_id, column_status=column)
                .exclude(pk=task.pk)
                .order_by("position", "id")
                .values_list("pk", flat=True)
            )
            target_ids.insert(min(position, len(target_ids)), task.pk)
            _apply_order(target_ids, column)

            if origin != column:
                origin_ids = list(
                    Task.objects.filter(project_id=task.project_id, column_status=origin)
                    .order_by("position", "id")
                    .values_list("pk", flat=True)
                )
                _apply_order(origin_ids, origin)

            if column == "DONE" and origin != "DONE" and task.project.owner_id != request.user.pk:
                Notification.objects.create(
                    user_id=task.project.owner_id,
                    type="TASK_DONE",
                    title="Tâche terminée",
                    message=f"La tâche « {task.title} » est passée en Terminé sur {task.project.name}.",
                    payload={"task_id": task.pk, "project_id": task.project_id},
                )

        task = Task.objects.select_related("assignee").get(pk=task.pk)
        return Response(TaskSerializer(task).data)
