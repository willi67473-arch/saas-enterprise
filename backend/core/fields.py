"""Champs relationnels DRF qui n'acceptent QUE des objets du tenant courant."""
from rest_framework import serializers

from accounts.models import User
from core.tenant import get_current_tenant_id


class TenantUserField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        "does_not_exist": "Utilisateur introuvable dans votre espace.",
        "incorrect_type": "Identifiant utilisateur invalide.",
    }

    def __init__(self, **kwargs):
        kwargs.setdefault("queryset", User.objects.all())
        super().__init__(**kwargs)

    def get_queryset(self):
        tenant_id = get_current_tenant_id()
        if tenant_id is None:
            return User.objects.none()
        return User.objects.filter(tenant_id=tenant_id)


class TenantRelatedField(serializers.PrimaryKeyRelatedField):
    """Clé primaire d'un objet métier du tenant courant (le queryset est relu à CHAQUE requête)."""

    def __init__(self, model, **kwargs):
        self.tenant_model = model
        kwargs.setdefault("queryset", model.unscoped.none())  # simple valeur de repli, jamais utilisée
        super().__init__(**kwargs)

    def get_queryset(self):
        return self.tenant_model.objects.all()
