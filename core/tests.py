from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import SSHCredential, WinRMCredential, Host


class CoreTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def create_ssh_credential(self, username='user', password='pass', hosts=None):
        if hosts is None:
            hosts = []
        data = {'username': username, 'password': password, 'host': hosts}
        response = self.client.post(reverse('ssh-credential-list'), data)
        return response

    def create_winrm_credential(self, username='user', password='pass', hosts=None, ssl=False):
        if hosts is None:
            hosts = []
        data = {'username': username, 'password': password,
                'host': hosts, 'ssl': ssl}
        response = self.client.post(reverse('winrm-credential-list'), data)
        return response

    def create_host(self, name='test_host', ip='192.168.1.1', os='linux'):
        data = {'name': name, 'ip': ip, 'os': os}
        response = self.client.post(reverse('host-list'), data)
        return response

    def test_ssh_credential_list(self):
        self.create_ssh_credential()
        self.create_ssh_credential(username='user2', password='pass')
        response = self.client.get(reverse('ssh-credential-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_ssh_credential_create(self):
        response = self.create_ssh_credential()
        self.assertEqual(response.status_code, 201)

    def test_ssh_credential_delete(self):
        id = self.create_ssh_credential().data.get('id')
        response = self.client.delete(
            reverse('ssh-credential-detail', args=[id]))
        self.assertEqual(response.status_code, 204)

    def test_ssh_credential_update(self):
        id = self.create_ssh_credential().data.get('id')
        first_host_id = self.create_host().data.get('id')
        second_host_id = self.create_host(
            name='test_host2', ip='192.168.1.2', os='windows').data.get('id')
        data = {'username': 'user_edited', 'password': 'pass_edited',
                'host': [first_host_id, second_host_id]}
        response = self.client.put(
            reverse('ssh-credential-detail', args=[id]), data)
        ssh_credential = SSHCredential.objects.get(id=id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('username'), 'user_edited')
        self.assertEqual(ssh_credential.username, 'user_edited')
        self.assertEqual(ssh_credential.get_password(), 'pass_edited')
        self.assertEqual(ssh_credential.host.all().count(), 2)

    def test_winrm_credential_list(self):
        self.create_winrm_credential()
        self.create_winrm_credential(username='user2', password='pass')
        response = self.client.get(reverse('winrm-credential-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_winrm_credential_create(self):
        response = self.create_winrm_credential()
        self.assertEqual(response.status_code, 201)

    def test_winrm_credential_delete(self):
        id = self.create_winrm_credential().data.get('id')
        response = self.client.delete(
            reverse('winrm-credential-detail', args=[id]))
        self.assertEqual(response.status_code, 204)

    def test_winrm_credential_update(self):
        id = self.create_winrm_credential().data.get('id')
        first_host_id = self.create_host().data.get('id')
        second_host_id = self.create_host(
            name='test_host2', ip='192.168.1.2', os='windows').data.get('id')
        data = {'username': 'user_edited', 'password': 'pass_edited',
                'host': [first_host_id, second_host_id], 'ssl': True}
        response = self.client.put(
            reverse('winrm-credential-detail', args=[id]), data)
        winrm_credential = WinRMCredential.objects.get(id=id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('username'), 'user_edited')
        self.assertEqual(winrm_credential.username, 'user_edited')
        self.assertEqual(winrm_credential.ssl, True)
        self.assertEqual(winrm_credential.get_password(), 'pass_edited')
        self.assertEqual(winrm_credential.host.all().count(), 2)

    def test_host_list(self):
        self.create_host()
        self.create_host(name='test_host2', ip='192.168.1.2', os='windows')
        response = self.client.get(reverse('host-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_host_create(self):
        response = self.create_host()
        self.assertEqual(response.status_code, 201)

    def test_host_create_bad_ip(self):
        response = self.create_host(ip='bad_ip')
        self.assertEqual(response.status_code, 400)

    def test_host_create_bad_os(self):
        response = self.create_host(os='bad_os')
        self.assertEqual(response.status_code, 400)

    def test_host_create_double_ip(self):
        self.create_host()
        response = self.create_host()
        self.assertEqual(response.status_code, 400)

    def test_host_delete(self):
        id = self.create_host().data.get('id')
        response = self.client.delete(reverse('host-detail', args=[id]))
        self.assertEqual(response.status_code, 204)

    def test_host_update(self):
        id = self.create_host().data.get('id')
        data = {'name': 'edited_host', 'ip': '192.168.99.99', 'os': 'windows'}
        response = self.client.put(reverse('host-detail', args=[id]), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('name'), 'edited_host')
        self.assertEqual(response.data.get('ip'), '192.168.99.99')
        self.assertEqual(response.data.get('os'), 'windows')

    def test_host_update_bad_put(self):
        id = self.create_host().data.get('id')
        data = {'name': 'edited_host', 'ip': '192.168.99.99'}
        response = self.client.put(reverse('host-detail', args=[id]), data)
        self.assertEqual(response.status_code, 400)
