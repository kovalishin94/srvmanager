from rest_framework import viewsets, mixins

from .models import EtalonInstance, UpdateFile, EtalonUpdate
from .serializers import EtalonInstancesSerializer, UpdateFileSerializer, EtalonUpdateSerializer


class EtalonInstanceViewSet(viewsets.ModelViewSet):
    queryset = EtalonInstance.objects.all()
    serializer_class = EtalonInstancesSerializer


class UpdateFileViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    queryset = UpdateFile.objects.all()
    serializer_class = UpdateFileSerializer

class EtalonUpdateViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    queryset = EtalonUpdate.objects.all()
    serializer_class = EtalonUpdateSerializer