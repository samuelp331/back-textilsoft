from rest_framework import serializers

from .models import CalificacionProveedor, Proveedor


class CalificacionProveedorSerializer(serializers.ModelSerializer):
    promedio = serializers.FloatField(read_only=True)

    class Meta:
        model = CalificacionProveedor
        fields = (
            "id",
            "proveedor",
            "calidad_suministro",
            "cumplimiento_tiempos",
            "precio_calidad",
            "promedio",
            "comentario",
            "creado_en",
        )
        read_only_fields = ("creado_en",)


class ProveedorSerializer(serializers.ModelSerializer):
    calificacion_promedio = serializers.SerializerMethodField()

    class Meta:
        model = Proveedor
        fields = (
            "id",
            "nombre",
            "nombre_contacto",
            "email",
            "telefono",
            "direccion",
            "notas",
            "productos_suministrados",
            "creado_en",
            "actualizado_en",
            "calificacion_promedio",
        )
        read_only_fields = ("creado_en", "actualizado_en")

    def get_calificacion_promedio(self, obj):
        calificaciones = obj.calificaciones.all()
        if not calificaciones.exists():
            return None
        total = sum(c.promedio for c in calificaciones)
        return round(total / calificaciones.count(), 1)
