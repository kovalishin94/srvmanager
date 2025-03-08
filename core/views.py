from rest_framework import viewsets

from .models import SSHCredential, WinRMCredential, Host
from .serializers import SSHCredentialSerializer, WinRMCredentialSerializer, HostSerializer


class SSHCredentialViewSet(viewsets.ModelViewSet):
    queryset = SSHCredential.objects.all()
    serializer_class = SSHCredentialSerializer


class WinRMCredentialViewSet(viewsets.ModelViewSet):
    queryset = WinRMCredential.objects.all()
    serializer_class = WinRMCredentialSerializer


class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.all()
    serializer_class = HostSerializer
