import pytest
from rest_framework.test import APIClient

from accounts.models import Rol, Usuario


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def rol_admin(db):
    r, _ = Rol.objects.get_or_create(nombre=Rol.Tipo.ADMINISTRADOR)
    return r


@pytest.fixture
def rol_supervisor(db):
    r, _ = Rol.objects.get_or_create(nombre=Rol.Tipo.SUPERVISOR)
    return r


@pytest.fixture
def rol_bodeguero(db):
    r, _ = Rol.objects.get_or_create(nombre=Rol.Tipo.BODEGUERO)
    return r


@pytest.fixture
def rol_operario(db):
    r, _ = Rol.objects.get_or_create(nombre=Rol.Tipo.OPERARIO)
    return r


@pytest.fixture
def user_factory(db):
    def _make(*, email, password, nombre, rol: Rol):
        return Usuario.objects.create_user(
            email=email,
            password=password,
            nombre=nombre,
            rol=rol,
        )

    return _make


@pytest.fixture
def admin_user(user_factory, rol_admin):
    return user_factory(
        email="admin@test.com",
        password="testpass123",
        nombre="Admin Test",
        rol=rol_admin,
    )


@pytest.fixture
def supervisor_user(user_factory, rol_supervisor):
    return user_factory(
        email="supervisor@test.com",
        password="testpass123",
        nombre="Supervisor Test",
        rol=rol_supervisor,
    )


@pytest.fixture
def bodeguero_user(user_factory, rol_bodeguero):
    return user_factory(
        email="bodeguero@test.com",
        password="testpass123",
        nombre="Bodeguero Test",
        rol=rol_bodeguero,
    )


@pytest.fixture
def operario_user(user_factory, rol_operario):
    return user_factory(
        email="operario@test.com",
        password="testpass123",
        nombre="Operario Test",
        rol=rol_operario,
    )


@pytest.fixture
def admin_api(admin_user):
    c = APIClient()
    c.force_authenticate(user=admin_user)
    return c


@pytest.fixture
def supervisor_api(supervisor_user):
    c = APIClient()
    c.force_authenticate(user=supervisor_user)
    return c


@pytest.fixture
def bodeguero_api(bodeguero_user):
    c = APIClient()
    c.force_authenticate(user=bodeguero_user)
    return c


@pytest.fixture
def operario_api(operario_user):
    c = APIClient()
    c.force_authenticate(user=operario_user)
    return c
