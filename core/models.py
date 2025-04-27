import base64
import hashlib
from cryptography.fernet import Fernet

from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator

key_material = hashlib.sha256(
    settings.SECRET_KEY[len('django-insecure-'):].encode()).digest()
fernet_key = base64.urlsafe_b64encode(key_material[:32])
fernet = Fernet(fernet_key)


class Host(models.Model):
    OS_CHOICES = (
        ('linux', 'Linux'),
        ('windows', 'Windows'),
    )

    name = models.CharField(max_length=80, unique=True)
    ip = models.GenericIPAddressField()
    os = models.CharField(max_length=10, choices=OS_CHOICES)

    def __str__(self):
        return self.name


class Credential(models.Model):
    username = models.CharField(max_length=100)
    _password = models.BinaryField()
    host = models.ManyToManyField(Host, blank=True)

    def set_password(self, password):
        self._password = fernet.encrypt(password.encode())

    def get_password(self) -> str:
        return fernet.decrypt(bytes(self._password)).decode()

    def __str__(self):
        return f"{self.username}_{self.id}"

    class Meta:
        abstract = True


class SSHCredential(Credential):
    port = models.PositiveIntegerField(
        validators=[MaxValueValidator(65535)], blank=True, default=22)
    ssh_key = models.FileField(upload_to='ssh_keys/', blank=True, null=True)
    passphrase = models.CharField(max_length=255, blank=True)

    def create_connect_params(self, ip: str) -> dict:
        connect_params = {
            'hostname': ip,
            'port': self.port,
            'username': self.username,
            'timeout': 20.0
        }
        if self.ssh_key:
            connect_params['key_filename'] = self.ssh_key.path
            if self.passphrase:
                connect_params['passphrase'] = self.passphrase
        else:
            connect_params['password'] = self.get_password()

        return connect_params


class WinRMCredential(Credential):
    port = models.PositiveIntegerField(
        validators=[MaxValueValidator(65535)], blank=True, default=5985)
    ssl = models.BooleanField(blank=True, default=False)
