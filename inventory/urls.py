from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    MovimientoInventarioViewSet,
    ProductoViewSet,
    RegistroEliminacionProductoListAPIView,
    UbicacionViewSet,
)

router = DefaultRouter()
router.register("productos", ProductoViewSet, basename="producto")
router.register("movimientos", MovimientoInventarioViewSet, basename="movimiento")
router.register("ubicaciones", UbicacionViewSet, basename="ubicacion")

urlpatterns = [
    path("eliminaciones-productos/", RegistroEliminacionProductoListAPIView.as_view()),
] + router.urls
