from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse


class Command(BaseCommand):
    help = 'Test logout functionality'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Testing logout functionality...')
        
        # Create a test client
        client = Client()
        
        # Check if logout URL exists
        try:
            logout_url = reverse('dashboard:logout')
            self.stdout.write(f'✅ Logout URL found: {logout_url}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Logout URL error: {e}')
            )
            return
        
        # Test GET request to logout
        try:
            response = client.get(logout_url)
            self.stdout.write(f'📝 GET logout response: {response.status_code}')
            if response.status_code == 302:
                self.stdout.write(f'↪️  Redirects to: {response.url}')
            elif response.status_code == 200:
                self.stdout.write('✅ 200 OK - Debug response:')
                if hasattr(response, 'content'):
                    content = response.content.decode('utf-8')[:500]
                    self.stdout.write(f'📄 Response content: {content}...')
            elif response.status_code == 400:
                self.stdout.write('⚠️  400 Bad Request - checking response content...')
                if hasattr(response, 'content'):
                    content = response.content.decode('utf-8')[:200]
                    self.stdout.write(f'📄 Response content: {content}...')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ GET logout error: {e}')
            )
        
        # Test POST request to logout
        try:
            response = client.post(logout_url)
            self.stdout.write(f'📝 POST logout response: {response.status_code}')
            if response.status_code == 302:
                self.stdout.write(f'↪️  Redirects to: {response.url}')
            elif response.status_code == 400:
                self.stdout.write('⚠️  400 Bad Request - checking response content...')
                if hasattr(response, 'content'):
                    content = response.content.decode('utf-8')[:200]
                    self.stdout.write(f'📄 Response content: {content}...')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ POST logout error: {e}')
            )
        
        # Test admin logout
        try:
            admin_logout_url = '/admin/logout/'
            response = client.get(admin_logout_url)
            self.stdout.write(f'📝 Admin logout response: {response.status_code}')
            if response.status_code == 302:
                self.stdout.write(f'↪️  Admin redirects to: {response.url}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Admin logout error: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Logout functionality test completed!')
        )