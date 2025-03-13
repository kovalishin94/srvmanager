from rest_framework import serializers

from .models import ExecuteCommand


class BaseOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'hosts', 'created_by', 'log',
                  'status', 'created_at', 'updated_at']


class ExecuteCommandSerializer(BaseOperationSerializer):
    class Meta:
        model = ExecuteCommand
        fields = BaseOperationSerializer.Meta.fields + \
            ['command', 'protocol', 'stdout', 'stderr']
