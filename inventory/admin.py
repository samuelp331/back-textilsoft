from django.contrib import admin

from .models import MovimientoInventario, Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "categoria", "cantidad", "cantidad_minima", "unidad")
    search_fields = ("codigo", "nombre", "categoria")
    list_filter = ("categoria", "unidad")


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("producto", "fecha", "tipo", "cantidad", "registrado_por")
    list_filter = ("tipo", "fecha")
    search_fields = ("producto__nombre", "motivo")

# Register your models here.
