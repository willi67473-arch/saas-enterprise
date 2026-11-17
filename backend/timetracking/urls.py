from django.urls import path

from timetracking.views import StartTimerView, StopTimerView, TimeEntryListView

urlpatterns = [
    path("time-entries", TimeEntryListView.as_view()),
    path("time-entries/start", StartTimerView.as_view()),
    path("time-entries/<int:pk>/stop", StopTimerView.as_view()),
]
