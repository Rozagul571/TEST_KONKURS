# django_app/__init__.py
default_app_config = 'django_app.core.apps.CoreConfig'

# django_app/core/apps.py
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_app.core'

    def ready(self):
        import django_app.core.signals