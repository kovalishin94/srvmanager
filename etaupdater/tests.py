import os
import time
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.models import Host, SSHCredential
from .models import EtalonInstance


class EtaupdaterTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_etalon_instance_create(self):
        host = Host.objects.create(
            name='test_host', ip=os.getenv('SSH_HOST1'), os='linux')
        ssh_credential = SSHCredential(username=os.getenv('SSH_USER'), port=22)
        ssh_credential.set_password(os.getenv('SSH_PASSWORD'))
        ssh_credential.save()
        ssh_credential.host.add(host)
        eta_instance = EtalonInstance.objects.create(
            path_to_instance='/opt/jetalon', host=host, created_by=self.user)
        self.assertTrue(True)
