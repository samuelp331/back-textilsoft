from collections import defaultdict

from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import ReportsAnalyticsPermission, ReportsOperationalPermission
from inventory.models import MovimientoInventario, Producto


class ReporteMovimientosAPIView(APIView):
    permission_classes = [ReportsOperationalPermission]

    def get(self, request):
        queryset = MovimientoInventario.objects.select_related("producto", "registrado_por").all()

        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        producto_id = request.query_params.get("producto_id")
        tipo = request.query_params.get("tipo")

        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        data = [
            {
                "id": mov.id,
                "fecha": mov.fecha,
                "producto_id": mov.producto_id,
                "producto_nombre": mov.producto.nombre,
                "tipo": mov.tipo,
                "cantidad": mov.cantidad,
                "motivo": mov.motivo,
                "registrado_por": mov.registrado_por_id,
                "registrado_por_nombre": mov.registrado_por.nombre if mov.registrado_por_id else None,
            }
            for mov in queryset
        ]
        return Response(data)


class ReporteConsumoAPIView(APIView):
    permission_classes = [ReportsAnalyticsPermission]

    def get(self, request):
        queryset = MovimientoInventario.objects.select_related("producto").filter(tipo="salida")
        categoria = request.query_params.get("categoria")
        if categoria:
            queryset = queryset.filter(producto__categoria__iexact=categoria)

        acumulado = defaultdict(int)
        productos = {}
        for mov in queryset:
            acumulado[mov.producto_id] += abs(mov.cantidad)
            productos[mov.producto_id] = mov.producto

        total = sum(acumulado.values()) or 1
        data = []
        for producto_id, cantidad in acumulado.items():
            producto = productos[producto_id]
            data.append(
                {
                    "producto_id": producto_id,
                    "producto_nombre": producto.nombre,
                    "categoria": producto.categoria,
                    "cantidad": cantidad,
                    "porcentaje": round((cantidad / total) * 100, 2),
                }
            )

        data.sort(key=lambda item: item["cantidad"], reverse=True)
        return Response(data)


class ReporteConsumoSerieAPIView(APIView):
    """
    Serie temporal de salidas (consumo) para un producto — tendencia y rotación (HU-07).
    agrupar: mes | semana | dia
    """

    permission_classes = [ReportsAnalyticsPermission]

    def get(self, request):
        producto_id = request.query_params.get("producto_id")
        if not producto_id:
            return Response(
                {"detail": "Indique producto_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        producto = Producto.objects.filter(pk=producto_id).first()
        if not producto:
            return Response(
                {"detail": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        agrupar = (request.query_params.get("agrupar") or "mes").lower()
        if agrupar == "dia":
            trunc = TruncDay("fecha")
        elif agrupar == "semana":
            trunc = TruncWeek("fecha")
        else:
            trunc = TruncMonth("fecha")

        queryset = MovimientoInventario.objects.filter(
            producto_id=producto_id,
            tipo=MovimientoInventario.Tipo.SALIDA,
        )

        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)

        rows = (
            queryset.annotate(periodo=trunc)
            .values("periodo")
            .annotate(cantidad=Sum("cantidad"))
            .order_by("periodo")
        )

        serie = []
        total_salidas = 0
        for row in rows:
            p = row["periodo"]
            if p is None:
                fecha_iso = None
            elif hasattr(p, "date"):
                fecha_iso = p.date().isoformat()
            else:
                fecha_iso = p.isoformat()
            cant = int(row["cantidad"] or 0)
            total_salidas += cant
            serie.append({"periodo": fecha_iso, "cantidad": cant})

        return Response(
            {
                "producto_id": producto.id,
                "producto_nombre": producto.nombre,
                "producto_codigo": producto.codigo,
                "agrupar": agrupar if agrupar in ("dia", "semana") else "mes",
                "total_salidas_periodo": total_salidas,
                "serie": serie,
            }
        )

