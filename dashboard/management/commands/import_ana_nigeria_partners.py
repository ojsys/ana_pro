"""
Management command to import ANA Nigeria partners from the official Excel list.

Usage:
    python manage.py import_ana_nigeria_partners
    python manage.py import_ana_nigeria_partners --file /path/to/file.xlsx
    python manage.py import_ana_nigeria_partners --update   # update existing rows too
"""

import os
from django.core.management.base import BaseCommand, CommandError
from dashboard.models import ANANigeriaPartner, PartnerOrganization


DEFAULT_XLSX = os.path.expanduser(
    "~/Downloads/List of AKILIMO  Nigeria Association Partners.xlsx"
)


def _bool(val):
    """Treat 'X', True, 1, 'x', 'yes' as True."""
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ('x', '1', 'yes', 'true')


class Command(BaseCommand):
    help = "Import ANA Nigeria partners from the official Excel spreadsheet"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default=DEFAULT_XLSX,
            help=f"Path to the Excel file (default: {DEFAULT_XLSX})",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing records (by default existing rows are skipped)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be imported without saving anything",
        )

    def handle(self, *args, **options):
        try:
            import openpyxl
        except ImportError:
            raise CommandError(
                "openpyxl is required. Install it with: pip install openpyxl"
            )

        filepath = options["file"]
        do_update = options["update"]
        dry_run = options["dry_run"]

        if not os.path.exists(filepath):
            raise CommandError(f"File not found: {filepath}")

        self.stdout.write(f"Loading workbook: {filepath}")
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active  # "Partners" sheet

        rows = list(ws.iter_rows(values_only=True))
        # Row 0 = top-level headers, Row 1 = sub-headers, Row 2+ = data
        data_rows = rows[2:]

        self.stdout.write(f"Found {len(data_rows)} partner rows to process")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing will be saved"))

        created = updated = skipped = 0

        for row in data_rows:
            if not row[1]:  # no organization name → skip blank rows
                continue

            org_name = str(row[1]).strip()
            phone_raw = row[4]
            phone = str(phone_raw).strip() if phone_raw is not None else ""

            fields = {
                "country": str(row[0]).strip() if row[0] else "NG",
                "contact_person": str(row[2]).strip() if row[2] else "",
                "email": str(row[3]).strip() if row[3] else "",
                "phone_number": phone,
                # Agro-input Supplier
                "is_fertilizer_company": _bool(row[5]),
                "is_agrochemical_supplier": _bool(row[6]),
                "is_seed_dealer": _bool(row[7]),
                # Development Org / Production Training
                "is_ngo": _bool(row[8]),
                "is_private_extension": _bool(row[9]),
                "is_national_extension_govt": _bool(row[10]),
                "is_farmer_association": _bool(row[11]),
                # Marketing & Processing
                "is_aggregator_buyer": _bool(row[12]),
                "is_industrial_flour_mill": _bool(row[13]),
                "is_starch_factory": _bool(row[14]),
                "is_local_processing_enterprise": _bool(row[15]),
                # Digital Advisory
                "is_social_enterprise": _bool(row[16]),
                "is_govt_advisory_service": _bool(row[17]),
                # Credit Provider
                "is_microcredit_institution": _bool(row[18]),
                "is_bank": _bool(row[19]),
                "is_cooperative_lending": _bool(row[20]),
                # Government
                "is_research_institute": _bool(row[21]),
                "is_university": _bool(row[22]),
                # Status
                "is_uploading_data": _bool(row[23]),
                "is_integrated_akilimo": _bool(row[24]) if len(row) > 24 else False,
            }

            # Try to link to an existing PartnerOrganization by name
            partner_org = PartnerOrganization.objects.filter(
                name__iexact=org_name
            ).first()
            if partner_org:
                fields["partner_organization"] = partner_org

            existing = ANANigeriaPartner.objects.filter(
                organization__iexact=org_name
            ).first()

            if existing:
                if do_update:
                    if not dry_run:
                        for attr, val in fields.items():
                            setattr(existing, attr, val)
                        existing.save()
                    updated += 1
                    self.stdout.write(f"  UPDATED  {org_name}")
                else:
                    skipped += 1
                    self.stdout.write(f"  skipped  {org_name} (already exists)")
            else:
                if not dry_run:
                    ANANigeriaPartner.objects.create(organization=org_name, **fields)
                created += 1
                self.stdout.write(f"  CREATED  {org_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone — created: {created}, updated: {updated}, skipped: {skipped}"
            )
        )
