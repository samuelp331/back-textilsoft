from django.urls import path

from .views import (
    AdminResumenAPIView,
    AdminUsuarioDetailAPIView,
    AdminUsuarioListCreateAPIView,
    LoginAPIView,
    PasswordResetConfirmAPIView,
    RecoverAccountAPIView,
    RegisterAPIView,
)

urlpatterns = [
    path("login", LoginAPIView.as_view(), name="login"),
    path("register", RegisterAPIView.as_view(), name="register"),
    path("recover-account", RecoverAccountAPIView.as_view(), name="recover-account"),
    path("password-reset-confirm", PasswordResetConfirmAPIView.as_view(), name="password-reset-confirm"),
    path("admin/resumen/", AdminResumenAPIView.as_view(), name="admin-resumen"),
    path("admin/usuarios/", AdminUsuarioListCreateAPIView.as_view(), name="admin-usuarios"),
    path("admin/usuarios/<int:pk>/", AdminUsuarioDetailAPIView.as_view(), name="admin-usuario-detail"),
]
