from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .category_utils import find_canonical_categoria, normalize_categoria_text
from .models import MovimientoInventario, Producto, RegistroEliminacionProducto, Ubicacion


class RegistroEliminacionProductoSerializer(serializers.ModelSerializer):
    eliminado_por_nombre = serializers.CharField(source="eliminado_por.nombre", read_only=True)

    class Meta:
        model = RegistroEliminacionProducto
        fields = (
            "id",
            "producto_id_original",
            "codigo",
            "nombre",
            "categoria",
            "cantidad_al_eliminar",
            "eliminado_en",
            "eliminado_por",
            "eliminado_por_nombre",
        )


class UbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacion
        fields = ("id", "pasillo", "estante", "seccion")


class ProductoSerializer(serializers.ModelSerializer):
    ubicacion_detalle = UbicacionSerializer(source="ubicacion", read_only=True)
    ubicacion_id = serializers.PrimaryKeyRelatedField(
        queryset=Ubicacion.objects.all(), source="ubicacion", write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Producto
        fields = (
            "id",
            "codigo",
            "nombre",
            "categoria",
            "ubicacion",
            "ubicacion_detalle",
            "ubicacion_id",
            "descripcion",
            "cantidad",
            "cantidad_minima",
            "precio",
            "unidad",
            "fecha_vencimiento",
            "dias_preaviso_vencimiento",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = ("creado_en", "actualizado_en")

    def validate_categoria(self, value):
        text = normalize_categoria_text(value)
        if not text:
            raise serializers.ValidationError("La categoría es obligatoria.")
        canonical = find_canonical_categoria(text)
        return canonical if canonical is not None else text

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and getattr(request.user, "is_authenticated", False) else None
        cantidad_inicial = int(validated_data.get("cantidad") or 0)

        with transaction.atomic():
            producto = super().create(validated_data)

            if cantidad_inicial > 0:
                MovimientoInventario.objects.create(
                    producto=producto,
                    fecha=timezone.localdate(),
                    tipo=MovimientoInventario.Tipo.ENTRADA,
                    cantidad=cantidad_inicial,
                    motivo="Registro inicial de producto",
                    registrado_por=user,
                )

        return producto


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    registrado_por_nombre = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = (
            "id",
            "producto",
            "producto_nombre",
            "fecha",
            "tipo",
            "cantidad",
            "motivo",
            "registrado_por",
            "registrado_por_nombre",
            "creado_en",
        )
        read_only_fields = ("creado_en", "registrado_por")

    def get_registrado_por_nombre(self, obj):
        user = getattr(obj, "registrado_por", None)
        return user.nombre if user else None

    def validate_cantidad(self, value):
        if value == 0:
            raise serializers.ValidationError("La cantidad no puede ser cero.")
        return value

    def create(self, validated_data):
        producto = validated_data["producto"]
        tipo = validated_data["tipo"]
        cantidad = validated_data["cantidad"]
        request = self.context.get("request")
        user = request.user if request and getattr(request.user, "is_authenticated", False) else None

        with transaction.atomic():
            producto = Producto.objects.select_for_update().get(pk=producto.pk)
            if tipo == MovimientoInventario.Tipo.ENTRADA:
                if cantidad < 0:
                    raise serializers.ValidationError({"cantidad": "En una entrada la cantidad debe ser positiva."})
                producto.cantidad += cantidad
            elif tipo == MovimientoInventario.Tipo.SALIDA:
                if cantidad < 0:
                    raise serializers.ValidationError({"cantidad": "En una salida la cantidad debe ser positiva."})
                if producto.cantidad < cantidad:
                    raise serializers.ValidationError({"cantidad": "Stock insuficiente para esta salida."})
                producto.cantidad -= cantidad
            elif tipo == MovimientoInventario.Tipo.AJUSTE:
                nuevas = producto.cantidad + cantidad
                if nuevas < 0:
                    raise serializers.ValidationError({"cantidad": "El ajuste dejaría existencias negativas."})
                producto.cantidad = nuevas
            producto.save(update_fields=["cantidad"])
            validated_data["producto"] = producto
            validated_data["registrado_por"] = user

            return MovimientoInventario.objects.create(**validated_data)
