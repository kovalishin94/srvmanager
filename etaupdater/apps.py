from django.apps import AppConfig


class EtaupdaterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'etaupdater'

    def ready(self):
        import etaupdater.signals
        _ = etaupdater.signals
