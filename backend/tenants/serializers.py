from rest_framework import serializers

from tenants.models import Plan, Tenant, TenantInvitation


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ("id", "name", "slug", "price_monthly", "max_projects", "max_users",
                  "has_time_tracking", "has_realtime_ws", "features")
        read_only_fields = fields


class TenantSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Tenant
        fields = ("id", "name", "subdomain", "subscription_status", "trial_ends_at", "plan", "created_at")
        read_only_fields = fields


class InvitationSerializer(serializers.ModelSerializer):
    """Le jeton n'est volontairement PAS exposé (seul le lien renvoyé à la création le contient)."""

    class Meta:
        model = TenantInvitation
        fields = ("id", "email", "role", "expires_at", "accepted_at", "created_at")
        read_only_fields = fields
