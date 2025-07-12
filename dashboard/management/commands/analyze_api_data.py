from django.core.management.base import BaseCommand
from dashboard.models import APIConfiguration
from dashboard.services import EiAMeliaAPIService
import json

class Command(BaseCommand):
    help = 'Analyze API data structure and suggest model updates'

    def add_arguments(self, parser):
        parser.add_argument('--sample-size', type=int, default=100, help='Number of records to analyze')

    def handle(self, *args, **options):
        sample_size = options.get('sample_size')
        
        # Get API configuration
        try:
            api_config = APIConfiguration.objects.filter(is_active=True).first()
            if not api_config:
                self.stdout.write(self.style.ERROR('No API configuration found'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting API configuration: {e}'))
            return

        self.stdout.write(f'📊 Analyzing {sample_size} records from EiA MELIA API...')
        
        try:
            api_service = EiAMeliaAPIService(api_config.token)
            
            # Get sample data
            response = api_service.get_participants_by_usecase('akilimo', page=1, page_size=sample_size)
            data = response.get('data', [])
            
            if not data:
                self.stdout.write(self.style.WARNING('No data returned from API'))
                return
            
            self.stdout.write(f'✅ Retrieved {len(data)} records')
            
            # Analyze field usage and types
            field_analysis = {}
            
            for record in data:
                for key, value in record.items():
                    if key not in field_analysis:
                        field_analysis[key] = {
                            'count': 0,
                            'types': set(),
                            'null_count': 0,
                            'sample_values': set(),
                            'max_length': 0
                        }
                    
                    field_analysis[key]['count'] += 1
                    
                    if value is None:
                        field_analysis[key]['null_count'] += 1
                    else:
                        field_analysis[key]['types'].add(type(value).__name__)
                        str_value = str(value)
                        field_analysis[key]['max_length'] = max(field_analysis[key]['max_length'], len(str_value))
                        if len(field_analysis[key]['sample_values']) < 5:
                            field_analysis[key]['sample_values'].add(str_value)
            
            # Print analysis
            self.stdout.write('\n📈 FIELD ANALYSIS:')
            self.stdout.write('=' * 80)
            
            for field, analysis in sorted(field_analysis.items()):
                null_percentage = (analysis['null_count'] / analysis['count']) * 100
                types = ', '.join(analysis['types'])
                samples = ', '.join(list(analysis['sample_values'])[:3])
                
                self.stdout.write(f'\n🔍 {field}:')
                self.stdout.write(f'   Types: {types}')
                self.stdout.write(f'   Null: {analysis["null_count"]}/{analysis["count"]} ({null_percentage:.1f}%)')
                self.stdout.write(f'   Max Length: {analysis["max_length"]}')
                self.stdout.write(f'   Samples: {samples}')
            
            # Suggest updated model
            self.stdout.write('\n💡 SUGGESTED MODEL UPDATES:')
            self.stdout.write('=' * 80)
            
            # Map API fields to appropriate Django field types
            field_mappings = {
                'id': 'models.BigIntegerField(unique=True)',
                'usecase': 'models.CharField(max_length=50)',
                'country': 'models.CharField(max_length=50)',
                'source_submitted_on': 'models.DateTimeField(null=True, blank=True)',
                'usecase_stage': 'models.CharField(max_length=50, null=True, blank=True)',
                'created_on': 'models.DateTimeField(null=True, blank=True)',
                'source_id': 'models.CharField(max_length=100, null=True, blank=True)',
                'data_source': 'models.CharField(max_length=50, null=True, blank=True)',
                'event_date': 'models.DateField(null=True, blank=True)',
                'event_year': 'models.IntegerField(null=True, blank=True)',
                'event_month': 'models.IntegerField(null=True, blank=True)',
                'event_type': 'models.CharField(max_length=100, null=True, blank=True)',
                'partner': 'models.CharField(max_length=100, null=True, blank=True)',
                'thematic_area': 'models.TextField(null=True, blank=True)',
                'thematic_area_overall': 'models.TextField(null=True, blank=True)',
                'event_format': 'models.CharField(max_length=50, null=True, blank=True)',
                'crop': 'models.CharField(max_length=50, null=True, blank=True)',
                'org_first_name': 'models.CharField(max_length=100, null=True, blank=True)',
                'org_surname': 'models.CharField(max_length=100, null=True, blank=True)',
                'org_phone_no': 'models.CharField(max_length=20, null=True, blank=True)',
                'farmer_first_name': 'models.CharField(max_length=100, null=True, blank=True)',
                'farmer_surname': 'models.CharField(max_length=100, null=True, blank=True)',
                'farmer_id': 'models.CharField(max_length=100, null=True, blank=True)',
                'farmer_gender': 'models.CharField(max_length=20, null=True, blank=True)',
                'farmer_age': 'models.CharField(max_length=10, null=True, blank=True)',
                'age_category': 'models.CharField(max_length=20, null=True, blank=True)',
                'farmer_organization': 'models.CharField(max_length=200, null=True, blank=True)',
                'farmer_position': 'models.CharField(max_length=100, null=True, blank=True)',
                'farmer_phone_no': 'models.CharField(max_length=20, null=True, blank=True)',
                'farmer_own_phone': 'models.CharField(max_length=10, null=True, blank=True)',
                'farmer_relationship': 'models.CharField(max_length=100, null=True, blank=True)',
                'participants_type': 'models.CharField(max_length=50, null=True, blank=True)',
                'admin_level1': 'models.CharField(max_length=100, null=True, blank=True)',  # State
                'admin_level2': 'models.CharField(max_length=100, null=True, blank=True)',  # LGA
                'event_city': 'models.CharField(max_length=200, null=True, blank=True)',
                'event_venue': 'models.CharField(max_length=500, null=True, blank=True)',
                'event_geopoint': 'models.CharField(max_length=100, null=True, blank=True)',
            }
            
            self.stdout.write('\nclass AkilimoParticipant(models.Model):')
            self.stdout.write('    """Updated model based on actual API data"""')
            
            for field, django_field in field_mappings.items():
                if field in field_analysis:
                    self.stdout.write(f'    {field} = {django_field}')
            
            self.stdout.write('    raw_data = models.JSONField(default=dict)')
            self.stdout.write('    created_at = models.DateTimeField(auto_now_add=True)')
            self.stdout.write('    updated_at = models.DateTimeField(auto_now=True)')
            
            # Suggest visualizations based on actual data
            self.stdout.write('\n🎨 VISUALIZATION OPPORTUNITIES:')
            self.stdout.write('=' * 80)
            
            categorical_fields = ['farmer_gender', 'admin_level1', 'admin_level2', 'event_type', 
                                'partner', 'age_category', 'event_format', 'crop', 'participants_type']
            
            geographic_fields = ['admin_level1', 'admin_level2', 'event_city', 'event_geopoint']
            
            time_fields = ['event_date', 'event_year', 'event_month', 'created_on']
            
            self.stdout.write('\n🥧 Categorical Data (Pie/Bar Charts):')
            for field in categorical_fields:
                if field in field_analysis:
                    null_pct = (field_analysis[field]['null_count'] / field_analysis[field]['count']) * 100
                    if null_pct < 50:  # Only suggest if less than 50% null
                        self.stdout.write(f'   - {field} distribution')
            
            self.stdout.write('\n🗺️ Geographic Visualizations:')
            for field in geographic_fields:
                if field in field_analysis:
                    null_pct = (field_analysis[field]['null_count'] / field_analysis[field]['count']) * 100
                    if null_pct < 50:
                        self.stdout.write(f'   - {field} distribution map')
            
            self.stdout.write('\n📅 Time-based Analysis:')
            for field in time_fields:
                if field in field_analysis:
                    null_pct = (field_analysis[field]['null_count'] / field_analysis[field]['count']) * 100
                    if null_pct < 50:
                        self.stdout.write(f'   - {field} trends over time')
            
            self.stdout.write('\n🔗 Cross-Analysis Opportunities:')
            self.stdout.write('   - Gender distribution by state (admin_level1)')
            self.stdout.write('   - Event types by partner organization')
            self.stdout.write('   - Age categories by geographic region')
            self.stdout.write('   - Thematic areas by state/LGA')
            self.stdout.write('   - Training events timeline by location')
            self.stdout.write('   - Partner performance by region')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Analysis failed: {e}'))