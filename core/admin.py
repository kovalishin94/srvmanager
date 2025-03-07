from django import forms
from django.contrib import admin

from .models import SSHCredential, WinRMCredential, Host


class CredentialAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = SSHCredential
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            instance.set_password(password)
        if commit:
            instance.save()
        return instance


@admin.register(SSHCredential)
class SSHCredentialAdmin(admin.ModelAdmin):
    form = CredentialAdminForm
    list_display = ['id', 'username', '_password', 'port']


@admin.register(WinRMCredential)
class WinRMCredentialAdmin(admin.ModelAdmin):
    form = CredentialAdminForm
    list_display = ['id', 'username', '_password', 'port', 'ssl']


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'os', 'ssh_credential', 'winrm_credential']
