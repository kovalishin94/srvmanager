from rest_framework import serializers

from ops.serializers import BaseOperationSerializer
from .models import EtalonInstance, UpdateFile, EtalonUpdate


class EtalonInstancesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtalonInstance
        fields = [
            'id',
            'url',
            'path_to_instance',
            'host',
            'version',
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

class EtalonUpdateSerializer(BaseOperationSerializer):
    instances = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EtalonInstance.objects.all(),
        write_only=True,
    )
    instances_display = EtalonInstancesSerializer(many=True, read_only=True, source='instances')
    class Meta:
        model = EtalonUpdate
        fields = BaseOperationSerializer.Meta.fields + ['instances', 'update_file', 'instances_display']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['instances'] = rep.pop('instances_display', [])
        return rep