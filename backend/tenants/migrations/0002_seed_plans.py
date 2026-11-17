"""Forfaits de référence : toujours présents après `migrate`, même sans `seed_demo`."""
from django.db import migrations

PLANS = [
    {"name": "FREE", "slug": "free", "price_monthly": 0, "max_projects": 3, "max_users": 5,
     "has_realtime_ws": False, "features": ["3 projets", "5 utilisateurs", "Kanban & suivi du temps"]},
    {"name": "PRO", "slug": "pro", "price_monthly": 29, "max_projects": 20, "max_users": 25,
     "has_realtime_ws": True, "features": ["20 projets", "25 utilisateurs", "Notifications temps réel", "Support prioritaire"]},
    {"name": "ENTERPRISE", "slug": "enterprise", "price_monthly": 99, "max_projects": 500, "max_users": 500,
     "has_realtime_ws": True, "features": ["Projets illimités*", "Utilisateurs illimités*", "SSO & audit", "Support dédié 24/7"]},
]


def create_plans(apps, schema_editor):
    Plan = apps.get_model("tenants", "Plan")
    for data in PLANS:
        slug = data["slug"]
        Plan.objects.update_or_create(slug=slug, defaults={k: v for k, v in data.items() if k != "slug"})


class Migration(migrations.Migration):
    dependencies = [("tenants", "0001_initial")]

    operations = [migrations.RunPython(create_plans, migrations.RunPython.noop)]
