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


def send_verifier_magic_link(verifier, login_url, conference=None):
    """Email a payment verifier a time-limited sign-in link for the
    Payment Verification page."""
    name = verifier.name or "there"
    org = conference.name if conference else "the conference"
    subject = (
        f"Payment Verification access — {conference.name}"
        if conference else "Payment Verification access link"
    )
    text_body = (
        f"Hi {name},\n\n"
        f"Use the link below to sign in to the Payment Verification page for {org}.\n"
        f"This link expires in 2 hours and only works while your access is active.\n\n"
        f"{login_url}\n\n"
        f"If you didn't request this, you can safely ignore this email.\n"
    )
    html_body = (
        '<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:0 auto;color:#222;">'
        '<h2 style="color:#1B5E20;">Payment Verification Access</h2>'
        f'<p>Hi {name},</p>'
        f'<p>Use the button below to sign in to the Payment Verification page for '
        f'<strong>{org}</strong>. This link expires in <strong>2 hours</strong> and only '
        f'works while your access is active.</p>'
        '<p style="text-align:center;margin:2rem 0;">'
        f'<a href="{login_url}" style="background:#1B5E20;color:#fff;text-decoration:none;'
        'padding:0.85rem 1.75rem;border-radius:10px;font-weight:bold;display:inline-block;">'
        'Open Payment Verification</a></p>'
        '<p style="color:#888;font-size:0.85rem;">If the button doesn\'t work, copy and paste this link:<br>'
        f'<a href="{login_url}">{login_url}</a></p>'
        '<p style="color:#888;font-size:0.85rem;">If you didn\'t request this, you can safely ignore this email.</p>'
        '</div>'
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[verifier.email],
        reply_to=[conference.contact_email] if conference and conference.contact_email else None,
    )
    message.attach_alternative(html_body, "text/html")
    try:
        sent = message.send(fail_silently=False)
    except Exception as exc:
        logger.error("Email FAILED [verifier-link] to=%s — %s", verifier.email, exc)
        raise
    logger.info("Email sent [verifier-link] to=%s (accepted=%s)", verifier.email, sent)
    return sent


def send_abstract_reviewer_magic_link(reviewer, login_url, conference=None):
    """Email an abstract reviewer a time-limited sign-in link that opens the
    Abstract Review page."""
    name = reviewer.name or "there"
    org = conference.name if conference else "the conference"
    subject = (
        f"Abstract review access — {conference.name}"
        if conference else "Abstract review access link"
    )
    text_body = (
        f"Hi {name},\n\n"
        f"You've been granted access to view the submitted abstracts for {org}.\n"
        f"Use your personal link below to open the Abstract Review page — it's permanent,\n"
        f"so you can bookmark it and return any time (it works while your access is active).\n\n"
        f"{login_url}\n\n"
        f"Please keep this link private, as anyone with it can view the abstracts.\n"
    )
    html_body = (
        '<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:0 auto;color:#222;">'
        '<h2 style="color:#1B5E20;">Abstract Review Access</h2>'
        f'<p>Hi {name},</p>'
        f'<p>You\'ve been granted access to view the submitted abstracts for '
        f'<strong>{org}</strong>. Use your personal button below to open the Abstract Review page. '
        f'This is a <strong>permanent link</strong> — you can bookmark it and return any time '
        f'(it works while your access is active).</p>'
        '<p style="text-align:center;margin:2rem 0;">'
        f'<a href="{login_url}" style="background:#1B5E20;color:#fff;text-decoration:none;'
        'padding:0.85rem 1.75rem;border-radius:10px;font-weight:bold;display:inline-block;">'
        'Open Abstract Review</a></p>'
        '<p style="color:#888;font-size:0.85rem;">If the button doesn\'t work, copy and paste this link:<br>'
        f'<a href="{login_url}">{login_url}</a></p>'
        '<p style="color:#888;font-size:0.85rem;">Please keep this link private, as anyone with it can view the abstracts.</p>'
        '</div>'
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[reviewer.email],
        reply_to=[conference.contact_email] if conference and conference.contact_email else None,
    )
    message.attach_alternative(html_body, "text/html")
    try:
        sent = message.send(fail_silently=False)
    except Exception as exc:
        logger.error("Email FAILED [abstract-reviewer-link] to=%s — %s", reviewer.email, exc)
        raise
    logger.info("Email sent [abstract-reviewer-link] to=%s (accepted=%s)", reviewer.email, sent)
    return sent


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
