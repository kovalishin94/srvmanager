import os
import tarfile

from datetime import datetime
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError

from core.models import Host
from ops.models import ExecuteCommand
from .validators import path_validator, update_file_validator


class EtalonInstance(models.Model):
    url = models.URLField(editable=False, blank=True)
    path_to_instance = models.TextField(validators=[path_validator])
    host = models.ForeignKey(
        Host, on_delete=models.CASCADE, related_name='etalon_instances')
    version = models.CharField(max_length=100, editable=False, blank=True)
    tag = models.CharField(max_length=20, editable=False, blank=True)
    stand = models.CharField(max_length=255, editable=False, blank=True)
    is_valid = models.BooleanField(editable=False, default=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def apply_params(self, params: dict) -> None:
        stand = params.get('STAND')
        version = params.get('BRANCH')
        tag = params.get('TAG')
        url = params.get('EXTERNAL_HOST_ADDRESS')

        if None in (stand, version, tag, url):
            self.is_valid = False
            self.save()
            return

        self.url = url
        self.version = version
        self.tag = tag
        self.stand = stand
        self.is_valid = True
        self.save()

    def create_execute_command(self) -> ExecuteCommand:
        execute_command = ExecuteCommand.objects.create(
            command=[
                f'cat {self.path_to_instance}/stand.env',
                f'cat {self.path_to_instance}/version.env'
            ],
            protocol='ssh',
            created_by=self.created_by
        )
        execute_command.hosts.add(self.host)
        return execute_command


class UpdateFile(models.Model):
    file = models.FileField(upload_to='updates/%Y/%m/',
                            validators=[
                                FileExtensionValidator(
                                    allowed_extensions=['gz']),
                                update_file_validator
                            ])
    version = models.CharField(max_length=100, editable=False)
    tag = models.CharField(max_length=20, editable=False)
    loaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def parse_config(config: str) -> dict:
        variables = {}
        for line in config.splitlines():
            if line.strip() and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                variables[key.strip()] = value.strip()
        return variables

    def set_version(self):
        with tarfile.open(self.file.path, 'r:gz') as archive:
            member = archive.getmember('./version.env')
            version_env = archive.extractfile(member)
            content = version_env.read().decode('utf-8')
            variables = self.parse_config(content)
            self.version, self.tag = variables.get(
                'BRANCH'), variables.get('TAG')
            self.save()

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.file.name = f"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}_" + \
                self.file.name
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file and os.path.exists(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)
