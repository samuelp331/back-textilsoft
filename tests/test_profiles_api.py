import pytest
from rest_framework import status

from profiles.models import PerfilUsuario


@pytest.mark.django_db
def test_perfil_me_get_crea_perfil(admin_api, admin_user):
    assert PerfilUsuario.objects.filter(usuario=admin_user).count() in (0, 1)
    resp = admin_api.get("/api/profile/me")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["email"] == admin_user.email
    assert PerfilUsuario.objects.filter(usuario=admin_user).exists()


@pytest.mark.django_db
def test_perfil_me_patch_actualiza(admin_api, admin_user):
    admin_api.get("/api/profile/me")
    resp = admin_api.patch(
        "/api/profile/me",
        {"celular": "3001234567", "cargo": "Jefe"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["celular"] == "3001234567"
    p = PerfilUsuario.objects.get(usuario=admin_user)
    assert p.cargo == "Jefe"


@pytest.mark.django_db
def test_perfil_me_requiere_autenticacion(api_client):
    r = api_client.get("/api/profile/me")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
