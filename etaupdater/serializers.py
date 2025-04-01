from rest_framework import serializers

from .models import EtalonInstance, UpdateFile


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
