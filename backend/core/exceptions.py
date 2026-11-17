"""Format d'erreur unique de l'API (attendu par le frontend).

- Validation : 422 {"message": "<première erreur>", "errors": {"champ": ["..."]}}
- Autres     : {"message": "..."}
"""
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.views import exception_handler as drf_exception_handler


class Gone(APIException):
    """410 : ressource définitivement indisponible (invitation expirée ou déjà utilisée)."""

    status_code = status.HTTP_410_GONE
    default_detail = "Invitation expirée ou déjà utilisée."
    default_code = "gone"


def _flatten(value):
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            out.extend(_flatten(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(_flatten(item))
        return out
    return [str(value)]


def _normalize_errors(data):
    if isinstance(data, dict):
        return {str(key): _flatten(value) for key, value in data.items()}
    return {"non_field_errors": _flatten(data)}


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # erreur serveur : laissée à Django (500)

    if isinstance(exc, ValidationError):
        errors = _normalize_errors(response.data)
        first = next((msgs[0] for msgs in errors.values() if msgs), "Les données fournies sont invalides.")
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        response.data = {"message": first, "errors": errors}
        return response

    status_code = response.status_code
    detail = response.data.get("detail") if isinstance(response.data, dict) else None

    if isinstance(exc, NotAuthenticated):
        message = "Authentification requise."
    elif status_code == status.HTTP_404_NOT_FOUND:  # NotFound DRF ou Http404 Django (get_object_or_404)
        message = "Ressource introuvable."
    elif isinstance(exc, Throttled):
        wait = int(exc.wait or 0)
        message = f"Trop de requêtes. Réessayez dans {wait} secondes." if wait else "Trop de requêtes."
    elif detail is not None:
        message = str(detail)
    else:
        message = "Erreur de requête."

    response.data = {"message": message}
    return response
