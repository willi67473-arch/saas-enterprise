"""Migration initiale de l'app « tenants » (générée à partir des modèles)."""
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [

    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('stripe_price_id', models.CharField(max_length=255, null=True, blank=True)),
                ('price_monthly', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('max_projects', models.PositiveIntegerField(default=3)),
                ('max_users', models.PositiveIntegerField(default=5)),
                ('has_time_tracking', models.BooleanField(default=True)),
                ('has_realtime_ws', models.BooleanField(default=False)),
                ('features', models.JSONField(default=list, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('subdomain', models.SlugField(max_length=63, unique=True)),
                ('plan', models.ForeignKey('tenants.Plan', null=True, blank=True, on_delete=models.SET_NULL, related_name='tenants')),
                ('stripe_id', models.CharField(max_length=255, null=True, blank=True)),
                ('pm_type', models.CharField(max_length=50, null=True, blank=True)),
                ('pm_last_four', models.CharField(max_length=4, null=True, blank=True)),
                ('trial_ends_at', models.DateTimeField(null=True, blank=True)),
                ('subscription_status', models.CharField(max_length=20, default='TRIALING')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TenantInvitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='invitations')),
                ('email', models.EmailField(max_length=255)),
                ('role', models.CharField(max_length=20, default='USER')),
                ('token_hash', models.CharField(max_length=64, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('accepted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
