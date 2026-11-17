from django.urls import path
from rest_framework.routers import DefaultRouter

from accounts.views import LoginView, LogoutView, MeView, TeamView, UserViewSet


class ApiRouter(DefaultRouter):
    include_root_view = False  # pas de page d'index publique listant les routes
    include_format_suffixes = False


router = ApiRouter(trailing_slash=False)
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("login", LoginView.as_view()),
    path("logout", LogoutView.as_view()),
    path("me", MeView.as_view()),
    path("team", TeamView.as_view()),
] + router.urls
