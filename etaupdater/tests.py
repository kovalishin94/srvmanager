import os

from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Host, SSHCredential
from core.tests import BaseTestCase
from .models import UpdateFile, PrepareUpdate, EtalonInstance


class EtaupdaterTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
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

    def test_update_file_create(self):
        with open("/app/test_files/good_update.tar.gz", 'rb') as f:
            test_file = SimpleUploadedFile(name=f.name, content=f.read())
        data = {
            "file": test_file,
        }
        response = self.client.post(reverse('update-file-list'), data)
        update_file = UpdateFile.objects.first()
        self.assertEqual(response.status_code, 201)
        os.remove(update_file.file.path)

    def test_prepare_update(self):
        with open("/app/test_files/good_update.tar.gz", 'rb') as f:
            test_file = SimpleUploadedFile(name=f.name, content=f.read())
        data_file = {"file": test_file}
        self.client.post(reverse('update-file-list'), data_file)
        data_instance = {
            'path_to_instance': '/opt/jetalon',
            'host': self.host.id,
        }
        self.client.post(reverse('etalon-instance-list'), data_instance)
        update_file = UpdateFile.objects.first()
        instance = EtalonInstance.objects.first()
        prepare_update = PrepareUpdate.objects.create(
            created_by=self.user,
            update_file=update_file
        )
        prepare_update.instances.add(instance)
