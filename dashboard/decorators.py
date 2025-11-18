"""
Access control decorators for dashboard views.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def require_active_subscription(view_func):
    """
    Decorator to require active annual dues subscription.

    Checks that:
    1. User has a membership record
    2. User has paid registration fees
    3. User has an active subscription for the current year
    4. Access is not suspended

    Redirects to appropriate page if requirements not met.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user has a membership
        if not hasattr(request.user, 'membership'):
            messages.error(
                request,
                'You need to complete membership registration before accessing this feature.'
            )
            return redirect('dashboard:register')

        membership = request.user.membership

        # Check if registration is paid
        if not membership.registration_paid:
            messages.warning(
                request,
                'Please complete your registration payment to access platform features.'
            )
            return redirect('dashboard:payment_selection')

        # Check if access is suspended
        if membership.access_suspended:
            messages.error(
                request,
                f'Your access has been suspended. Reason: {membership.access_suspended_reason or "Contact admin for details."}'
            )
            return redirect('dashboard:index')

        # Check if subscription is active
        if not membership.has_active_subscription:
            messages.warning(
                request,
                'Your annual membership subscription has expired. Please renew to continue accessing platform features.'
            )
            return redirect('dashboard:renewal')

        return view_func(request, *args, **kwargs)

    return wrapper


def require_registration_payment(view_func):
    """
    Decorator to require registration payment only (not annual dues).

    Used for basic features that should be accessible after registration
    but before annual dues payment.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user has a membership
        if not hasattr(request.user, 'membership'):
            messages.error(
                request,
                'You need to complete membership registration before accessing this feature.'
            )
            return redirect('dashboard:register')

        membership = request.user.membership

        # Check if registration is paid
        if not membership.registration_paid:
            messages.warning(
                request,
                'Please complete your registration payment to access this feature.'
            )
            return redirect('dashboard:payment_selection')

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_or_subscription_required(view_func):
    """
    Decorator for views that should be accessible by admins regardless of subscription,
    but require active subscription for regular members.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Admins can always access
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # For non-admins, require active subscription
        if not hasattr(request.user, 'membership'):
            messages.error(
                request,
                'You need to complete membership registration before accessing this feature.'
            )
            return redirect('dashboard:register')

        membership = request.user.membership

        if not membership.registration_paid:
            messages.warning(
                request,
                'Please complete your registration payment to access this feature.'
            )
            return redirect('dashboard:payment_selection')

        if membership.access_suspended:
            messages.error(
                request,
                f'Your access has been suspended. Reason: {membership.access_suspended_reason or "Contact admin for details."}'
            )
            return redirect('dashboard:index')

        if not membership.has_active_subscription:
            messages.warning(
                request,
                'Your annual membership subscription has expired. Please renew to continue accessing platform features.'
            )
            return redirect('dashboard:renewal')

        return view_func(request, *args, **kwargs)

    return wrapper
