from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import CorePageNumberPagination
from .models import EtalonInstance, UpdateFile, EtalonUpdate
from .serializers import EtalonInstancesSerializer, UpdateFileSerializer, EtalonUpdateSerializer
from .tasks import check_execute_command


class EtalonInstanceViewSet(viewsets.ModelViewSet):
    queryset = EtalonInstance.objects.all().order_by('-created_at')
    serializer_class = EtalonInstancesSerializer
    pagination_class = CorePageNumberPagination

    @action(methods=["POST"], detail=True)
    def check(self, request, pk=None):
        instance = self.get_object()
        execute_command = instance.create_execute_command()
        check_execute_command.apply_async(args=[execute_command.id, instance.id], countdown=10)
        return Response(status=status.HTTP_200_OK)


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
    queryset = EtalonUpdate.objects.prefetch_related('instances', 'update_file').order_by('-created_at')
    serializer_class = EtalonUpdateSerializer
    pagination_class = CorePageNumberPagination