import os
import tarfile

from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError

from core.models import Host
from ops.models import ExecuteCommand
from .validators import path_validator


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


class UpdateFile(models.Model):
    file = models.FileField(upload_to='updates/%Y/%m/')
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

    def check_files(self) -> bool:
        check_result = 0
        targets = ("./version.env", "./jetalon.env")
        with tarfile.open(self.file.path, 'r:gz') as archive:
            members = archive.getmembers()
            for member in members:
                if member.path == "./stand.env":
                    return False
                if member.path in targets:
                    check_result += 1
            return check_result == len(targets)

    def set_version(self):
        with tarfile.open(self.file.path, 'r:gz') as archive:
            member = archive.getmember('./version.env')
            version_env = archive.extractfile(member)
            content = version_env.read().decode('utf-8')
            variables = self.parse_config(content)
            self.version, self.tag = variables.get(
                'BRANCH'), variables.get('TAG')

    def save(self, *args, **kwargs):
        try:
            self.file.name = f"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}_" + \
                self.file.name
            super().save(*args, **kwargs)
            is_valid = self.check_files()
            self.set_version()
        except KeyError:
            self.delete()
            raise ValidationError(
                "Файл version.env не найден, либо не содержит необходимых ключей")
        except Exception as e:
            self.delete()
            raise ValidationError(
                f"В процессе валидации возникла непредвиденная ошибка: {str(e)}")
        if not is_valid:
            self.delete()
            raise ValidationError("Файл не является обновлением Эталона")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file and os.path.exists(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)
