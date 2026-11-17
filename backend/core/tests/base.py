from django.core.cache import cache
from rest_framework.test import APITestCase

from accounts.models import AuthToken, User
from core.tenant import tenant_context
from projects.models import Project, Task
from tenants.models import Plan, Tenant

PASSWORD = "Passw0rd!x"


class ApiTestCase(APITestCase):
    """Deux tenants (T1 et T2) avec des utilisateurs de chaque rôle. Les forfaits viennent des migrations."""

    def setUp(self):
        super().setUp()
        cache.clear()  # remet à zéro les compteurs d'anti brute-force entre les tests
        self.free = Plan.objects.get(slug="free")
        self.pro = Plan.objects.get(slug="pro")
        self.enterprise = Plan.objects.get(slug="enterprise")
        self.t1 = Tenant.objects.create(name="Tenant Un", subdomain="un", plan=self.enterprise, subscription_status="ACTIVE")
        self.t2 = Tenant.objects.create(name="Tenant Deux", subdomain="deux", plan=self.enterprise, subscription_status="ACTIVE")
        self.owner1 = self.make_user(self.t1, "owner1@test.io", "SUPER_ADMIN")
        self.admin1 = self.make_user(self.t1, "admin1@test.io", "ADMIN")
        self.manager1 = self.make_user(self.t1, "manager1@test.io", "MANAGER")
        self.member1 = self.make_user(self.t1, "member1@test.io", "USER")
        self.owner2 = self.make_user(self.t2, "owner2@test.io", "SUPER_ADMIN")

    # ---- fabriques -----------------------------------------------------------------
    def make_user(self, tenant, email, role, **extra):
        return User.objects.create_user(
            email=email, password=PASSWORD, tenant=tenant, nom="Nom", prenom=email.split("@")[0],
            role=role, plan="ENTERPRISE", status="ACTIVE", avatar="https://x.test/a.png", **extra,
        )

    def in_tenant(self, tenant):
        return tenant_context(tenant.pk)

    def make_project(self, tenant, owner, code="PRJ-1"):
        with self.in_tenant(tenant):
            return Project.objects.create(code=code, name=f"Projet {code}", owner=owner)

    def make_task(self, project, title="Tâche", column="TODO", position=0):
        with self.in_tenant(project.tenant):
            return Task.objects.create(project=project, title=title, column_status=column, position=position)

    # ---- authentification ----------------------------------------------------------
    def login_as(self, user):
        raw = AuthToken.issue(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
        return raw

    def anonymous(self):
        self.client.credentials()

    # ---- raccourcis API ------------------------------------------------------------
    def client_payload(self, identifiant="CLT-9", **extra):
        return {"identifiant": identifiant, "nom": "Nom", "prenom": "Prénom", "email": "c@test.io",
                "telephone": "123", "statut": "ACTIF", **extra}

    def api_create_project(self, code="PRJ-A"):
        response = self.client.post("/api/projects", {"code": code, "name": f"Projet {code}"}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()["id"]

    def api_create_task(self, project_id, title, column="TODO", **extra):
        payload = {"title": title, "column_status": column, "priority": "MEDIUM", **extra}
        response = self.client.post(f"/api/projects/{project_id}/tasks", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def board(self, project_id):
        """{colonne: [(position, titre), ...]} tel que renvoyé par GET /api/projects."""
        projects = self.client.get("/api/projects").json()
        project = next(p for p in projects if p["id"] == project_id)
        board = {}
        for task in project["tasks"]:
            board.setdefault(task["column_status"], []).append((task["position"], task["title"]))
        return board
