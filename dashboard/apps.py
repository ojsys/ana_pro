from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    verbose_name = 'AKILIMO Nigeria Dashboard'

    def ready(self):
        """Import signal handlers when Django starts"""
        import dashboard.signals  # noqa
