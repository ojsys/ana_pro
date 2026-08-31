"""
Give every ANA Nigeria partner a PartnerOrganization record.

The public partner page lives on PartnerOrganization, but only a minority of
ANANigeriaPartner rows were ever linked to one — so most partner cards on the
website had nowhere to link to. This matches the remainder by name and creates
a PartnerOrganization for any that still has none, carrying across the contact
details and category already held on the ANA record.

Safe to re-run: rows that are already linked are left alone.
"""
import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from dashboard.models import ANANigeriaPartner, PartnerOrganization


def normalize(name):
    """Loose key for matching names across the two tables."""
    key = re.sub(r'[^a-z0-9]+', ' ', (name or '').lower())
    return re.sub(r'\s+', ' ', key).strip()


def make_code(name, taken):
    """Build a short unique code from the organization name."""
    words = re.findall(r'[A-Za-z0-9]+', name or '')
    if not words:
        base = 'PARTNER'
    elif len(words) == 1:
        base = words[0][:12].upper()
    else:
        base = ''.join(w[0] for w in words[:6]).upper()

    base = base[:40] or 'PARTNER'
    code, n = base, 2
    while code in taken:
        suffix = f'-{n}'
        code = f'{base[:40 - len(suffix)]}{suffix}'
        n += 1
    taken.add(code)
    return code


class Command(BaseCommand):
    help = 'Ensure every ANA Nigeria partner has a linked PartnerOrganization (and so a public page)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would change without writing anything')

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']

        orgs_by_key = {}
        for org in PartnerOrganization.objects.all():
            orgs_by_key.setdefault(normalize(org.name), org)

        taken_codes = set(PartnerOrganization.objects.values_list('code', flat=True))
        taken_slugs = set(PartnerOrganization.objects.values_list('slug', flat=True))

        linked = created = already = 0

        for ana in ANANigeriaPartner.objects.filter(is_active=True).order_by('organization'):
            if ana.partner_organization_id:
                already += 1
                continue

            key = normalize(ana.organization)
            org = orgs_by_key.get(key)

            if org:
                linked += 1
                if not dry:
                    ana.partner_organization = org
                    ana.save(update_fields=['partner_organization'])
                self.stdout.write(f'  link   {ana.organization}  ->  {org.name}')
                continue

            created += 1
            self.stdout.write(self.style.SUCCESS(f'  create {ana.organization}'))
            if dry:
                continue

            base_slug = slugify(ana.organization)[:200] or 'partner'
            slug, n = base_slug, 2
            while slug in taken_slugs:
                slug = f'{base_slug}-{n}'
                n += 1
            taken_slugs.add(slug)

            org = PartnerOrganization.objects.create(
                name=ana.organization,
                code=make_code(ana.organization, taken_codes),
                slug=slug,
                organization_type=ana.primary_category,
                contact_person=ana.contact_person or '',
                email=ana.email or '',
                phone_number=(ana.phone_number or '')[:20],
                country='Nigeria',
                status=PartnerOrganization.STATUS_APPROVED,
                is_active=True,
                has_public_page=True,
            )
            orgs_by_key[key] = org
            ana.partner_organization = org
            ana.save(update_fields=['partner_organization'])

        verb = 'Would link' if dry else 'Linked'
        verb2 = 'would create' if dry else 'created'
        self.stdout.write(self.style.SUCCESS(
            f'\n{verb} {linked} existing organization(s), {verb2} {created} new one(s). '
            f'{already} were already linked.'
        ))

        if dry:
            transaction.set_rollback(True)
