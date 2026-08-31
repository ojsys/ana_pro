"""
Grant a free membership to existing users.

Useful right after switching Site Settings -> Registration Mode to "Free": every
existing account that has no active subscription is given one for the current year,
so they immediately get platform access, a certificate and an ID card.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from dashboard.membership_service import grant_free_membership, is_free_registration_mode


class Command(BaseCommand):
    help = 'Grant a free membership for the current year to existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            help='Only grant to this username (default: all active users)',
        )
        parser.add_argument(
            '--include-staff',
            action='store_true',
            help='Also grant to staff and superuser accounts',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without writing anything',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Run even when Registration Mode is set to Paid',
        )

    def handle(self, *args, **options):
        if not is_free_registration_mode() and not options['force']:
            self.stdout.write(self.style.ERROR(
                'Registration Mode is "Paid". Switch it to "Free" in Site Settings, '
                'or re-run with --force to grant anyway.'
            ))
            return

        users = User.objects.filter(is_active=True)
        if options['username']:
            users = users.filter(username=options['username'])
        if not options['include_staff']:
            users = users.exclude(is_staff=True).exclude(is_superuser=True)

        total = users.count()
        if not total:
            self.stdout.write(self.style.WARNING('No matching users found.'))
            return

        granted = 0
        skipped = 0
        for user in users.iterator():
            membership = getattr(user, 'membership', None)
            if membership and not membership.is_free_membership and membership.has_active_subscription:
                skipped += 1
                continue

            if options['dry_run']:
                self.stdout.write(f'  would grant: {user.username} ({user.email})')
            else:
                grant_free_membership(user)
            granted += 1

        verb = 'Would grant' if options['dry_run'] else 'Granted'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} free membership to {granted} of {total} user(s). '
            f'{skipped} paying member(s) with an active subscription were left unchanged.'
        ))
