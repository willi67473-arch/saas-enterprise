from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.models import AuthToken, User
from accounts.serializers import (
    TeamMemberSerializer,
    UserSerializer,
    UserWithTenantSerializer,
    UserWriteSerializer,
)
from core.constants import DEFAULT_AVATAR, SUPER_ADMIN
from core.permissions import IsAdminRole
from core.security import generate_password
from core.views import TenantAPIView, TenantGenericViewSet
from projects.models import Project


def plan_label(plan):
    return (plan.name if plan else "FREE").upper()


def login_payload(user, raw_token):
    user = User.objects.select_related("tenant__plan").get(pk=user.pk)
    return {
        "access_token": raw_token,
        "token_type": "Bearer",
        "user": UserWithTenantSerializer(user).data,
    }


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_auth"

    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        email = str(payload.get("email", "")).strip().lower()
        password = payload.get("password", "")
        if not email or not isinstance(password, str) or not password:
            raise ValidationError({"email": ["Courriel et mot de passe requis."]})

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            make_password(password)  # temps de réponse comparable : n'indique pas si le compte existe
            return Response({"message": "Identifiants invalides."}, status=401)
        if not user.check_password(password):
            return Response({"message": "Identifiants invalides."}, status=401)
        if user.status == "SUSPENDED":
            return Response({"message": "Ce compte est suspendu."}, status=403)

        User.objects.filter(pk=user.pk).update(last_login=timezone.now())
        return Response(login_payload(user, AuthToken.issue(user)))


class LogoutView(TenantAPIView):
    def post(self, request):
        request.auth.delete()  # révocation immédiate du jeton courant
        return Response({"message": "Déconnexion réussie."})


class MeView(TenantAPIView):
    def get(self, request):
        return Response(UserWithTenantSerializer(request.user).data)


class TeamView(TenantAPIView):
    """Annuaire léger (tous rôles) : sert à assigner les tâches."""

    def get(self, request):
        members = User.objects.filter(tenant_id=request.user.tenant_id, status="ACTIVE").order_by("prenom", "id")
        return Response(TeamMemberSerializer(members, many=True).data)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    TenantGenericViewSet,
):
    permission_classes = [IsAuthenticated, IsAdminRole]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        # Les utilisateurs ne sont pas filtrés par le manager scopé : filtre explicite sur le tenant.
        return User.objects.filter(tenant_id=self.request.user.tenant_id).order_by("-id")

    def list(self, request, *args, **kwargs):
        return Response(UserSerializer(self.get_queryset(), many=True).data)

    def create(self, request, *args, **kwargs):
        serializer = UserWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)

        tenant = request.user.tenant
        plan = tenant.plan
        if plan and self.get_queryset().count() >= plan.max_users:
            raise PermissionDenied(f"Quota d'utilisateurs atteint pour le forfait {plan.name}. Passez au plan supérieur.")

        password = data.pop("password", None)
        temporary = None
        if not password:
            password = temporary = generate_password()  # renvoyé UNE seule fois

        user = User.objects.create_user(
            email=data.pop("email"),
            password=password,
            tenant=tenant,
            plan=plan_label(plan),
            avatar=DEFAULT_AVATAR,
            **data,
        )
        return Response(
            {"message": "Utilisateur créé", "data": UserSerializer(user).data, "temporary_password": temporary},
            status=201,
        )

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        # Seul le propriétaire peut modifier le compte propriétaire (sinon un ADMIN pourrait le détourner).
        if user.role == SUPER_ADMIN and request.user.role != SUPER_ADMIN:
            raise PermissionDenied("Seul le propriétaire de l'espace peut modifier ce compte.")

        serializer = UserWriteSerializer(user, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        password = data.pop("password", None)
        for field, value in data.items():
            setattr(user, field, value)
        if password:
            user.set_password(password)
            # Un nouveau mot de passe invalide les sessions existantes (sauf la session courante si c'est le sien).
            stale = user.auth_tokens.all()
            if user.pk == request.user.pk:
                stale = stale.exclude(pk=request.auth.pk)
            stale.delete()
        user.save()
        return Response({"message": "Utilisateur mis à jour", "data": UserSerializer(user).data})

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError("Vous ne pouvez pas supprimer votre propre compte.")
        if user.role == SUPER_ADMIN and request.user.role != SUPER_ADMIN:
            raise PermissionDenied("Seul le propriétaire de l'espace peut modifier ce compte.")
        if user.role == SUPER_ADMIN:
            raise ValidationError("Le propriétaire de l'espace ne peut pas être supprimé.")
        with transaction.atomic():
            # Ses projets sont réattribués à l'auteur de la suppression (évite la perte de données en cascade).
            Project.unscoped.filter(owner=user).update(owner=request.user)
            user.delete()
        return Response({"message": "Utilisateur supprimé"})
