from django.dispatch import receiver
from django.db.models.signals import post_save

from ops.models import ExecuteCommand
from .models import EtalonInstance
from .tasks import check_execute_command


@receiver(post_save, sender=EtalonInstance)
def etalon_instance_post_save(sender, instance: EtalonInstance, created, **kwargs):
    if not created:
        return

    execute_command = ExecuteCommand.objects.create(
        command=[
            f'cat {instance.path_to_instance}/stand.env',
            f'cat {instance.path_to_instance}/version.env'
        ],
        protocol='ssh',
        created_by=instance.created_by
    )
    execute_command.hosts.add(instance.host)
    check_execute_command.apply_async(
        args=[execute_command.id, instance.id], countdown=10)
