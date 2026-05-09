import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from urllib.parse import urlencode

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import MovimientoInventario, Producto
from suppliers.models import Proveedor

from .models import Rol, Usuario, UsuarioGestionAuditoria
from .permissions import AdministradorPermission
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    RecoverAccountSerializer,
    RegisterSerializer,
    UsuarioAdminCreateSerializer,
    UsuarioAdminListSerializer,
    UsuarioAdminUpdateSerializer,
    UsuarioSerializer,
)

try:
    from profiles.models import PerfilUsuario
except Exception:  # pragma: no cover
    PerfilUsuario = None


logger = logging.getLogger(__name__)


_RECOVERY_RESPONSE_DETAIL = (
    "Si ese correo está registrado, recibirás un mensaje con un enlace para restablecer la contraseña. "
    "Revisa también correo no deseado (spam)."
)
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request=request, username=email, password=password)
        if not user:
            return Response(
                {"detail": "Credenciales invalidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        usuario_data = UsuarioSerializer(user).data
        rol_data = {
            "id": user.rol.id,
            "nombre": user.rol.nombre,
        }

        return Response(
            {
                "token": token.key,
                "usuario": usuario_data,
                "rol": rol_data,
            },
            status=status.HTTP_200_OK,
        )


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        rol_asignado, _ = Rol.objects.get_or_create(nombre=data["rol"])
        try:
            user = Usuario.objects.create_user(
                email=data["email"],
                password=data["password"],
                nombre=data["nombre"],
                rol=rol_asignado,
                estado=Usuario.Estado.ACTIVO,
            )
        except IntegrityError:
            return Response(
                {"email": ["Ya existe una cuenta con este correo."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if PerfilUsuario is not None:
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
            perfil.identificacion = data.get("identificacion", "")
            perfil.celular = data.get("celular", "")
            cargo_txt = (data.get("cargo") or "").strip()
            perfil.cargo = cargo_txt or user.rol.get_nombre_display()
            perfil.direccion = data.get("direccion", "")
            perfil.save()

        return Response(
            {"detail": "Registro exitoso. Ya puedes iniciar sesion."},
            status=status.HTTP_201_CREATED,
        )


class RecoverAccountAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RecoverAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = Usuario.objects.filter(email__iexact=email).first()
        if user:
            uid = force_str(urlsafe_base64_encode(force_bytes(user.pk)))
            token_str = default_token_generator.make_token(user)
            base_url = getattr(settings, "PASSWORD_RESET_FRONTEND_URL", "http://127.0.0.1:5173").strip().rstrip("/")
            query = urlencode({"page": "resetPassword", "uid": uid, "token": token_str})
            reset_link = f"{base_url}/index.html?{query}"

            subject = "Recuperación de cuenta - TextilSoft"
            body = (
                f"Hola {user.nombre},\n\n"
                "Solicitaste restablecer tu contraseña en TextilSoft. "
                "Abre este enlace en tu navegador para elegir una nueva contraseña:\n\n"
                f"{reset_link}\n\n"
                "Si no solicitaste este cambio, puedes ignorar este mensaje.\n"
            )
            try:
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception("Fallo el envío de correo de recuperacion para solicitud desde %s", email)

        return Response({"detail": _RECOVERY_RESPONSE_DETAIL}, status=status.HTTP_200_OK)


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pk_str = serializer.validated_data["uid"]
        token_str = serializer.validated_data["token"]
        password_new = serializer.validated_data["password"]

        try:
            uid_plain = force_str(urlsafe_base64_decode(pk_str))
            user = Usuario.objects.get(pk=uid_plain)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return Response(
                {"detail": "El enlace no es valido o ha expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token_str):
            return Response(
                {"detail": "El enlace no es valido o ha expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password_new)
        user.save(update_fields=["password"])
        Token.objects.filter(user=user).delete()

        return Response(
            {"detail": "Contraseña actualizada. Ya puedes iniciar sesion."},
            status=status.HTTP_200_OK,
        )


class AdminResumenAPIView(APIView):
    """
    KPIs consolidados solo para administradores (panel administrativo).
    """

    permission_classes = [AdministradorPermission]

    def get(self, request):
        usuarios = Usuario.objects.filter(estado=Usuario.Estado.ACTIVO).count()
        productos = Producto.objects.count()
        productos_stock_ok = Producto.objects.filter(cantidad__gt=F("cantidad_minima")).count()
        proveedores = Proveedor.objects.count()
        movimientos = MovimientoInventario.objects.count()

        return Response(
            {
                "usuarios_activos": usuarios,
                "productos": productos,
                "productos_stock_ok": productos_stock_ok,
                "proveedores": proveedores,
                "movimientos": movimientos,
            }
        )


class AdminUsuarioListCreateAPIView(APIView):
    """CRUD de usuarios (crear y listar) — solo administrador de la aplicación."""

    permission_classes = [AdministradorPermission]

    def get(self, request):
        qs = Usuario.objects.select_related("rol").order_by("email")
        return Response(UsuarioAdminListSerializer(qs, many=True).data)

    def post(self, request):
        ser = UsuarioAdminCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(UsuarioAdminListSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminUsuarioDetailAPIView(APIView):
    """Detalle, actualización parcial y baja lógica (DELETE) — solo administrador."""

    permission_classes = [AdministradorPermission]

    def get(self, request, pk):
        user = get_object_or_404(Usuario.objects.select_related("rol"), pk=pk)
        return Response(UsuarioAdminListSerializer(user).data)

    def patch(self, request, pk):
        user = get_object_or_404(Usuario.objects.select_related("rol"), pk=pk)
        ser = UsuarioAdminUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        user.refresh_from_db()
        return Response(UsuarioAdminListSerializer(user).data)

    def delete(self, request, pk):
        user = get_object_or_404(Usuario, pk=pk)
        if user.pk == request.user.pk:
            return Response(
                {"detail": "No puede desactivar su propia cuenta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        was_active = user.estado == Usuario.Estado.ACTIVO
        user.estado = Usuario.Estado.INACTIVO
        user.save(update_fields=["estado"])
        Token.objects.filter(user=user).delete()
        if was_active:
            UsuarioGestionAuditoria.objects.create(
                usuario_afectado=user,
                ejecutado_por=request.user,
                accion=UsuarioGestionAuditoria.Accion.DESACTIVAR,
                detalle="",
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
