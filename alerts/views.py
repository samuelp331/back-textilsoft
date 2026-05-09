from django.utils import timezone
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import AlertsPermission, AlertsResolutionPermission
from inventory.models import Producto

from .models import ResolucionAlerta
from .serializers import ResolucionAlertaSerializer


class AlertasInventarioAPIView(APIView):
    permission_classes = [AlertsPermission]

    def get(self, request):
        hoy = timezone.localdate()
        alertas = []

        for producto in Producto.objects.select_related('ubicacion').all():
            ubicacion_info = ""
            if producto.ubicacion:
                ubicacion_info = f"P{producto.ubicacion.pasillo}-E{producto.ubicacion.estante}-S{producto.ubicacion.seccion}"

            if producto.cantidad <= producto.cantidad_minima:
                alertas.append(
                    {
                        "type": "low-stock",
                        "product_id": producto.id,
                        "product_name": producto.nombre,
                        "current": producto.cantidad,
                        "minimum": producto.cantidad_minima,
                        "ubicacion": ubicacion_info,
                    }
                )

            if producto.fecha_vencimiento:
                dias = (producto.fecha_vencimiento - hoy).days
                if dias < 0:
                    alertas.append(
                        {
                            "type": "expired",
                            "product_id": producto.id,
                            "product_name": producto.nombre,
                            "days_overdue": abs(dias),
                            "expiration_date": producto.fecha_vencimiento,
                            "ubicacion": ubicacion_info,
                        }
                    )
                elif dias <= producto.dias_preaviso_vencimiento:
                    alertas.append(
                        {
                            "type": "expiration",
                            "product_id": producto.id,
                            "product_name": producto.nombre,
                            "days_left": dias,
                            "expiration_date": producto.fecha_vencimiento,
                            "ubicacion": ubicacion_info,
                        }
                    )

        return Response(alertas)


class ResolucionAlertaListCreateAPIView(ListCreateAPIView):
    permission_classes = [AlertsResolutionPermission]
    serializer_class = ResolucionAlertaSerializer

    def get_queryset(self):
        return ResolucionAlerta.objects.select_related("usuario", "producto").all()

