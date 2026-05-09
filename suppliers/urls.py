from rest_framework.routers import DefaultRouter

from .views import CalificacionProveedorViewSet, ProveedorViewSet

router = DefaultRouter()
router.register("proveedores", ProveedorViewSet, basename="proveedor")
router.register("calificaciones", CalificacionProveedorViewSet, basename="calificacion")

urlpatterns = router.urls
