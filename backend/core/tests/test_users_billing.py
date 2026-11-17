from core.tests.base import PASSWORD, ApiTestCase
from tenants.models import Tenant


class UserQuotaTests(ApiTestCase):
    def small_tenant(self):
        """Tenant FREE (5 utilisateurs max) déjà plein : propriétaire + 4 membres."""
        tenant = Tenant.objects.create(name="Petit", subdomain="petit", plan=self.free, subscription_status="ACTIVE")
        owner = self.make_user(tenant, "petit-owner@test.io", "SUPER_ADMIN")
        for i in range(4):
            self.make_user(tenant, f"petit{i}@test.io", "USER")
        return tenant, owner

    def test_user_quota_blocks_creation(self):
        _, owner = self.small_tenant()
        self.login_as(owner)
        payload = {"nom": "N", "prenom": "P", "email": "sixieme@test.io", "role": "USER", "status": "ACTIVE"}
        response = self.client.post("/api/users", payload, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.json()["message"].startswith("Quota d'utilisateurs atteint"))

    def test_pending_invitations_count_toward_quota(self):
        tenant = Tenant.objects.create(name="Petit", subdomain="petit", plan=self.free, subscription_status="ACTIVE")
        owner = self.make_user(tenant, "petit-owner@test.io", "SUPER_ADMIN")
        for i in range(3):
            self.make_user(tenant, f"petit{i}@test.io", "USER")
        self.login_as(owner)  # 4 utilisateurs sur 5
        self.assertEqual(self.client.post("/api/tenants/invite", {"email": "a@test.io", "role": "USER"}, format="json").status_code, 201)
        blocked = self.client.post("/api/tenants/invite", {"email": "b@test.io", "role": "USER"}, format="json")
        self.assertEqual(blocked.status_code, 403)

    def test_temporary_password_is_returned_once_and_works(self):
        self.login_as(self.owner1)
        payload = {"nom": "N", "prenom": "P", "email": "temp@test.io", "role": "USER", "status": "ACTIVE", "password": None}
        response = self.client.post("/api/users", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        temporary = response.json()["temporary_password"]
        self.assertTrue(temporary and len(temporary) >= 12)
        self.assertNotIn("password", response.json()["data"])
        self.anonymous()
        login = self.client.post("/api/login", {"email": "temp@test.io", "password": temporary}, format="json")
        self.assertEqual(login.status_code, 200)

    def test_password_change_revokes_other_sessions(self):
        old_raw = self.login_as(self.member1)
        self.login_as(self.owner1)
        payload = {"nom": "N", "prenom": "P", "email": self.member1.email, "role": "USER", "status": "ACTIVE", "password": "BrandNewPass1"}
        self.assertEqual(self.client.put(f"/api/users/{self.member1.pk}", payload, format="json").status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {old_raw}")
        self.assertEqual(self.client.get("/api/me").status_code, 401)


class InvitationAndRegistrationTests(ApiTestCase):
    def test_invitation_flow_single_use(self):
        self.login_as(self.admin1)
        invited = self.client.post("/api/tenants/invite", {"email": "Nouveau@Test.io", "role": "MANAGER"}, format="json")
        self.assertEqual(invited.status_code, 201, invited.content)
        link = invited.json()["invitation_link"]
        self.assertIn("/?invite=", link)
        token = link.split("?invite=")[1]
        self.assertEqual(len(token), 40)
        self.assertNotIn("token", invited.json()["data"])  # jamais exposé

        self.anonymous()
        preview = self.client.get(f"/api/invitations/{token}")
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.json(), {"email": "nouveau@test.io", "role": "MANAGER", "tenant_name": "Tenant Un"})

        payload = {"token": token, "nom": "Nouveau", "prenom": "Membre", "password": "Chosen-Pass1"}
        accepted = self.client.post("/api/invitations/accept", payload, format="json")
        self.assertEqual(accepted.status_code, 201, accepted.content)
        self.assertEqual(accepted.json()["user"]["role"], "MANAGER")
        self.assertEqual(accepted.json()["user"]["tenant_id"], str(self.t1.pk))

        again = self.client.post("/api/invitations/accept", payload, format="json")
        self.assertEqual(again.status_code, 410)
        self.assertEqual(self.client.get(f"/api/invitations/{token}").status_code, 410)

    def test_unknown_invitation_is_410(self):
        self.assertEqual(self.client.get("/api/invitations/n-existe-pas").status_code, 410)

    def test_cannot_invite_existing_user_email(self):
        self.login_as(self.admin1)
        response = self.client.post("/api/tenants/invite", {"email": self.owner2.email, "role": "USER"}, format="json")
        self.assertEqual(response.status_code, 422)

    def test_register_tenant_creates_owner_on_free_trial(self):
        payload = {"company_name": "Neuve SARL", "subdomain": "Neuve-SARL", "nom": "Doe", "prenom": "Jane",
                   "email": "jane@neuve.io", "password": "Str0ng-Password", "plan_slug": "free"}
        response = self.client.post("/api/tenants/register", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual(body["user"]["role"], "SUPER_ADMIN")
        self.assertEqual(body["tenant"]["subscription_status"], "TRIALING")
        self.assertEqual(body["tenant"]["plan"]["slug"], "free")
        self.assertEqual(body["tenant"]["subdomain"], "neuve-sarl")
        self.assertIsNotNone(body["tenant"]["trial_ends_at"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {body['access_token']}")
        self.assertEqual(self.client.get("/api/me").json()["tenant"]["name"], "Neuve SARL")

    def test_register_rejects_duplicates_and_weak_password(self):
        base = {"company_name": "X", "subdomain": "un", "nom": "D", "prenom": "J", "email": "x@x.io", "password": "Str0ng-Password"}
        duplicate = self.client.post("/api/tenants/register", base, format="json")
        self.assertEqual(duplicate.status_code, 422)
        self.assertIn("subdomain", duplicate.json()["errors"])
        weak = self.client.post("/api/tenants/register", {**base, "subdomain": "libre", "password": "court"}, format="json")
        self.assertEqual(weak.status_code, 422)
        self.assertIn("password", weak.json()["errors"])


class SubscriptionTests(ApiTestCase):
    def test_owner_can_change_plan_and_members_follow(self):
        self.login_as(self.owner1)
        response = self.client.post("/api/billing/subscribe", {"plan_id": self.pro.pk}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["tenant"]["plan"]["slug"], "pro")
        self.member1.refresh_from_db()
        self.assertEqual(self.member1.plan, "PRO")

    def test_downgrade_refused_when_usage_exceeds_limits(self):
        tenant = Tenant.objects.create(name="Gros", subdomain="gros", plan=self.enterprise, subscription_status="ACTIVE")
        owner = self.make_user(tenant, "gros-owner@test.io", "SUPER_ADMIN")
        for i in range(5):
            self.make_user(tenant, f"gros{i}@test.io", "USER")  # 6 utilisateurs > 5 (FREE)
        self.login_as(owner)
        response = self.client.post("/api/billing/subscribe", {"plan_id": self.free.pk}, format="json")
        self.assertEqual(response.status_code, 422)
        self.assertIn("Impossible de passer", response.json()["message"])

    def test_billing_exposes_usage_and_plans(self):
        self.login_as(self.member1)  # lecture ouverte à tous les rôles
        body = self.client.get("/api/billing").json()
        self.assertEqual(set(body["usage"]), {"users", "projects", "pending_invitations"})
        self.assertEqual(len(body["plans"]), 3)
        self.assertEqual(body["usage"]["users"], 4)

    def test_project_limit_of_the_plan_is_enforced(self):
        tenant = Tenant.objects.create(name="Libre", subdomain="libre", plan=self.free, subscription_status="ACTIVE")
        owner = self.make_user(tenant, "libre-owner@test.io", "SUPER_ADMIN")
        self.login_as(owner)
        for i in range(3):
            self.api_create_project(f"PRJ-{i}")
        blocked = self.client.post("/api/projects", {"code": "PRJ-X", "name": "Trop"}, format="json")
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("Limite de 3 projets", blocked.json()["message"])
