from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Rol


class RolePermission(BasePermission):
    """
    Permisos por rol para proteger endpoints sensibles.
    """

    allowed_roles = ()
    read_roles = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        role_name = getattr(getattr(user, "rol", None), "nombre", None)
        if role_name is None:
            return False

        if request.method in SAFE_METHODS and self.read_roles:
            return role_name in self.read_roles or role_name in self.allowed_roles

        return role_name in self.allowed_roles


class InventoryAuditPermission(RolePermission):
    """
    Auditoría de eliminaciones de producto: administrador, supervisor y bodeguero.
    """

    allowed_roles = (
        Rol.Tipo.ADMINISTRADOR,
        Rol.Tipo.SUPERVISOR,
        Rol.Tipo.BODEGUERO,
    )


class InventoryPermission(RolePermission):
    """
    Productos (catalogo):
    - administradores, supervisores y bodegueros: CRUD
    - operarios: solo lectura
    """

    allowed_roles = (
        Rol.Tipo.ADMINISTRADOR,
        Rol.Tipo.SUPERVISOR,
        Rol.Tipo.BODEGUERO,
    )
    read_roles = (Rol.Tipo.OPERARIO,)


class InventoryMovementPermission(RolePermission):
    """
    Movimientos de inventario:
    - administradores, supervisores y bodegueros: lectura y creacion/edicion
    - operarios: lectura y creacion (solo salida, se valida en la vista)
    """

    allowed_roles = (
        Rol.Tipo.ADMINISTRADOR,
        Rol.Tipo.SUPERVISOR,
        Rol.Tipo.BODEGUERO,
    )
    read_roles = (Rol.Tipo.OPERARIO,)

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        role_name = getattr(getattr(user, "rol", None), "nombre", None)
        if role_name is None:
            return False

        if role_name in self.allowed_roles:
            return True

        if role_name == Rol.Tipo.OPERARIO:
            # Operario puede consultar y crear movimientos; la vista
            # limita que el tipo permitido sea solamente "salida".
            return request.method in SAFE_METHODS or request.method == "POST"

        return False


class SupplierPermission(RolePermission):
    """
    Proveedores:
    - administradores y supervisores: CRUD
    - bodegueros: lectura
    - operarios: sin acceso
    """

    allowed_roles = (
        Rol.Tipo.ADMINISTRADOR,
        Rol.Tipo.SUPERVISOR,
    )
    read_roles = (Rol.Tipo.BODEGUERO,)


class ReportsOperationalPermission(RolePermission):
    """
    Reportes operativos (movimientos):
    - administradores, supervisores y bodegueros: acceso
    - operarios: sin acceso
    """

    allowed_roles = (
        Rol.Tipo.ADMINISTRADOR,
        Rol.Tipo.SUPERVISOR,
        Rol.Tipo.BODEGUERO,
    )


class ReportsAnalyticsPermission(RolePermission):
    """
    Reportes analiticos/consolidados:
    - administradores y supervisores: acceso
    - bodegueros y operarios: sin acceso
    """

    allowed_roles = (
        Rol.Tipo.ADMINISTRADOR,
        Rol.Tipo.SUPERVISOR,
    )


class AlertsPermission(RolePermission):
    """
    Alertas:
    - administradores, supervisores y bodegueros: lectura (API GET)
    - operarios: solo lectura (misma información que el inventario en solo lectura)
    """

    allowed_roles = (
        Rol.Tipo.ADMINISTRADOR,
        Rol.Tipo.SUPERVISOR,
        Rol.Tipo.BODEGUERO,
    )
    read_roles = (Rol.Tipo.OPERARIO,)


class AdministradorPermission(BasePermission):
    """Solo administrador de aplicacion (o superusuario Django)."""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_superuser", False):
            return True
        role_name = getattr(getattr(user, "rol", None), "nombre", None)
        return role_name == Rol.Tipo.ADMINISTRADOR


class AlertsResolutionPermission(BasePermission):
    """
    Historial de resolución de alertas: lectura para los mismos roles que ven alertas;
    registro de atención solo administrador, supervisor y bodeguero.
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        role_name = getattr(getattr(user, "rol", None), "nombre", None)
        if role_name is None:
            return False

        can_read = role_name in (
            Rol.Tipo.ADMINISTRADOR,
            Rol.Tipo.SUPERVISOR,
            Rol.Tipo.BODEGUERO,
            Rol.Tipo.OPERARIO,
        )
        can_write = role_name in (
            Rol.Tipo.ADMINISTRADOR,
            Rol.Tipo.SUPERVISOR,
            Rol.Tipo.BODEGUERO,
        )
        if request.method in SAFE_METHODS:
            return can_read
        return can_write
