from django.apps import AppConfig


class OpsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ops'

    def ready(self):
        import ops.signals
        _ = ops.signals
