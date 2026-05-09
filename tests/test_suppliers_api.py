import pytest
from rest_framework import status

from suppliers.models import CalificacionProveedor, Proveedor


@pytest.mark.django_db
def test_proveedor_busqueda_q(supervisor_api):
    Proveedor.objects.create(nombre="Alpha SA", email="a@a.com")
    Proveedor.objects.create(nombre="Beta", nombre_contacto="Gamma")
    r = supervisor_api.get("/api/suppliers/proveedores/", {"q": "gamma"})
    assert r.status_code == status.HTTP_200_OK
    assert len(r.data) == 1
    assert r.data[0]["nombre"] == "Beta"


@pytest.mark.django_db
def test_bodeguero_no_puede_crear_proveedor(bodeguero_api):
    r = bodeguero_api.post(
        "/api/suppliers/proveedores/",
        {"nombre": "Nuevo"},
        format="json",
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_bodeguero_puede_listar_proveedores(bodeguero_api, supervisor_api):
    supervisor_api.post(
        "/api/suppliers/proveedores/",
        {"nombre": "SoloLectura"},
        format="json",
    )
    r = bodeguero_api.get("/api/suppliers/proveedores/")
    assert r.status_code == status.HTTP_200_OK
    assert any(p["nombre"] == "SoloLectura" for p in r.data)


@pytest.mark.django_db
def test_calificacion_promedio_en_serializador(supervisor_api):
    p_resp = supervisor_api.post(
        "/api/suppliers/proveedores/",
        {"nombre": "ProvCal"},
        format="json",
    )
    pid = p_resp.data["id"]
    supervisor_api.post(
        "/api/suppliers/calificaciones/",
        {
            "proveedor": pid,
            "calidad_suministro": CalificacionProveedor.Calificacion.BUENO,
            "cumplimiento_tiempos": CalificacionProveedor.Calificacion.BUENO,
            "precio_calidad": CalificacionProveedor.Calificacion.EXCELENTE,
        },
        format="json",
    )
    r = supervisor_api.get("/api/suppliers/proveedores/")
    item = next(x for x in r.data if x["id"] == pid)
    assert item["calificacion_promedio"] is not None
    assert item["calificacion_promedio"] > 4.0


@pytest.mark.django_db
def test_calificacion_model_promedio():
    prov = Proveedor.objects.create(nombre="P")
    c = CalificacionProveedor.objects.create(
        proveedor=prov,
        calidad_suministro=3,
        cumplimiento_tiempos=3,
        precio_calidad=3,
    )
    assert c.promedio == 3.0
