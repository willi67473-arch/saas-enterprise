from business.models import Client, Product
from core.tests.base import ApiTestCase


class TenantIsolationTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        with self.in_tenant(self.t1):
            self.c1 = Client.objects.create(identifiant="CLT-1", nom="A", prenom="A", email="a@a.io", telephone="1")
        with self.in_tenant(self.t2):
            self.c2 = Client.objects.create(identifiant="CLT-1", nom="B", prenom="B", email="b@b.io", telephone="2")

    def test_list_returns_only_own_tenant(self):
        self.login_as(self.owner1)
        response = self.client.get("/api/clients")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([c["id"] for c in response.json()], [self.c1.pk])

    def test_foreign_object_is_404_not_403(self):
        self.login_as(self.owner1)
        payload = self.client_payload("CLT-1")
        not_found = self.client.put(f"/api/clients/{self.c2.pk}", payload, format="json")
        self.assertEqual(not_found.status_code, 404)
        self.assertEqual(not_found.json(), {"message": "Ressource introuvable."})
        self.assertEqual(self.client.delete(f"/api/clients/{self.c2.pk}").status_code, 404)
        self.assertTrue(Client.unscoped.filter(pk=self.c2.pk).exists())

    def test_create_ignores_tenant_sent_in_body(self):
        self.login_as(self.owner1)
        payload = self.client_payload("CLT-NEW", tenant_id=str(self.t2.pk), tenant=str(self.t2.pk))
        response = self.client.post("/api/clients", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        created = Client.unscoped.get(pk=response.json()["data"]["id"])
        self.assertEqual(created.tenant_id, self.t1.pk)

    def test_tenant_header_cannot_select_another_tenant(self):
        self.login_as(self.owner1)
        response = self.client.get("/api/clients", HTTP_X_TENANT_ID=str(self.t2.pk))
        self.assertEqual([c["id"] for c in response.json()], [self.c1.pk])

    def test_identifiant_unique_per_tenant_only(self):
        # CLT-1 existe déjà dans T1 ET dans T2 : autorisé. Un doublon dans le même tenant est refusé.
        self.login_as(self.owner1)
        duplicate = self.client.post("/api/clients", self.client_payload("CLT-1"), format="json")
        self.assertEqual(duplicate.status_code, 422)
        self.assertIn("identifiant", duplicate.json()["errors"])
        self.assertEqual(self.client.post("/api/clients", self.client_payload("CLT-2"), format="json").status_code, 201)

    def test_unauthenticated_requests_are_401(self):
        self.assertEqual(self.client.get("/api/clients").status_code, 401)

    def test_users_list_is_scoped_to_tenant(self):
        self.login_as(self.admin1)
        emails = {u["email"] for u in self.client.get("/api/users").json()}
        self.assertIn("owner1@test.io", emails)
        self.assertNotIn("owner2@test.io", emails)

    def test_cannot_assign_task_to_user_of_another_tenant(self):
        self.login_as(self.owner1)
        project_id = self.api_create_project()
        response = self.client.post(
            f"/api/projects/{project_id}/tasks",
            {"title": "T", "column_status": "TODO", "priority": "LOW", "assignee_id": self.owner2.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("assignee_id", response.json()["errors"])

    def test_cannot_track_time_on_project_of_another_tenant(self):
        foreign = self.make_project(self.t2, self.owner2)
        self.login_as(self.owner1)
        response = self.client.post("/api/time-entries/start", {"project_id": foreign.pk}, format="json")
        self.assertEqual(response.status_code, 422)

    def test_foreign_project_is_404(self):
        foreign = self.make_project(self.t2, self.owner2)
        self.login_as(self.owner1)
        self.assertEqual(self.client.patch(f"/api/projects/{foreign.pk}", {"name": "x"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/projects/{foreign.pk}").status_code, 404)

    def test_manager_fails_closed_without_tenant_context(self):
        # Hors requête, sans tenant courant : aucune donnée (jamais "tout").
        self.assertEqual(Client.objects.count(), 0)
        with self.in_tenant(self.t1):
            self.assertEqual(Client.objects.count(), 1)

    def test_dashboard_counts_are_scoped(self):
        with self.in_tenant(self.t2):
            Product.objects.create(identifiant="P", nom="p", prix=1, quantite_stock=1, categorie="c")
        self.login_as(self.owner1)
        counts = self.client.get("/api/dashboard").json()["counts"]
        self.assertEqual(counts["clients"], 1)
        self.assertEqual(counts["products"], 0)
        self.assertEqual(counts["users"], 4)
