from django.urls import path

from .views import ReporteConsumoAPIView, ReporteConsumoSerieAPIView, ReporteMovimientosAPIView

urlpatterns = [
    path("movimientos", ReporteMovimientosAPIView.as_view(), name="reporte-movimientos"),
    path("consumo", ReporteConsumoAPIView.as_view(), name="reporte-consumo"),
    path("consumo-serie", ReporteConsumoSerieAPIView.as_view(), name="reporte-consumo-serie"),
]
