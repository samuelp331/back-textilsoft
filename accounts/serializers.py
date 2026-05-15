from django.conf import settings
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import Rol, Usuario, UsuarioGestionAuditoria

try:
    from profiles.models import PerfilUsuario
except Exception:  # pragma: no cover
    PerfilUsuario = None


class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all())

    class Meta:
        model = Usuario
        fields = ("id", "nombre", "email", "rol")


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class RegisterSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=120)
    identificacion = serializers.CharField(max_length=40, required=False, allow_blank=True)
    celular = serializers.CharField(max_length=30, required=False, allow_blank=True)
    cargo = serializers.CharField(max_length=120, required=False, allow_blank=True)
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=6)
    rol = serializers.ChoiceField(
        choices=[c.value for c in Rol.Tipo],
        default=Rol.Tipo.OPERARIO,
        required=False,
    )

    def validate_rol(self, value):
        allowed = getattr(settings, "REGISTRATION_ASSIGNABLE_ROLES", ())
        if allowed and value not in allowed:
            raise serializers.ValidationError("Este rol no puede asignarse en el registro.")
        return value

    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value


class RecoverAccountSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=6)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False, min_length=6)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Las contrasenas no coinciden."})
        return attrs


class RolDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ("id", "nombre")


class UsuarioAdminListSerializer(serializers.ModelSerializer):
    rol = RolDetailSerializer(read_only=True)
    perfil = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ("id", "nombre", "email", "rol", "estado", "perfil")

    def get_perfil(self, obj):
        if PerfilUsuario is None:
            return None
        try:
            p = obj.perfil
        except PerfilUsuario.DoesNotExist:
            return None
        return {
            "identificacion": p.identificacion or "",
            "celular": p.celular or "",
            "direccion": p.direccion or "",
        }


class UsuarioAdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=6)
    rol = serializers.SlugRelatedField(slug_field="nombre", queryset=Rol.objects.all())
    identificacion = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")
    celular = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")

    class Meta:
        model = Usuario
        fields = ("nombre", "email", "password", "rol", "identificacion", "celular", "direccion")

    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        identificacion = (validated_data.pop("identificacion", "") or "").strip()
        celular = (validated_data.pop("celular", "") or "").strip()
        direccion = (validated_data.pop("direccion", "") or "").strip()
        password = validated_data.pop("password")
        rol = validated_data.pop("rol")
        try:
            user = Usuario.objects.create_user(
                email=validated_data["email"],
                password=password,
                nombre=validated_data["nombre"],
                rol=rol,
                estado=Usuario.Estado.ACTIVO,
            )
        except IntegrityError:
            raise serializers.ValidationError({"email": ["Ya existe una cuenta con este correo."]})

        if PerfilUsuario is not None:
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
            perfil.identificacion = identificacion
            perfil.celular = celular
            perfil.direccion = direccion
            perfil.cargo = user.rol.get_nombre_display()
            perfil.save(update_fields=["identificacion", "celular", "direccion", "cargo"])

        UsuarioGestionAuditoria.objects.create(
            usuario_afectado=user,
            ejecutado_por=request.user,
            accion=UsuarioGestionAuditoria.Accion.CREAR,
            detalle="",
        )
        return user


class UsuarioAdminUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
        min_length=6,
    )
    rol = serializers.SlugRelatedField(
        slug_field="nombre",
        queryset=Rol.objects.all(),
        required=False,
    )
    identificacion = serializers.CharField(max_length=40, required=False, allow_blank=True)
    celular = serializers.CharField(max_length=30, required=False, allow_blank=True)
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = ("nombre", "email", "rol", "estado", "password", "identificacion", "celular", "direccion")

    def validate_email(self, value):
        qs = Usuario.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value

    def validate(self, attrs):
        inst = self.instance
        req_user = self.context["request"].user
        if inst and inst.pk == req_user.pk:
            if attrs.get("estado") == Usuario.Estado.INACTIVO:
                raise serializers.ValidationError({"estado": "No puede desactivar su propia cuenta."})
        return attrs

    def update(self, instance, validated_data):
        perfil_ident = validated_data.pop("identificacion", None)
        perfil_cel = validated_data.pop("celular", None)
        perfil_dir = validated_data.pop("direccion", None)

        password = validated_data.pop("password", None)
        if password == "":
            password = None

        revoke = False
        if password:
            revoke = True
        if validated_data.get("estado") == Usuario.Estado.INACTIVO:
            revoke = True
        if "rol" in validated_data and validated_data["rol"].id != instance.rol_id:
            revoke = True
        if "email" in validated_data and validated_data["email"].lower() != instance.email.lower():
            revoke = True

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()

        perfil_update_fields = []
        if PerfilUsuario is not None and any(
            x is not None for x in (perfil_ident, perfil_cel, perfil_dir)
        ):
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=instance)
            if perfil_ident is not None:
                perfil.identificacion = perfil_ident.strip()
                perfil_update_fields.append("identificacion")
            if perfil_cel is not None:
                perfil.celular = perfil_cel.strip()
                perfil_update_fields.append("celular")
            if perfil_dir is not None:
                perfil.direccion = perfil_dir.strip()
                perfil_update_fields.append("direccion")
            if perfil_update_fields:
                perfil.save(update_fields=perfil_update_fields)

        if "rol" in validated_data and PerfilUsuario is not None:
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=instance)
            perfil.cargo = instance.rol.get_nombre_display()
            perfil.save(update_fields=["cargo"])

        if revoke:
            Token.objects.filter(user=instance).delete()

        UsuarioGestionAuditoria.objects.create(
            usuario_afectado=instance,
            ejecutado_por=self.context["request"].user,
            accion=UsuarioGestionAuditoria.Accion.ACTUALIZAR,
            detalle="",
        )
        return instance
