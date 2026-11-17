"""Migration initiale de l'app « business » (générée à partir des modèles)."""
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey('tenants.Tenant', editable=False, on_delete=models.CASCADE, related_name='+')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifiant', models.CharField(max_length=50)),
                ('nom', models.CharField(max_length=255)),
                ('prenom', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=255)),
                ('telephone', models.CharField(max_length=50)),
                ('entreprise', models.CharField(max_length=255, null=True, blank=True)),
                ('adresse', models.CharField(max_length=500, null=True, blank=True)),
                ('statut', models.CharField(max_length=20, default='ACTIF')),
            ],
        ),
        migrations.AddConstraint(
            model_name='client',
            constraint=models.UniqueConstraint(fields=['tenant', 'identifiant'], name='uniq_client_tenant_identifiant'),
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey('tenants.Tenant', editable=False, on_delete=models.CASCADE, related_name='+')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('matricule', models.CharField(max_length=50)),
                ('nom', models.CharField(max_length=255)),
                ('prenom', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=255)),
                ('telephone', models.CharField(max_length=50)),
                ('poste', models.CharField(max_length=255)),
                ('departement', models.CharField(max_length=255)),
                ('salaire', models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ('date_embauche', models.DateField()),
                ('statut', models.CharField(max_length=20, default='ACTIF')),
            ],
        ),
        migrations.AddConstraint(
            model_name='employee',
            constraint=models.UniqueConstraint(fields=['tenant', 'matricule'], name='uniq_employee_tenant_matricule'),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey('tenants.Tenant', editable=False, on_delete=models.CASCADE, related_name='+')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifiant', models.CharField(max_length=50)),
                ('nom', models.CharField(max_length=255)),
                ('image', models.URLField(max_length=2000, null=True, blank=True)),
                ('prix', models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ('disponibilite', models.CharField(max_length=20, default='EN STOCK')),
                ('quantite_stock', models.PositiveIntegerField(default=0)),
                ('categorie', models.CharField(max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(fields=['tenant', 'identifiant'], name='uniq_product_tenant_identifiant'),
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey('tenants.Tenant', editable=False, on_delete=models.CASCADE, related_name='+')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifiant', models.CharField(max_length=50)),
                ('nom', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('prix_tarif', models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ('duree_estimee', models.CharField(max_length=100)),
                ('statut', models.CharField(max_length=20, default='DISPONIBLE')),
            ],
        ),
        migrations.AddConstraint(
            model_name='service',
            constraint=models.UniqueConstraint(fields=['tenant', 'identifiant'], name='uniq_service_tenant_identifiant'),
        ),
    ]
