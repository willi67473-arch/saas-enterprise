from core.tests.base import ApiTestCase


class KanbanTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.owner1)
        self.pid = self.api_create_project()

    def move(self, task_id, column, position):
        response = self.client.patch(f"/api/tasks/{task_id}/move", {"column_status": column, "position": position}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_new_task_goes_to_end_of_column(self):
        self.api_create_task(self.pid, "a")
        self.api_create_task(self.pid, "b")
        self.assertEqual(self.board(self.pid)["TODO"], [(0, "a"), (1, "b")])

    def test_move_to_other_column_reindexes_both_columns(self):
        a = self.api_create_task(self.pid, "a")
        b = self.api_create_task(self.pid, "b")
        c = self.api_create_task(self.pid, "c")
        self.move(c["id"], "IN_PROGRESS", 0)
        board = self.board(self.pid)
        self.assertEqual(board["TODO"], [(0, "a"), (1, "b")])
        self.assertEqual(board["IN_PROGRESS"], [(0, "c")])

        self.move(a["id"], "IN_PROGRESS", 0)  # insertion en tête : c descend
        board = self.board(self.pid)
        self.assertEqual(board["IN_PROGRESS"], [(0, "a"), (1, "c")])
        self.assertEqual(board["TODO"], [(0, "b")])  # colonne d'origine réindexée sans trou

    def test_reorder_inside_same_column(self):
        for title in ("x", "y", "z"):
            task = self.api_create_task(self.pid, title, "DONE")
        self.move(task["id"], "DONE", 0)
        self.assertEqual(self.board(self.pid)["DONE"], [(0, "z"), (1, "x"), (2, "y")])

    def test_position_beyond_end_is_clamped(self):
        a = self.api_create_task(self.pid, "a")
        self.api_create_task(self.pid, "b")
        self.move(a["id"], "TODO", 99)
        self.assertEqual(self.board(self.pid)["TODO"], [(0, "b"), (1, "a")])

    def test_invalid_column_is_422(self):
        task = self.api_create_task(self.pid, "a")
        response = self.client.patch(f"/api/tasks/{task['id']}/move", {"column_status": "NOPE", "position": 0}, format="json")
        self.assertEqual(response.status_code, 422)
        self.assertIn("column_status", response.json()["errors"])

    def test_done_notifies_project_owner_only_when_someone_else_moves_it(self):
        task = self.api_create_task(self.pid, "a")
        self.move(task["id"], "DONE", 0)  # le propriétaire le termine lui-même : pas de notification
        self.assertEqual(self.client.get("/api/notifications").json(), [])

        other = self.api_create_task(self.pid, "b")
        self.login_as(self.manager1)
        self.move(other["id"], "DONE", 0)
        self.login_as(self.owner1)
        notifications = self.client.get("/api/notifications").json()
        self.assertEqual([n["type"] for n in notifications], ["TASK_DONE"])
        self.assertFalse(notifications[0]["is_read"])

        notif_id = notifications[0]["id"]
        self.login_as(self.manager1)
        self.assertEqual(self.client.patch(f"/api/notifications/{notif_id}/read").status_code, 404)  # pas la sienne
        self.login_as(self.owner1)
        self.assertTrue(self.client.patch(f"/api/notifications/{notif_id}/read").json()["is_read"])

    def test_assignment_notifies_assignee_and_exposes_assignee_object(self):
        task = self.api_create_task(self.pid, "a", assignee_id=self.member1.pk, tags=["qa", "docs"])
        self.assertEqual(task["assignee"]["id"], self.member1.pk)
        self.assertEqual(set(task["assignee"]), {"id", "nom", "prenom", "avatar"})
        self.assertEqual(task["tags"], ["qa", "docs"])
        self.login_as(self.member1)
        self.assertEqual([n["type"] for n in self.client.get("/api/notifications").json()], ["TASK_ASSIGNED"])
        self.assertEqual(self.client.post("/api/notifications/read-all").status_code, 200)
        self.assertTrue(all(n["is_read"] for n in self.client.get("/api/notifications").json()))

    def test_projects_list_shape(self):
        self.api_create_task(self.pid, "a")
        project = self.client.get("/api/projects").json()[0]
        self.assertEqual(set(project["owner"]), {"id", "nom", "prenom"})
        self.assertIsInstance(project["budget_hours"], (int, float))
        self.assertEqual(len(project["tasks"]), 1)

    def test_update_and_delete_task(self):
        task = self.api_create_task(self.pid, "a")
        updated = self.client.patch(f"/api/tasks/{task['id']}", {"title": "renommée", "priority": "URGENT"}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["title"], "renommée")
        self.assertEqual(self.client.delete(f"/api/tasks/{task['id']}").status_code, 200)
        self.assertEqual(self.board(self.pid), {})
