import pytest
from django.core import mail
from django.test import override_settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.authtoken.models import Token

from accounts.models import Rol, Usuario
from inventory.models import MovimientoInventario, Producto
from profiles.models import PerfilUsuario
from suppliers.models import Proveedor


@pytest.mark.django_db
def test_login_exito(api_client, operario_user):
    resp = api_client.post(
        "/api/login",
        {"email": operario_user.email, "password": "testpass123"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "token" in resp.data
    assert resp.data["usuario"]["email"] == operario_user.email


@pytest.mark.django_db
def test_login_credenciales_invalidas(api_client, operario_user):
    resp = api_client.post(
        "/api/login",
        {"email": operario_user.email, "password": "mal"},
        format="json",
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_registro_publico_deshabilitado(api_client, db):
    payload = {
        "nombre": "Nuevo",
        "email": "nuevo@test.com",
        "password": "secret12",
        "rol": Rol.Tipo.OPERARIO,
    }
    resp = api_client.post("/api/register", payload, format="json")
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert not Usuario.objects.filter(email="nuevo@test.com").exists()


@pytest.mark.django_db
def test_registro_publico_rechaza_aunque_email_duplicado(api_client, operario_user):
    resp = api_client.post(
        "/api/register",
        {
            "nombre": "Otro",
            "email": operario_user.email,
            "password": "secret12",
            "rol": Rol.Tipo.OPERARIO,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@override_settings(REGISTRATION_ASSIGNABLE_ROLES=("operario",))
def test_registro_publico_rechaza_cualquier_rol(api_client):
    resp = api_client.post(
        "/api/register",
        {
            "nombre": "X",
            "email": "x@test.com",
            "password": "secret12",
            "rol": Rol.Tipo.ADMINISTRADOR,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert not Usuario.objects.filter(email="x@test.com").exists()


@pytest.mark.django_db
def test_recover_account_envia_correo_si_existe(api_client, operario_user):
    mail.outbox.clear()
    resp = api_client.post(
        "/api/recover-account",
        {"email": operario_user.email},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1
    assert operario_user.email in mail.outbox[0].to


@pytest.mark.django_db
def test_recover_account_sin_filtrar_existencia(api_client):
    mail.outbox.clear()
    resp = api_client.post(
        "/api/recover-account",
        {"email": "noexiste@test.com"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_confirm_exito(api_client, operario_user):
    uid = urlsafe_base64_encode(force_bytes(operario_user.pk))
    tok = default_token_generator.make_token(operario_user)
    resp = api_client.post(
        "/api/password-reset-confirm",
        {
            "uid": uid,
            "token": tok,
            "password": "nueva123",
            "password_confirm": "nueva123",
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    operario_user.refresh_from_db()
    assert operario_user.check_password("nueva123")
    assert not Token.objects.filter(user=operario_user).exists()


@pytest.mark.django_db
def test_password_reset_confirm_token_invalido(api_client, operario_user):
    uid = urlsafe_base64_encode(force_bytes(operario_user.pk))
    resp = api_client.post(
        "/api/password-reset-confirm",
        {
            "uid": uid,
            "token": "invalido",
            "password": "nueva123",
            "password_confirm": "nueva123",
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_admin_resumen_solo_administrador(admin_api, supervisor_api, operario_api):
    Producto.objects.create(
        codigo="P1",
        nombre="Prod",
        categoria="Cat",
        cantidad=5,
        cantidad_minima=1,
    )
    Proveedor.objects.create(nombre="Prov")
    MovimientoInventario.objects.create(
        producto=Producto.objects.get(codigo="P1"),
        tipo=MovimientoInventario.Tipo.ENTRADA,
        cantidad=1,
        motivo="init",
    )

    ok = admin_api.get("/api/admin/resumen/")
    assert ok.status_code == status.HTTP_200_OK
    assert ok.data["productos"] == 1
    assert ok.data["proveedores"] == 1

    denied_sup = supervisor_api.get("/api/admin/resumen/")
    assert denied_sup.status_code == status.HTTP_403_FORBIDDEN

    denied_op = operario_api.get("/api/admin/resumen/")
    assert denied_op.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_usuarios_list_create_patch_delete(admin_api, admin_user, supervisor_api, rol_operario, rol_supervisor):
    r_list = admin_api.get("/api/admin/usuarios/")
    assert r_list.status_code == status.HTTP_200_OK
    assert isinstance(r_list.data, list)

    denied = supervisor_api.get("/api/admin/usuarios/")
    assert denied.status_code == status.HTTP_403_FORBIDDEN

    r_create = admin_api.post(
        "/api/admin/usuarios/",
        {
            "nombre": "Usuario Gestion",
            "email": "gestion@test.com",
            "password": "secret12",
            "rol": Rol.Tipo.OPERARIO,
            "identificacion": "CC-100",
            "celular": "3001234567",
            "direccion": "Calle Empresa 1",
        },
        format="json",
    )
    assert r_create.status_code == status.HTTP_201_CREATED
    u = Usuario.objects.get(email="gestion@test.com")
    assert u.rol.nombre == Rol.Tipo.OPERARIO
    perfil = PerfilUsuario.objects.get(usuario=u)
    assert perfil.identificacion == "CC-100"
    assert perfil.celular == "3001234567"
    assert perfil.direccion == "Calle Empresa 1"

    r_dup = admin_api.post(
        "/api/admin/usuarios/",
        {
            "nombre": "Otro",
            "email": "gestion@test.com",
            "password": "secret12",
            "rol": Rol.Tipo.OPERARIO,
        },
        format="json",
    )
    assert r_dup.status_code == status.HTTP_400_BAD_REQUEST

    tok_before = Token.objects.create(user=u)
    r_patch = admin_api.patch(
        f"/api/admin/usuarios/{u.pk}/",
        {"rol": Rol.Tipo.SUPERVISOR},
        format="json",
    )
    assert r_patch.status_code == status.HTTP_200_OK
    u.refresh_from_db()
    assert u.rol.nombre == Rol.Tipo.SUPERVISOR
    assert not Token.objects.filter(key=tok_before.key).exists()

    r_self = admin_api.patch(
        f"/api/admin/usuarios/{admin_user.pk}/",
        {"estado": Usuario.Estado.INACTIVO},
        format="json",
    )
    assert r_self.status_code == status.HTTP_400_BAD_REQUEST

    r_del = admin_api.delete(f"/api/admin/usuarios/{u.pk}/")
    assert r_del.status_code == status.HTTP_204_NO_CONTENT
    u.refresh_from_db()
    assert u.estado == Usuario.Estado.INACTIVO
    assert not Token.objects.filter(user=u).exists()
