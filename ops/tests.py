import os
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.models import Host, WinRMCredential, SSHCredential


class CoreTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_execute_winrm_command_create_list(self):
        host = Host.objects.create(
            name='test_host', ip=os.getenv('WINRM_HOST1'), os='windows')
        host2 = Host.objects.create(
            name='test_host2', ip=os.getenv('WINRM_HOST2'), os='windows')
        winrm_credential = WinRMCredential(username=os.getenv('WINRM_USER'))
        winrm_credential.set_password(os.getenv('WINRM_PASSWORD'))
        winrm_credential.save()
        winrm_credential.host.add(host, host2)
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

    def test_execute_ssh_command_create_list(self):
        host = Host.objects.create(
            name='test_host', ip=os.getenv('SSH_HOST1'), os='linux')
        host2 = Host.objects.create(
            name='test_host2', ip=os.getenv('SSH_HOST2'), os='linux')

        ssh_credential = SSHCredential.objects.create(
            username=os.getenv('SSH_USER'))
        ssh_credential.set_password(os.getenv('SSH_PASSWORD'))
        ssh_credential.save()
        ssh_credential.host.add(host, host2)

        data1 = {
            'command': '["uptime -p", "uptime"]',
            'protocol': 'ssh',
            'hosts': [host.id, host2.id],
            'created_by': self.user.id
        }

        data2 = {
            'command': '["df -h", "ls -la"]',
            'protocol': 'ssh',
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

    def test_execute_command_delete(self):
        host = Host.objects.create(
            name='test_host', ip='192.168.0.1', os='windows')

        data1 = {
            'command': '["ping 8.8.8.8"]',
            'protocol': 'winrm',
            'hosts': [host.id],
            'created_by': self.user.id
        }

        response_create = self.client.post(
            reverse('execute-command-list'), data1)
        response_delete = self.client.delete(
            reverse('execute-command-detail', args=[response_create.data.get('id')]))

        self.assertEqual(response_create.status_code, 201)
        self.assertEqual(response_delete.status_code, 204)
