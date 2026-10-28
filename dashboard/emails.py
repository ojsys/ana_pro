"""
Transactional emails for membership.

  1. A welcome email when an organization signs up, pointing the admin to the
     dashboard to pay (or, in free mode, telling them their membership is active).
  2. Once a payment succeeds: a registration confirmation (registration fee only)
     and a receipt of payment, sent to the person who paid.
"""
import logging
from datetime import date

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _absolute_url(url_name):
    return getattr(settings, 'SITE_URL', '').rstrip('/') + reverse(url_name)


def _site_context():
    from website.models import SiteSettings
    site = SiteSettings.objects.first()
    return {
        'site_name': site.site_title if site else 'AKILIMO Nigeria Association',
        'contact_email': site.primary_email if site else '',
        'contact_phone': site.primary_phone if site else '',
        'dashboard_url': _absolute_url('dashboard:home'),
    }


def _send(subject, template_base, context, to_email, label):
    """Render an HTML/plain-text pair and send a single email."""
    context = {**_site_context(), **context}
    html_body = render_to_string(f"{template_base}.html", context)
    try:
        text_body = render_to_string(f"{template_base}.txt", context)
    except Exception:
        text_body = strip_tags(html_body)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
        reply_to=[context['contact_email']] if context['contact_email'] else None,
    )
    message.attach_alternative(html_body, "text/html")
    try:
        sent = message.send(fail_silently=False)
    except Exception as exc:
        logger.error("Email FAILED [%s] to=%s — %s", label, to_email, exc)
        raise
    logger.info("Email sent [%s] to=%s (accepted=%s)", label, to_email, sent)
    return sent


def send_welcome_email(user):
    """Welcome a newly signed-up organization admin and point them to payment."""
    from .membership_service import get_billing_organization, get_membership_fee, is_free_registration_mode
    from .models import MAX_ORGANIZATION_MEMBERS

    free = is_free_registration_mode()
    return _send(
        subject="Welcome to AKILIMO Nigeria Association",
        template_base='dashboard/emails/welcome',
        context={
            'user': user,
            'organization': get_billing_organization(user),
            'free_registration': free,
            'registration_fee': None if free else get_membership_fee(user, 'registration'),
            'annual_dues': None if free else get_membership_fee(user, 'annual_dues'),
            'year': date.today().year,
            'payment_url': _absolute_url('dashboard:payment_selection'),
            'max_members': MAX_ORGANIZATION_MEMBERS,
        },
        to_email=user.email,
        label='welcome',
    )


def _payment_context(payment):
    from .membership_service import get_billing_organization
    user = payment.membership.member
    organization = get_billing_organization(user)
    return {
        'user': user,
        'payment': payment,
        'organization': organization,
        'membership_type': organization.membership_category if organization else None,
        'receipt_number': payment.paystack_reference or str(payment.payment_id)[:8].upper(),
    }


def send_registration_confirmation(payment):
    context = _payment_context(payment)
    return _send(
        subject="Your AKILIMO Nigeria Association membership is confirmed",
        template_base='dashboard/emails/registration_confirmed',
        context=context,
        to_email=context['user'].email,
        label='registration-confirmed',
    )


def send_payment_receipt(payment):
    context = _payment_context(payment)
    return _send(
        subject=f"Payment receipt — {payment.get_payment_purpose_display()} [{context['receipt_number']}]",
        template_base='dashboard/emails/payment_receipt',
        context=context,
        to_email=context['user'].email,
        label='receipt',
    )


def send_payment_emails(payment_id):
    """
    Send the confirmation (for a registration fee) and the receipt for a successful
    payment, once. The payment is claimed before sending so the Paystack callback
    and webhook can't both email the member; if sending fails the claim is
    released so the receipt can be resent from the admin.
    """
    from .models import Payment

    claimed = Payment.objects.filter(
        pk=payment_id, status='successful', receipt_email_sent_at__isnull=True,
    ).update(receipt_email_sent_at=timezone.now())
    if not claimed:
        return False

    payment = Payment.objects.select_related('membership__member__profile').get(pk=payment_id)
    if not payment.membership.member.email:
        logger.warning("Payment %s: payer has no email address, receipt not sent", payment.payment_id)
        return False
    try:
        if payment.payment_purpose == 'registration':
            send_registration_confirmation(payment)
        send_payment_receipt(payment)
    except Exception:
        Payment.objects.filter(pk=payment_id).update(receipt_email_sent_at=None)
        logger.error("Payment %s: confirmation emails not sent", payment.payment_id, exc_info=True)
        return False
    return True
