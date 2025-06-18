from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import ExecuteCommand, SendFile
from .serializers import ExecuteCommandSerializer, SendFileSerializer


class OperationPageNumberPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        next_page = self.page.next_page_number() if self.page.has_next() else None
        prev_page = self.page.previous_page_number() if self.page.has_previous() else None

        return Response({
            'count': self.page.paginator.count,
            'next': next_page,
            'previous': prev_page,
            'current': self.page.number,
            'num_pages': self.page.paginator.num_pages,
            'results': data
        })

class ExecuteCommandViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    queryset = ExecuteCommand.objects.select_related('created_by').prefetch_related('hosts')
    serializer_class = ExecuteCommandSerializer
    pagination_class = OperationPageNumberPagination


class SendFileViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = SendFile.objects.select_related('created_by').prefetch_related('hosts')
    serializer_class = SendFileSerializer
