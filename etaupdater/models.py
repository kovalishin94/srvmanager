import time
import os
import tarfile
import requests

from urllib.parse import urljoin
from datetime import datetime
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.conf import settings

from core.models import Host
from ops.models import ExecuteCommand, BaseOperation, SendFile
from .validators import path_validator, update_file_validator

class UnhealthException(Exception):
    pass


class EtalonInstance(models.Model):
    """
    Площадка Эталона 3
    """
    DOCKER_COMMAND_CHOICES = (
        ('docker-compose', 'Old'),
        ('docker compose', 'New'),
    )

    url = models.URLField(editable=False, blank=True) # URL площадки берется из .env файла лежащего в path_to_instance
    path_to_instance = models.TextField(validators=[path_validator]) # Путь на хосте, где лежит площадка Эталона
    host = models.ForeignKey(
        Host, on_delete=models.CASCADE, related_name='etalon_instances') # Хост, на котором расположена площадка
    version = models.CharField(max_length=100, editable=False, blank=True) # Версия Эталона, берется из .env файла лежащего в path_to_instance
    tag = models.CharField(max_length=20, editable=False, blank=True) # Тег Эталона, берется из .env файла лежащего в path_to_instance
    stand = models.CharField(max_length=255, editable=False, blank=True) # Стенд Эталона, берется из .env файла лежащего в path_to_instance
    is_valid = models.BooleanField(editable=False, default=False) # Флаг валидности площадки
    ready_to_update = models.BooleanField(editable=False, default=False) # Флаг готовности площадки к обновлению
    docker_command = models.CharField(choices=DOCKER_COMMAND_CHOICES, default='docker compose', max_length=255) # Команда для запуска Docker, необъодима из-за наличия старых версий Docker Compose
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, editable=False) # Пользователь, создавший площадку
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def apply_params(self, stdout: str) -> None:
        """
        Получаем на вход stdout команды cat .env и парсим его, чтобы заполнить
        поля url, version, tag, stand
        """
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
        """
        Создаем задачу на выполнение команды cat .env для получения параметров площадки
        """
        execute_command = ExecuteCommand.objects.create(
            command=[f'cat {self.path_to_instance}/.env'],
            protocol='ssh',
            sudo=True,
            created_by=self.created_by,
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
                            ]) # Файл архива обновления в формате .tar.gz с валидацией
    version = models.CharField(max_length=100, editable=False) # Версия Эталона, берется из файла version.env внутри архива обновления
    tag = models.CharField(max_length=20, editable=False) # Тег Эталона, берется из файла version.env внутри архива обновления
    loaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def parse_config(config: str) -> dict:
        """
        Парсим конфиг в формате KEY=VALUE
        """
        variables = {}
        for line in config.splitlines():
            if line.strip() and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                variables[key.strip()] = value.strip()
        return variables

    def set_version(self):
        """
        Извлекаем из архива обновления файл version.env и парсим его, чтобы заполнить
        поля version и tag
        """
        with tarfile.open(self.file.path, 'r:gz') as archive:
            member = archive.getmember('./version.env')
            version_env = archive.extractfile(member)
            content = version_env.read().decode('utf-8')
            variables = self.parse_config(content)
            self.version, self.tag = variables.get(
                'BRANCH'), variables.get('TAG')
            self.save()

    def save(self, *args, **kwargs):
        """
        Переопределяем метод save, чтобы при создании нового объекта
        проставить имя файла с текущей датой и временем для уникальности наименования.
        Проверяем, что объект создается впервые с помощью self._state.adding.
        """
        if self._state.adding:
            self.file.name = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}_' + \
                self.file.name
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Переопределяем метод delete, чтобы при удалении объекта
        удалить файл из файловой системы.
        """
        if self.file and os.path.exists(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)

class EtalonUpdate(BaseOperation):
    """
    Операция по обновлению площадок Эталона 3 (EtalonInstance) с помощью файла обновления.

    Атрибуты:
        instances (ManyToMany[EtalonInstance]): Площадки эталона, которые будут обновлены.
        update_file (ForeignKey[UpdateFile | None]): Файл обновления с ресурсами (может быть None),
            при удалении связанного объекта UpdateFile здесь устанавливается значение NULL.

    """
    instances = models.ManyToManyField(EtalonInstance)
    update_file = models.ForeignKey(UpdateFile, on_delete=models.SET_NULL, null=True)

    def run(self, host_id: int) -> bool:
        """
        Запускает процесс обновления площадок Эталона на указанном хосте.
        При неудаче на любом этапе процесс прерывается и возвращается False, это означает, 
        что воркер работающий на данном хосте дальше не пойдет и оставшиеся площадки обновлены не будут.
        """

        # Получаем хост и связанные площадки
        host = Host.objects.get(id=host_id)
        instances = self.instances.filter(host=host, is_valid=True)

        # Создаем задачу на отправку файла обновления на хост и следим за ее выполнением, если неудачно - выходим
        if not self.__send_file_to_host(host):
            return False

        # Для каждой площадки создаем задачу на выполнение команд по обновлению и следим за ее выполнением
        # Если на каком-то этапе неудачно - выходим
        for instance in instances:
            if not self.__process_update(instance):
                return False
            if not self.__check_health(instance, f"[{instance.stand}] health check"):
                return False
            instance.version = self.update_file.version
            instance.tag = self.update_file.tag
            instance.save(update_fields=["version", "tag", "updated_at"])

        return True

    def __wait_operation(self, op: BaseOperation, ctx: str) -> bool:
        """
        Универсальный метод ожидания завершения операции. С помощью переменных
        settings.ETALON_UPDATE_OPERATION_TIMEOUT и settings.ETALON_UPDATE_OPERATION_WAIT_INTERVAL
        можно настроить таймаут ожидания и интервал между проверками статуса операции.
        """
        started = datetime.now()
        while True:
            op.refresh_from_db()
            if op.status == 'completed':
                self.add_log(f"{ctx}: успешно")
                return True
            if op.status == 'error':
                self.add_log(f"{ctx}: завершилось ошибкой")
                return False
            if (datetime.now() - started).seconds > settings.ETALON_UPDATE_OPERATION_TIMEOUT:
                self.add_log(f"{ctx}: завершилось по таймауту")
                return False
            time.sleep(settings.ETALON_UPDATE_OPERATION_WAIT_INTERVAL)

    def __send_file_to_host(self, host: Host) -> bool:
        """
        Создает задачу на отправку файла обновления на указанный хост.
        """
        send_file = SendFile.objects.create(
            created_by=self.created_by,
            protocol='sftp',
            local_path=self.update_file.file.path,
            target_path='/tmp/update_jetalon.tar.gz'
        )
        send_file.hosts.add(host)
        return self.__wait_operation(send_file, f"[{host.ip}] отправка файла")

    def __process_update(self, instance: EtalonInstance) -> bool:
        """
        Создает задачу на выполнение команд по обновлению площадки Эталона.
        Распаковывает архив обновления, запускает скрипт prepare_update.sh и перезапускает контейнеры Docker.
        """
        fp = "/tmp/update_jetalon.tar.gz"
        path = instance.path_to_instance
        execute_command = ExecuteCommand.objects.create(
            created_by=self.created_by,
            protocol='ssh',
            command=[
                f'tar -xzf {fp} -C {path}',
                f'cd {path} && ./prepare_update.sh',
                f'cd {path} && {instance.docker_command} up -d'
            ],
            sudo=True
        )
        execute_command.hosts.add(instance.host)

        return self.__wait_operation(execute_command, f"[{instance.stand}] выполнение команд обновления")
    
    def __check_health(self, instance: EtalonInstance, ctx: str) -> bool:
        """
        Проверяет здоровье площадки Эталона, опрашивая эндпоинт /csp/sou/rest/dev/main/actuator/health
        до тех пор, пока не получит статус "UP" или не истечет таймаут.
        """
        url = urljoin(instance.url, "/csp/sou/rest/dev/main/actuator/health")
        started = datetime.now()
        while True:
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                if response.json().get("status") != "UP":
                    raise UnhealthException("Статус площадки отличен от UP")
                self.add_log(f"{ctx}: успешно")
                return True
            except Exception as e:
                if (datetime.now() - started).seconds > settings.ETALON_UPDATE_OPERATION_TIMEOUT:
                    self.add_log(f"{ctx}: завершилось по таймауту")
                    return False
                self.add_log(f"{ctx}: {e}. Следующая попытка через {settings.ETALON_UPDATE_OPERATION_WAIT_INTERVAL}")
                time.sleep(settings.ETALON_UPDATE_OPERATION_WAIT_INTERVAL)