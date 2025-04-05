from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.contrib.auth.models import User

from .models import SSHCredential, WinRMCredential, Host
from .serializers import SSHCredentialSerializer, WinRMCredentialSerializer, HostSerializer, UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class SSHCredentialViewSet(viewsets.ModelViewSet):
    queryset = SSHCredential.objects.all()
    serializer_class = SSHCredentialSerializer


class WinRMCredentialViewSet(viewsets.ModelViewSet):
    queryset = WinRMCredential.objects.all()
    serializer_class = WinRMCredentialSerializer


class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.all()
    serializer_class = HostSerializer
