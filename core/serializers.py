from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Host, SSHCredential, WinRMCredential

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class HostShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ['id', 'name', 'ip']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'is_staff',
            'is_superuser']

class CredentialSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = None
        fields = ['id', 'username', 'password', 'host']

    def create(self, validated_data: dict):
        password = validated_data.pop('password')
        hosts = validated_data.pop('host', [])
        instance = self.Meta.model(**validated_data)
        instance.set_password(password)
        instance.save()
        instance.host.set(hosts)
        return instance

    def update(self, instance, validated_data: dict):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)

        if 'host' in validated_data:
            hosts = validated_data.pop('host')
            instance.host.set(hosts)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class SSHCredentialSerializer(CredentialSerializer):
    class Meta(CredentialSerializer.Meta):
        model = SSHCredential
        fields = CredentialSerializer.Meta.fields + \
            ['port', 'ssh_key', 'passphrase']
        extra_kwargs = {'ssh_key': {'write_only': True}, 'passphrase': {'write_only': True}}


class WinRMCredentialSerializer(CredentialSerializer):
    class Meta(CredentialSerializer.Meta):
        model = WinRMCredential
        fields = CredentialSerializer.Meta.fields + ['port', 'ssl']

class HostSerializer(serializers.ModelSerializer):
    ssh_credentials = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=SSHCredential.objects.all(),
        source='sshcredential_set',
        required=False,
        allow_empty=True
    )
    winrm_credentials = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=WinRMCredential.objects.all(),
        source='winrmcredential_set',
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Host
        fields = ['id', 'name', 'ip', 'os', 'ssh_credentials', 'winrm_credentials']

    def create(self, validated_data):
        ssh_credentials = validated_data.pop('sshcredential_set', [])
        winrm_credentials = validated_data.pop('winrmcredential_set', [])
        host = super().create(validated_data)
        host.sshcredential_set.set(ssh_credentials)
        host.winrmcredential_set.set(winrm_credentials)
        return host

    def update(self, instance, validated_data):
        ssh_credentials = validated_data.pop('sshcredential_set', None)
        winrm_credentials = validated_data.pop('winrmcredential_set', None)
        host = super().update(instance, validated_data)
        if ssh_credentials is not None:
            host.sshcredential_set.set(ssh_credentials)
        if winrm_credentials is not None:
            host.winrmcredential_set.set(winrm_credentials)
        return host