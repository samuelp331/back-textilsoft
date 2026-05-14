import pytest
from datetime import date, timedelta

from rest_framework import status

from inventory.models import MovimientoInventario, Producto, Ubicacion


@pytest.fixture
def ubicacion(admin_api):
    r = admin_api.post(
        "/api/inventory/ubicaciones/",
        {"pasillo": "A", "estante": "1", "seccion": "X"},
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    return r.data["id"]


@pytest.fixture
def producto(admin_api, ubicacion):
    r = admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "SKU-1",
            "nombre": "Tela",
            "categoria": "Telas",
            "ubicacion_id": ubicacion,
            "cantidad": 100,
            "cantidad_minima": 10,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    return r.data["id"]


@pytest.mark.django_db
def test_producto_filtros_categoria(admin_api, ubicacion):
    # crear dos productos con distinta categoría
    admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "A1",
            "nombre": "P1",
            "categoria": "Hilos",
            "ubicacion_id": ubicacion,
        },
        format="json",
    )
    admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "A2",
            "nombre": "P2",
            "categoria": "Telas",
            "ubicacion_id": ubicacion,
        },
        format="json",
    )
    r = admin_api.get("/api/inventory/productos/", {"categoria": "Telas"})
    assert r.status_code == status.HTTP_200_OK
    nombres = {item["nombre"] for item in r.data}
    assert nombres == {"P2"}


@pytest.mark.django_db
def test_alta_producto_con_stock_crea_movimiento_inicial(admin_api, ubicacion):
    """El stock al dar de alta un producto debe quedar reflejado en movimientos (reportes/kardex)."""
    r = admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "INI-1",
            "nombre": "Prod inicial",
            "categoria": "Telas",
            "ubicacion_id": ubicacion,
            "cantidad": 42,
            "cantidad_minima": 5,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED, r.data
    pid = r.data["id"]
    assert Producto.objects.get(pk=pid).cantidad == 42

    movs = MovimientoInventario.objects.filter(producto_id=pid)
    assert movs.count() == 1
    m = movs.get()
    assert m.tipo == MovimientoInventario.Tipo.ENTRADA
    assert m.cantidad == 42
    assert m.motivo == "Registro inicial de producto"

    rep = admin_api.get("/api/reports/movimientos", {"producto_id": pid})
    assert rep.status_code == status.HTTP_200_OK
    assert len(rep.data) >= 1
    assert any(row["cantidad"] == 42 and row["tipo"] == "entrada" for row in rep.data)


@pytest.mark.django_db
def test_alta_producto_sin_stock_no_crea_movimiento(admin_api, ubicacion):
    r = admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "INI-0",
            "nombre": "Sin stock",
            "categoria": "Telas",
            "ubicacion_id": ubicacion,
            "cantidad": 0,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED, r.data
    pid = r.data["id"]
    assert MovimientoInventario.objects.filter(producto_id=pid).count() == 0


@pytest.mark.django_db
def test_producto_categorias_endpoint(admin_api, ubicacion):
    admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "C1",
            "nombre": "X",
            "categoria": "Telas",
            "ubicacion_id": ubicacion,
        },
        format="json",
    )
    r = admin_api.get("/api/inventory/productos/categorias/")
    assert r.status_code == status.HTTP_200_OK
    assert "Telas" in r.data


@pytest.mark.django_db
def test_categoria_reutiliza_grafia_existente(admin_api, ubicacion):
    """Misma categoría con distinto espaciado o mayúsculas no crea otra entrada lógica."""
    admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "K1",
            "nombre": "P1",
            "categoria": "Telas",
            "ubicacion_id": ubicacion,
        },
        format="json",
    )
    r2 = admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "K2",
            "nombre": "P2",
            "categoria": "  telas  ",
            "ubicacion_id": ubicacion,
        },
        format="json",
    )
    assert r2.status_code == status.HTTP_201_CREATED
    assert r2.data["categoria"] == "Telas"

    r_cat = admin_api.get("/api/inventory/productos/categorias/")
    assert r_cat.status_code == status.HTTP_200_OK
    assert list(r_cat.data).count("Telas") == 1


@pytest.mark.django_db
def test_operario_no_puede_crear_producto(operario_api, ubicacion):
    r = operario_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "OP",
            "nombre": "Nope",
            "categoria": "Cat",
            "ubicacion_id": ubicacion,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_operario_no_puede_actualizar_producto(operario_api, admin_api, ubicacion):
    r = admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "OPU",
            "nombre": "Prod",
            "categoria": "Cat",
            "ubicacion_id": ubicacion,
            "cantidad": 10,
        },
        format="json",
    )
    assert r.status_code == status.HTTP_201_CREATED
    pid = r.data["id"]
    denied = operario_api.put(
        f"/api/inventory/productos/{pid}/",
        {
            "codigo": "OPU",
            "nombre": "Prod",
            "categoria": "Cat",
            "cantidad": 5,
        },
        format="json",
    )
    assert denied.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_operario_puede_listar_productos(operario_api, admin_api, ubicacion):
    admin_api.post(
        "/api/inventory/productos/",
        {
            "codigo": "R1",
            "nombre": "Visible",
            "categoria": "Cat",
            "ubicacion_id": ubicacion,
        },
        format="json",
    )
    r = operario_api.get("/api/inventory/productos/")
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) >= 1


