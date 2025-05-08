from rest_framework import viewsets
from rest_framework import mixins

from .models import ExecuteCommand, SendFile
from .serializers import ExecuteCommandSerializer, SendFileSerializer


class ExecuteCommandViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    queryset = ExecuteCommand.objects.select_related('created_by').prefetch_related('hosts')
    serializer_class = ExecuteCommandSerializer


class SendFileViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = SendFile.objects.select_related('created_by').prefetch_related('hosts')
    serializer_class = SendFileSerializer
