import pytest
from django.test import override_settings

from accounts.models import Rol
from accounts.serializers import PasswordResetConfirmSerializer, RegisterSerializer


@pytest.mark.django_db
def test_register_serializer_password_confirm_password_reset_confirm():
    ser = PasswordResetConfirmSerializer(
        data={
            "uid": "x",
            "token": "y",
            "password": "aaa",
            "password_confirm": "bbb",
        }
    )
    assert ser.is_valid() is False


@pytest.mark.django_db
def test_register_serializer_valida_rol_permitido(rol_operario):
    with override_settings(REGISTRATION_ASSIGNABLE_ROLES=("operario",)):
        ser = RegisterSerializer(
            data={
                "nombre": "A",
                "email": "serial@test.com",
                "password": "secret12",
                "rol": Rol.Tipo.OPERARIO,
            }
        )
        assert ser.is_valid(), ser.errors


@pytest.mark.django_db
def test_register_serializer_rechaza_email_duplicado(operario_user):
    ser = RegisterSerializer(
        data={
            "nombre": "A",
            "email": operario_user.email.upper(),
            "password": "secret12",
            "rol": Rol.Tipo.OPERARIO,
        }
    )
    assert ser.is_valid() is False
