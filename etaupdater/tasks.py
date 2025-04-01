import uuid
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from ops.models import ExecuteCommand, SendFile
from .models import EtalonInstance, PrepareUpdate

@shared_task(bind=True, max_retries=3)
def check_execute_command(self, execute_command_id: uuid, etalon_instance_id: int):
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


@shared_task(bind=True, max_retries=3)
def process_stage(self, prepare_update_id: uuid, tasks_ids: dict, stage: str = 'first'):
    """

    """
    prepare_update = PrepareUpdate.objects.get(id=prepare_update_id)
    stage_conf = prepare_update.get_stage_conf(stage)
    stage_full_name = stage_conf.get('stage_full_name')
    try:
        count_completed_tasks = prepare_update.check_operations(
            tasks_ids, stage)

        if count_completed_tasks is None:
            raise self.retry(exc=Exception(
                'Имеются не завершенные задачи.'), countdown=10)

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
