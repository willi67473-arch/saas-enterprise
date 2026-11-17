from rest_framework import serializers

from accounts.models import User
from core.constants import ASSIGNABLE_ROLES
from tenants.models import Plan, Tenant


class RegisterTenantSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    subdomain = serializers.RegexField(
        r"^[A-Za-z0-9_-]+$",
        max_length=63,
        error_messages={"invalid": "Seuls les lettres, chiffres, tirets et underscores sont autorisés."},
    )
    nom = serializers.CharField(max_length=255)
    prenom = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True, trim_whitespace=False)
    plan_slug = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_subdomain(self, value):
        value = value.lower()
        if Tenant.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError("Ce sous-domaine est déjà pris.")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cette adresse courriel est déjà utilisée.")
        return value

    def validate(self, attrs):
        slug = attrs.pop("plan_slug", None) or "free"
        plan = Plan.objects.filter(slug=slug).first()
        if plan is None:
            raise serializers.ValidationError({"plan_slug": ["Forfait inconnu."]})
        attrs["plan"] = plan
        return attrs


class InviteSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    role = serializers.ChoiceField(choices=ASSIGNABLE_ROLES)


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    nom = serializers.CharField(max_length=255)
    prenom = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True, trim_whitespace=False)


class SubscribeSerializer(serializers.Serializer):
    plan_id = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), source="plan")
