from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime, parse_date
from dashboard.models import APIConfiguration, AkilimoParticipant, DataSyncLog
from dashboard.services import EiAMeliaAPIService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug sync issues - detailed analysis of skipped records'

    def add_arguments(self, parser):
        parser.add_argument('--sample-size', type=int, default=50, help='Number of records to analyze')
        parser.add_argument('--check-existing', action='store_true', help='Check existing records in database')

    def handle(self, *args, **options):
        sample_size = options.get('sample_size')
        check_existing = options.get('check_existing')

        self.stdout.write(f'🔍 Debugging sync issues...')
        self.stdout.write(f'   Sample size: {sample_size}')

        # Get API configuration
        try:
            api_config = APIConfiguration.objects.filter(is_active=True).first()
            if not api_config:
                self.stdout.write(self.style.ERROR('No API configuration found'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting API configuration: {e}'))
            return

        if check_existing:
            self.analyze_existing_records()

        try:
            api_service = EiAMeliaAPIService(api_config.token)
            
            # Get sample data
            response = api_service.get_participants_by_usecase('akilimo', page=1, page_size=sample_size)
            participants_data = response.get('data', [])
            
            if not participants_data:
                self.stdout.write('⚠️  No data returned from API')
                return
            
            self.stdout.write(f'✅ Retrieved {len(participants_data)} records from API')
            
            # Analyze each record for potential issues
            issues_found = {
                'missing_id': 0,
                'duplicate_id': 0,
                'invalid_dates': 0,
                'database_errors': 0,
                'successful': 0
            }
            
            existing_ids = set(AkilimoParticipant.objects.values_list('external_id', flat=True))
            api_ids_in_batch = []
            
            for i, participant_data in enumerate(participants_data, 1):
                self.stdout.write(f'\n🔍 Analyzing record {i}/{len(participants_data)}:')
                
                # Check for missing ID
                external_id = participant_data.get('id')
                if not external_id:
                    self.stdout.write(f'   ❌ Missing ID: {participant_data}')
                    issues_found['missing_id'] += 1
                    continue
                
                self.stdout.write(f'   📊 ID: {external_id}')
                
                # Check for duplicates in current batch
                if external_id in api_ids_in_batch:
                    self.stdout.write(f'   ⚠️  Duplicate ID in current batch: {external_id}')
                    issues_found['duplicate_id'] += 1
                
                api_ids_in_batch.append(external_id)
                
                # Check if already exists in database
                if external_id in existing_ids:
                    self.stdout.write(f'   🔄 Already exists in database: {external_id}')
                
                # Check required fields
                missing_fields = []
                important_fields = ['usecase', 'country', 'farmer_first_name', 'farmer_surname']
                for field in important_fields:
                    if not participant_data.get(field):
                        missing_fields.append(field)
                
                if missing_fields:
                    self.stdout.write(f'   ⚠️  Missing fields: {missing_fields}')
                
                # Check date parsing
                date_issues = []
                
                # Event date
                if participant_data.get('event_date'):
                    try:
                        parse_date(participant_data['event_date'])
                    except Exception as e:
                        date_issues.append(f"event_date: {e}")
                
                # Source submitted on
                if participant_data.get('source_submitted_on'):
                    try:
                        parse_datetime(participant_data['source_submitted_on'])
                    except Exception as e:
                        date_issues.append(f"source_submitted_on: {e}")
                
                # Created on
                if participant_data.get('created_on'):
                    try:
                        parse_datetime(participant_data['created_on'])
                    except Exception as e:
                        date_issues.append(f"created_on: {e}")
                
                if date_issues:
                    self.stdout.write(f'   📅 Date parsing issues: {date_issues}')
                    issues_found['invalid_dates'] += 1
                
                # Try to create the record to see if there are database issues
                try:
                    result = self.test_record_creation(participant_data, external_id in existing_ids)
                    if result == 'success':
                        issues_found['successful'] += 1
                        self.stdout.write(f'   ✅ Record would process successfully')
                    else:
                        self.stdout.write(f'   ❌ Record processing failed: {result}')
                        issues_found['database_errors'] += 1
                        
                except Exception as e:
                    self.stdout.write(f'   ❌ Database error: {e}')
                    issues_found['database_errors'] += 1
            
            # Summary
            self.stdout.write(f'\n📈 ANALYSIS SUMMARY:')
            self.stdout.write(f'=' * 50)
            self.stdout.write(f'   📊 Total records analyzed: {len(participants_data)}')
            self.stdout.write(f'   ✅ Would process successfully: {issues_found["successful"]}')
            self.stdout.write(f'   ❌ Missing ID: {issues_found["missing_id"]}')
            self.stdout.write(f'   🔄 Duplicate IDs: {issues_found["duplicate_id"]}')
            self.stdout.write(f'   📅 Date parsing issues: {issues_found["invalid_dates"]}')
            self.stdout.write(f'   💾 Database errors: {issues_found["database_errors"]}')
            
            skip_rate = ((issues_found['missing_id'] + issues_found['duplicate_id'] + issues_found['database_errors']) / len(participants_data)) * 100
            self.stdout.write(f'   📉 Estimated skip rate: {skip_rate:.1f}%')
            
            if skip_rate > 5:
                self.stdout.write(f'\n🚨 HIGH SKIP RATE DETECTED!')
                self.stdout.write(f'   Consider investigating data quality issues.')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Analysis failed: {e}'))

    def analyze_existing_records(self):
        """Analyze existing records in database"""
        self.stdout.write(f'\n📊 EXISTING DATABASE RECORDS:')
        self.stdout.write(f'=' * 50)
        
        total_records = AkilimoParticipant.objects.count()
        self.stdout.write(f'   Total records: {total_records:,}')
        
        if total_records > 0:
            # Check for duplicate external_ids
            from django.db.models import Count
            duplicates = AkilimoParticipant.objects.values('external_id').annotate(
                count=Count('external_id')
            ).filter(count__gt=1)
            
            if duplicates:
                self.stdout.write(f'   ⚠️  Duplicate external_ids found: {len(duplicates)}')
                for dup in duplicates[:5]:
                    self.stdout.write(f'      ID {dup["external_id"]}: {dup["count"]} records')
            else:
                self.stdout.write(f'   ✅ No duplicate external_ids found')
            
            # Check for records with missing critical data
            missing_country = AkilimoParticipant.objects.filter(country__isnull=True).count()
            missing_gender = AkilimoParticipant.objects.filter(farmer_gender__isnull=True).count()
            missing_names = AkilimoParticipant.objects.filter(
                farmer_first_name__isnull=True, 
                farmer_surname__isnull=True
            ).count()
            
            self.stdout.write(f'   📊 Data quality:')
            self.stdout.write(f'      Missing country: {missing_country}')
            self.stdout.write(f'      Missing gender: {missing_gender}')
            self.stdout.write(f'      Missing names: {missing_names}')

    def test_record_creation(self, participant_data, exists_in_db):
        """Test if a record can be created without actually saving it"""
        try:
            external_id = participant_data.get('id')
            
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
            
            # Try to create model instance (without saving)
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
            
            # Test model validation without saving
            instance = AkilimoParticipant(**model_data)
            instance.full_clean()  # This will raise ValidationError if there are issues
            
            if exists_in_db:
                return 'exists'
            else:
                return 'success'
                
        except Exception as e:
            return f'validation_error: {e}'