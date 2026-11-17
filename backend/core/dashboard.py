from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework.response import Response

from accounts.models import User
from business.models import Client, Employee, Product, Service
from core.views import TenantAPIView
from projects.models import Project, Task
from timetracking.models import TimeEntry


class DashboardView(TenantAPIView):
    def get(self, request):
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month = TimeEntry.objects.filter(started_at__gte=month_start)
        total = month.aggregate(s=Sum("duration_seconds"))["s"] or 0
        billable = month.filter(is_billable=True).aggregate(s=Sum("duration_seconds"))["s"] or 0

        by_status = {
            row["column_status"]: row["total"]
            for row in Task.objects.values("column_status").annotate(total=Count("id"))
        }
        low_stock = list(
            Product.objects.filter(quantite_stock__lte=5)
            .order_by("quantite_stock", "id")
            .values("id", "identifiant", "nom", "quantite_stock", "disponibilite")[:5]
        )
        return Response(
            {
                "counts": {
                    "clients": Client.objects.count(),
                    "employees": Employee.objects.count(),
                    "products": Product.objects.count(),
                    "services": Service.objects.count(),
                    "users": User.objects.filter(tenant_id=request.user.tenant_id).count(),
                    "projects": Project.objects.count(),
                },
                "tasks_by_status": by_status,
                "hours_this_month": {"total": round(total / 3600, 2), "billable": round(billable / 3600, 2)},
                "low_stock": low_stock,
            }
        )
