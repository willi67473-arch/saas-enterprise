"""Données de démonstration : un tenant complet + un second tenant pour démontrer l'isolation.

    python manage.py seed_demo            # idempotent : ne fait rien si la démo existe déjà
    python manage.py seed_demo --flush    # supprime les deux tenants de démo puis les recrée
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from business.models import Client, Employee, Product, Service
from core.constants import DEFAULT_AVATAR
from core.tenant import tenant_context
from notifications.models import Notification
from projects.models import Project, Task
from tenants.models import Plan, Tenant
from timetracking.models import TimeEntry

DEMO_SUBDOMAIN = "demo"
OTHER_SUBDOMAIN = "autre"
PASSWORD = "password"
AVATAR_F = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=256"


class Command(BaseCommand):
    help = "Crée les données de démonstration (comptes admin@enterprise.ca, manager@..., user@..., claire@autre.fr)."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Supprime puis recrée les tenants de démonstration.")

    def plan(self, slug):
        try:
            return Plan.objects.get(slug=slug)
        except Plan.DoesNotExist:
            raise CommandError(f"Forfait « {slug} » introuvable : lancez d'abord `python manage.py migrate`.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            deleted, _ = Tenant.objects.filter(subdomain__in=[DEMO_SUBDOMAIN, OTHER_SUBDOMAIN]).delete()
            self.stdout.write(f"Anciennes données de démo supprimées ({deleted} objets).")
        elif Tenant.objects.filter(subdomain=DEMO_SUBDOMAIN).exists():
            self.stdout.write(self.style.WARNING("La démo existe déjà. Utilisez --flush pour la recréer."))
            return

        enterprise, free = self.plan("enterprise"), self.plan("free")
        now = timezone.now()

        # ---------- Tenant #1 : « Enterprise Démo Inc. » ----------
        acme = Tenant.objects.create(
            name="Enterprise Démo Inc.", subdomain=DEMO_SUBDOMAIN, plan=enterprise, subscription_status="ACTIVE"
        )

        def make_user(email, prenom, nom, role, avatar):
            return User.objects.create_user(
                email=email, password=PASSWORD, tenant=acme, nom=nom, prenom=prenom,
                role=role, plan="ENTERPRISE", status="ACTIVE", avatar=avatar,
            )

        admin = make_user("admin@enterprise.ca", "Jean-Marc", "Kouamé", "SUPER_ADMIN", AVATAR_F)
        manager = make_user("manager@enterprise.ca", "Awa", "Ndiaye", "MANAGER", DEFAULT_AVATAR)
        member = make_user("user@enterprise.ca", "Luc", "Tremblay", "USER", DEFAULT_AVATAR)

        with tenant_context(acme.pk):
            Client.objects.create(identifiant="CLT-1001", nom="Dupont", prenom="Sophie", email="sophie.dupont@logitech.ca",
                                  telephone="+1 514-555-0199", entreprise="LogiTech Canada",
                                  adresse="1250 Rue de la Gauchetière, Montréal", statut="ACTIF")
            Client.objects.create(identifiant="CLT-1002", nom="Gagnon", prenom="Marc", email="m.gagnon@nordik.ca",
                                  telephone="+1 418-555-0102", entreprise="Nordik Solutions",
                                  adresse="45 Boulevard Laurier, Québec", statut="PROSPECT")

            Employee.objects.create(matricule="EMP-001", nom="Ndiaye", prenom="Awa", email="a.ndiaye@enterprise.ca",
                                    telephone="+1 438-555-0144", poste="Développeuse Fullstack Senior",
                                    departement="Ingénierie Logicielle", salaire=85000,
                                    date_embauche=date(2024, 3, 15), statut="ACTIF")
            Employee.objects.create(matricule="EMP-002", nom="Tremblay", prenom="Luc", email="l.tremblay@enterprise.ca",
                                    telephone="+1 438-555-0188", poste="Analyste Produit", departement="Produit",
                                    salaire=72000, date_embauche=date(2025, 1, 20), statut="EN CONGÉ")

            Product.objects.create(identifiant="PRD-500", nom='MacBook Pro M3 16"',
                                   image="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&q=80&w=256",
                                   prix="3299.99", disponibilite="EN STOCK", quantite_stock=18,
                                   categorie="Matériel Informatique",
                                   description="Station de travail professionnelle M3 Max 36GB RAM.")
            Product.objects.create(identifiant="PRD-501", nom="Écran 4K Dell UltraSharp",
                                   image="https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&q=80&w=256",
                                   prix="799.00", disponibilite="EN RUPTURE", quantite_stock=0,
                                   categorie="Périphériques", description="Écran 32 pouces IPS Thunderbolt 4.")
            Product.objects.create(identifiant="PRD-502", nom="Clavier mécanique sans fil",
                                   image="https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&q=80&w=256",
                                   prix="189.50", disponibilite="EN STOCK", quantite_stock=4,
                                   categorie="Périphériques", description="Switchs silencieux, Bluetooth multi-appareils.")

            Service.objects.create(identifiant="SRV-201", nom="Audit & Architecture SaaS Cloud",
                                   description="Évaluation complète de la sécurité, scalabilité et performances.",
                                   prix_tarif="1500.00", duree_estimee="3 Jours", statut="DISPONIBLE")
            Service.objects.create(identifiant="SRV-202", nom="Formation équipe Django & React",
                                   description="Atelier pratique sur la stack du projet, en présentiel ou à distance.",
                                   prix_tarif="2400.00", duree_estimee="2 Jours", statut="DISPONIBLE")

            p1 = Project.objects.create(code="PRJ-001", name="Refonte du portail client",
                                        description="Nouvelle expérience client web & mobile.", status="ACTIVE",
                                        budget_hours=320, hourly_rate=120,
                                        deadline=(now + timedelta(days=60)).date(), owner=admin)
            p2 = Project.objects.create(code="PRJ-002", name="Migration vers le cloud",
                                        description="Migration de l'infrastructure vers un hébergement managé.",
                                        status="PLANNING", budget_hours=180, hourly_rate=135,
                                        deadline=(now + timedelta(days=120)).date(), owner=manager)

            tasks = [  # 8 tâches réparties dans les 4 colonnes
                (p1, "Maquettes écrans connexion & tableau de bord", "DONE", "HIGH", manager, ["design"]),
                (p1, "API d'authentification par jeton", "DONE", "URGENT", admin, ["backend"]),
                (p1, "Page Kanban avec glisser-déposer", "IN_REVIEW", "HIGH", manager, ["frontend"]),
                (p1, "Intégration du suivi du temps", "IN_PROGRESS", "MEDIUM", member, ["frontend", "backend"]),
                (p1, "Tests de charge de l'API", "TODO", "MEDIUM", None, ["qa"]),
                (p1, "Rédiger la documentation utilisateur", "TODO", "LOW", member, ["docs"]),
                (p2, "Inventaire des services existants", "IN_PROGRESS", "HIGH", manager, ["infra"]),
                (p2, "Plan de bascule et retour arrière", "TODO", "URGENT", None, ["infra"]),
            ]
            positions = {}
            for index, (project, title, column, priority, assignee, tags) in enumerate(tasks):
                key = (project.pk, column)
                positions[key] = positions.get(key, -1) + 1
                Task.objects.create(project=project, assignee=assignee, title=title, column_status=column,
                                    priority=priority, position=positions[key], tags=tags,
                                    due_date=date.today() + timedelta(days=5 + index * 4))

            for user, project, desc, seconds, billable, days_ago in [
                (admin, p1, "Architecture API", 3 * 3600 + 1200, True, 1),
                (manager, p1, "Revue de code Kanban", 5400, True, 1),
                (member, p1, "Réunion de cadrage", 3600, False, 2),
                (manager, p2, "Atelier d'inventaire", 2 * 3600, True, 3),
            ]:
                start = (now - timedelta(days=days_ago)).replace(hour=9, minute=0, second=0, microsecond=0)
                TimeEntry.objects.create(user=user, project=project, description=desc, started_at=start,
                                         ended_at=start + timedelta(seconds=seconds), duration_seconds=seconds,
                                         is_billable=billable, is_running=False)

            Notification.objects.create(user=admin, type="TASK_DONE", title="Tâche terminée", is_read=False,
                                        message="La tâche « Maquettes écrans connexion & tableau de bord » est passée en Terminé.")
            Notification.objects.create(user=admin, type="INFO", title="Bienvenue", is_read=True,
                                        message="Votre espace Enterprise Démo Inc. est prêt.")

        # ---------- Tenant #2 : prouve l'isolation des données ----------
        other = Tenant.objects.create(name="Autre Société SARL", subdomain=OTHER_SUBDOMAIN, plan=free,
                                      trial_ends_at=now + timedelta(days=14), subscription_status="TRIALING")
        User.objects.create_user(email="claire@autre.fr", password=PASSWORD, tenant=other, nom="Martin", prenom="Claire",
                                 role="SUPER_ADMIN", plan="FREE", status="ACTIVE", avatar=AVATAR_F)
        with tenant_context(other.pk):
            Client.objects.create(identifiant="CLT-1001", nom="Leroy", prenom="Paul", email="paul@leroy.fr",
                                  telephone="+33 1 55 55 01 01", entreprise="Leroy & Fils", statut="ACTIF")

        self.stdout.write(self.style.SUCCESS("Démo créée : admin@enterprise.ca / manager@enterprise.ca / user@enterprise.ca "
                                             "(mot de passe « password ») + claire@autre.fr (autre tenant)."))
