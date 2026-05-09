from django.conf import settings
from django.db import models
from django.utils import timezone


class RegistroEliminacionProducto(models.Model):
    """Auditoría de productos eliminados del catálogo (HU: log al borrar)."""

    producto_id_original = models.PositiveIntegerField()
    codigo = models.CharField(max_length=40)
    nombre = models.CharField(max_length=160)
    categoria = models.CharField(max_length=120)
    cantidad_al_eliminar = models.IntegerField()
    eliminado_en = models.DateTimeField(auto_now_add=True)
    eliminado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos_eliminaciones_registradas",
    )

    class Meta:
        ordering = ("-eliminado_en",)

    def __str__(self):
        return f"Eliminado {self.codigo} ({self.nombre})"


class Ubicacion(models.Model):
    pasillo = models.CharField(max_length=20)
    estante = models.CharField(max_length=20)
    seccion = models.CharField(max_length=20)

    class Meta:
        ordering = ("pasillo", "estante", "seccion")
        unique_together = ("pasillo", "estante", "seccion")

    def __str__(self):
        return f"Pasillo {self.pasillo} - Estante {self.estante} - Sección {self.seccion}"


class Producto(models.Model):
    class Unidad(models.TextChoices):
        UNIDAD = "unidad", "Unidad"
        METRO = "metro", "Metro"
        ROLLO = "rollo", "Rollo"

    codigo = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=160)
    categoria = models.CharField(max_length=120)
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
    )
    descripcion = models.TextField(blank=True)
    cantidad = models.IntegerField(default=0)
    cantidad_minima = models.PositiveIntegerField(default=0)
    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unidad = models.CharField(max_length=20, choices=Unidad.choices, default=Unidad.UNIDAD)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    dias_preaviso_vencimiento = models.PositiveIntegerField(default=30)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class MovimientoInventario(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SALIDA = "salida", "Salida"
        AJUSTE = "ajuste", "Ajuste"

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="movimientos",
    )
    fecha = models.DateField(default=timezone.localdate)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    cantidad = models.IntegerField()
    motivo = models.TextField()
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_inventario",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-fecha", "-id")

    def __str__(self):
        return f"{self.producto.nombre} - {self.tipo} ({self.cantidad})"
