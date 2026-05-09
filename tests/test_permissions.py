import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.permissions import (
    AdministradorPermission,
    AlertsPermission,
    InventoryMovementPermission,
    InventoryPermission,
    ReportsAnalyticsPermission,
    ReportsOperationalPermission,
    SupplierPermission,
)


@pytest.fixture
def rf():
    return APIRequestFactory()


def _wrap(rf, method, path="/x", user=None, **kwargs):
    if method == "get":
        django_req = rf.get(path)
    else:
        django_req = rf.post(path)
    if user is not None:
        force_authenticate(django_req, user=user)
    return Request(django_req)


@pytest.mark.django_db
def test_inventory_permission_operario_lectura_no_escritura(rf, operario_user, rol_operario):
    perm = InventoryPermission()
    get_req = _wrap(rf, "get", user=operario_user)
    post_req = _wrap(rf, "post", user=operario_user)
    assert perm.has_permission(get_req, None) is True
    assert perm.has_permission(post_req, None) is False


@pytest.mark.django_db
def test_supplier_permission_bodeguero_solo_get(rf, bodeguero_user):
    perm = SupplierPermission()
    get_req = _wrap(rf, "get", user=bodeguero_user)
    post_req = _wrap(rf, "post", user=bodeguero_user)
    assert perm.has_permission(get_req, None) is True
    assert perm.has_permission(post_req, None) is False


@pytest.mark.django_db
def test_inventory_movement_operario_post_permitido_en_permiso(rf, operario_user):
    perm = InventoryMovementPermission()
    post_req = _wrap(rf, "post", user=operario_user)
    assert perm.has_permission(post_req, None) is True


@pytest.mark.django_db
def test_administrador_permission_anonimo(rf):
    perm = AdministradorPermission()
    req = _wrap(rf, "get", user=AnonymousUser())
    assert perm.has_permission(req, None) is False


@pytest.mark.django_db
def test_reports_analytics_supervisor(rf, supervisor_user):
    perm = ReportsAnalyticsPermission()
    req = _wrap(rf, "get", user=supervisor_user)
    assert perm.has_permission(req, None) is True


@pytest.mark.django_db
def test_reports_operational_bodeguero(rf, bodeguero_user):
    perm = ReportsOperationalPermission()
    req = _wrap(rf, "get", user=bodeguero_user)
    assert perm.has_permission(req, None) is True


@pytest.mark.django_db
def test_alerts_operario_solo_lectura(rf, operario_user):
    perm = AlertsPermission()
    get_req = _wrap(rf, "get", user=operario_user)
    post_req = _wrap(rf, "post", user=operario_user)
    assert perm.has_permission(get_req, None) is True
    assert perm.has_permission(post_req, None) is False
