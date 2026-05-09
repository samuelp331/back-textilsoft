import pytest

from profiles.models import PerfilUsuario


@pytest.mark.django_db
def test_signal_crea_perfil_al_crear_usuario(user_factory, rol_operario):
    u = user_factory(
        email="signal@test.com",
        password="x",
        nombre="Sig",
        rol=rol_operario,
    )
    assert PerfilUsuario.objects.filter(usuario=u).exists()
