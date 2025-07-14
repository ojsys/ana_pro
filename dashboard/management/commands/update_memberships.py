from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Membership
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update expired memberships and send renewal notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to the database',
        )
        parser.add_argument(
            '--notify-days',
            type=int,
            default=30,
            help='Days before expiration to send notifications (default: 30)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        notify_days = options['notify_days']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        now = timezone.now()
        
        # Find expired memberships
        expired_memberships = Membership.objects.filter(
            end_date__lt=now,
            status='active'
        )
        
        expired_count = expired_memberships.count()
        if expired_count > 0:
            self.stdout.write(f'Found {expired_count} expired memberships')
            
            if not dry_run:
                # Update expired memberships
                updated = expired_memberships.update(status='expired')
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {updated} expired memberships')
                )
            else:
                for membership in expired_memberships:
                    self.stdout.write(
                        f'Would expire: {membership.member.username} - '
                        f'{membership.get_membership_type_display()} '
                        f'(expired {membership.end_date})'
                    )
        else:
            self.stdout.write('No expired memberships found')
        
        # Find memberships expiring soon
        warning_date = now + timezone.timedelta(days=notify_days)
        expiring_soon = Membership.objects.filter(
            end_date__gte=now,
            end_date__lte=warning_date,
            status='active'
        )
        
        expiring_count = expiring_soon.count()
        if expiring_count > 0:
            self.stdout.write(
                f'Found {expiring_count} memberships expiring within {notify_days} days'
            )
            
            for membership in expiring_soon:
                days_remaining = (membership.end_date - now).days
                self.stdout.write(
                    f'Expiring soon: {membership.member.username} - '
                    f'{membership.get_membership_type_display()} '
                    f'({days_remaining} days remaining)'
                )
                
                # Here you could send email notifications
                # Example: send_renewal_notification(membership)
        else:
            self.stdout.write(f'No memberships expiring within {notify_days} days')
        
        # Statistics
        total_memberships = Membership.objects.count()
        active_memberships = Membership.objects.filter(status='active').count()
        pending_memberships = Membership.objects.filter(status='pending').count()
        expired_memberships_total = Membership.objects.filter(status='expired').count()
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('MEMBERSHIP STATISTICS')
        self.stdout.write('='*50)
        self.stdout.write(f'Total memberships: {total_memberships}')
        self.stdout.write(f'Active: {active_memberships}')
        self.stdout.write(f'Pending: {pending_memberships}')
        self.stdout.write(f'Expired: {expired_memberships_total}')
        
        # Membership type breakdown
        individual_count = Membership.objects.filter(membership_type='individual').count()
        organization_count = Membership.objects.filter(membership_type='organization').count()
        
        self.stdout.write('\nMEMBERSHIP TYPES')
        self.stdout.write('-'*20)
        self.stdout.write(f'Individual: {individual_count}')
        self.stdout.write(f'Organization: {organization_count}')
        
        self.stdout.write(
            self.style.SUCCESS('\nMembership update completed successfully!')
        )