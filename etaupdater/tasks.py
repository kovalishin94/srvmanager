import uuid
from celery import shared_task, chord, group
from celery.exceptions import MaxRetriesExceededError

from core.models import Host
from ops.models import ExecuteCommand
from .models import EtalonInstance, PrepareUpdate, EtalonUpdate


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


@shared_task(bind=True, max_retries=5)
def process_stage(self, prepare_update_id: uuid, tasks_ids: dict, stage: str = 'first'):
    """
    Задача по отработке каждой стадии выполнения PrepareUpdate.
    """
    prepare_update = PrepareUpdate.objects.get(id=prepare_update_id)
    stage_conf = prepare_update.get_stage_conf(stage)
    stage_full_name = stage_conf.get('stage_full_name')
    try:
        count_completed_tasks = prepare_update.check_operations(
            tasks_ids, stage)

        if count_completed_tasks is None:
            raise self.retry(exc=Exception(
                'Имеются не завершенные задачи.'), countdown=60)

        if count_completed_tasks == 0:
            prepare_update.error_log(
                f'Нет ни одной успешной задачи на стадии {stage_full_name}. Подготовка к обновлению завершена с ошибкой.')
            return

        prepare_update.add_log(
            f'На стадии {stage_full_name} успешно отработало {count_completed_tasks} задач.')

        next_tasks_ids = stage_conf.get('next_fn')(list(tasks_ids.values()))

        next_stage = stage_conf.get('next_stage', None)

        if next_stage is None:
            return

        if not next_tasks_ids:
            prepare_update.error_log(
                f'Задачи для следующей стадии не были созданы.')
            return

        process_stage.delay(prepare_update_id, next_tasks_ids, next_stage)

    except MaxRetriesExceededError:
        prepare_update.error_log(f'Не удалось дождаться завершения задач на стадии {stage_full_name}. Подготовка к обновлению прервана.')


#----------------------EtalonUpdate----------------------
@shared_task
def finalize_update(results, etalon_update_id: uuid):
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

    # каждая под-таска работает с одним хостом
    subtasks = group(
        run_host_update.s(etalon_update_id, host.id) for host in hosts
    )
    chord(subtasks)(finalize_update.s(etalon_update_id))

@shared_task
def run_host_update(etalon_update_id: uuid, host_id: int):
    """
    Запускается параллельно по количеству уникальных хостов.
    """
    etalon_update = EtalonUpdate.objects.get(id=etalon_update_id)
    return etalon_update.run(host_id)