from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Host, SSHCredential, WinRMCredential


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

class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ['id', 'name', 'ip', 'os']


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


class WinRMCredentialSerializer(CredentialSerializer):
    class Meta(CredentialSerializer.Meta):
        model = WinRMCredential
        fields = CredentialSerializer.Meta.fields + ['port', 'ssl']
