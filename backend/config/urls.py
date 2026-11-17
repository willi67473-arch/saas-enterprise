from django.urls import include, path, re_path

from core.dashboard import DashboardView
from core.views import api_not_found

urlpatterns = [
    path("api/dashboard", DashboardView.as_view()),
    path("api/", include("accounts.urls")),
    path("api/", include("billing.urls")),
    path("api/", include("business.urls")),
    path("api/", include("projects.urls")),
    path("api/", include("timetracking.urls")),
    path("api/", include("notifications.urls")),
    # Toute autre URL /api/... : réponse JSON (et non une page HTML)
    re_path(r"^api/.*$", api_not_found),
]
