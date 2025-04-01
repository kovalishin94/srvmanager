from rest_framework import viewsets, mixins

from .models import EtalonInstance, UpdateFile
from .serializers import EtalonInstancesSerializer, UpdateFileSerializer


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
