from django.contrib import admin

# Register your models here.

from .models import Rol, Usuario, UsuarioGestionAuditoria

admin.site.register(Rol)
admin.site.register(Usuario)


@admin.register(UsuarioGestionAuditoria)
class UsuarioGestionAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("creado_en", "accion", "usuario_afectado", "ejecutado_por")
    list_filter = ("accion",)
    search_fields = ("usuario_afectado__email", "ejecutado_por__email", "detalle")
    readonly_fields = ("creado_en",)
