"""
Registration mode helpers.

The site can run registration in one of two modes (Site Settings -> Registration Mode):

* ``free`` - anyone who signs up is immediately given an active membership for the
  current year. Nothing is charged and no Payment record is created.
* ``paid`` - the existing registration fee / annual dues flow is enforced.

Free memberships are flagged with ``Membership.is_free_membership`` so they can be
told apart from paying members, reported on, and revoked when the site switches back
to paid mode.
"""
import logging
from datetime import date

from django.utils import timezone

logger = logging.getLogger(__name__)

FREE = 'free'
PAID = 'paid'


def get_registration_mode():
    """
    Return the current registration mode ('free' or 'paid').

    Defaults to 'free' when settings are unavailable (fresh install, mid-migration)
    so that sign-ups are never blocked by a missing configuration row.
    """
    try:
        from website.models import SiteSettings
        site_settings = SiteSettings.objects.first()
        if site_settings:
            return site_settings.registration_mode
    except Exception:
        pass
    return FREE


def is_free_registration_mode():
    """True when membership is currently free."""
    return get_registration_mode() == FREE


def grant_free_membership(user, membership_type=None, save=True):
    """
    Give ``user`` an active membership for the current year at no charge.

    Safe to call repeatedly: an already-active free membership for the current year
    is left untouched, and a membership that has rolled into a new year is renewed.
    Paying members are never downgraded to a free membership.

    Returns the Membership instance, or None if one could not be created.
    """
    from .models import Membership

    current_year = date.today().year

    defaults = {'status': 'active'}
    if membership_type:
        defaults['membership_type'] = membership_type

    membership, created = Membership.objects.get_or_create(member=user, defaults=defaults)

    type_changed = bool(membership_type) and membership.membership_type != membership_type
    if type_changed:
        membership.membership_type = membership_type

    # A paying member with a live subscription keeps what they paid for.
    if not membership.is_free_membership and membership.has_active_subscription:
        if type_changed:
            membership.save()
        return membership

    already_current = (
        membership.is_free_membership
        and membership.annual_dues_paid_for_year == current_year
        and membership.subscription_end_date == date(current_year, 12, 31)
        and not membership.access_suspended
    )
    if already_current and not created:
        if type_changed:
            membership.save()
        return membership

    membership.is_free_membership = True
    membership.free_membership_granted_at = timezone.now()
    membership.status = 'active'
    membership.access_suspended = False
    membership.access_suspended_reason = ''

    # Registration fee is waived in free mode.
    membership.registration_paid = True
    if not membership.registration_payment_date:
        membership.registration_payment_date = timezone.now()

    # Grant the current subscription year so certificates, ID cards and platform
    # access all unlock through the normal access rules.
    membership.subscription_year = current_year
    membership.annual_dues_paid_for_year = current_year
    membership.subscription_start_date = date(current_year, 1, 1)
    membership.subscription_end_date = date(current_year, 12, 31)

    if save:
        membership.save()

    logger.info(
        "Free membership granted to %s for %s (created=%s)",
        user.get_username(), current_year, created
    )
    return membership


def revoke_free_membership(membership, keep_registration=False):
    """
    Turn a free membership back into an unpaid one.

    ``keep_registration=True`` leaves the registration fee marked as waived and only
    clears the annual dues, so the member is asked to renew rather than to register
    from scratch.
    """
    membership.is_free_membership = False
    membership.free_membership_granted_at = None
    membership.annual_dues_paid_for_year = None
    membership.subscription_start_date = None
    membership.subscription_end_date = None
    membership.last_annual_dues_payment_date = None

    if not keep_registration:
        # Only clear registration if it was never actually paid for.
        has_paid_registration = membership.payments.filter(
            payment_purpose='registration', status='successful'
        ).exists()
        if not has_paid_registration:
            membership.registration_paid = False
            membership.registration_payment_date = None

    membership.status = 'pending'
    membership.save()
    return membership


def ensure_membership_for_user(user, membership_type=None):
    """
    Make sure ``user`` has a membership that reflects the current registration mode.

    In free mode this grants (or renews) a free membership. In paid mode it only
    guarantees that a Membership row exists so the payment flow has something to
    attach to.
    """
    from .models import Membership

    if is_free_registration_mode():
        return grant_free_membership(user, membership_type=membership_type)

    membership, _ = Membership.objects.get_or_create(
        member=user,
        defaults={
            'status': 'pending',
            **({'membership_type': membership_type} if membership_type else {}),
        }
    )
    return membership
