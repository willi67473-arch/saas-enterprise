from rest_framework import serializers


class TenantUniqueSerializerMixin:
    """Unicité métier PAR TENANT (le manager scopé limite déjà la recherche au tenant courant)."""

    tenant_unique_fields = ()
    tenant_unique_message = "Cette valeur est déjà utilisée dans votre espace."

    def validate(self, attrs):
        attrs = super().validate(attrs)
        model = self.Meta.model
        errors = {}
        for field in self.tenant_unique_fields:
            if field in attrs:
                queryset = model.objects.filter(**{field: attrs[field]})
                if self.instance is not None:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    errors[field] = [self.tenant_unique_message]
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
