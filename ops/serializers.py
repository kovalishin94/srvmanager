from rest_framework import serializers

from core.serializers import UserShortSerializer, HostShortSerializer
from core.models import Host
from .models import ExecuteCommand, SendFile


class BaseOperationSerializer(serializers.ModelSerializer):
    created_by = UserShortSerializer(read_only=True)
    created_at = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S', read_only=True) # type: ignore
    updated_at = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S', read_only=True) # type: ignore
    class Meta:
        model = None
        fields = ['id', 'created_by', 'log',
                  'status', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class ExecuteCommandSerializer(BaseOperationSerializer):
    hosts = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Host.objects.all(),
    )
    hosts_display = HostShortSerializer(many=True, read_only=True, source='hosts')
    class Meta:
        model = ExecuteCommand
        fields = BaseOperationSerializer.Meta.fields + \
            ['hosts', 'hosts_display', 'command', 'protocol', 'sudo', 'stdout', 'stderr']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['hosts'] = rep.pop('hosts_display', [])
        return rep

class SendFileSerializer(BaseOperationSerializer):
    hosts = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Host.objects.all(),
    )
    hosts_display = HostShortSerializer(many=True, read_only=True, source='hosts')
    class Meta:
        model = SendFile
        fields = BaseOperationSerializer.Meta.fields + \
            ['hosts', 'hosts_display', 'protocol', 'local_path', 'target_path', 'file']
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['hosts'] = rep.pop('hosts_display', [])
        return rep
