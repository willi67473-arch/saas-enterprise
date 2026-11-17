from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response

from core.constants import MANAGER_ROLES
from core.views import TenantAPIView
from timetracking.models import TimeEntry
from timetracking.serializers import StartTimerSerializer, TimeEntrySerializer


class Conflict(APIException):
    status_code = 409
    default_detail = "Un chronomètre est déjà actif. Réessayez."
    default_code = "conflict"


def entries_queryset():
    return TimeEntry.objects.select_related("project", "task", "user")


def close_entry(entry, now):
    """Arrête un chronomètre : durée en secondes ENTIÈRES POSITIVES (au moins 1)."""
    seconds = int((now - entry.started_at).total_seconds())
    entry.ended_at = now
    entry.duration_seconds = max(1, seconds)
    entry.is_running = False
    entry.save(update_fields=["ended_at", "duration_seconds", "is_running", "updated_at"])


class TimeEntryListView(TenantAPIView):
    def get(self, request):
        queryset = entries_queryset().order_by("-started_at", "-id")
        # Un simple utilisateur ne voit que ses propres temps ; les managers voient tout le tenant.
        if request.user.role not in MANAGER_ROLES:
            queryset = queryset.filter(user=request.user)

        entries = list(queryset[:300])
        total = sum(e.duration_seconds for e in entries)
        billable = sum(e.duration_seconds for e in entries if e.is_billable)
        return Response(
            {
                "entries": TimeEntrySerializer(entries, many=True).data,
                "summary": {
                    "total_hours": round(total / 3600, 2),
                    "billable_hours": round(billable / 3600, 2),
                    "non_billable_hours": round((total - billable) / 3600, 2),
                },
            }
        )


class StartTimerView(TenantAPIView):
    def post(self, request):
        serializer = StartTimerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            with transaction.atomic():
                now = timezone.now()
                # Un seul chronomètre actif par utilisateur : on arrête le précédent.
                for running in TimeEntry.objects.filter(user=request.user, is_running=True):
                    close_entry(running, now)
                entry = TimeEntry.objects.create(
                    user=request.user,
                    project=data["project"],
                    task=data.get("task"),
                    description=data.get("description") or "Session de travail",
                    started_at=now,
                    is_billable=data["is_billable"],
                    is_running=True,
                )
        except IntegrityError:
            raise Conflict()  # contrainte unique "un chronomètre actif par utilisateur"

        return Response(TimeEntrySerializer(entries_queryset().get(pk=entry.pk)).data, status=201)


class StopTimerView(TenantAPIView):
    def patch(self, request, pk):
        entry = get_object_or_404(entries_queryset(), pk=pk)  # 404 hors tenant
        if entry.user_id != request.user.pk:
            raise PermissionDenied("Ce chronomètre appartient à un autre utilisateur.")
        if entry.is_running:  # idempotent : un second appel ne change rien
            close_entry(entry, timezone.now())
        return Response(TimeEntrySerializer(entries_queryset().get(pk=entry.pk)).data)
