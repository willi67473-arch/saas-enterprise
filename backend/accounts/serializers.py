from rest_framework import serializers

from accounts.models import User
from core.constants import ALL_ROLES, SUPER_ADMIN, USER_STATUSES
from tenants.serializers import TenantSerializer


class UserSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "tenant_id", "nom", "prenom", "email", "role", "plan", "status", "avatar",
                  "created_at", "updated_at")
        read_only_fields = fields


class UserWithTenantSerializer(UserSerializer):
    tenant = TenantSerializer(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("tenant",)
        read_only_fields = fields


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "nom", "prenom", "role", "avatar")
        read_only_fields = fields


class UserWriteSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=255)
    prenom = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255)
    role = serializers.ChoiceField(choices=ALL_ROLES)
    status = serializers.ChoiceField(choices=USER_STATUSES)
    password = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True,
        min_length=8, max_length=128, trim_whitespace=False,
    )

    def validate_email(self, value):
        value = value.strip().lower()
        queryset = User.objects.filter(email__iexact=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Cette adresse courriel est déjà utilisée.")
        return value

    def validate_role(self, value):
        # SÉCURITÉ : le rôle SUPER_ADMIN ne s'attribue jamais via l'API (il n'est conservé que s'il existe déjà).
        if value == SUPER_ADMIN and not (self.instance is not None and self.instance.role == SUPER_ADMIN):
            raise serializers.ValidationError("Le rôle SUPER_ADMIN ne peut pas être attribué.")
        return value

    def validate(self, attrs):
        instance = self.instance
        if instance is not None:
            if instance.role == SUPER_ADMIN:
                attrs["role"] = SUPER_ADMIN  # le propriétaire n'est jamais rétrogradé
            current = self.context["request"].user
            if instance.pk == current.pk:
                if attrs.get("status") == "SUSPENDED":
                    raise serializers.ValidationError({"status": ["Vous ne pouvez pas suspendre votre propre compte."]})
                if attrs.get("role") != instance.role:
                    raise serializers.ValidationError({"role": ["Vous ne pouvez pas modifier votre propre rôle."]})
        return attrs
