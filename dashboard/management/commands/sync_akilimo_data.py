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
        parser.add_argument('--batch-size', type=int, default=50, help='Number of records per API page/batch')
        parser.add_argument('--max-records', type=int, default=None,
                            help='Maximum total records to sync (omit to sync ALL available records)')
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

        self.stdout.write(f'✅ Using API: {api_config.name} ({api_config.base_url})')

        # Create sync log entry
        if not dry_run:
            sync_log = DataSyncLog.objects.create(
                sync_type='akilimo_participants',
                status='started'
            )

        try:
            # Initialize API service — pass base_url from database config
            api_service = EiAMeliaAPIService(api_config.token, base_url=api_config.base_url)
            
            # Get first page to understand total records
            first_response = api_service.get_participants_by_usecase('akilimo', page=1, page_size=1)
            total_available = first_response.get('count', 0)
            
            self.stdout.write(f'📊 Total records available: {total_available:,}')
            
            if max_records is not None:
                total_to_sync = min(max_records, total_available)
                self.stdout.write(f'📝 Will sync: {total_to_sync:,} records (capped by --max-records)')
            else:
                total_to_sync = None  # unlimited — stop when API has no more pages
                self.stdout.write(f'📝 Will sync: all {total_available:,} available records')

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
            has_next = True

            while has_next:
                # Stop early if a record cap was requested
                if total_to_sync is not None and total_processed >= total_to_sync:
                    break

                # Shrink last batch to honour the cap exactly
                if total_to_sync is not None:
                    remaining = total_to_sync - total_processed
                    current_batch_size = min(batch_size, remaining)
                else:
                    current_batch_size = batch_size

                self.stdout.write(f'\n📦 Processing batch {page} ({current_batch_size} records)...')

                # Retry up to 3 times on transient errors (502, 503, timeout)
                max_retries = 3
                retry_delay = 5  # seconds between retries
                response = None

                for attempt in range(1, max_retries + 1):
                    try:
                        response = api_service.get_participants_by_usecase(
                            'akilimo',
                            page=page,
                            page_size=current_batch_size
                        )
                        break  # success — exit retry loop
                    except Exception as e:
                        self.stdout.write(
                            f'   ⚠️  Attempt {attempt}/{max_retries} failed: {e}'
                        )
                        if attempt < max_retries:
                            import time
                            self.stdout.write(f'   ⏳ Retrying in {retry_delay}s...')
                            time.sleep(retry_delay)
                            retry_delay *= 2  # exponential back-off
                        else:
                            self.stdout.write(f'❌ Batch {page} failed after {max_retries} attempts — stopping.')
                            has_next = False

                if response is None:
                    break

                try:
                    participants_data = response.get('data', [])

                    if not participants_data:
                        self.stdout.write('⚠️  No more data available')
                        break

                    # Check if the API signals more pages
                    has_next = bool(response.get('next'))

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

                    progress_denom = total_to_sync if total_to_sync else total_available
                    pct = (total_processed / progress_denom * 100) if progress_denom else 0
                    self.stdout.write(
                        f'   ✅ Batch complete: {batch_created} created, {batch_updated} updated, {batch_skipped} skipped'
                    )
                    self.stdout.write(
                        f'   📈 Progress: {total_processed:,}/{progress_denom:,} ({pct:.1f}%)'
                    )

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
            
            def s(val, max_len=None):
                """Convert to string and optionally truncate for MySQL VARCHAR limits."""
                if val is None:
                    return val
                val = str(val)
                return val[:max_len] if max_len else val

            # Prepare data for model
            model_data = {
                'external_id': external_id,
                'source_id': s(participant_data.get('source_id'), 100),
                'usecase': s(participant_data.get('usecase', 'AKILIMO'), 50),
                'usecase_ref_id': s(participant_data.get('usecase_ref_id'), 50),
                'usecase_stage': s(participant_data.get('usecase_stage'), 50),
                'country': s(participant_data.get('country'), 50),
                'event_date': event_date,
                'event_year': participant_data.get('event_year'),
                'event_month': participant_data.get('event_month'),
                'event_type': s(participant_data.get('event_type'), 100),
                'event_format': s(participant_data.get('event_format'), 50),
                'event_city': s(participant_data.get('event_city'), 500),
                'event_venue': s(participant_data.get('event_venue'), 500),
                'event_geopoint': s(participant_data.get('event_geopoint'), 100),
                'farmer_first_name': s(participant_data.get('farmer_first_name'), 100),
                'farmer_surname': s(participant_data.get('farmer_surname'), 100),
                'farmer_gender': s(participant_data.get('farmer_gender'), 20),
                'farmer_age': s(participant_data.get('farmer_age'), 10),
                'age_category': s(participant_data.get('age_category'), 20),
                'farmer_phone_no': s(participant_data.get('farmer_phone_no'), 20),
                'farmer_own_phone': s(participant_data.get('farmer_own_phone'), 10),
                'farmer_organization': s(participant_data.get('farmer_organization'), 200),
                'farmer_position': s(participant_data.get('farmer_position'), 100),
                'farmer_relationship': s(participant_data.get('farmer_relationship'), 100),
                'participants_type': s(participant_data.get('participants_type'), 50),
                'admin_level1': s(participant_data.get('admin_level1'), 100),
                'admin_level2': s(participant_data.get('admin_level2'), 100),
                'partner': s(participant_data.get('partner'), 100),
                'org_first_name': s(participant_data.get('org_first_name'), 100),
                'org_surname': s(participant_data.get('org_surname'), 100),
                'org_phone_no': s(participant_data.get('org_phone_no'), 20),
                'crop': s(participant_data.get('crop'), 50),
                'thematic_area': participant_data.get('thematic_area'),
                'thematic_area_overall': participant_data.get('thematic_area_overall'),
                'data_source': s(participant_data.get('data_source'), 100),
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