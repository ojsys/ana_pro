def site_settings(request):
    """Make SiteSettings available in every template globally."""
    try:
        from .models import SiteSettings
        settings_obj = SiteSettings.objects.first()
        return {'site_settings': settings_obj}
    except Exception:
        return {'site_settings': None}
