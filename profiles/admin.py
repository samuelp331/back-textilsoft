from django.contrib import admin

from .models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "identificacion", "celular", "cargo")
    search_fields = ("usuario__email", "usuario__nombre", "identificacion")

# Register your models here.
