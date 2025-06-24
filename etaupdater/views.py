from rest_framework import viewsets, mixins

from core.views import CorePageNumberPagination
from .models import EtalonInstance, UpdateFile, EtalonUpdate
from .serializers import EtalonInstancesSerializer, UpdateFileSerializer, EtalonUpdateSerializer


class EtalonInstanceViewSet(viewsets.ModelViewSet):
    queryset = EtalonInstance.objects.all()
    serializer_class = EtalonInstancesSerializer
    pagination_class = CorePageNumberPagination


class UpdateFileViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    queryset = UpdateFile.objects.all()
    serializer_class = UpdateFileSerializer
    pagination_class = CorePageNumberPagination

class EtalonUpdateViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    queryset = EtalonUpdate.objects.all()
    serializer_class = EtalonUpdateSerializer
    pagination_class = CorePageNumberPagination