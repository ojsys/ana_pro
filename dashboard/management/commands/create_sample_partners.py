from django.core.management.base import BaseCommand
from dashboard.models import PartnerOrganization


class Command(BaseCommand):
    help = 'Create sample partner organizations for testing'

    def handle(self, *args, **options):
        partners = [
            {
                'name': 'International Institute of Tropical Agriculture',
                'code': 'IITA',
                'description': 'Leading international agricultural research institute focusing on tropical agriculture',
                'organization_type': 'Research Institute',
                'contact_person': 'Dr. John Smith',
                'email': 'contact@iita.org',
                'phone_number': '+234-802-123-4567',
                'city': 'Ibadan',
                'state': 'Oyo',
                'country': 'Nigeria'
            },
            {
                'name': 'Cassava Growers Association of Nigeria',
                'code': 'CGAN',
                'description': 'National association of cassava farmers and producers',
                'organization_type': 'Farmers Association',
                'contact_person': 'Mrs. Amina Hassan',
                'email': 'info@cgan.org.ng',
                'phone_number': '+234-803-987-6543',
                'city': 'Abuja',
                'state': 'FCT',
                'country': 'Nigeria'
            },
            {
                'name': 'Nigeria Agricultural Development Programme',
                'code': 'NADP',
                'description': 'Government agency promoting agricultural development',
                'organization_type': 'Government',
                'contact_person': 'Eng. Mohammed Bello',
                'email': 'contact@nadp.gov.ng',
                'phone_number': '+234-809-456-7890',
                'city': 'Kaduna',
                'state': 'Kaduna',
                'country': 'Nigeria'
            },
            {
                'name': 'Green Agriculture Initiative',
                'code': 'GAI',
                'description': 'NGO promoting sustainable agricultural practices',
                'organization_type': 'NGO',
                'contact_person': 'Dr. Sarah Okafor',
                'email': 'hello@greenagri.org',
                'phone_number': '+234-807-111-2222',
                'city': 'Lagos',
                'state': 'Lagos',
                'country': 'Nigeria'
            },
            {
                'name': 'Farmers Development Union',
                'code': 'FDU',
                'description': 'Union supporting smallholder farmer development',
                'organization_type': 'Union',
                'contact_person': 'Chief Adebayo Adewale',
                'email': 'support@fdu.ng',
                'phone_number': '+234-805-333-4444',
                'city': 'Abeokuta',
                'state': 'Ogun',
                'country': 'Nigeria'
            },
            {
                'name': 'Root Crops Research Institute',
                'code': 'RCRI',
                'description': 'Research institute specializing in root and tuber crops',
                'organization_type': 'Research Institute',
                'contact_person': 'Prof. Chinonso Okwu',
                'email': 'research@rcri.edu.ng',
                'phone_number': '+234-806-555-6666',
                'city': 'Enugu',
                'state': 'Enugu',
                'country': 'Nigeria'
            }
        ]

        created_count = 0
        for partner_data in partners:
            partner, created = PartnerOrganization.objects.get_or_create(
                code=partner_data['code'],
                defaults=partner_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created partner: {partner.name} ({partner.code})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Partner already exists: {partner.name} ({partner.code})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} new partner organizations'
            )
        )