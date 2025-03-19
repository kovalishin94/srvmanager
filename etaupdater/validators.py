import tarfile
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

path_validator = RegexValidator(
    regex=r'^(/[a-zA-Z0-9._\-/]+)$',
    message='Путь должен начинаться с / и содержать только буквы, цифры, точки, подчеркивания, дефисы и слеши.',
    code='invalid_path'
)


def update_file_validator(file):
    check_result = 0
    targets = ("./version.env", "./jetalon.env")
    with tarfile.open(fileobj=file, mode='r:gz') as archive:
        members = archive.getmembers()
        for member in members:
            if member.path == "./stand.env":
                raise ValidationError(
                    'Файл stand.env не должен присутствовать в архиве.')
            if member.path in targets:
                check_result += 1
    if check_result != len(targets):
        raise ValidationError('Файл обновления не прошел валидацию.')
