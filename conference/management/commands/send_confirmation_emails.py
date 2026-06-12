"""
Send the payment receipt + welcome email to registrations whose payment is
already confirmed (e.g. backfilling registrations confirmed before the
automatic emails were added).

Examples:
    # Preview which registrations would be emailed
    python manage.py send_confirmation_emails --dry-run

    # Send to all confirmed registrations that haven't been emailed yet
    python manage.py send_confirmation_emails

    # Re-send to everyone confirmed, even if already emailed
    python manage.py send_confirmation_emails --resend

    # Limit to one conference (by slug) or a single ticket
    python manage.py send_confirmation_emails --conference akilimo-lagos-2026
    python manage.py send_confirmation_emails --ticket ANC2026-T00001 --resend
"""
from django.core.management.base import BaseCommand, CommandError

from conference.models import Registration
from conference.emails import send_registration_confirmation


class Command(BaseCommand):
    help = "Send receipt + welcome emails to registrations with confirmed payment."

    def add_arguments(self, parser):
        parser.add_argument(
            '--resend', action='store_true',
            help='Include registrations that have already been emailed.',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='List who would be emailed without sending anything.',
        )
        parser.add_argument(
            '--conference', metavar='SLUG',
            help='Limit to a single conference by slug.',
        )
        parser.add_argument(
            '--ticket', metavar='TICKET_ID',
            help='Limit to a single registration by ticket ID.',
        )

    def handle(self, *args, **options):
        resend = options['resend']
        dry_run = options['dry_run']

        qs = Registration.objects.filter(payment_status='confirmed').select_related(
            'conference', 'category'
        )
        if options['conference']:
            qs = qs.filter(conference__slug=options['conference'])
        if options['ticket']:
            qs = qs.filter(ticket_id=options['ticket'])
        if not resend:
            qs = qs.filter(confirmation_email_sent=False)

        qs = qs.order_by('registered_at')
        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.WARNING(
                "No matching confirmed registrations to email."
                + ("" if resend else " (use --resend to include already-emailed ones)")
            ))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"DRY RUN — would email {total} registration(s):\n"
            ))
            for reg in qs:
                flag = "" if not reg.confirmation_email_sent else " (already sent)"
                self.stdout.write(f"  • {reg.ticket_id}  {reg.full_name} <{reg.email}>{flag}")
            return

        self.stdout.write(f"Sending receipt + welcome email to {total} registration(s)...\n")

        sent = 0
        failed = 0
        for reg in qs:
            try:
                send_registration_confirmation(reg)
            except Exception as exc:
                failed += 1
                self.stderr.write(self.style.ERROR(
                    f"  ✗ {reg.ticket_id} <{reg.email}> — {exc}"
                ))
                continue

            if not reg.confirmation_email_sent:
                Registration.objects.filter(pk=reg.pk).update(confirmation_email_sent=True)
            sent += 1
            self.stdout.write(self.style.SUCCESS(f"  ✓ {reg.ticket_id} <{reg.email}>"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done. Sent: {sent}.") + (
            self.style.ERROR(f" Failed: {failed}.") if failed else ""
        ))
        if failed:
            raise CommandError(f"{failed} email(s) failed to send. See errors above.")
