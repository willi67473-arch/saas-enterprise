from accounts.models import User
from core.tests.base import ApiTestCase


class RolePermissionTests(ApiTestCase):
    def test_user_can_read_but_not_write_clients(self):
        self.login_as(self.member1)
        self.assertEqual(self.client.get("/api/clients").status_code, 200)
        denied = self.client.post("/api/clients", self.client_payload(), format="json")
        self.assertEqual(denied.status_code, 403)
        self.assertIn("message", denied.json())

    def test_user_cannot_see_employees_or_users(self):
        self.login_as(self.member1)
        self.assertEqual(self.client.get("/api/employees").status_code, 403)
        self.assertEqual(self.client.get("/api/users").status_code, 403)

    def test_user_cannot_manage_billing_or_invitations(self):
        self.login_as(self.member1)
        self.assertEqual(self.client.post("/api/billing/subscribe", {"plan_id": self.pro.pk}, format="json").status_code, 403)
        self.assertEqual(self.client.post("/api/tenants/invite", {"email": "x@y.io", "role": "USER"}, format="json").status_code, 403)

    def test_manager_can_write_clients_and_read_employees_but_not_manage_users(self):
        self.login_as(self.manager1)
        self.assertEqual(self.client.post("/api/clients", self.client_payload(), format="json").status_code, 201)
        self.assertEqual(self.client.get("/api/employees").status_code, 200)
        self.assertEqual(self.client.get("/api/users").status_code, 403)
        self.assertEqual(self.client.post("/api/tenants/invite", {"email": "x@y.io", "role": "USER"}, format="json").status_code, 403)

    def test_admin_can_manage_users_and_invite(self):
        self.login_as(self.admin1)
        self.assertEqual(self.client.get("/api/users").status_code, 200)
        invited = self.client.post("/api/tenants/invite", {"email": "new@y.io", "role": "USER"}, format="json")
        self.assertEqual(invited.status_code, 201)

    def test_only_managers_can_delete_a_project(self):
        project = self.make_project(self.t1, self.owner1)
        self.login_as(self.member1)
        self.assertEqual(self.client.delete(f"/api/projects/{project.pk}").status_code, 403)
        self.login_as(self.manager1)
        self.assertEqual(self.client.delete(f"/api/projects/{project.pk}").status_code, 200)

    def test_admin_cannot_modify_the_owner_account(self):
        self.login_as(self.admin1)
        payload = {"nom": "X", "prenom": "Y", "email": "owner1@test.io", "role": "SUPER_ADMIN", "status": "ACTIVE", "password": "NewPassw0rd!"}
        self.assertEqual(self.client.put(f"/api/users/{self.owner1.pk}", payload, format="json").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/users/{self.owner1.pk}").status_code, 403)

    def test_nobody_can_delete_self_or_owner(self):
        self.login_as(self.owner1)
        self.assertEqual(self.client.delete(f"/api/users/{self.owner1.pk}").status_code, 422)
        other_owner = self.make_user(self.t1, "owner1b@test.io", "SUPER_ADMIN")
        self.assertEqual(self.client.delete(f"/api/users/{other_owner.pk}").status_code, 422)

    def test_super_admin_role_cannot_be_granted_through_api(self):
        self.login_as(self.owner1)
        payload = {"nom": "N", "prenom": "P", "email": "boss@test.io", "role": "SUPER_ADMIN", "status": "ACTIVE"}
        response = self.client.post("/api/users", payload, format="json")
        self.assertEqual(response.status_code, 422)
        self.assertIn("role", response.json()["errors"])
        promote = {"nom": "N", "prenom": "P", "email": self.member1.email, "role": "SUPER_ADMIN", "status": "ACTIVE"}
        self.assertEqual(self.client.put(f"/api/users/{self.member1.pk}", promote, format="json").status_code, 422)

    def test_cannot_suspend_self(self):
        self.login_as(self.admin1)
        payload = {"nom": "N", "prenom": "P", "email": self.admin1.email, "role": "ADMIN", "status": "SUSPENDED"}
        response = self.client.put(f"/api/users/{self.admin1.pk}", payload, format="json")
        self.assertEqual(response.status_code, 422)
        self.assertIn("status", response.json()["errors"])

    def test_suspended_user_cannot_login_nor_use_existing_token(self):
        raw = self.login_as(self.member1)
        User.objects.filter(pk=self.member1.pk).update(status="SUSPENDED")
        self.assertEqual(self.client.get("/api/me").status_code, 403)
        self.anonymous()
        login = self.client.post("/api/login", {"email": self.member1.email, "password": "Passw0rd!x"}, format="json")
        self.assertEqual(login.status_code, 403)

    def test_time_entries_visibility_depends_on_role(self):
        project = self.make_project(self.t1, self.owner1)
        self.login_as(self.member1)
        self.client.post("/api/time-entries/start", {"project_id": project.pk}, format="json")
        self.login_as(self.manager1)
        self.client.post("/api/time-entries/start", {"project_id": project.pk}, format="json")
        self.assertEqual(len(self.client.get("/api/time-entries").json()["entries"]), 2)
        self.login_as(self.member1)
        entries = self.client.get("/api/time-entries").json()["entries"]
        self.assertEqual([e["user"]["id"] for e in entries], [self.member1.pk])
