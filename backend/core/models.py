"""Base de l'isolation multi-tenant.

SÉCURITÉ : `objects` (le manager par défaut) FILTRE toujours sur le tenant courant et renvoie
un résultat VIDE s'il n'y en a pas (échec fermé). Seul `unscoped` voit tout : à réserver aux
scripts d'administration, jamais à une vue d'API.
"""
from django.db import models

from core.tenant import TenantNotSet, get_current_tenant_id


class TenantScopedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        tenant_id = get_current_tenant_id()
        if tenant_id is None:
            return queryset.none()
        return queryset.filter(tenant_id=tenant_id)


class TenantOwnedModel(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="+", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()  # défini en premier : manager par défaut
    unscoped = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Le tenant vient TOUJOURS du contexte (utilisateur authentifié), jamais du client.
        if self.tenant_id is None:
            tenant_id = get_current_tenant_id()
            if tenant_id is None:
                raise TenantNotSet("Aucun tenant courant : impossible d'enregistrer cet objet.")
            self.tenant_id = tenant_id
        super().save(*args, **kwargs)
