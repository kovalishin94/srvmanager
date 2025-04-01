from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed

from .models import EtalonInstance, UpdateFile, PrepareUpdate
from .tasks import check_execute_command, check_sending_files


@receiver(post_save, sender=EtalonInstance)
def etalon_instance_post_save(sender, instance: EtalonInstance, created, **kwargs):
    if not created:
        return

    execute_command = instance.create_execute_command()

    check_execute_command.apply_async(
        args=[execute_command.id, instance.id], countdown=10)


@receiver(post_save, sender=UpdateFile)
def update_file_post_save(sender, instance: UpdateFile, created, **kwargs):
    if not created:
        return

    instance.set_version()


@receiver(m2m_changed, sender=PrepareUpdate.instances.through)
def prepare_update_post_save(sender, instance: PrepareUpdate, action, **kwargs):
    if action != "post_add" or instance.log.keys():
        return

    instance.status = 'progress'
    instance.add_log('Запуск подготовки обновления площадок Эталона.')

    send_file_tasks_ids = instance.create_tasks_to_send_file()

    if not send_file_tasks_ids:
        instance.status = 'error'
        instance.add_log(
            'Не создалось ни одной задачи по отправке файла обновления. Статус обновления - ошибка.')
        return

    check_sending_files.apply_async(
        args=[instance.id, send_file_tasks_ids],
        countdown=10
    )
