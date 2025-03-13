from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed

from .models import ExecuteCommand
from .tasks import run_operation


@receiver(m2m_changed, sender=ExecuteCommand.hosts.through)
def execute_command_post_save(sender, instance: ExecuteCommand, action, **kwargs):
    if action != "post_add" or instance.log.keys():
        return

    run_operation.delay(instance.id, 'execute-command')
