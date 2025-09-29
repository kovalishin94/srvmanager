import uuid
from celery import shared_task, chord, group
from celery.exceptions import MaxRetriesExceededError

from core.models import Host
from ops.models import ExecuteCommand
from .models import EtalonInstance, EtalonUpdate


@shared_task(bind=True, max_retries=3)
def check_execute_command(self, execute_command_id: uuid, etalon_instance_id: int):
    """
    Проверка выполнения операции получения данных о площадке при создании EtalonInstance.
    """
    execute_command = ExecuteCommand.objects.get(id=execute_command_id)
    etalon_instance = EtalonInstance.objects.get(id=etalon_instance_id)
    try:
        if execute_command.status not in ('completed', 'error'):
            raise self.retry(exc=Exception(
                'Имеются не завершенные задачи.'), countdown=10)

        if not len(execute_command.stdout.values()):
            etalon_instance.is_valid = False
            return

        etalon_instance.apply_params(list(execute_command.stdout.values())[-1])

    except MaxRetriesExceededError:
        etalon_instance.is_valid = False

@shared_task
def finalize_update(results, etalon_update_id: uuid):
    """
    Завершение обновления, анализ результатов.
    Если хотя бы на одном хосте была ошибка, то считаем что обновление завершилось с ошибкой.
    """
    etalon_update = EtalonUpdate.objects.get(id=etalon_update_id)
    if False in results:
        etalon_update.status = "error"
        etalon_update.save(update_fields=["status"])
        etalon_update.add_log("Обновление завершилось с ошибками.")
        return
    etalon_update.status = "completed"
    etalon_update.save(update_fields=["status"])
    etalon_update.add_log("Обновление успешно выполнено.")

@shared_task
def run_etalon_update(etalon_update_id: uuid):
    """
    Точка входа — запускается сигналом m2m для EtalonUpdate.
    Создаём по одному подпроцессу на каждый уникальный хост.
    """
    etalon_update = EtalonUpdate.objects.get(id=etalon_update_id)
    etalon_update.status = 'progress'
    etalon_update.save(update_fields=['status'])
    etalon_update.add_log("Начинается обновление")

    hosts = Host.objects.filter(id__in=etalon_update.instances.values_list('host_id', flat=True).distinct())

    # создаем группу задач для каждого хоста, 1 воркер 1 хост
    subtasks = group(
        run_host_update.s(etalon_update_id, host.id) for host in hosts
    )
    # создаем цепочку, которая после завершения всех задач вызовет finalize_update и передаст ей результаты
    chord(subtasks)(finalize_update.s(etalon_update_id))

@shared_task
def run_host_update(etalon_update_id: uuid, host_id: int):
    """
    Запускается параллельно по количеству уникальных хостов.
    """
    etalon_update = EtalonUpdate.objects.get(id=etalon_update_id)
    return etalon_update.run(host_id)