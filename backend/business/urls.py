from rest_framework.routers import DefaultRouter

from business.views import ClientViewSet, EmployeeViewSet, ProductViewSet, ServiceViewSet


class ApiRouter(DefaultRouter):
    include_root_view = False
    include_format_suffixes = False


router = ApiRouter(trailing_slash=False)
router.register("clients", ClientViewSet, basename="client")
router.register("employees", EmployeeViewSet, basename="employee")
router.register("products", ProductViewSet, basename="product")
router.register("services", ServiceViewSet, basename="service")

urlpatterns = router.urls
