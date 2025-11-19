"""
Signal handlers for automatic membership updates based on payment status
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date
import logging

from .models import Payment, Membership

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Payment)
def track_payment_status_change(sender, instance, **kwargs):
    """
    Track if payment status is changing to successful.
    This runs before save to capture the old state.
    """
    if instance.pk:  # Only for existing payments
        try:
            old_instance = Payment.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Payment.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Payment)
def update_membership_on_payment_success(sender, instance, created, **kwargs):
    """
    Automatically update membership status when payment is marked as successful.
    This handles both automatic verification and manual admin updates.
    """
    # Check if payment just became successful
    previous_status = getattr(instance, '_previous_status', None)
    is_newly_successful = (
        instance.status == 'successful' and
        (created or previous_status != 'successful')
    )

    if not is_newly_successful:
        return

    try:
        membership = instance.membership

        # Update paid_at if not already set
        if not instance.paid_at:
            instance.paid_at = timezone.now()
            Payment.objects.filter(pk=instance.pk).update(paid_at=timezone.now())

        # Update membership based on payment purpose
        if instance.payment_purpose == 'registration':
            logger.info(f"Updating membership {membership.id} - Registration payment {instance.payment_id} successful")

            membership.registration_paid = True
            membership.registration_payment_date = instance.paid_at or timezone.now()
            membership.status = 'active'

            logger.info(f"Membership {membership.id} registration marked as paid")

        elif instance.payment_purpose == 'annual_dues':
            logger.info(f"Updating membership {membership.id} - Annual dues payment {instance.payment_id} successful for year {instance.subscription_year}")

            if instance.subscription_year:
                membership.annual_dues_paid_for_year = instance.subscription_year
                membership.subscription_start_date = date(instance.subscription_year, 1, 1)
                membership.subscription_end_date = date(instance.subscription_year, 12, 31)
                membership.last_annual_dues_payment_date = instance.paid_at or timezone.now()
                membership.status = 'active'
                membership.access_suspended = False

                logger.info(f"Membership {membership.id} annual dues updated for year {instance.subscription_year}")
            else:
                logger.warning(f"Payment {instance.payment_id} is for annual_dues but has no subscription_year")

        # Save membership changes
        membership.save()

        logger.info(f"Membership {membership.id} successfully updated from payment {instance.payment_id}")

    except Membership.DoesNotExist:
        logger.error(f"Payment {instance.payment_id} has no associated membership")
    except Exception as e:
        logger.error(f"Error updating membership from payment {instance.payment_id}: {str(e)}", exc_info=True)


@receiver(post_save, sender=Payment)
def log_payment_status_change(sender, instance, created, **kwargs):
    """
    Log all payment status changes for audit trail
    """
    if created:
        logger.info(f"New payment created: {instance.payment_id} - Status: {instance.status} - Purpose: {instance.payment_purpose}")
    else:
        previous_status = getattr(instance, '_previous_status', None)
        if previous_status and previous_status != instance.status:
            logger.info(
                f"Payment {instance.payment_id} status changed: {previous_status} -> {instance.status} "
                f"(Membership: {instance.membership.id}, Purpose: {instance.payment_purpose})"
            )