@pytest.mark.django_db
def test_movimiento_operario_solo_salida(operario_api, producto):
    deny = operario_api.post(
        "/api/inventory/movimientos/",
        {
            "producto": producto,
            "fecha": str(date.today()),
            "tipo": MovimientoInventario.Tipo.ENTRADA,
            "cantidad": 1,
            "motivo": "test",
        },
        format="json",
    )
    assert deny.status_code == status.HTTP_403_FORBIDDEN

    assert Producto.objects.get(pk=producto).cantidad == 100

    ok = operario_api.post(
        "/api/inventory/movimientos/",
        {
            "producto": producto,
            "fecha": str(date.today()),
            "tipo": MovimientoInventario.Tipo.SALIDA,
            "cantidad": 1,
            "motivo": "consumo",
        },
        format="json",
    )
    assert ok.status_code == status.HTTP_201_CREATED
    assert Producto.objects.get(pk=producto).cantidad == 99
    assert ok.data.get("registrado_por") is not None


@pytest.mark.django_db
def test_movimientos_filtras_por_fecha(admin_api, producto):
    d0 = date.today() - timedelta(days=2)
    assert Producto.objects.get(pk=producto).cantidad == 100
    admin_api.post(
        "/api/inventory/movimientos/",
        {
            "producto": producto,
            "fecha": str(d0),
            "tipo": MovimientoInventario.Tipo.ENTRADA,
            "cantidad": 5,
            "motivo": "ingreso",
        },
        format="json",
    )
    assert Producto.objects.get(pk=producto).cantidad == 105
    r = admin_api.get(
        "/api/inventory/movimientos/",
        {"fecha_desde": str(d0), "fecha_hasta": str(date.today())},
    )
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) >= 1


@pytest.mark.django_db
def test_movimiento_salida_rechaza_sin_stock(admin_api, producto):
    Producto.objects.filter(pk=producto).update(cantidad=2)
    r = admin_api.post(
        "/api/inventory/movimientos/",
        {
            "producto": producto,
            "fecha": str(date.today()),
            "tipo": MovimientoInventario.Tipo.SALIDA,
            "cantidad": 10,
            "motivo": "x",
        },
        format="json",
    )
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert Producto.objects.get(pk=producto).cantidad == 2


@pytest.mark.django_db
def test_modelo_producto_str():
    p = Producto.objects.create(
        codigo="Z",
        nombre="Nombre",
        categoria="C",
    )
    assert "Z" in str(p)
    assert "Nombre" in str(p)


@pytest.mark.django_db
def test_ubicacion_unique_together():
    Ubicacion.objects.create(pasillo="P", estante="E", seccion="S")
    from django.db import IntegrityError

    with pytest.raises(IntegrityError):
        Ubicacion.objects.create(pasillo="P", estante="E", seccion="S")


@pytest.mark.django_db
def test_import_csv_payload_frontend_equivalente_persiste_campos(admin_api):
    """
    La importación CSV en el frontend arma objetos y usa inventoryData.mapProductToApi
    (POST /api/inventory/productos/). Este test reproduce ese payload para validar que los
    datos quedan bien guardados y son coherentes al listar.
    """
    payloads = [
        {
            "codigo": "IMP-CSV-001",
            "nombre": "Hilo polyester 40/2",
            "categoria": "Hilos",
            "ubicacion": None,
            "descripcion": "Hilo para costura industrial",
            "cantidad": 150,
            "cantidad_minima": 0,
            "precio": 12.5,
            "unidad": "metro",
            "fecha_vencimiento": None,
            "dias_preaviso_vencimiento": 30,
        },
        {
            "codigo": "IMP-CSV-002",
            "nombre": "Tela drill algodón",
            "categoria": "Telas",
            "ubicacion": None,
            "descripcion": "Rollo estándar",
            "cantidad": 25,
            "cantidad_minima": 0,
            "precio": 89.99,
            "unidad": "rollo",
            "fecha_vencimiento": None,
            "dias_preaviso_vencimiento": 30,
        },
    ]
    for body in payloads:
        r = admin_api.post("/api/inventory/productos/", body, format="json")
        assert r.status_code == status.HTTP_201_CREATED, r.data

    r_list = admin_api.get("/api/inventory/productos/")
    assert r_list.status_code == status.HTTP_200_OK
    by_code = {item["codigo"]: item for item in r_list.data}

    assert by_code["IMP-CSV-001"]["nombre"] == "Hilo polyester 40/2"
    assert by_code["IMP-CSV-001"]["categoria"] == "Hilos"
    assert by_code["IMP-CSV-001"]["descripcion"] == "Hilo para costura industrial"
    assert by_code["IMP-CSV-001"]["cantidad"] == 150
    assert float(by_code["IMP-CSV-001"]["precio"]) == 12.5
    assert by_code["IMP-CSV-001"]["unidad"] == "metro"

    assert by_code["IMP-CSV-002"]["unidad"] == "rollo"
    assert by_code["IMP-CSV-002"]["cantidad"] == 25
