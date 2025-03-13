import os
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.models import Host, WinRMCredential


class CoreTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_execute_command_create_list(self):
        host = Host.objects.create(
            name='test_host', ip=os.getenv('WINRM_HOST1'), os='windows')
        host2 = Host.objects.create(
            name='test_host2', ip=os.getenv('WINRM_HOST2'), os='windows')
        winrm_credential = WinRMCredential(username=os.getenv('WINRM_USER'))
        winrm_credential.set_password(os.getenv('WINRM_PASSWORD'))
        winrm_credential.save()
        winrm_credential.host.add(host)
        winrm_credential.host.add(host2)
        data1 = {
            'command': '["netstat -an | findstr LISTENING"]',
            'protocol': 'winrm',
            'hosts': [host.id, host2.id],
            'created_by': self.user.id
        }

        data2 = {
            'command': '["ping 8.8.8.8"]',
            'protocol': 'winrm',
            'hosts': [host.id, host2.id],
            'created_by': self.user.id
        }

        response_create1 = self.client.post(
            reverse('execute-command-list'), data1)
        response_create2 = self.client.post(
            reverse('execute-command-list'), data2)
        response_get = self.client.get(reverse('execute-command-list'))

        self.assertEqual(response_create1.status_code, 201)
        self.assertEqual(response_create2.status_code, 201)
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(len(response_get.data), 2)
