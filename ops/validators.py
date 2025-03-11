from django.core.exceptions import ValidationError


def validate_command(value):
    if not isinstance(value, list):
        raise ValidationError('Команды должны идти списком.')

    for command in value:
        if not isinstance(command, str):
            raise ValidationError('Все элементы списка должны быть строками.')
