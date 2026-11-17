from datetime import timedelta

from django.utils import timezone

from core.tests.base import ApiTestCase
from projects.models import Task
from timetracking.models import TimeEntry


class TimeTrackingTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.project = self.make_project(self.t1, self.owner1)
        self.login_as(self.member1)

    def start(self, **extra):
        return self.client.post("/api/time-entries/start", {"project_id": self.project.pk, **extra}, format="json")

    def test_only_one_running_timer_per_user(self):
        first = self.start(description="A")
        self.assertEqual(first.status_code, 201, first.content)
        # On recule le début du premier pour que la durée arrêtée soit nettement positive.
        TimeEntry.unscoped.filter(pk=first.json()["id"]).update(started_at=timezone.now() - timedelta(seconds=90))
        second = self.start(description="B")
        self.assertEqual(second.status_code, 201)

        running = TimeEntry.unscoped.filter(user=self.member1, is_running=True)
        self.assertEqual([e.pk for e in running], [second.json()["id"]])
        closed = TimeEntry.unscoped.get(pk=first.json()["id"])
        self.assertFalse(closed.is_running)
        self.assertIsInstance(closed.duration_seconds, int)
        self.assertGreaterEqual(closed.duration_seconds, 90)

    def test_duration_is_never_zero_or_negative(self):
        entry = self.start().json()
        stopped = self.client.patch(f"/api/time-entries/{entry['id']}/stop").json()
        self.assertGreaterEqual(stopped["duration_seconds"], 1)
        self.assertFalse(stopped["is_running"])
        self.assertIsNotNone(stopped["ended_at"])

    def test_stop_is_idempotent(self):
        entry = self.start().json()
        first = self.client.patch(f"/api/time-entries/{entry['id']}/stop").json()
        second = self.client.patch(f"/api/time-entries/{entry['id']}/stop").json()
        self.assertEqual(first["duration_seconds"], second["duration_seconds"])
        self.assertEqual(first["ended_at"], second["ended_at"])

    def test_cannot_stop_someone_elses_timer(self):
        entry = self.start().json()
        self.login_as(self.manager1)
        response = self.client.patch(f"/api/time-entries/{entry['id']}/stop")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(TimeEntry.unscoped.get(pk=entry["id"]).is_running)

    def test_task_must_belong_to_selected_project(self):
        other_project = self.make_project(self.t1, self.owner1, code="PRJ-2")
        task = self.make_task(other_project)
        response = self.start(task_id=task.pk)
        self.assertEqual(response.status_code, 422)
        self.assertIn("task_id", response.json()["errors"])

    def test_entry_shape_matches_contract(self):
        task = self.make_task(self.project)
        entry = self.start(task_id=task.pk, is_billable=False).json()
        self.assertEqual(set(entry["project"]), {"id", "code", "name", "hourly_rate"})
        self.assertEqual(set(entry["task"]), {"id", "title"})
        self.assertEqual(set(entry["user"]), {"id", "nom", "prenom"})
        self.assertIsInstance(entry["project"]["hourly_rate"], (int, float))
        self.assertFalse(entry["is_billable"])

    def test_summary_hours(self):
        now = timezone.now()
        with self.in_tenant(self.t1):
            TimeEntry.objects.create(user=self.member1, project=self.project, started_at=now, duration_seconds=3600, is_billable=True)
            TimeEntry.objects.create(user=self.member1, project=self.project, started_at=now, duration_seconds=1800, is_billable=False)
        summary = self.client.get("/api/time-entries").json()["summary"]
        self.assertEqual(summary, {"total_hours": 1.5, "billable_hours": 1.0, "non_billable_hours": 0.5})
