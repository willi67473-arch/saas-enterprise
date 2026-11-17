from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from business.models import Client, Employee, Product, Service
from business.serializers import ClientSerializer, EmployeeSerializer, ProductSerializer, ServiceSerializer
from core.permissions import IsManagerRole, ManagerWriteOnly
from core.views import TenantGenericViewSet


class TenantCrudViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    TenantGenericViewSet,
):
    """CRUD limité au tenant courant, réponses au format {message, data} attendu par le frontend.

    Pas de route de détail en lecture (GET /ressource/{id}), comme dans le contrat d'API.
    """

    model = None
    label = "Élément"
    permission_classes = [IsAuthenticated, ManagerWriteOnly]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        # IMPORTANT : jamais d'attribut `queryset` de classe, il serait évalué hors tenant au chargement.
        return self.model.objects.order_by("-id")

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()  # le tenant est posé par TenantOwnedModel.save()
        return Response(
            {"message": f"{self.label} créé(e)", "data": self.get_serializer(instance).data}, status=201
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()  # 404 si l'objet appartient à un autre tenant
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({"message": f"{self.label} mis(e) à jour", "data": self.get_serializer(instance).data})

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response({"message": f"{self.label} supprimé(e)"})


class ClientViewSet(TenantCrudViewSet):
    model = Client
    label = "Client"
    serializer_class = ClientSerializer


class ProductViewSet(TenantCrudViewSet):
    model = Product
    label = "Produit"
    serializer_class = ProductSerializer


class ServiceViewSet(TenantCrudViewSet):
    model = Service
    label = "Service"
    serializer_class = ServiceSerializer


class EmployeeViewSet(TenantCrudViewSet):
    """Données salariales : lecture ET écriture réservées aux managers et au-dessus."""

    model = Employee
    label = "Employé"
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsManagerRole]
