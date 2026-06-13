"""
Signal handlers for conference registration.

When a registration's payment becomes confirmed — whether via the Paystack
callback, a free/waived registration, or a manual confirmation by an admin —
the participant is automatically sent a payment receipt and a welcome email.
"""
import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Registration
from .emails import send_registration_confirmation

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Registration)
def track_registration_status_change(sender, instance, **kwargs):
    """Capture the previous payment status so we can detect transitions."""
    if instance.pk:
        try:
            instance._previous_status = (
                Registration.objects.filter(pk=instance.pk)
                .values_list('payment_status', flat=True)
                .first()
            )
        except Registration.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Registration)
def send_confirmation_on_payment(sender, instance, created, **kwargs):
    """
    Send the receipt and welcome email the first time a registration is
    confirmed. Guarded by ``confirmation_email_sent`` so the emails are
    only ever sent once, regardless of how often the record is saved.
    """
    previous_status = getattr(instance, '_previous_status', None)
    just_confirmed = (
        instance.payment_status == 'confirmed'
        and (created or previous_status != 'confirmed')
    )

    if not just_confirmed or instance.confirmation_email_sent:
        return

    try:
        send_registration_confirmation(instance)
    except Exception as exc:
        # Never let an email failure break the payment/confirmation flow.
        logger.error(
            "Failed to send confirmation emails for registration %s: %s",
            instance.ticket_id, exc, exc_info=True,
        )
        return

    # Mark as sent without re-triggering signals or touching updated_at.
    # The full confirmation includes the receipt, so flag both.
    Registration.objects.filter(pk=instance.pk).update(
        confirmation_email_sent=True, receipt_email_sent=True,
    )
    instance.confirmation_email_sent = True
    instance.receipt_email_sent = True
