"""Tenant courant, stocké dans un ContextVar (isolé par requête / par thread)."""
from contextlib import contextmanager
from contextvars import ContextVar


class TenantNotSet(RuntimeError):
    """Création d'un objet métier sans tenant courant : on refuse plutôt que de deviner."""


_current_tenant_id = ContextVar("current_tenant_id", default=None)


def get_current_tenant_id():
    return _current_tenant_id.get()


def set_current_tenant(tenant_id):
    """Retourne un jeton à repasser à reset_current_tenant()."""
    return _current_tenant_id.set(tenant_id)


def reset_current_tenant(token):
    _current_tenant_id.reset(token)


@contextmanager
def tenant_context(tenant_id):
    """Utilisation hors requête (seed, tests, scripts) : `with tenant_context(t.pk): ...`"""
    token = _current_tenant_id.set(tenant_id)
    try:
        yield
    finally:
        _current_tenant_id.reset(token)
