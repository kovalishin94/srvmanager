from rest_framework import viewsets
from rest_framework import mixins

from .models import ExecuteCommand
from .serializers import ExecuteCommandSerializer


class ExecuteCommandViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    queryset = ExecuteCommand.objects.all()
    serializer_class = ExecuteCommandSerializer
