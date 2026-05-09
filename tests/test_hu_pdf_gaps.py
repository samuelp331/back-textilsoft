import pytest
from datetime import date

from rest_framework import status

from inventory.models import Producto, RegistroEliminacionProducto
from alerts.models import ResolucionAlerta
from inventory.models import MovimientoInventario


@pytest.mark.django_db
def test_eliminar_producto_deja_registro_auditoria(admin_api, bodeguero_api):
    p = Producto.objects.create(codigo="DEL1", nombre="X", categoria="C", cantidad=3)
    rid = p.id
    r = admin_api.delete(f"/api/inventory/productos/{rid}/")
    assert r.status_code == status.HTTP_204_NO_CONTENT
    assert not Producto.objects.filter(pk=rid).exists()
    reg = RegistroEliminacionProducto.objects.get(producto_id_original=rid)
    assert reg.codigo == "DEL1"
    assert reg.cantidad_al_eliminar == 3

    lista = bodeguero_api.get("/api/inventory/eliminaciones-productos/")
    assert lista.status_code == status.HTTP_200_OK
    assert any(x["producto_id_original"] == rid for x in lista.data)


@pytest.mark.django_db
def test_eliminaciones_operario_prohibido(operario_api):
    r = operario_api.get("/api/inventory/eliminaciones-productos/")
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_resolucion_alerta_crear_y_listar(bodeguero_api):
    p = Producto.objects.create(codigo="A1", nombre="Prod", categoria="C")
    r = bodeguero_api.post(
        "/api/alerts/resoluciones/",
        {
            "producto": p.id,
            "tipo_alerta": ResolucionAlerta.TipoAlerta.LOW_STOCK,
            "accion": ResolucionAlerta.Accion.MANUAL,
            "notas": "Revisado en bodega",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    assert r.data["producto_nombre"] == "Prod"

    lst = bodeguero_api.get("/api/alerts/resoluciones/")
    assert lst.status_code == status.HTTP_200_OK
    assert len(lst.data) >= 1


@pytest.mark.django_db
def test_resolucion_alerta_operario_no_puede_crear(operario_api):
    p = Producto.objects.create(codigo="A2", nombre="P", categoria="C")
    r = operario_api.post(
        "/api/alerts/resoluciones/",
        {
            "producto": p.id,
            "tipo_alerta": "low-stock",
            "accion": "manual",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_reporte_consumo_serie(supervisor_api):
    p = Producto.objects.create(codigo="S1", nombre="Serie", categoria="T")
    MovimientoInventario.objects.create(
        producto=p,
        fecha=date(2026, 1, 15),
        tipo=MovimientoInventario.Tipo.SALIDA,
        cantidad=4,
        motivo="c1",
    )
    MovimientoInventario.objects.create(
        producto=p,
        fecha=date(2026, 2, 10),
        tipo=MovimientoInventario.Tipo.SALIDA,
        cantidad=6,
        motivo="c2",
    )
    r = supervisor_api.get(
        "/api/reports/consumo-serie",
        {"producto_id": p.id, "agrupar": "mes"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.data["producto_nombre"] == "Serie"
    assert len(r.data["serie"]) == 2
    assert r.data["total_salidas_periodo"] == 10


@pytest.mark.django_db
def test_proveedor_productos_suministrados_y_calif_filtro(supervisor_api):
    from suppliers.models import CalificacionProveedor, Proveedor

    pr = Proveedor.objects.create(nombre="Prov", productos_suministrados="Hilo, Tela")
    CalificacionProveedor.objects.create(
        proveedor=pr,
        calidad_suministro=4,
        cumplimiento_tiempos=4,
        precio_calidad=5,
    )
    r = supervisor_api.get(f"/api/suppliers/proveedores/{pr.id}/")
    assert r.status_code == status.HTTP_200_OK
    assert "Hilo" in r.data["productos_suministrados"]

    r2 = supervisor_api.get("/api/suppliers/calificaciones/", {"proveedor": pr.id})
    assert r2.status_code == status.HTTP_200_OK
    assert len(r2.data) == 1
