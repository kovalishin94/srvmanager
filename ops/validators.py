from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_command(value):
    if not isinstance(value, list):
        raise ValidationError('Команды должны идти списком.')

    for command in value:
        if not isinstance(command, str):
            raise ValidationError('Все элементы списка должны быть строками.')


path_validator = RegexValidator(
    regex=r'^(/[a-zA-Z0-9._\-/]+)$',
    message='Путь должен начинаться с / и содержать только буквы, цифры, точки, подчеркивания, дефисы и слеши.',
    code='invalid_path'
)
