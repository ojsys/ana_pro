from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import APIConfiguration, ParticipantRecord, DataSyncLog
from dashboard.services import AkilimoDataService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync participant data from EiA MELIA API'

    def add_arguments(self, parser):
        parser.add_argument('--max-pages', type=int, default=10, help='Maximum number of pages to fetch')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without saving')

    def handle(self, *args, **options):
        max_pages = options.get('max_pages')
        dry_run = options.get('dry_run')

        # Get API configuration
        try:
            api_config = APIConfiguration.objects.filter(is_active=True).first()
            if not api_config or not api_config.token:
                self.stdout.write(
                    self.style.ERROR('No active API configuration found. Please run setup_api command first.')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting API configuration: {e}')
            )
            return

        self.stdout.write(f'Using API: {api_config.name}')
        self.stdout.write(f'Base URL: {api_config.base_url}')

        # Create sync log entry
        if not dry_run:
            sync_log = DataSyncLog.objects.create(
                sync_type='participants',
                status='started'
            )

        try:
            # Initialize data service
            data_service = AkilimoDataService(api_config.token)
            
            self.stdout.write('Fetching participants data from API...')
            
            # Get all participants data
            participants_data = data_service.get_all_akilimo_participants()
            
            self.stdout.write(f'Found {len(participants_data)} participants')

            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved'))
                for i, participant in enumerate(participants_data[:5]):  # Show first 5
                    self.stdout.write(f'  {i+1}. ID: {participant.get("id", "N/A")}, Location: {participant.get("location", "N/A")}')
                if len(participants_data) > 5:
                    self.stdout.write(f'  ... and {len(participants_data) - 5} more')
                return

            created_count = 0
            updated_count = 0
            
            for i, participant_data in enumerate(participants_data):
                if (i + 1) % 50 == 0:
                    self.stdout.write(f'Processed {i + 1}/{len(participants_data)} participants...')
                
                external_id = participant_data.get('id', str(participant_data.get('participant_id', '')))
                
                if not external_id:
                    continue
                
                # Extract relevant fields from API response
                participant_record, created = ParticipantRecord.objects.update_or_create(
                    external_id=external_id,
                    defaults={
                        'gender': participant_data.get('gender'),
                        'age_group': participant_data.get('age_group'),
                        'location': participant_data.get('location'),
                        'state': participant_data.get('state'),
                        'lga': participant_data.get('lga'),
                        'event_type': participant_data.get('event_type'),
                        'facilitator': participant_data.get('facilitator'),
                        'farm_size': participant_data.get('farm_size'),
                        'previous_yield': participant_data.get('previous_yield'),
                        'expected_yield': participant_data.get('expected_yield'),
                        'raw_data': participant_data
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # Update sync log
            sync_log.records_processed = len(participants_data)
            sync_log.records_created = created_count
            sync_log.records_updated = updated_count
            sync_log.mark_completed('success')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Sync completed successfully!\n'
                    f'Records processed: {len(participants_data)}\n'
                    f'Records created: {created_count}\n'
                    f'Records updated: {updated_count}'
                )
            )
            
        except Exception as e:
            logger.error(f"Data sync failed: {e}")
            if not dry_run:
                sync_log.mark_completed('failed', str(e))
            
            self.stdout.write(
                self.style.ERROR(f'Sync failed: {e}')
            )