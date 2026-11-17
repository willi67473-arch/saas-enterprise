"""Authentification par jeton Bearer : expirant (TOKEN_LIFETIME_DAYS) et révocable (/logout)."""
from datetime import timedelta

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from accounts.models import AuthToken
from core.security import hash_token

LAST_USED_REFRESH = timedelta(minutes=5)


class BearerTokenAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("En-tête Authorization invalide.")
        try:
            raw = parts[1].decode("utf-8")
        except UnicodeError:
            raise AuthenticationFailed("Jeton invalide.")

        try:
            token = AuthToken.objects.select_related("user__tenant__plan").get(key=hash_token(raw))
        except AuthToken.DoesNotExist:
            raise AuthenticationFailed("Jeton invalide ou révoqué.")

        now = timezone.now()
        if token.expires_at <= now:
            token.delete()
            raise AuthenticationFailed("Votre session a expiré. Veuillez vous reconnecter.")

        user = token.user
        if user.status == "SUSPENDED":
            raise PermissionDenied("Ce compte est suspendu.")

        if token.last_used_at is None or now - token.last_used_at > LAST_USED_REFRESH:
            AuthToken.objects.filter(pk=token.pk).update(last_used_at=now)

        return (user, token)

    def authenticate_header(self, request):
        return "Bearer"  # fait renvoyer 401 (et non 403) quand l'authentification manque
