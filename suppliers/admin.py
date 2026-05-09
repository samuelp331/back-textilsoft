from django.contrib import admin

from .models import Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nombre_contacto", "email", "telefono")
    search_fields = ("nombre", "nombre_contacto", "email")

# Register your models here.
