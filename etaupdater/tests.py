import os

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.models import Host, SSHCredential


class EtaupdaterTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.host = Host.objects.create(
            name='test_host', ip=os.getenv('SSH_HOST1'), os='linux')
        ssh_credential = SSHCredential(username=os.getenv('SSH_USER'), port=22)
        ssh_credential.set_password(os.getenv('SSH_PASSWORD'))
        ssh_credential.save()
        ssh_credential.host.add(self.host)

    def test_etalon_instance_create(self):
        data = {
            'path_to_instance': '/opt/jetalon',
            'host': self.host.id,
        }
        response = self.client.post(reverse('etalon-instance-list'), data)
        self.assertTrue(response.status_code, 201)

    def test_etalon_instance_update_list(self):
        data = {
            'path_to_instance': '/opt/jetalon',
            'host': self.host.id,
        }
        id = self.client.post(
            reverse('etalon-instance-list'), data).data.get('id')
        response_get = self.client.get(reverse('etalon-instance-list'))

        data_updated = {
            'path_to_instance': '/opt',
            'host': self.host.id,
        }
        response_update = self.client.put(
            reverse('etalon-instance-detail', args=[id]), data_updated)
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(len(response_get.data), 1)
        self.assertEqual(response_update.data.get('path_to_instance'), '/opt')
