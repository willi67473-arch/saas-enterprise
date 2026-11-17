from datetime import timedelta

from django.utils import timezone

from accounts.models import AuthToken
from core.tests.base import PASSWORD, ApiTestCase


class AuthenticationTests(ApiTestCase):
    def login(self, email, password=PASSWORD):
        return self.client.post("/api/login", {"email": email, "password": password}, format="json")

    def test_login_returns_documented_shape(self):
        response = self.login("owner1@test.io")
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body["token_type"], "Bearer")
        self.assertTrue(body["access_token"])
        self.assertEqual(body["user"]["tenant"]["plan"]["slug"], "enterprise")
        self.assertNotIn("password", body["user"])

    def test_wrong_password_is_401_with_message(self):
        response = self.login("owner1@test.io", "mauvais")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"message": "Identifiants invalides."})
        self.assertEqual(self.login("inconnu@test.io").status_code, 401)

    def test_logout_revokes_the_token(self):
        token = self.login("owner1@test.io").json()["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/me").status_code, 200)
        self.assertEqual(self.client.post("/api/logout").status_code, 200)
        self.assertEqual(self.client.get("/api/me").status_code, 401)

    def test_expired_token_is_rejected(self):
        self.login_as(self.owner1)
        AuthToken.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        response = self.client.get("/api/me")
        self.assertEqual(response.status_code, 401)
        self.assertIn("expiré", response.json()["message"])

    def test_token_lifetime_is_seven_days_and_stored_hashed(self):
        raw = AuthToken.issue(self.owner1)
        stored = AuthToken.objects.get()
        self.assertNotEqual(stored.key, raw)
        self.assertEqual(len(stored.key), 64)
        delta = stored.expires_at - timezone.now()
        self.assertGreater(delta, timedelta(days=6, hours=23))
        self.assertLessEqual(delta, timedelta(days=7))

    def test_garbage_token_is_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer nimportequoi")
        self.assertEqual(self.client.get("/api/me").status_code, 401)

    def test_login_is_rate_limited(self):
        for _ in range(10):
            self.assertEqual(self.login("owner1@test.io", "mauvais").status_code, 401)
        blocked = self.login("owner1@test.io", "mauvais")
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("message", blocked.json())

    def test_team_lists_active_members_of_tenant_only(self):
        self.login_as(self.member1)
        team = self.client.get("/api/team").json()
        self.assertEqual({m["id"] for m in team}, {self.owner1.pk, self.admin1.pk, self.manager1.pk, self.member1.pk})
        self.assertEqual(set(team[0]), {"id", "nom", "prenom", "role", "avatar"})


class ContractTests(ApiTestCase):
    def test_validation_errors_use_422_message_and_errors(self):
        self.login_as(self.owner1)
        response = self.client.post("/api/clients", {}, format="json")
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertIsInstance(body["message"], str)
        self.assertIsInstance(body["errors"], dict)
        self.assertIsInstance(body["errors"]["identifiant"], list)
        self.assertEqual(body["message"], next(iter(body["errors"].values()))[0])

    def test_null_for_required_field_is_a_field_error(self):
        self.login_as(self.owner1)
        response = self.client.post("/api/clients", self.client_payload(nom=None), format="json")
        self.assertEqual(response.status_code, 422)
        self.assertIn("nom", response.json()["errors"])

    def test_decimals_are_json_numbers_and_stock_rules_apply(self):
        self.login_as(self.owner1)
        payload = {"identifiant": "P-1", "nom": "Stylo", "prix": "12.50", "disponibilite": "EN STOCK",
                   "quantite_stock": 0, "categorie": "Papeterie", "image": None, "description": None}
        created = self.client.post("/api/products", payload, format="json")
        self.assertEqual(created.status_code, 201, created.content)
        row = self.client.get("/api/products").json()[0]
        self.assertIsInstance(row["prix"], (int, float))
        self.assertEqual(row["prix"], 12.5)
        self.assertEqual(row["disponibilite"], "EN RUPTURE")  # stock 0 => rupture
        self.assertTrue(row["image"].startswith("https://"))  # image par défaut

    def test_datetimes_are_iso_utc(self):
        self.login_as(self.owner1)
        self.client.post("/api/clients", self.client_payload(), format="json")
        created_at = self.client.get("/api/clients").json()[0]["created_at"]
        self.assertTrue(created_at.endswith("Z"), created_at)

    def test_lists_are_plain_arrays_and_crud_has_no_detail_route(self):
        self.login_as(self.owner1)
        self.assertIsInstance(self.client.get("/api/services").json(), list)
        created = self.client.post("/api/clients", self.client_payload(), format="json").json()["data"]
        self.assertEqual(self.client.get(f"/api/clients/{created['id']}").status_code, 405)

    def test_unknown_api_url_is_json_404(self):
        response = self.client.get("/api/n-existe-pas")
        self.assertEqual(response.status_code, 404)
        self.assertIn("message", response.json())

    def test_public_plans_endpoint(self):
        response = self.client.get("/api/plans")
        self.assertEqual(response.status_code, 200)
        plans = response.json()
        self.assertEqual([p["slug"] for p in plans], ["free", "pro", "enterprise"])
        self.assertEqual([p["price_monthly"] for p in plans], [0, 29, 99])
        self.assertIsInstance(plans[0]["features"], list)

    def test_employee_salary_is_number_and_dates_are_plain(self):
        self.login_as(self.manager1)
        payload = {"matricule": "E-1", "nom": "N", "prenom": "P", "email": "e@e.io", "telephone": "1", "poste": "Dev",
                   "departement": "IT", "salaire": "85000", "date_embauche": "2024-03-15", "statut": "EN CONGÉ"}
        self.assertEqual(self.client.post("/api/employees", payload, format="json").status_code, 201)
        row = self.client.get("/api/employees").json()[0]
        self.assertEqual(row["salaire"], 85000)
        self.assertEqual(row["date_embauche"], "2024-03-15")
