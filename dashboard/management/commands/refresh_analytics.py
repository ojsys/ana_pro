"""
Recompute the public analytics snapshot.

The public analytics page reads a stored snapshot so visitors never wait on the
aggregation (~1 minute over 200k participant rows). Run this after each data
sync — e.g. from the same cron entry that runs sync_akilimo_data.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard.analytics import save_snapshot


class Command(BaseCommand):
    help = 'Rebuild the public analytics snapshot shown on /analytics/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--country',
            default='nigeria',
            help="Country to compute for, or 'all' for every country (default: nigeria)",
        )
        parser.add_argument(
            '--both',
            action='store_true',
            help="Refresh both the Nigeria and the all-countries snapshots",
        )

    def handle(self, *args, **options):
        countries = ['nigeria', 'all'] if options['both'] else [options['country']]

        for country in countries:
            started = timezone.now()
            self.stdout.write(f"Computing analytics for '{country}'…")
            data = save_snapshot(country=country)
            elapsed = (timezone.now() - started).total_seconds()
            totals = data['totals']
            self.stdout.write(self.style.SUCCESS(
                f"  {totals['farmers']:,} farmers · {totals['states']} states · "
                f"{totals['lgas']} LGAs · {totals['partners']} partners  ({elapsed:.0f}s)"
            ))
