from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PerfilUsuario
from .serializers import PerfilUsuarioSerializer


class PerfilMeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
        serializer = PerfilUsuarioSerializer(perfil)
        return Response(serializer.data)

    def put(self, request):
        return self._upsert(request)

    def patch(self, request):
        return self._upsert(request, partial=True)

    def _upsert(self, request, partial=False):
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
        serializer = PerfilUsuarioSerializer(
            perfil,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

# Create your views here.
