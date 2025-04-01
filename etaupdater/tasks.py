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
def check_pulling_images(self, prepare_update_id: uuid, pull_images_tasks_ids: dict):
    prepare_update = PrepareUpdate.objects.get(id=prepare_update_id)
    try:
        count_completed_tasks = prepare_update.check_operations(
            pull_images_tasks_ids, 'third')

        if count_completed_tasks is None:
            raise self.retry(exc=Exception(
                'Имеются не завершенные задачи.'), countdown=10)

        if count_completed_tasks == 0:
            prepare_update.error_log(
                'Нет ни одной успешной задачи по скачиванию докер образов. Подготовка к обновлению завершена с ошибкой.')
            return

        prepare_update.finish(list(pull_images_tasks_ids.values()))

    except MaxRetriesExceededError:
        prepare_update.error_log(
            'Не получилось выполнить команды скачивания докер образов. Подробности смотрите в логах фоновых ExecuteCommand.')


@shared_task(bind=True, max_retries=3)
def check_preparing_update(self, prepare_update_id: uuid, execute_command_tasks_ids: dict):
    """
    Проверка выполнения команд разархивирования. Второй этап подготовки к обновлению.
    """
    prepare_update = PrepareUpdate.objects.get(id=prepare_update_id)

    try:
        count_completed_tasks = prepare_update.check_operations(
            execute_command_tasks_ids, 'second')

        if count_completed_tasks is None:
            raise self.retry(exc=Exception(
                'Имеются не завершенные задачи.'), countdown=10)

        if count_completed_tasks == 0:
            prepare_update.error_log(
                'Нет ни одной успешной задачи по выполнению команды обновления. Подготовка к обновлению завершена с ошибкой.')
            return

        pull_images_tasks_ids = prepare_update.create_task_to_pull_images(
            list(execute_command_tasks_ids.values()))

        if not pull_images_tasks_ids:
            prepare_update.error_log(
                'Задачи на скачивание докер образов не были созданы.')
            return

        check_pulling_images.delay(prepare_update_id, pull_images_tasks_ids)

    except MaxRetriesExceededError:
        prepare_update.error_log(
            'Не получилось выполнить команды подготовки к обновлению. Подробности смотрите в логах фоновых ExecuteCommand.')


@shared_task(bind=True, max_retries=3)
def check_sending_files(self, prepare_update_id: uuid, send_file_tasks_ids: dict):
    """
    Проверка выполнения созданных задач SendFile. Первый этап подготовки к обновлению.
    """
    prepare_update = PrepareUpdate.objects.get(id=prepare_update_id)

    try:
        count_completed_tasks = prepare_update.check_operations(
            send_file_tasks_ids, 'first')

        if count_completed_tasks is None:
            raise self.retry(exc=Exception(
                'Имеются не завершенные задачи.'), countdown=10)

        if count_completed_tasks == 0:
            prepare_update.error_log(
                'Нет ни одной успешной задачи по отправке файла обновления. Подготовка к обновлению завершена с ошибкой.')
            return

        prepare_update.add_log(
            f'Файл обновления успешно отправлен на {count_completed_tasks} площадки.')
        execute_command_tasks_ids = prepare_update.create_tasks_to_prepare_update(
            list(send_file_tasks_ids.values()))

        if not execute_command_tasks_ids:
            prepare_update.error_log(
                'Задачи на подготовку к обновлению не были созданы.')
            return

        check_preparing_update.delay(
            prepare_update_id, execute_command_tasks_ids)
    except MaxRetriesExceededError as exc:
        prepare_update.error_log(
            'Не получилось отправить файл обновления. Подробности смотрите в логах фоновых SendFile.')
