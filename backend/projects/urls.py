from django.urls import path

from projects.views import (
    ProjectDetailView,
    ProjectListCreateView,
    TaskCreateView,
    TaskDetailView,
    TaskMoveView,
)

urlpatterns = [
    path("projects", ProjectListCreateView.as_view()),
    path("projects/<int:pk>", ProjectDetailView.as_view()),
    path("projects/<int:pk>/tasks", TaskCreateView.as_view()),
    path("tasks/<int:pk>", TaskDetailView.as_view()),
    path("tasks/<int:pk>/move", TaskMoveView.as_view()),
]
