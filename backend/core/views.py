from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from core.tenant import reset_current_tenant, set_current_tenant


class TenantContextMixin:
    """Pose le tenant courant APRÈS l'authentification et le retire à la fin de la requête.

    Le tenant est déduit UNIQUEMENT de l'utilisateur authentifié : jamais d'un en-tête,
    d'un paramètre d'URL ou du corps de la requête.
    """

    _tenant_token = None

    def perform_authentication(self, request):
        super().perform_authentication(request)
        user = request.user
        if user and user.is_authenticated:
            if not user.tenant_id:
                raise PermissionDenied("Aucun espace entreprise associé à ce compte.")
            self._tenant_token = set_current_tenant(user.tenant_id)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if self._tenant_token is not None:
            reset_current_tenant(self._tenant_token)
            self._tenant_token = None
        return response


class TenantAPIView(TenantContextMixin, APIView):
    pass


class TenantGenericViewSet(TenantContextMixin, viewsets.GenericViewSet):
    pass


def api_not_found(request, *args, **kwargs):
    return JsonResponse({"message": "Ressource introuvable."}, status=404)
