import uuid
from celery import shared_task

from ops.models import ExecuteCommand
from .models import EtalonInstance, UpdateFile


@shared_task
def check_execute_command(execute_command_id: uuid, etalon_instance_id: int):
    execute_command = ExecuteCommand.objects.get(id=execute_command_id)
    etalon_instance = EtalonInstance.objects.get(id=etalon_instance_id)
    params = dict()
    if execute_command.status == 'completed':
        for value in execute_command.stdout.values():
            params.update(UpdateFile.parse_config(value))

    etalon_instance.apply_params(params)
