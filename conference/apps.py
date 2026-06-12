from django.apps import AppConfig


class ConferenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'conference'
    verbose_name = 'AKILIMO Conference'

    def ready(self):
        """Import signal handlers when Django starts"""
        import conference.signals  # noqa
