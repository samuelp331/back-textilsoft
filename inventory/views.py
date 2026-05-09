from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from accounts.models import Rol
from accounts.permissions import InventoryAuditPermission, InventoryMovementPermission, InventoryPermission
from .category_utils import unique_categorias_for_list
from .models import MovimientoInventario, Producto, RegistroEliminacionProducto, Ubicacion
from .serializers import (
    MovimientoInventarioSerializer,
    ProductoSerializer,
    RegistroEliminacionProductoSerializer,
    UbicacionSerializer,
)


class RegistroEliminacionProductoListAPIView(ListAPIView):
    """Listado de bajas de producto para auditoría (supervisor, bodeguero, administrador)."""

    permission_classes = [InventoryAuditPermission]
    serializer_class = RegistroEliminacionProductoSerializer

    def get_queryset(self):
        qs = RegistroEliminacionProducto.objects.select_related("eliminado_por").all()
        limite = self.request.query_params.get("limite") or "50"
        try:
            n = max(1, min(int(limite), 200))
        except ValueError:
            n = 50
        return qs[:n]


class UbicacionViewSet(viewsets.ModelViewSet):
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer
    permission_classes = [InventoryPermission]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related("ubicacion").all()
    serializer_class = ProductoSerializer
    permission_classes = [InventoryPermission]

    def perform_destroy(self, instance):
        user = self.request.user if getattr(self.request.user, "is_authenticated", False) else None
        RegistroEliminacionProducto.objects.create(
            producto_id_original=instance.pk,
            codigo=instance.codigo,
            nombre=instance.nombre,
            categoria=instance.categoria,
            cantidad_al_eliminar=instance.cantidad,
            eliminado_por=user,
        )
        instance.delete()

    def get_queryset(self):
        queryset = Producto.objects.select_related("ubicacion").all()

        categoria = self.request.query_params.get("categoria")
        ubicacion_id = self.request.query_params.get("ubicacion_id")
        pasillo = self.request.query_params.get("pasillo")

        if categoria:
            queryset = queryset.filter(categoria__icontains=categoria)
        if ubicacion_id:
            queryset = queryset.filter(ubicacion_id=ubicacion_id)
        if pasillo:
            queryset = queryset.filter(ubicacion__pasillo__icontains=pasillo)

        return queryset

    @action(detail=False, methods=["get"])
    def categorias(self, request):
        return Response(unique_categorias_for_list())


class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [InventoryMovementPermission]

    def get_queryset(self):
        queryset = MovimientoInventario.objects.select_related("producto", "registrado_por").all()

        fecha_desde = self.request.query_params.get("fecha_desde")
        fecha_hasta = self.request.query_params.get("fecha_hasta")
        producto_id = self.request.query_params.get("producto_id")
        tipo = self.request.query_params.get("tipo")

        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        return queryset

    def create(self, request, *args, **kwargs):
        role_name = getattr(getattr(request.user, "rol", None), "nombre", None)
        movement_type = request.data.get("tipo")

        # Operario: solo puede registrar salidas de insumos.
        if role_name == Rol.Tipo.OPERARIO and movement_type != "salida":
            return Response(
                {"detail": "El operario solo puede registrar movimientos tipo salida."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().create(request, *args, **kwargs)

# Create your views here.
