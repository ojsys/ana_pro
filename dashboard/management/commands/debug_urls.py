from django.core.management.base import BaseCommand
from django.urls import reverse
from django.conf import settings


class Command(BaseCommand):
    help = 'Debug URL configuration and settings'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Debugging URL and Settings Configuration...')
        
        # Check URL resolution
        try:
            logout_url = reverse('dashboard:logout')
            self.stdout.write(f'✅ dashboard:logout resolves to: {logout_url}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ dashboard:logout resolution error: {e}')
            )
        
        # Check settings
        self.stdout.write('\n📋 Important Settings:')
        self.stdout.write(f'DEBUG: {settings.DEBUG}')
        self.stdout.write(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
        
        # Check middleware
        self.stdout.write('\n🔧 Middleware:')
        for i, middleware in enumerate(settings.MIDDLEWARE, 1):
            self.stdout.write(f'{i}. {middleware}')
        
        # Check if there are any custom error handlers
        if hasattr(settings, 'handler400'):
            self.stdout.write(f'\n⚠️  Custom 400 handler: {settings.handler400}')
        else:
            self.stdout.write('\n✅ No custom 400 handler')
        
        # Check CSRF settings
        csrf_settings = [
            'CSRF_COOKIE_SECURE',
            'CSRF_COOKIE_HTTPONLY', 
            'CSRF_COOKIE_SAMESITE',
            'CSRF_TRUSTED_ORIGINS'
        ]
        
        self.stdout.write('\n🔒 CSRF Settings:')
        for setting in csrf_settings:
            value = getattr(settings, setting, 'Not set')
            self.stdout.write(f'{setting}: {value}')
        
        self.stdout.write('\n🎉 Debug completed!')