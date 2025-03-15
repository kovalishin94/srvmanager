from django.core.validators import RegexValidator

path_validator = RegexValidator(
    regex=r'^(/[a-zA-Z0-9._\-/]+)$',
    message='Путь должен начинаться с / и содержать только буквы, цифры, точки, подчеркивания, дефисы и слеши.',
    code='invalid_path'
)
