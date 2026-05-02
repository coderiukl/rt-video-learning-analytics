from django.apps import AppConfig


import os

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'

    def ready(self):
        # Chỉ chạy scheduler trên main process của runserver để tránh bị chạy 2 lần
        if os.environ.get('RUN_MAIN') == 'true':
            from . import scheduler
            scheduler.start()
