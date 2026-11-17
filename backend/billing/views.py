from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.models import AuthToken, User
from accounts.serializers import UserWithTenantSerializer
from accounts.views import plan_label
from billing.serializers import (
    AcceptInvitationSerializer,
    InviteSerializer,
    RegisterTenantSerializer,
    SubscribeSerializer,
)
from core.constants import DEFAULT_AVATAR, SUPER_ADMIN
from core.exceptions import Gone
from core.permissions import IsAdminRole
from core.security import generate_token, hash_token
from core.views import TenantAPIView
from projects.models import Project
from tenants.models import Plan, Tenant, TenantInvitation
from tenants.serializers import InvitationSerializer, PlanSerializer, TenantSerializer


class PublicView(APIView):
    """Vue publique : pas d'authentification, limitée à 10 requêtes/minute (anti brute-force)."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_auth"


def _pending_invitations(tenant_id):
    return TenantInvitation.objects.filter(tenant_id=tenant_id, accepted_at__isnull=True, expires_at__gt=timezone.now())


class PlansView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(PlanSerializer(Plan.objects.order_by("price_monthly", "id"), many=True).data)


class RegisterTenantView(PublicView):
    """Onboarding : crée l'espace entreprise ET son propriétaire (SUPER_ADMIN), de façon atomique."""

    def post(self, request):
        serializer = RegisterTenantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            tenant = Tenant.objects.create(
                name=data["company_name"],
                subdomain=data["subdomain"],
                plan=data["plan"],
                trial_ends_at=timezone.now() + timedelta(days=14),
                subscription_status="TRIALING",
            )
            owner = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                tenant=tenant,
                nom=data["nom"],
                prenom=data["prenom"],
                role=SUPER_ADMIN,
                plan=plan_label(data["plan"]),
                status="ACTIVE",
                avatar=DEFAULT_AVATAR,
            )
        raw = AuthToken.issue(owner)
        owner = User.objects.select_related("tenant__plan").get(pk=owner.pk)
        return Response(
            {
                "tenant": TenantSerializer(owner.tenant).data,
                "user": UserWithTenantSerializer(owner).data,
                "access_token": raw,
            },
            status=201,
        )


def _valid_invitation(token):
    invitation = (
        TenantInvitation.objects.select_related("tenant__plan").filter(token_hash=hash_token(token or "")).first()
    )
    if invitation is None or invitation.accepted_at is not None or invitation.expires_at <= timezone.now():
        raise Gone()
    return invitation


class InvitationPreviewView(PublicView):
    def get(self, request, token):
        invitation = _valid_invitation(token)
        return Response(
            {"email": invitation.email, "role": invitation.role, "tenant_name": invitation.tenant.name}
        )


class AcceptInvitationView(PublicView):
    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        invitation = _valid_invitation(data["token"])

        if User.objects.filter(email__iexact=invitation.email).exists():
            raise ValidationError({"email": ["Un compte existe déjà avec cet e-mail."]})

        with transaction.atomic():
            # Mise à jour conditionnelle : garantit qu'une invitation ne sert qu'UNE fois, même en concurrence.
            claimed = TenantInvitation.objects.filter(pk=invitation.pk, accepted_at__isnull=True).update(
                accepted_at=timezone.now()
            )
            if claimed != 1:
                raise Gone()
            user = User.objects.create_user(
                email=invitation.email.lower(),
                password=data["password"],
                tenant=invitation.tenant,
                nom=data["nom"],
                prenom=data["prenom"],
                role=invitation.role,
                plan=plan_label(invitation.tenant.plan),
                status="ACTIVE",
                avatar=DEFAULT_AVATAR,
            )
        raw = AuthToken.issue(user)
        user = User.objects.select_related("tenant__plan").get(pk=user.pk)
        return Response({"user": UserWithTenantSerializer(user).data, "access_token": raw}, status=201)


class BillingView(TenantAPIView):
    def get(self, request):
        tenant = request.user.tenant
        return Response(
            {
                "tenant": TenantSerializer(tenant).data,
                "usage": {
                    "users": User.objects.filter(tenant_id=tenant.pk).count(),
                    "projects": Project.objects.count(),
                    "pending_invitations": _pending_invitations(tenant.pk).count(),
                },
                "plans": PlanSerializer(Plan.objects.order_by("price_monthly", "id"), many=True).data,
            }
        )


class SubscribeView(TenantAPIView):
    """Mode démonstration : changement de forfait immédiat, sans paiement (voir README pour Stripe)."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.validated_data["plan"]
        tenant = request.user.tenant

        if User.objects.filter(tenant_id=tenant.pk).count() > plan.max_users or Project.objects.count() > plan.max_projects:
            raise ValidationError(
                f"Impossible de passer à {plan.name} : votre consommation actuelle dépasse les limites de ce forfait."
            )

        with transaction.atomic():
            tenant.plan = plan
            tenant.subscription_status = "ACTIVE"
            tenant.save()
            User.objects.filter(tenant_id=tenant.pk).update(plan=plan_label(plan))
        return Response({"message": f"Forfait mis à jour vers {plan.name}.", "tenant": TenantSerializer(tenant).data})


class InvitationListView(TenantAPIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        invitations = TenantInvitation.objects.filter(tenant_id=request.user.tenant_id).order_by("-id")[:50]
        return Response(InvitationSerializer(invitations, many=True).data)


class InviteView(TenantAPIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = InviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        role = serializer.validated_data["role"]
        tenant = request.user.tenant

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError({"email": ["Un compte existe déjà avec cet e-mail."]})
        if _pending_invitations(tenant.pk).filter(email__iexact=email).exists():
            raise ValidationError({"email": ["Une invitation est déjà en attente pour cet e-mail."]})

        used = User.objects.filter(tenant_id=tenant.pk).count() + _pending_invitations(tenant.pk).count()
        if tenant.plan and used >= tenant.plan.max_users:
            raise PermissionDenied(
                f"Quota d'utilisateurs atteint pour le forfait {tenant.plan.name}. Passez au plan supérieur."
            )

        raw = generate_token(30)  # 40 caractères, affiché UNE seule fois (seule l'empreinte est stockée)
        invitation = TenantInvitation.objects.create(
            tenant=tenant,
            email=email,
            role=role,
            token_hash=hash_token(raw),
            expires_at=timezone.now() + timedelta(days=7),
        )
        return Response(
            {
                "message": "Invitation générée avec succès.",
                "invitation_link": f"{settings.FRONTEND_URL.rstrip('/')}/?invite={raw}",
                "data": InvitationSerializer(invitation).data,
            },
            status=201,
        )
