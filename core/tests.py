from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import Host


class JWTAuthTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_ssh_credential_list(self):
        response = self.client.get(reverse('ssh-credential-list'))
        self.assertEqual(response.status_code, 200)

    def test_winrm_credential_list(self):
        response = self.client.get(reverse('winrm-credential-list'))
        self.assertEqual(response.status_code, 200)

    def test_host_list(self):
        response = self.client.get(reverse('host-list'))
        self.assertEqual(response.status_code, 200)

    def test_create_ssh_credential(self):
        data = {'username': 'user', 'password': 'pass'}
        response = self.client.post(reverse('ssh-credential-list'), data)
        self.assertEqual(response.status_code, 201)

    def test_create_winrm_credential(self):
        data = {'username': 'user', 'password': 'pass'}
        response = self.client.post(reverse('winrm-credential-list'), data)
        self.assertEqual(response.status_code, 201)

    def test_create_host(self):
        data = {'name': 'test_host', 'ip': '192.168.1.1', 'os': 'linux'}
        response = self.client.post(reverse('host-list'), data)
        self.assertEqual(response.status_code, 201)
