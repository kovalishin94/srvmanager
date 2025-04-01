import os
import tarfile

from uuid import UUID
from typing import Dict, Callable, Tuple, Type
from datetime import datetime
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.conf import settings

from core.models import Host
from ops.models import ExecuteCommand, BaseOperation, SendFile
from .validators import path_validator, update_file_validator


class EtalonInstance(models.Model):
    """
    Площадка Эталона 3
    """
    url = models.URLField(editable=False, blank=True)
    path_to_instance = models.TextField(validators=[path_validator])
    host = models.ForeignKey(
        Host, on_delete=models.CASCADE, related_name='etalon_instances')
    version = models.CharField(max_length=100, editable=False, blank=True)
    tag = models.CharField(max_length=20, editable=False, blank=True)
    stand = models.CharField(max_length=255, editable=False, blank=True)
    is_valid = models.BooleanField(editable=False, default=False)
    ready_to_update = models.BooleanField(editable=False, default=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def apply_params(self, stdout: str) -> None:
        params = UpdateFile.parse_config(stdout)

        stand = params.get('STAND')
        version = params.get('BRANCH')
        tag = params.get('TAG')
        url = params.get('EXTERNAL_HOST_ADDRESS')

        if None in (stand, version, tag, url):
            self.is_valid = False
            self.save()
            return

        self.url = url
        self.version = version
        self.tag = tag
        self.stand = stand
        self.is_valid = True
        self.save()

    def create_execute_command(self) -> ExecuteCommand:
        execute_command = ExecuteCommand.objects.create(
            command=[f'cat {self.path_to_instance}/.env'],
            protocol='ssh',
            created_by=self.created_by
        )
        execute_command.hosts.add(self.host)
        return execute_command


class UpdateFile(models.Model):
    """
    Файл обновления Эталона 3
    """
    file = models.FileField(upload_to='updates/%Y/%m/',
                            validators=[
                                FileExtensionValidator(
                                    allowed_extensions=['gz']),
                                update_file_validator
                            ])
    version = models.CharField(max_length=100, editable=False)
    tag = models.CharField(max_length=20, editable=False)
    loaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def parse_config(config: str) -> dict:
        variables = {}
        for line in config.splitlines():
            if line.strip() and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                variables[key.strip()] = value.strip()
        return variables

    def set_version(self):
        with tarfile.open(self.file.path, 'r:gz') as archive:
            member = archive.getmember('./version.env')
            version_env = archive.extractfile(member)
            content = version_env.read().decode('utf-8')
            variables = self.parse_config(content)
            self.version, self.tag = variables.get(
                'BRANCH'), variables.get('TAG')
            self.save()

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.file.name = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}_' + \
                self.file.name
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file and os.path.exists(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)


