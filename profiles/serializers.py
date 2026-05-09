from rest_framework import serializers

from .models import PerfilUsuario


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source="usuario.id", read_only=True)
    nombre = serializers.CharField(source="usuario.nombre", read_only=True)
    email = serializers.EmailField(source="usuario.email", read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = (
            "usuario_id",
            "nombre",
            "email",
            "identificacion",
            "celular",
            "cargo",
            "direccion",
            "fecha_contratacion",
            "foto_base64",
        )
