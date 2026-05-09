from django.db.models import Q
from rest_framework import viewsets

from accounts.permissions import SupplierPermission
from .models import CalificacionProveedor, Proveedor
from .serializers import CalificacionProveedorSerializer, ProveedorSerializer


class ProveedorViewSet(viewsets.ModelViewSet):
    serializer_class = ProveedorSerializer
    permission_classes = [SupplierPermission]

    def get_queryset(self):
        queryset = Proveedor.objects.all()
        q = self.request.query_params.get("q")
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q)
                | Q(nombre_contacto__icontains=q)
                | Q(email__icontains=q)
            )
        return queryset.order_by("nombre")


class CalificacionProveedorViewSet(viewsets.ModelViewSet):
    serializer_class = CalificacionProveedorSerializer
    permission_classes = [SupplierPermission]

    def get_queryset(self):
        queryset = CalificacionProveedor.objects.select_related("proveedor").all().order_by("-creado_en")
        proveedor_id = self.request.query_params.get("proveedor")
        if proveedor_id:
            queryset = queryset.filter(proveedor_id=proveedor_id)
        return queryset
