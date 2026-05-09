import pytest
from datetime import date, timedelta

from unittest.mock import patch
from rest_framework import status

from inventory.models import Producto, Ubicacion


@pytest.mark.django_db
@patch("alerts.views.timezone.localdate", return_value=date(2026, 6, 15))
def test_alertas_stock_bajo_y_vencimiento(_mock_localdate, bodeguero_api):
    u = Ubicacion.objects.create(pasillo="1", estante="1", seccion="1")
    Producto.objects.create(
        codigo="LOW",
        nombre="Bajo",
        categoria="C",
        ubicacion=u,
        cantidad=2,
        cantidad_minima=5,
    )
    Producto.objects.create(
        codigo="EXP",
        nombre="PorVencer",
        categoria="C",
        cantidad=10,
        cantidad_minima=0,
        fecha_vencimiento=date(2026, 6, 20),
        dias_preaviso_vencimiento=10,
    )
    Producto.objects.create(
        codigo="BAD",
        nombre="Vencido",
        categoria="C",
        cantidad=1,
        cantidad_minima=0,
        fecha_vencimiento=date(2026, 6, 1),
        dias_preaviso_vencimiento=30,
    )
    r = bodeguero_api.get("/api/alerts/")
    assert r.status_code == status.HTTP_200_OK
    types = {a["type"] for a in r.data}
    assert "low-stock" in types
    assert "expiration" in types
    assert "expired" in types


@pytest.mark.django_db
def test_alertas_operario_lectura_ok(operario_api):
    r = operario_api.get("/api/alerts/")
    assert r.status_code == status.HTTP_200_OK
    assert isinstance(r.data, list)
