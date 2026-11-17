from django.db import models

from core.models import TenantOwnedModel


class Client(TenantOwnedModel):
    identifiant = models.CharField(max_length=50)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    telephone = models.CharField(max_length=50)
    entreprise = models.CharField(max_length=255, null=True, blank=True)
    adresse = models.CharField(max_length=500, null=True, blank=True)
    statut = models.CharField(max_length=20, default="ACTIF")  # ACTIF | INACTIF | PROSPECT

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "identifiant"], name="uniq_client_tenant_identifiant"),
        ]


class Employee(TenantOwnedModel):
    matricule = models.CharField(max_length=50)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    telephone = models.CharField(max_length=50)
    poste = models.CharField(max_length=255)
    departement = models.CharField(max_length=255)
    salaire = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_embauche = models.DateField()
    statut = models.CharField(max_length=20, default="ACTIF")  # ACTIF | EN CONGÉ | INACTIF

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "matricule"], name="uniq_employee_tenant_matricule"),
        ]


class Product(TenantOwnedModel):
    identifiant = models.CharField(max_length=50)
    nom = models.CharField(max_length=255)
    image = models.URLField(max_length=2000, null=True, blank=True)
    prix = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    disponibilite = models.CharField(max_length=20, default="EN STOCK")  # EN STOCK | EN RUPTURE
    quantite_stock = models.PositiveIntegerField(default=0)
    categorie = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "identifiant"], name="uniq_product_tenant_identifiant"),
        ]


class Service(TenantOwnedModel):
    identifiant = models.CharField(max_length=50)
    nom = models.CharField(max_length=255)
    description = models.TextField()
    prix_tarif = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    duree_estimee = models.CharField(max_length=100)
    statut = models.CharField(max_length=20, default="DISPONIBLE")  # DISPONIBLE | INDISPONIBLE

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "identifiant"], name="uniq_service_tenant_identifiant"),
        ]
