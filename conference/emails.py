"""
Transactional emails for conference registration.

Sent once a registration's payment is confirmed:
  1. A payment receipt (proof of payment).
  2. A conference welcome email.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _ticket_url(registration):
    """Absolute URL to the public ticket-verification page."""
    base = getattr(settings, 'SITE_URL', '').rstrip('/')
    if not base:
        return ''
    return f"{base}/conference/ticket/{registration.ticket_id}/"


def _send(subject, template_base, context, to_email, reply_to=None, label=None, ref=None):
    """Render an HTML/plain-text pair and send a single email.

    ``label`` (e.g. "receipt"/"welcome") and ``ref`` (e.g. the ticket id) are
    used only for log lines so each email can be traced individually.
    """
    label = label or template_base
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
        reply_to=[reply_to] if reply_to else None,
    )
    message.attach_alternative(html_body, "text/html")
    try:
        sent = message.send(fail_silently=False)
    except Exception as exc:
        logger.error("Email FAILED [%s] ref=%s to=%s — %s", label, ref, to_email, exc)
        raise
    logger.info("Email sent [%s] ref=%s to=%s (accepted=%s)", label, ref, to_email, sent)
    return sent


def _context_for(registration):
    return {
        'registration': registration,
        'conference': registration.conference,
        'ticket_url': _ticket_url(registration),
    }


def send_payment_receipt(registration):
    """Send only the payment receipt (proof the payment was successful)."""
    conference = registration.conference
    ref = registration.ticket_id
    _send(
        subject=f"Payment Receipt — {conference.name} [{ref}]",
        template_base='conference/emails/payment_receipt',
        context=_context_for(registration),
        to_email=registration.email,
        reply_to=conference.contact_email or None,
        label='receipt',
        ref=ref,
    )
    return True


def send_welcome(registration):
    """Send only the conference welcome email."""
    conference = registration.conference
    ref = registration.ticket_id
    _send(
        subject=f"Welcome to {conference.name}! 🎉",
        template_base='conference/emails/welcome',
        context=_context_for(registration),
        to_email=registration.email,
        reply_to=conference.contact_email or None,
        label='welcome',
        ref=ref,
    )
    return True


def send_registration_confirmation(registration):
    """
    Send the payment receipt and the welcome email for a confirmed
    registration. Returns True if both emails were sent successfully.
    """
    # 1. Payment receipt — sent first; proof the payment was successful.
    send_payment_receipt(registration)
    # 2. Conference welcome email — sent after the receipt.
    send_welcome(registration)

    logger.info(
        "Confirmation emails complete [receipt+welcome] ref=%s to=%s",
        registration.ticket_id, registration.email,
    )
    return True
