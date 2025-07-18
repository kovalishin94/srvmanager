from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.contrib.auth.models import User

from .models import SSHCredential, WinRMCredential, Host
from .serializers import SSHCredentialSerializer, WinRMCredentialSerializer, HostSerializer, UserSerializer

class CorePageNumberPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 10000

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
    pagination_class = CorePageNumberPagination


class WinRMCredentialViewSet(viewsets.ModelViewSet):
    queryset = WinRMCredential.objects.all()
    serializer_class = WinRMCredentialSerializer
    pagination_class = CorePageNumberPagination


class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.all()
    serializer_class = HostSerializer
    pagination_class = CorePageNumberPagination
