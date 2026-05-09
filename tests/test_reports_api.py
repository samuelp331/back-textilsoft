import pytest
from datetime import date, timedelta

from rest_framework import status

from inventory.models import MovimientoInventario, Producto


@pytest.mark.django_db
def test_reporte_movimientos_filtra(bodeguero_api):
    prod = Producto.objects.create(
        codigo="Rp1",
        nombre="Rep",
        categoria="C",
    )
    MovimientoInventario.objects.create(
        producto=prod,
        fecha=date.today() - timedelta(days=10),
        tipo=MovimientoInventario.Tipo.SALIDA,
        cantidad=2,
        motivo="x",
    )
    MovimientoInventario.objects.create(
        producto=prod,
        fecha=date.today(),
        tipo=MovimientoInventario.Tipo.ENTRADA,
        cantidad=5,
        motivo="y",
    )
    r = bodeguero_api.get("/api/reports/movimientos", {"tipo": "entrada"})
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) == 1
    assert r.data[0]["tipo"] == MovimientoInventario.Tipo.ENTRADA


@pytest.mark.django_db
def test_reporte_consumo_porcentajes(supervisor_api):
    p1 = Producto.objects.create(
        codigo="C1",
        nombre="P1",
        categoria="Hilo",
    )
    p2 = Producto.objects.create(
        codigo="C2",
        nombre="P2",
        categoria="Hilo",
    )
    MovimientoInventario.objects.create(
        producto=p1,
        fecha=date.today(),
        tipo=MovimientoInventario.Tipo.SALIDA,
        cantidad=10,
        motivo="a",
    )
    MovimientoInventario.objects.create(
        producto=p2,
        fecha=date.today(),
        tipo=MovimientoInventario.Tipo.SALIDA,
        cantidad=30,
        motivo="b",
    )
    r = supervisor_api.get("/api/reports/consumo", {"categoria": "Hilo"})
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) == 2
    by_id = {item["producto_id"]: item for item in r.data}
    assert by_id[p2.id]["porcentaje"] == 75.0
    assert by_id[p1.id]["porcentaje"] == 25.0


@pytest.mark.django_db
def test_reporte_movimientos_operario_prohibido(operario_api):
    r = operario_api.get("/api/reports/movimientos")
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_reporte_consumo_bodeguero_prohibido(bodeguero_api):
    r = bodeguero_api.get("/api/reports/consumo")
    assert r.status_code == status.HTTP_403_FORBIDDEN
