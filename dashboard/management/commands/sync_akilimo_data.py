from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from dashboard.models import APIConfiguration, AkilimoParticipant, DataSyncLog
from dashboard.services import EiAMeliaAPIService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync Akilimo participant data from EiA MELIA API to new model structure'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=3000, help='Number of records per batch')
        parser.add_argument('--max-records', type=int, default=5000, help='Maximum total records to sync (for testing)')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without saving')
        parser.add_argument('--force', action='store_true', help='Update existing records')

    def handle(self, *args, **options):
        batch_size = options.get('batch_size')
        max_records = options.get('max_records')
        dry_run = options.get('dry_run')
        force_update = options.get('force')

        self.stdout.write(f'🚀 Starting Akilimo data sync...')
        self.stdout.write(f'   Batch size: {batch_size}')
        self.stdout.write(f'   Max records: {max_records}')
        self.stdout.write(f'   Dry run: {dry_run}')
        self.stdout.write(f'   Force update: {force_update}')

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

        self.stdout.write(f'✅ Using API: {api_config.name}')

        # Create sync log entry
        if not dry_run:
            sync_log = DataSyncLog.objects.create(
                sync_type='akilimo_participants',
                status='started'
            )

        try:
            # Initialize API service
            api_service = EiAMeliaAPIService(api_config.token)
            
            # Get first page to understand total records
            first_response = api_service.get_participants_by_usecase('akilimo', page=1, page_size=1)
            total_available = first_response.get('count', 0)
            
            self.stdout.write(f'📊 Total records available: {total_available:,}')
            
            if max_records:
                total_to_sync = min(max_records, total_available)
                self.stdout.write(f'📝 Will sync: {total_to_sync:,} records (limited)')
            else:
                total_to_sync = total_available
                self.stdout.write(f'📝 Will sync: {total_to_sync:,} records (all)')

            if dry_run:
                self.stdout.write(self.style.WARNING('🔍 DRY RUN - No data will be saved'))
                
                # Show sample of what would be processed
                sample_response = api_service.get_participants_by_usecase('akilimo', page=1, page_size=3)
                sample_data = sample_response.get('data', [])
                
                self.stdout.write(f'\n📋 Sample of {len(sample_data)} records that would be processed:')
                for i, record in enumerate(sample_data, 1):
                    self.stdout.write(f'   {i}. ID: {record.get("id")}, Name: {record.get("farmer_first_name")} {record.get("farmer_surname")}, Location: {record.get("admin_level1")}')
                
                return

            # Sync data in batches
            total_processed = 0
            total_created = 0
            total_updated = 0
            total_skipped = 0
            page = 1
            
            while total_processed < total_to_sync:
                # Calculate current batch size
                remaining = total_to_sync - total_processed
                current_batch_size = min(batch_size, remaining)
                
                self.stdout.write(f'\n📦 Processing batch {page} ({current_batch_size} records)...')
                
                try:
                    response = api_service.get_participants_by_usecase(
                        'akilimo', 
                        page=page, 
                        page_size=current_batch_size
                    )
                    
                    participants_data = response.get('data', [])
                    
                    if not participants_data:
                        self.stdout.write('⚠️  No more data available')
                        break
                    
                    # Process each participant in the batch
                    batch_created = 0
                    batch_updated = 0
                    batch_skipped = 0
                    
                    for participant_data in participants_data:
                        result = self.process_participant(participant_data, force_update)
                        if result == 'created':
                            batch_created += 1
                        elif result == 'updated':
                            batch_updated += 1
                        else:
                            batch_skipped += 1
                    
                    total_processed += len(participants_data)
                    total_created += batch_created
                    total_updated += batch_updated
                    total_skipped += batch_skipped
                    
                    self.stdout.write(f'   ✅ Batch complete: {batch_created} created, {batch_updated} updated, {batch_skipped} skipped')
                    self.stdout.write(f'   📈 Progress: {total_processed:,}/{total_to_sync:,} ({(total_processed/total_to_sync)*100:.1f}%)')
                    
                    page += 1
                    
                except Exception as e:
                    self.stdout.write(f'❌ Error processing batch {page}: {e}')
                    break
            
            # Update sync log
            sync_log.records_processed = total_processed
            sync_log.records_created = total_created
            sync_log.records_updated = total_updated
            sync_log.mark_completed('success')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Sync completed successfully!\n'
                    f'   📊 Records processed: {total_processed:,}\n'
                    f'   ✨ Records created: {total_created:,}\n'
                    f'   🔄 Records updated: {total_updated:,}\n'
                    f'   ⏭️  Records skipped: {total_skipped:,}'
                )
            )
            
        except Exception as e:
            logger.error(f"Data sync failed: {e}")
            if not dry_run:
                sync_log.mark_completed('failed', str(e))
            
            self.stdout.write(
                self.style.ERROR(f'❌ Sync failed: {e}')
            )

    def process_participant(self, participant_data, force_update=False):
        """Process a single participant record"""
        try:
            external_id = participant_data.get('id')
            if not external_id:
                return 'skipped'
            
            # Check if record already exists
            existing = AkilimoParticipant.objects.filter(external_id=external_id).first()
            
            if existing and not force_update:
                return 'skipped'
            
            # Parse dates
            event_date = None
            if participant_data.get('event_date'):
                try:
                    event_date = parse_date(participant_data['event_date'])
                except:
                    pass
            
            source_submitted_on = None
            if participant_data.get('source_submitted_on'):
                try:
                    source_submitted_on = parse_datetime(participant_data['source_submitted_on'])
                except:
                    pass
            
            api_created_on = None
            if participant_data.get('created_on'):
                try:
                    api_created_on = parse_datetime(participant_data['created_on'])
                except:
                    pass
            
            # Prepare data for model
            model_data = {
                'external_id': external_id,
                'source_id': participant_data.get('source_id'),
                'usecase': participant_data.get('usecase', 'AKILIMO'),
                'usecase_ref_id': participant_data.get('usecase_ref_id'),
                'usecase_stage': participant_data.get('usecase_stage'),
                'country': participant_data.get('country'),
                'event_date': event_date,
                'event_year': participant_data.get('event_year'),
                'event_month': participant_data.get('event_month'),
                'event_type': participant_data.get('event_type'),
                'event_format': participant_data.get('event_format'),
                'event_city': participant_data.get('event_city'),
                'event_venue': participant_data.get('event_venue'),
                'event_geopoint': participant_data.get('event_geopoint'),
                'farmer_first_name': participant_data.get('farmer_first_name'),
                'farmer_surname': participant_data.get('farmer_surname'),
                'farmer_gender': participant_data.get('farmer_gender'),
                'farmer_age': participant_data.get('farmer_age'),
                'age_category': participant_data.get('age_category'),
                'farmer_phone_no': participant_data.get('farmer_phone_no'),
                'farmer_own_phone': participant_data.get('farmer_own_phone'),
                'farmer_organization': participant_data.get('farmer_organization'),
                'farmer_position': participant_data.get('farmer_position'),
                'farmer_relationship': participant_data.get('farmer_relationship'),
                'participants_type': participant_data.get('participants_type'),
                'admin_level1': participant_data.get('admin_level1'),
                'admin_level2': participant_data.get('admin_level2'),
                'partner': participant_data.get('partner'),
                'org_first_name': participant_data.get('org_first_name'),
                'org_surname': participant_data.get('org_surname'),
                'org_phone_no': participant_data.get('org_phone_no'),
                'crop': participant_data.get('crop'),
                'thematic_area': participant_data.get('thematic_area'),
                'thematic_area_overall': participant_data.get('thematic_area_overall'),
                'data_source': participant_data.get('data_source'),
                'source_submitted_on': source_submitted_on,
                'api_created_on': api_created_on,
                'raw_data': participant_data
            }
            
            if existing:
                # Update existing record
                for key, value in model_data.items():
                    setattr(existing, key, value)
                existing.save()
                return 'updated'
            else:
                # Create new record
                AkilimoParticipant.objects.create(**model_data)
                return 'created'
                
        except Exception as e:
            logger.error(f"Error processing participant {participant_data.get('id', 'unknown')}: {e}")
            return 'skipped'