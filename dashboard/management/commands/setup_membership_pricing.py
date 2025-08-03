from django.core.management.base import BaseCommand
from dashboard.models import MembershipPricing
from decimal import Decimal


class Command(BaseCommand):
    help = 'Setup default membership pricing if it does not exist'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Setting up membership pricing...')
        
        # Create or update individual pricing
        individual_pricing, created = MembershipPricing.objects.get_or_create(
            membership_type='individual',
            defaults={
                'price': Decimal('10000.00'),
                'is_active': True
            }
        )
        
        # Ensure the price is correct even if record exists
        if not created and individual_pricing.price != Decimal('10000.00'):
            individual_pricing.price = Decimal('10000.00')
            individual_pricing.is_active = True
            individual_pricing.save()
            self.stdout.write('🔄 Updated individual membership pricing to ₦10,000')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✅ Created individual membership pricing: ₦10,000')
            )
        else:
            self.stdout.write(
                f'ℹ️  Individual membership pricing exists: ₦{individual_pricing.price}'
            )
        
        # Create or update organization pricing
        organization_pricing, created = MembershipPricing.objects.get_or_create(
            membership_type='organization',
            defaults={
                'price': Decimal('50000.00'),
                'is_active': True
            }
        )
        
        # Ensure the price is correct even if record exists
        if not created and organization_pricing.price != Decimal('50000.00'):
            organization_pricing.price = Decimal('50000.00')
            organization_pricing.is_active = True
            organization_pricing.save()
            self.stdout.write('🔄 Updated organization membership pricing to ₦50,000')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✅ Created organization membership pricing: ₦50,000')
            )
        else:
            self.stdout.write(
                f'ℹ️  Organization membership pricing exists: ₦{organization_pricing.price}'
            )
        
        # Show all pricing
        self.stdout.write('\n📋 Current membership pricing:')
        for pricing in MembershipPricing.objects.all():
            status = "✅ Active" if pricing.is_active else "❌ Inactive"
            self.stdout.write(
                f'  • {pricing.get_membership_type_display()}: ₦{pricing.price} {status}'
            )