"""
Load the sponsorship packages, benefits and exhibition booths for the
conference from the published "Sponsorship Packages & Benefits" sheet.

Everything written here is editable afterwards in the Django admin:

  Conference > Sponsorship Packages          - the tiers and their prices
  Conference > Sponsorship Benefits          - the rows of the comparison table
  Conference > Sponsorship Benefit Values    - individual cells
  Conference > Exhibitor Packages            - the standalone booths

Re-running updates the existing rows in place rather than duplicating them, so
it is safe to run again after the sheet is revised. Text is kept to plain ASCII
because the production database has not yet been converted to utf8mb4 - see
`manage.py fix_mysql_charset`.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from conference.models import (
    Conference, ExhibitorPackage, SponsorshipBenefit,
    SponsorshipPackage, SponsorshipPackageBenefit,
)

# Columns: name, position, price, price_display, accent colour, featured
PACKAGES = [
    ('Diamond',            'Exclusive Conference Presented By', Decimal('10000000'), '', '#7FD4E8', False),
    ('Platinum',           'Strategic Partner',                 Decimal('7500000'),  '', '#9AA5B1', True),
    ('Gold',               'Gold Sponsor',                      Decimal('5000000'),  '', '#D4A017', False),
    ('Silver',             'Silver Sponsor',                    Decimal('2500000'),  '', '#8E9AA6', False),
    ('Bronze',             'Bronze Sponsor',                    Decimal('1000000'),  '', '#A9714B', False),
    ('Supporting Partner', 'Supporting Partner',                None,
     'NGN 50,000 - NGN 500,000', '#2E7D32', False),
]

# Rows of the comparison table, in order.
BENEFITS = [
    'Exhibition Booth',
    'Speaking Opportunity',
    'Policy/Stakeholder Access',
    'Logo & Brand Visibility',
    'Media & PR',
    'Conference Passes',
    'Proceedings Advertisement',
    'Delegate Bag Insert',
    'Post-Event Report',
    'Recognition',
]

# benefit label -> {package name: cell value}
VALUES = {
    'Exhibition Booth': {
        'Diamond': 'Premium 3m x 3m',
        'Platinum': 'Premium 3m x 3m',
        'Gold': '2m x 2m',
        'Silver': '2m x 2m',
        'Bronze': '',
        'Supporting Partner': '',
    },
    'Speaking Opportunity': {
        'Diamond': '15-min keynote/strategic address + gala toast',
        'Platinum': '15-min strategic address + panel',
        'Gold': '10-min session + panel',
        'Silver': '5-min welcome/session',
        'Bronze': '5-min welcome/session',
        'Supporting Partner': '',
    },
    'Policy/Stakeholder Access': {
        'Diamond': 'Executive roundtable with selected policymakers & industry leaders',
        'Platinum': 'High-level roundtable with policymakers/sector stakeholders',
        'Gold': 'Priority networking with key stakeholders',
        'Silver': 'Networking access',
        'Bronze': 'Networking access',
        'Supporting Partner': 'General networking',
    },
    'Logo & Brand Visibility': {
        'Diamond': 'Stage, conference materials, website, programme, screens, bags & lanyards',
        'Platinum': 'Stage, conference materials, website, programme, screens, bags & lanyards',
        'Gold': 'Programme, website, app/screens',
        'Silver': 'Programme, website & session materials',
        'Bronze': 'Programme & website',
        'Supporting Partner': "Website/supporters' recognition",
    },
    'Media & PR': {
        'Diamond': 'Co-branded media release + interview',
        'Platinum': 'Co-branded media release + interview',
        'Gold': 'Press mention + dedicated social post',
        'Silver': 'Group social media recognition',
        'Bronze': 'Group social media recognition',
        'Supporting Partner': 'Group acknowledgement',
    },
    'Conference Passes': {
        'Diamond': '10 + 6 VIP Gala',
        'Platinum': '10 + 6 VIP Gala',
        'Gold': '7 + 3 Gala',
        'Silver': '5 + 2 Gala',
        'Bronze': '3 + 1 Gala',
        'Supporting Partner': '1-2 passes depending on contribution',
    },
    'Proceedings Advertisement': {
        'Diamond': 'Back cover - full page',
        'Platinum': 'Back cover/full page',
        'Gold': 'Inside cover/half page',
        'Silver': 'Half page',
        'Bronze': 'Name/logo listing',
        'Supporting Partner': 'Name under NGN 250k; Logo NGN 250k and above',
    },
    'Delegate Bag Insert': {
        'Diamond': 'Yes', 'Platinum': 'Yes', 'Gold': 'Yes',
        'Silver': 'Yes', 'Bronze': 'Yes', 'Supporting Partner': 'Yes',
    },
    'Post-Event Report': {
        'Diamond': 'Full report + available opt-in engagement data',
        'Platinum': 'Full report + available opt-in engagement data',
        'Gold': 'Summary report',
        'Silver': 'Summary report',
        'Bronze': 'Summary report',
        'Supporting Partner': 'Acknowledgement/summary',
    },
    'Recognition': {
        'Diamond': 'Stage award + certificate',
        'Platinum': 'Stage award + certificate',
        'Gold': 'MC recognition + certificate',
        'Silver': 'MC recognition + certificate',
        'Bronze': 'Certificate',
        'Supporting Partner': 'Certificate',
    },
}

BOOTH_INCLUDES = '1 chair\n1 table\n1 spotlight\nSocket\nWaste bin'

BOOTHS = [
    ('Standard Shell Scheme Booth', Decimal('350000'),
     '2m x 2m booth; 2m x 2m backwall with demarcation sides', 'bi-shop', 1),
    ('Premium Shell Scheme Booth', Decimal('700000'),
     '3m x 3m booth; 3m x 3m backwall with demarcation sides', 'bi-shop-window', 2),
]

PAYMENT = {
    'sponsorship_contact_email': 'finance_fundraising@akilimonigeria.org',
    'bank_account_name': 'Agrimpact for Sustainable Dev Initiative',
    'bank_account_number': '0513118178',
    'bank_name': 'Sterling Bank/Alt Bank',
}


class Command(BaseCommand):
    help = 'Load the sponsorship packages, benefits and exhibition booths onto the active conference'

    def add_arguments(self, parser):
        parser.add_argument('--conference', help='Conference slug (default: the active one)')
        parser.add_argument('--overwrite-values', action='store_true',
                            help='Reset benefit cells that have since been edited in the admin')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['conference']:
            conference = Conference.objects.filter(slug=options['conference']).first()
        else:
            conference = Conference.objects.filter(is_active=True).first()

        if not conference:
            self.stderr.write('No conference found. Create one first, or pass --conference <slug>.')
            return

        self.stdout.write(f'Conference: {conference.name}\n')

        # Payment / contact details, only filling what is blank so a later
        # admin edit is never clobbered.
        changed = []
        for field, value in PAYMENT.items():
            if not getattr(conference, field):
                setattr(conference, field, value)
                changed.append(field)
        if changed:
            conference.save(update_fields=changed)
            self.stdout.write(f'  payment details set: {", ".join(changed)}')
        else:
            self.stdout.write('  payment details already set - left alone')

        # Rows
        benefits = {}
        for order, label in enumerate(BENEFITS, 1):
            benefit, created = SponsorshipBenefit.objects.update_or_create(
                conference=conference, label=label,
                defaults={'order': order, 'is_active': True},
            )
            benefits[label] = benefit
        self.stdout.write(f'  benefit rows: {len(benefits)}')

        # Columns
        packages = {}
        for order, (name, position, price, price_display, colour, featured) in enumerate(PACKAGES, 1):
            package, _ = SponsorshipPackage.objects.update_or_create(
                conference=conference, name=name,
                defaults={
                    'position': position,
                    'price': price,
                    'price_display': price_display,
                    'accent_color': colour,
                    'is_featured': featured,
                    'order': order,
                    'is_active': True,
                },
            )
            packages[name] = package
        self.stdout.write(f'  packages: {len(packages)}')

        # Cells
        written = kept = 0
        for label, per_package in VALUES.items():
            benefit = benefits[label]
            for package_name, value in per_package.items():
                package = packages[package_name]
                cell, created = SponsorshipPackageBenefit.objects.get_or_create(
                    package=package, benefit=benefit, defaults={'value': value},
                )
                if created:
                    written += 1
                elif options['overwrite_values'] and cell.value != value:
                    cell.value = value
                    cell.save(update_fields=['value'])
                    written += 1
                else:
                    kept += 1
        self.stdout.write(f'  benefit values: {written} written, {kept} left as they are')

        # Standalone booths
        for name, price, space, icon, order in BOOTHS:
            ExhibitorPackage.objects.update_or_create(
                conference=conference, name=name,
                defaults={
                    'price': price,
                    'space_structure': space,
                    'perks': BOOTH_INCLUDES,
                    'icon': icon,
                    'order': order,
                    'is_active': True,
                },
            )
        self.stdout.write(f'  exhibition booths: {len(BOOTHS)}')

        self.stdout.write(self.style.SUCCESS(
            '\nDone. Everything above is editable in the admin under Conference.'
        ))
        if not options['overwrite_values'] and kept:
            self.stdout.write(
                'Existing benefit values were preserved. Use --overwrite-values to reset '
                'them to the published sheet.'
            )
