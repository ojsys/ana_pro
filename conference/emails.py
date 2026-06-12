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


def _send(subject, template_base, context, to_email, reply_to=None):
    """Render an HTML/plain-text pair and send a single email."""
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
    message.send(fail_silently=False)


def send_registration_confirmation(registration):
    """
    Send the payment receipt and the welcome email for a confirmed
    registration. Returns True if both emails were sent successfully.
    """
    conference = registration.conference
    reply_to = conference.contact_email or None
    context = {
        'registration': registration,
        'conference': conference,
        'ticket_url': _ticket_url(registration),
    }

    # 1. Payment receipt
    _send(
        subject=f"Payment Receipt — {conference.name} [{registration.ticket_id}]",
        template_base='conference/emails/payment_receipt',
        context=context,
        to_email=registration.email,
        reply_to=reply_to,
    )

    # 2. Conference welcome email
    _send(
        subject=f"Welcome to {conference.name}! 🎉",
        template_base='conference/emails/welcome',
        context=context,
        to_email=registration.email,
        reply_to=reply_to,
    )

    logger.info(
        "Confirmation emails sent for registration %s to %s",
        registration.ticket_id, registration.email,
    )
    return True
