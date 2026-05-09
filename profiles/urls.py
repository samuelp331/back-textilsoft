from django.urls import path

from .views import PerfilMeAPIView

urlpatterns = [
    path("me", PerfilMeAPIView.as_view(), name="profile-me"),
]
