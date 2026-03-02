from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"
    verbose_name = "Sozlamalar"

    def ready(self):
        from . import signals
