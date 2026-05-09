from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hash seguro
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("estado", Usuario.Estado.ACTIVO)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        rol = extra_fields.get("rol")
        if rol is None:
            rol, _ = Rol.objects.get_or_create(nombre=Rol.Tipo.ADMINISTRADOR)
            extra_fields["rol"] = rol

        return self.create_user(email, password, **extra_fields)


class Rol(models.Model):
    class Tipo(models.TextChoices):
        ADMINISTRADOR = "administrador", "Administrador"
        SUPERVISOR = "supervisor", "Supervisor"
        BODEGUERO = "bodeguero", "Bodeguero"
        OPERARIO = "operario", "Operario"

    nombre = models.CharField(max_length=20, choices=Tipo.choices, unique=True)

    def __str__(self):
        return self.get_nombre_display()


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"

    nombre = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name="usuarios")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre"]

    @property
    def is_active(self):
        return self.estado == self.Estado.ACTIVO

    def __str__(self):
        return f"{self.nombre} ({self.email})"


class UsuarioGestionAuditoria(models.Model):
    """
    Registro de acciones de administración sobre cuentas (crear, editar, desactivar).
    El usuario afectado permanece en base de datos si solo se desactiva (baja lógica).
    """

    class Accion(models.TextChoices):
        CREAR = "crear", "Crear"
        ACTUALIZAR = "actualizar", "Actualizar"
        DESACTIVAR = "desactivar", "Desactivar"

    usuario_afectado = models.ForeignKey(
        "Usuario",
        on_delete=models.CASCADE,
        related_name="gestiones_auditadas",
    )
    ejecutado_por = models.ForeignKey(
        "Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gestiones_realizadas",
    )
    accion = models.CharField(max_length=20, choices=Accion.choices)
    detalle = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "Auditoría de gestión de usuario"
        verbose_name_plural = "Auditorías de gestión de usuarios"

    def __str__(self):
        return f"{self.accion} → {self.usuario_afectado_id} @ {self.creado_en}"
