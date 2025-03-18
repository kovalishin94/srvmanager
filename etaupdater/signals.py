from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import EtalonInstance
from .tasks import check_execute_command


@receiver(post_save, sender=EtalonInstance)
def etalon_instance_post_save(sender, instance: EtalonInstance, created, **kwargs):
    if not created:
        return

    execute_command = instance.create_execute_command()

    check_execute_command.apply_async(
        args=[execute_command.id, instance.id], countdown=10)
