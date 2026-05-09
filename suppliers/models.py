from django.db import models


class Proveedor(models.Model):
    nombre = models.CharField(max_length=160)
    nombre_contacto = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=40, blank=True)
    direccion = models.TextField(blank=True)
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    productos_suministrados = models.TextField(
        blank=True,
        help_text="Descripción de materias primas o productos que suministra (una por línea o separados por coma).",
    )

    class Meta:
        ordering = ("nombre",)

    def __str__(self):
        return self.nombre


class CalificacionProveedor(models.Model):
    class Calificacion(models.IntegerChoices):
        MUY_BAJO = 1, "Muy Bajo"
        BAJO = 2, "Bajo"
        REGULAR = 3, "Regular"
        BUENO = 4, "Bueno"
        EXCELENTE = 5, "Excelente"

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name="calificaciones",
    )
    calidad_suministro = models.IntegerField(choices=Calificacion.choices)
    cumplimiento_tiempos = models.IntegerField(choices=Calificacion.choices)
    precio_calidad = models.IntegerField(choices=Calificacion.choices)
    comentario = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-creado_en",)

    @property
    def promedio(self):
        return (self.calidad_suministro + self.cumplimiento_tiempos + self.precio_calidad) / 3

    def __str__(self):
        return f"{self.proveedor.nombre} - Calificacion {self.promedio:.1f}"
