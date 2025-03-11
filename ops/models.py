import winrm
import uuid
import datetime

from django.db import models
from django.contrib.auth.models import User

from core.models import Host
from .validators import validate_command


class BaseOperation(models.Model):
    STATUS_CHOICES = (
        ('queue', 'В очереди'),
        ('progress', 'Выполняется'),
        ('error', 'Ошибка'),
        ('completed', 'Выполнено'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(Host, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, editable=False)
    log = models.JSONField(blank=True, default=dict, editable=False)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, editable=False, default='queue')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def add_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log[timestamp] = message
        self.save()

    class Meta:
        abstract = True


class ExecuteCommand(BaseOperation):
    PROTOCOL_CHOICES = (
        ('winrm', 'WinRM'),
        ('ssh', 'SSH'),
    )

    command = models.JSONField(validators=[validate_command])
    protocol = models.CharField(max_length=10, choices=PROTOCOL_CHOICES)
    stdout = models.JSONField(blank=True, default=dict, editable=False)
    stderr = models.JSONField(blank=True, default=dict, editable=False)

    def run_winrm(self) -> str:
        winrm_credential = self.host.winrmcredential_set.first()
        if not winrm_credential:
            self.add_log('Нет учетных записей для выполнения команды.')
            return

        server = f"http://{self.host.ip}:{winrm_credential.port}/wsman"
        session = winrm.Session(server, auth=(
            winrm_credential.username, winrm_credential.get_password()), transport='ntlm')

        result = session.run_ps(self.command[0])
        return result.std_out.decode('cp1251')
