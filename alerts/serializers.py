from rest_framework import serializers

from .models import ResolucionAlerta


class ResolucionAlertaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)

    class Meta:
        model = ResolucionAlerta
        fields = (
            "id",
            "producto",
            "producto_nombre",
            "tipo_alerta",
            "accion",
            "notas",
            "usuario_nombre",
            "creado_en",
        )
        read_only_fields = ("id", "producto_nombre", "usuario_nombre", "creado_en")

    def create(self, validated_data):
        producto = validated_data.get("producto")
        request = self.context.get("request")
        user = request.user if request and getattr(request.user, "is_authenticated", False) else None
        validated_data["producto_nombre"] = producto.nombre
        validated_data["usuario"] = user
        return super().create(validated_data)
