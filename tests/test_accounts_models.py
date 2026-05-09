import pytest

from accounts.models import Rol, Usuario, UsuarioManager


@pytest.mark.django_db
def test_create_user_sin_email_lanza_error():
    manager = UsuarioManager()
    manager.model = Usuario
    with pytest.raises(ValueError, match="email"):
        manager.create_user(email="", password="x")


@pytest.mark.django_db
def test_usuario_is_active_según_estado(rol_operario):
    u = Usuario.objects.create_user(
        email="a@test.com",
        password="x",
        nombre="A",
        rol=rol_operario,
        estado=Usuario.Estado.ACTIVO,
    )
    assert u.is_active is True
    u.estado = Usuario.Estado.INACTIVO
    u.save()
    assert u.is_active is False


@pytest.mark.django_db
def test_create_superuser_asigna_rol_admin_si_falta(db):
    user = Usuario.objects.create_superuser(
        email="su@test.com",
        password="pw",
        nombre="Super",
    )
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.rol.nombre == Rol.Tipo.ADMINISTRADOR
