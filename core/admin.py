from django.contrib import admin

from .models import SSHCredential, WinRMCredential, Host


@admin.register(SSHCredential)
class SSHCredentialAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', '_password', 'port']


@admin.register(WinRMCredential)
class WinRMCredentialAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', '_password', 'port', 'ssl']


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'os', 'ssh_credential', 'winrm_credential']
