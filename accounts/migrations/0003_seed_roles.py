from django.db import migrations


def seed_roles(apps, schema_editor):
    Rol = apps.get_model("accounts", "Rol")
    for nombre in ("administrador", "supervisor", "bodeguero", "operario"):
        Rol.objects.get_or_create(nombre=nombre)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_usuario_gestion_auditoria"),
    ]

    operations = [
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]