# noinspection GrazieInspection
class PrepareUpdate(BaseOperation):
    """
    Операция подготовки к обновлению площадки Эталона 3. Состоит из нескольких этапов:

    1) Отправка файла обновления UpdateFile на площадки эталона, путем создания экземпляров класса SendFile.
    2) Выполнение команды разархивирования и запуск ./prepare_update.sh путем создания экземпляров класса ExecuteCommand.
    3) Загрузка образов docker путем выполнения команды docker compose pull -q, также созданием ExecuteCommand.

    Логика построена таким образом, что при ошибках на одном из этапов PrepareUpdate - в дальнейших этапах отбрасываются только
    площадки с ошибками.
    """
    instances = models.ManyToManyField(EtalonInstance)
    update_file = models.ForeignKey(
        UpdateFile, on_delete=models.SET_NULL, null=True)

    def get_stage_conf(self, stage: str) -> dict:
        fn_by_stage = {
            'first': {
                'next_fn': self.create_tasks_to_prepare_update,
                'next_stage': 'second',
                'stage_full_name': 'отправки файлов обновления',
                'operation_type': SendFile,
                'check': lambda *a: True
            },
            'second': {
                'next_fn': self.create_task_to_pull_images,
                'next_stage': 'third',
                'stage_full_name': 'разархивирования и prepare_update.sh',
                'operation_type': ExecuteCommand,
                'check': self.check_env
            },
            'third': {
                'next_fn': self.finish,
                'next_stage': None,
                'stage_full_name': 'скачивания докер образов',
                'operation_type': ExecuteCommand,
                'check': self.check_docker_images
            }
        }
        return fn_by_stage[stage]

    def check_operations(self, ids: dict, stage: str) -> int | None:
        stage_conf = self.get_stage_conf(stage)
        operation_type = stage_conf['operation_type']
        check_function = stage_conf['check']
        operations = operation_type.objects.filter(id__in=ids)
        count_completed_tasks = 0
        for operation in operations:
            if operation.status == 'completed':
                if not check_function(operation):
                    ids.pop(operation.id)
                    continue
                count_completed_tasks += 1
                continue
            if operation.status == 'error':
                removed_instance_id = ids.pop(str(operation.id))
                self.add_log(
                    f'''Есть ошибки при выполнении операции с Id - {operation.id}. 
                    Для инстанса Эталона с Id - {removed_instance_id} подготовка к обновлению окончена неудачно.''')
                continue
            return None
        return count_completed_tasks

    def check_docker_images(self, operation: ExecuteCommand) -> bool | None:
        """
        Проверка количества докер образов с новой версией.
        """
        if not isinstance(operation, ExecuteCommand):
            return None

        stdout = list(operation.stdout.values())

        if not stdout:
            self.add_log(
                f'Не корректный вывод docker images. Id операции - {operation.id}')
            return False
        if int(stdout[-1]) != settings.ETALON_DOCKER_IMAGES_COUNT:
            self.add_log(
                f'Количество докер образов с новой версией не соответствует. Id операции - {operation.id}')
            return False
        return True

    def check_env(self, operation: ExecuteCommand) -> bool | None:
        """
        Проверка вывода .env после выполнения ./prepare_update.sh, с целью убедиться в соответствии
        версией и тега файлу обновления UpdateFile.
        """
        if not isinstance(operation, ExecuteCommand):
            return None

        stdout = list(operation.stdout.values())

        if len(stdout) != 3:
            self.add_log(
                f'Не корректный вывод файла .env. Id операции - {operation.id}')
            return False

        env_conf = UpdateFile.parse_config(stdout[-1])
        if self.update_file.version != env_conf.get('BRANCH'):
            self.add_log(
                f'Версия файла обновления и версия в .env не соответствуют. Смотрите фоновую {operation.id}.')
            return False

        if self.update_file.tag != env_conf.get('TAG'):
            self.add_log(
                f'Тег файла обновления и тег в .env не соответствуют. Смотрите фоновую {operation.id}.')
            return False

        return True

    def create_tasks_to_send_file(self) -> Dict[str, UUID]:
        """
        Первый этап PrepareUpdate - отправка файла обновления в директории площадок Эталона.
        """
        self.add_log('Начинается создание задач на отправку файла обновления.')
        result = {}
        for instance in self.instances.all():
            if not instance.is_valid:
                self.add_log(
                    f'Обнаружен невалидный EtalonInstance. id - {instance.id}. Он будет удален из задачи.')
                self.instances.remove(instance)
                continue
            send_file = SendFile.objects.create(
                created_by=self.created_by,
                protocol='sftp',
                local_path=self.update_file.file.path,
                target_path=f'{instance.path_to_instance}/update_jetalon.tar.gz'
            )
            send_file.hosts.add(instance.host)
            result[str(send_file.id)] = instance.id

        if result:
            self.add_log(
                f'Успешно создано {len(result)} задач на отправку файла обновления.')

        return result

    def create_tasks_to_prepare_update(self, instance_ids: list) -> Dict[str, UUID]:
        """
        Второй этап PrepareUpdate - разархивирование файла обновления в директории Эталона 3,
        выполнение ./prepare_update.sh и проверка корректности выполнения команд.
        """
        self.add_log(
            'Начинается создание задач на выполнение команд подготовки к обновлению.')
        result = {}
        instances = EtalonInstance.objects.filter(id__in=instance_ids)

        for instance in instances:
            execute_command = ExecuteCommand.objects.create(
                created_by=self.created_by,
                protocol='ssh',
                command=[f'cd {instance.path_to_instance}; tar xvf update_jetalon.tar.gz',
                         f'cd {instance.path_to_instance}; ./prepare_update.sh',
                         f'cat {instance.path_to_instance}/.env']
            )
            execute_command.hosts.add(instance.host)
            result[str(execute_command.id)] = instance.id
        if result:
            self.add_log(
                f'Успешно создано {len(result)} задач на подготовку к обновлению.')

        return result

    def create_task_to_pull_images(self, instance_ids: list) -> Dict[str, UUID]:
        """
        Третий этап PrepareUpdate - pulling docker образов и проверка их количества.
        """
        self.add_log(
            'Начинается создание задач на выполнение команды docker pull.')
        result = {}
        instances = EtalonInstance.objects.filter(
            id__in=instance_ids).distinct('host')

        for instance in instances:
            execute_command = ExecuteCommand.objects.create(
                created_by=self.created_by,
                protocol='ssh',
                command=[
                    f'cd {instance.path_to_instance}; docker compose pull -q',
                    f'docker images | grep {self.update_file.version} | grep {self.update_file.tag} | wc -l'
                ]
            )
            execute_command.hosts.add(instance.host)
            result[str(execute_command.id)] = instance.id

        if result:
            self.add_log(
                f'Успешно создано {len(result)} задач на скачивание докер образов.')

        return result

    def finish(self, instance_ids: list):
        instances = EtalonInstance.objects.filter(id__in=instance_ids)
        for instance in instances:
            instance.ready_to_update = True
            instance.save()

        self.status = 'completed'
        self.add_log('Подготовка к обновлению завершена.')
