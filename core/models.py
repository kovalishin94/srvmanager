import base64
import hashlib
from cryptography.fernet import Fernet

from django.db import models
from django.conf import settings

key_material = hashlib.sha256(
    settings.SECRET_KEY[len('django-insecure-'):].encode()).digest()
fernet_key = base64.urlsafe_b64encode(key_material[:32])
fernet = Fernet(fernet_key)


class Credential(models.Model):
    username = models.CharField(max_length=100)
    _password = models.BinaryField()

    def set_password(self, password):
        self._password = fernet.encrypt(password.encode())

    def get_password(self) -> str:
        return fernet.decrypt(bytes(self._password)).decode()

    class Meta:
        abstract = True


class Host(models.Model):
    OS_CHOICES = (
        ('linux', 'Linux'),
        ('windows', 'Windows'),
    )

    name = models.CharField(max_length=80)
    ip = models.GenericIPAddressField(unique=True)
    os = models.CharField(max_length=10, choices=OS_CHOICES)

    def __str__(self):
        return self.name
