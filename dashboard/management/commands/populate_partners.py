from django.core.management.base import BaseCommand
from django.db import transaction
from dashboard.models import PartnerOrganization, AkilimoParticipant
from django.utils.text import slugify
import re

class Command(BaseCommand):
    help = 'Populate Partner Organizations table with partners from AKILIMOParticipant data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to show what would be created',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing partner organizations',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        overwrite = options['overwrite']
        
        self.stdout.write(self.style.SUCCESS('Starting Partner Organization population...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all unique partners from AkilimoParticipant data
        partners_data = AkilimoParticipant.objects.exclude(
            partner__isnull=True
        ).exclude(
            partner__exact=''
        ).values('partner').distinct().order_by('partner')
        
        self.stdout.write(f'Found {partners_data.count()} unique partners in AkilimoParticipant data')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for partner_data in partners_data:
                partner_name = partner_data['partner'].strip()
                
                if not partner_name:
                    continue
                
                # Clean and normalize partner name
                cleaned_name = self.clean_partner_name(partner_name)
                
                # Generate a code from the name
                partner_code = self.generate_partner_code(cleaned_name)
                
                # Get statistics for this partner
                partner_stats = self.get_partner_statistics(partner_name)
                
                # Check if partner already exists
                existing_partner = PartnerOrganization.objects.filter(
                    name__iexact=cleaned_name
                ).first()
                
                if existing_partner:
                    if overwrite:
                        # Update existing partner with new information
                        existing_partner.code = partner_code
                        existing_partner.description = self.generate_description(cleaned_name, partner_stats)
                        existing_partner.organization_type = self.guess_organization_type(cleaned_name)
                        
                        if not dry_run:
                            existing_partner.save()
                        
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Updated: {cleaned_name} (Code: {partner_code})')
                        )
                    else:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Skipped existing: {cleaned_name}')
                        )
                    continue
                
                # Create new partner organization
                partner_org_data = {
                    'name': cleaned_name,
                    'code': partner_code,
                    'description': self.generate_description(cleaned_name, partner_stats),
                    'organization_type': self.guess_organization_type(cleaned_name),
                    'country': 'Nigeria',  # Default for AKILIMO Nigeria
                    'is_active': True,
                }
                
                if not dry_run:
                    partner_org = PartnerOrganization.objects.create(**partner_org_data)
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created: {cleaned_name} (Code: {partner_code})')
                    )
                else:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Would create: {cleaned_name} (Code: {partner_code})')
                    )
                
                # Display partner statistics
                self.stdout.write(f'  → {partner_stats["farmers"]} farmers, {partner_stats["events"]} events')
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write(f'Total processed: {created_count + updated_count + skipped_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nThis was a DRY RUN - no changes were made'))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS('\nPartner Organizations successfully populated!'))

    def clean_partner_name(self, name):
        """Clean and normalize partner organization names"""
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', name.strip())
        
        # Common cleaning patterns
        replacements = {
            'NGO': 'NGO',
            'ngo': 'NGO',
            'Ltd': 'Limited',
            'LTD': 'Limited',
            'Inc': 'Incorporated',
            'INC': 'Incorporated',
        }
        
        for old, new in replacements.items():
            cleaned = re.sub(rf'\b{old}\b', new, cleaned, flags=re.IGNORECASE)
        
        return cleaned

    def generate_partner_code(self, name):
        """Generate a unique code for the partner organization"""
        # Take first letter of each significant word (skip common words)
        skip_words = {'and', 'of', 'for', 'the', 'in', 'on', 'at', 'to', 'a', 'an'}
        
        words = [word for word in name.split() if word.lower() not in skip_words]
        
        if len(words) == 1:
            # Single word - take first 4-6 characters
            code = words[0][:6].upper()
        elif len(words) == 2:
            # Two words - take first 3-4 characters of each
            code = f"{words[0][:3]}{words[1][:3]}".upper()
        else:
            # Multiple words - take first letter of each
            code = ''.join([word[0] for word in words[:6]]).upper()
        
        # Ensure minimum length of 3
        if len(code) < 3:
            code = slugify(name).replace('-', '').upper()[:6]
        
        # Check for uniqueness and add number suffix if needed
        base_code = code
        counter = 1
        while PartnerOrganization.objects.filter(code=code).exists():
            code = f"{base_code}{counter}"
            counter += 1
        
        return code

    def get_partner_statistics(self, partner_name):
        """Get statistics for a partner from AkilimoParticipant data"""
        participants = AkilimoParticipant.objects.filter(partner__iexact=partner_name)
        
        return {
            'farmers': participants.count(),
            'events': participants.values('event_date', 'event_venue').distinct().count(),
            'cities': participants.exclude(event_city__isnull=True).values('event_city').distinct().count(),
            'years': participants.exclude(event_year__isnull=True).values('event_year').distinct().count(),
        }

    def generate_description(self, name, stats):
        """Generate a description based on partner statistics"""
        description_parts = [
            f"{name} is a partner organization in the AKILIMO Nigeria program."
        ]
        
        if stats['farmers'] > 0:
            description_parts.append(f"They have reached {stats['farmers']} farmers")
            
            if stats['events'] > 0:
                description_parts[-1] += f" through {stats['events']} events"
                
            if stats['cities'] > 1:
                description_parts[-1] += f" across {stats['cities']} cities"
                
            if stats['years'] > 1:
                description_parts[-1] += f" over {stats['years']} years"
                
            description_parts[-1] += "."
        
        return " ".join(description_parts)

    def guess_organization_type(self, name):
        """Guess organization type based on name patterns"""
        name_lower = name.lower()
        
        # Common patterns
        if any(word in name_lower for word in ['ngo', 'foundation', 'trust', 'society', 'association']):
            return 'NGO'
        elif any(word in name_lower for word in ['government', 'ministry', 'department', 'agency', 'state', 'federal']):
            return 'Government'
        elif any(word in name_lower for word in ['university', 'college', 'institute', 'research', 'academic']):
            return 'Academic'
        elif any(word in name_lower for word in ['company', 'limited', 'ltd', 'incorporated', 'inc', 'enterprise']):
            return 'Private'
        elif any(word in name_lower for word in ['cooperative', 'coop', 'union', 'group']):
            return 'Cooperative'
        else:
            return 'Other'