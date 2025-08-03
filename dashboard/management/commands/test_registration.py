from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse


class Command(BaseCommand):
    help = 'Test user registration functionality'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Testing user registration functionality...')
        
        # Create a test client
        client = Client()
        
        # Check if registration URL exists
        try:
            register_url = reverse('dashboard:register')
            self.stdout.write(f'✅ Registration URL found: {register_url}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Registration URL error: {e}')
            )
            return
        
        # Test GET request to registration page
        try:
            response = client.get(register_url)
            self.stdout.write(f'📝 GET registration response: {response.status_code}')
            if response.status_code == 200:
                self.stdout.write('✅ Registration page loads successfully')
            else:
                self.stdout.write(f'⚠️  Unexpected status code: {response.status_code}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ GET registration error: {e}')
            )
        
        # Check current user count
        initial_user_count = User.objects.count()
        self.stdout.write(f'📊 Initial user count: {initial_user_count}')
        
        # Test user registration with test data
        test_data = {
            'username': 'testuser123',
            'email': 'testuser123@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        }
        
        try:
            response = client.post(register_url, test_data)
            self.stdout.write(f'📝 POST registration response: {response.status_code}')
            
            if response.status_code == 302:
                self.stdout.write(f'↪️  Registration redirects to: {response.url}')
                
                # Check if user was created
                final_user_count = User.objects.count()
                if final_user_count > initial_user_count:
                    self.stdout.write('✅ User was created successfully')
                    
                    # Check if user can be found
                    try:
                        created_user = User.objects.get(username='testuser123')
                        self.stdout.write(f'✅ Created user: {created_user.username} ({created_user.email})')
                        
                        # Clean up - delete test user
                        created_user.delete()
                        self.stdout.write('🧹 Test user cleaned up')
                        
                    except User.DoesNotExist:
                        self.stdout.write('❌ User was not found after creation')
                        
                else:
                    self.stdout.write('❌ User count did not increase')
                    
            elif response.status_code == 200:
                self.stdout.write('⚠️  Registration form returned with errors')
                if hasattr(response, 'context') and 'form' in response.context:
                    form_errors = response.context['form'].errors
                    self.stdout.write(f'📋 Form errors: {form_errors}')
            else:
                self.stdout.write(f'❌ Unexpected response status: {response.status_code}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ POST registration error: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Registration functionality test completed!')
        )