import uuid
from celery import shared_task, chord

from .models import ExecuteCommand, SendFile

types = {
    'execute-command': ExecuteCommand,
    'send-file': SendFile
}


@shared_task
def check_results(results, operation_id: uuid, operation_type: str):
    model = types.get(operation_type)
    operation = model.objects.get(id=operation_id)

    for result in results:
        if result == False:
            operation.status = 'error'
            operation.save(update_fields=['status'])
            operation.add_log('Операция завершена с ошибками.')
            return

    operation.status = 'completed'
    operation.save(update_fields=['status'])
    operation.add_log('Операция успешно завершена.')


@shared_task
def run_operation(operation_id: uuid, operation_type: str):
    model = types.get(operation_type)

    if not model:
        return

    operation = model.objects.get(id=operation_id)
    operation.status = 'progress'
    operation.save(update_fields=['status'])
    operation.add_log('Операция запущена.')

    tasks = [
        run_suboperation.s(operation_id, host.id, operation_type) for host in operation.hosts.all()
    ]

    chord(tasks)(check_results.s(operation_id, operation_type))


@shared_task
def run_suboperation(operation_id: uuid, host_id: int, operation_type: str):
    model = types.get(operation_type)
    operation = model.objects.get(id=operation_id)
    return operation.run(host_id)
