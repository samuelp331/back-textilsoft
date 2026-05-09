from django.conf import settings
from django.db import models


class ResolucionAlerta(models.Model):
    """Registro de atención a una alerta de inventario (historial HU)."""

    class TipoAlerta(models.TextChoices):
        LOW_STOCK = "low-stock", "Stock bajo"
        EXPIRATION = "expiration", "Proximo a vencer"
        EXPIRED = "expired", "Vencido"

    class Accion(models.TextChoices):
        REABASTECER = "reabastecer", "Reabastecer"
        EXTENDER = "extender", "Extender vigencia"
        DESCARTAR = "descartar", "Descartar"
        MANUAL = "manual", "Marcada como atendida"

    producto = models.ForeignKey(
        "inventory.Producto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resoluciones_alerta",
    )
    producto_nombre = models.CharField(max_length=160)
    tipo_alerta = models.CharField(max_length=20, choices=TipoAlerta.choices)
    accion = models.CharField(max_length=20, choices=Accion.choices)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alertas_resueltas",
    )
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-creado_en",)

    def __str__(self):
        return f"{self.producto_nombre} ({self.tipo_alerta})"
