from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed

from .models import EtalonInstance, UpdateFile, EtalonUpdate
from .tasks import check_execute_command, run_etalon_update


@receiver(post_save, sender=EtalonInstance)
def etalon_instance_post_save(sender, instance: EtalonInstance, created, **kwargs):
    """
    При создании новой площадки Эталона создаем задачу на cat .env для парсинга
    и сохранения переменных окружения.
    """
    _ = sender, kwargs
    if not created:
        return
    execute_command = instance.create_execute_command()

    check_execute_command.apply_async(
        args=[execute_command.id, instance.id], countdown=10)


@receiver(post_save, sender=UpdateFile)
def update_file_post_save(sender, instance: UpdateFile, created, **kwargs):
    """
    При создании нового файла обновления парсим его и валидируем.
    """
    _ = sender, kwargs
    if not created:
        return

    instance.set_version()

@receiver(m2m_changed, sender=EtalonUpdate.instances.through)
def etalon_update_post_save(sender, instance: EtalonUpdate, action, **kwargs):
    """
    При добавлении площадок в обновление запускаем процесс обновления.
    Имеено при добавлении площадок в связь, а не при создании операции,
    т.к. площадки связанные ManyToMany добавляются позже чем сам объект.
    """
    _ = sender, kwargs
    if action != "post_add" or instance.log:
        return
    run_etalon_update.delay(instance.id)