from rest_framework import serializers

from business.models import Client, Employee, Product, Service
from core.constants import (
    CLIENT_STATUSES,
    DEFAULT_PRODUCT_IMAGE,
    EMPLOYEE_STATUSES,
    PRODUCT_AVAILABILITY,
    SERVICE_STATUSES,
)
from core.serializers import TenantUniqueSerializerMixin

_TIMESTAMPS = ("created_at", "updated_at")


class ClientSerializer(TenantUniqueSerializerMixin, serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(read_only=True)
    statut = serializers.ChoiceField(choices=CLIENT_STATUSES)
    tenant_unique_fields = ("identifiant",)

    class Meta:
        model = Client
        fields = ("id", "tenant_id", "identifiant", "nom", "prenom", "email", "telephone",
                  "entreprise", "adresse", "statut") + _TIMESTAMPS
        read_only_fields = ("id",) + _TIMESTAMPS


class EmployeeSerializer(TenantUniqueSerializerMixin, serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(read_only=True)
    salaire = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    statut = serializers.ChoiceField(choices=EMPLOYEE_STATUSES)
    tenant_unique_fields = ("matricule",)

    class Meta:
        model = Employee
        fields = ("id", "tenant_id", "matricule", "nom", "prenom", "email", "telephone", "poste",
                  "departement", "salaire", "date_embauche", "statut") + _TIMESTAMPS
        read_only_fields = ("id",) + _TIMESTAMPS


class ProductSerializer(TenantUniqueSerializerMixin, serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(read_only=True)
    prix = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    quantite_stock = serializers.IntegerField(min_value=0)
    disponibilite = serializers.ChoiceField(choices=PRODUCT_AVAILABILITY)
    tenant_unique_fields = ("identifiant",)

    class Meta:
        model = Product
        fields = ("id", "tenant_id", "identifiant", "nom", "image", "prix", "disponibilite",
                  "quantite_stock", "categorie", "description") + _TIMESTAMPS
        read_only_fields = ("id",) + _TIMESTAMPS

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Image par défaut si absente ou vidée
        if ("image" in attrs and not attrs["image"]) or (self.instance is None and "image" not in attrs):
            attrs["image"] = DEFAULT_PRODUCT_IMAGE
        # Cohérence stock / disponibilité : stock à 0 => rupture
        quantity = attrs.get("quantite_stock", self.instance.quantite_stock if self.instance else None)
        if quantity == 0:
            attrs["disponibilite"] = "EN RUPTURE"
        return attrs


class ServiceSerializer(TenantUniqueSerializerMixin, serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(read_only=True)
    prix_tarif = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    statut = serializers.ChoiceField(choices=SERVICE_STATUSES)
    tenant_unique_fields = ("identifiant",)

    class Meta:
        model = Service
        fields = ("id", "tenant_id", "identifiant", "nom", "description", "prix_tarif",
                  "duree_estimee", "statut") + _TIMESTAMPS
        read_only_fields = ("id",) + _TIMESTAMPS
