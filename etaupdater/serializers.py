from rest_framework import serializers

from ops.serializers import BaseOperationSerializer
from core.serializers import UserShortSerializer
from .models import EtalonInstance, UpdateFile, EtalonUpdate


class EtalonInstancesSerializer(serializers.ModelSerializer):
    created_by = UserShortSerializer(read_only=True)
    class Meta:
        model = EtalonInstance
        fields = [
            'id',
            'url',
            'path_to_instance',
            'host',
            'version',
            'docker_command',
            'tag',
            'stand',
            'is_valid',
            'created_by',
            'created_at',
            'updated_at'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class UpdateFileSerializer(serializers.ModelSerializer):
    loaded_by = UserShortSerializer(read_only=True)
    created_at = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S', read_only=True)
    class Meta:
        model = UpdateFile
        fields = [
            'id',
            'file',
            'version',
            'tag',
            'loaded_by',
            'created_at'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['loaded_by'] = request.user
        return super().create(validated_data)

class EtalonInstanceShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtalonInstance
        fields = ['id', 'url', 'version', 'tag', 'stand']

class UpdateFileShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpdateFile
        fields = ['id', 'version', 'tag']

class EtalonUpdateSerializer(BaseOperationSerializer):
    instances = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EtalonInstance.objects.all(),
        write_only=True,
    )
    instances_display = EtalonInstanceShortSerializer(many=True, read_only=True, source='instances')
    update_file = serializers.PrimaryKeyRelatedField(
        queryset=UpdateFile.objects.all(),
        write_only=True,
        required=True,
    )
    update_file_display = UpdateFileShortSerializer(read_only=True, source='update_file')
    class Meta:
        model = EtalonUpdate
        fields = BaseOperationSerializer.Meta.fields + ['instances', 'update_file', 'instances_display', 'update_file_display']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['instances'] = rep.pop('instances_display', [])
        rep['update_file'] = rep.pop('update_file_display', None)
        return rep