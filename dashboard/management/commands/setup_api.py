from django.core.management.base import BaseCommand
from dashboard.models import APIConfiguration

class Command(BaseCommand):
    help = 'Setup API configuration for EiA MELIA API'

    def add_arguments(self, parser):
        parser.add_argument('--token', type=str, help='API token for EiA MELIA API')
        parser.add_argument('--name', type=str, default='EiA MELIA API', help='Configuration name')
        parser.add_argument('--url', type=str, default='https://my.eia.cgiar.org/api/v1/melia', help='API base URL')

    def handle(self, *args, **options):
        token = options.get('token')
        
        if not token:
            self.stdout.write(
                self.style.ERROR('Please provide an API token using --token argument')
            )
            return

        name = options.get('name')
        base_url = options.get('url')

        # Create or update API configuration
        config, created = APIConfiguration.objects.update_or_create(
            name=name,
            defaults={
                'token': token,
                'base_url': base_url,
                'is_active': True
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created API configuration: {name}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated API configuration: {name}')
            )

        self.stdout.write(f'Base URL: {base_url}')
        self.stdout.write(f'Token: {token[:10]}...')
        self.stdout.write(
            'You can now use the dashboard to sync data from the EiA MELIA API'
        )