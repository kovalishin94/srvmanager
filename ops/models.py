import uuid
import winrm
import paramiko

from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

from core.models import Host, WinRMCredential, SSHCredential
from .validators import validate_command


class BaseOperation(models.Model):
    STATUS_CHOICES = (
        ('queue', 'В очереди'),
        ('progress', 'Выполняется'),
        ('error', 'Ошибка'),
        ('completed', 'Выполнено'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hosts = models.ManyToManyField(Host, blank=True)
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
        print(self.id, message)
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

    def run_winrm_command(self, session: winrm.Session, ip: str):
        for command in self.command:
            result = session.run_ps(command)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stdout = result.std_out.decode('cp1251')
            stderr = result.std_err.decode('cp1251')
            key = f'{timestamp} [{ip}]'
            if stdout:
                self.stdout[key] = stdout
            if stderr:
                self.stderr[key] = stderr
            self.save()

    def run_winrm(self, host: Host) -> bool:
        winrm_credential: WinRMCredential = host.winrmcredential_set.first()
        if not winrm_credential:
            self.add_log(
                f'[{host.ip}] Нет учетных записей для выполнения команды.')
            return False

        http = 'https' if winrm_credential.ssl else 'http'
        server = f"{http}://{host.ip}:{winrm_credential.port}/wsman"
        session = winrm.Session(server, auth=(
            winrm_credential.username, winrm_credential.get_password()), transport='ntlm')
        try:
            self.run_winrm_command(session, host.ip)
            self.add_log(f'[{host.ip}]Команда выполнена.')
        except Exception as e:
            self.add_log(
                f'[{host.ip}] В результате выполнения команды возникла следующая ошибка: {e}')
            return False

        return True

    def run_ssh_command(self, client: paramiko.SSHClient, ip: str):
        for command in self.command:
            stdin, stdout, stderr = client.exec_command(command)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            key = f'{timestamp} [{ip}]'
            stdout = stdout.read().decode('utf-8')
            stderr = stderr.read().decode('utf-8')
            if stdout:
                self.stdout[key] = stdout
            if stderr:
                self.stderr[key] = stderr
            self.save()

    def run_ssh(self, host: Host) -> bool:
        ssh_credential: SSHCredential = host.sshcredential_set.first()
        if not ssh_credential:
            self.add_log(
                f'[{host.ip}] Нет учетных записей для выполнения команды.')
            return False

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_params = {
            'hostname': host.ip,
            'port': ssh_credential.port,
            'username': ssh_credential.username,
            'timeout': 120.0
        }
        if ssh_credential.ssh_key:
            connect_params['key_filename'] = ssh_credential.ssh_key.path
            if ssh_credential.passphrase:
                connect_params['passphrase'] = ssh_credential.passphrase
        else:
            connect_params['password'] = ssh_credential.get_password()

        try:
            client.connect(**connect_params)
            self.run_ssh_command(client, host.ip)
            self.add_log(f'[{host.ip}]Команда выполнена.')
        except Exception as e:
            self.add_log(
                f'[{host.ip}] В результате выполнения команды возникла следующая ошибка: {e}')
        finally:
            client.close()

    def run(self, host_id: int):
        host = Host.objects.get(id=host_id)
        if self.protocol == 'winrm':
            return self.run_winrm(host)
        if self.protocol == 'ssh':
            return self.run_ssh(host)
