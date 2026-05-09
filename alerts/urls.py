from django.urls import path

from .views import AlertasInventarioAPIView, ResolucionAlertaListCreateAPIView

urlpatterns = [
    path("", AlertasInventarioAPIView.as_view(), name="alertas-inventario"),
    path("resoluciones/", ResolucionAlertaListCreateAPIView.as_view(), name="alertas-resoluciones"),
]
