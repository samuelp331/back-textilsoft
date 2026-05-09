from django.conf import settings
from django.db import models
from django.utils import timezone


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    identificacion = models.CharField(max_length=40, blank=True)
    celular = models.CharField(max_length=30, blank=True)
    cargo = models.CharField(max_length=120, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_contratacion = models.DateField(default=timezone.localdate)
    foto_base64 = models.TextField(blank=True)

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"Perfil: {self.usuario.email}"

# Create your models here.
