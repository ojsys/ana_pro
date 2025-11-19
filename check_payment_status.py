#!/usr/bin/env python
"""
Diagnostic script to check payment and membership status
Run this on the server to debug payment issues
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/home/akilimon/ana_pro')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akilimo_nigeria.settings.production')
django.setup()

from dashboard.models import Payment, Membership
from django.contrib.auth.models import User
from datetime import datetime, timedelta

def check_recent_payments():
    """Check payments from the last 24 hours"""
    print("\n" + "="*60)
    print("RECENT PAYMENTS (Last 24 hours)")
    print("="*60)

    yesterday = datetime.now() - timedelta(days=1)
    recent_payments = Payment.objects.filter(created_at__gte=yesterday).order_by('-created_at')

    if not recent_payments.exists():
        print("❌ NO PAYMENTS in last 24 hours")
        return None

    for payment in recent_payments:
        print(f"\n📄 Payment ID: {payment.payment_id}")
        print(f"   Member: {payment.membership.member.username} ({payment.membership.member.email})")
        print(f"   Amount: ₦{payment.amount:,.2f}")
        print(f"   Status: {payment.status.upper()}")
        print(f"   Purpose: {payment.payment_purpose}")
        print(f"   Subscription Year: {payment.subscription_year or 'N/A'}")
        print(f"   Created: {payment.created_at}")
        print(f"   Paid At: {payment.paid_at or 'Not set'}")
        print(f"   Paystack Ref: {payment.paystack_reference or 'N/A'}")

        # Check associated membership
        membership = payment.membership
        print(f"\n   Associated Membership:")
        print(f"   - Status: {membership.status}")
        print(f"   - Registration Paid: {membership.registration_paid}")
        print(f"   - Annual Dues Year: {membership.annual_dues_paid_for_year or 'Not set'}")
        print(f"   - Subscription Dates: {membership.subscription_start_date} to {membership.subscription_end_date}")
        print(f"   - Has Platform Access: {membership.has_platform_access}")
        print(f"   - Access Suspended: {membership.access_suspended}")

    return recent_payments.first()

def check_signals_deployed():
    """Check if signals.py is deployed and registered"""
    print("\n" + "="*60)
    print("SIGNAL SYSTEM CHECK")
    print("="*60)

    # Check if signals.py exists
    signals_path = '/home/akilimon/ana_pro/dashboard/signals.py'
    if os.path.exists(signals_path):
        print("✓ signals.py file exists")

        # Check if it's imported in apps.py
        apps_path = '/home/akilimon/ana_pro/dashboard/apps.py'
        with open(apps_path, 'r') as f:
            apps_content = f.read()
            if 'import dashboard.signals' in apps_content:
                print("✓ signals imported in apps.py")
            else:
                print("❌ signals NOT imported in apps.py")
                print("   Fix: Add 'import dashboard.signals' to apps.py ready() method")
    else:
        print("❌ signals.py file NOT FOUND")
        print("   This is the problem! The automatic update system is not deployed.")
        print("   Deploy signals.py to enable automatic membership updates.")

    # Check if signal handlers are registered
    from django.db.models import signals
    from dashboard.models import Payment

    post_save_receivers = signals.post_save._live_receivers(Payment)
    if post_save_receivers:
        print(f"✓ {len(post_save_receivers)} signal receivers registered for Payment model")
    else:
        print("❌ NO signal receivers registered for Payment model")
        print("   The automatic update system is not working!")

def check_user_membership(email):
    """Check specific user's membership status"""
    print("\n" + "="*60)
    print(f"USER MEMBERSHIP STATUS: {email}")
    print("="*60)

    try:
        user = User.objects.get(email=email)
        print(f"✓ User found: {user.username}")

        try:
            membership = Membership.objects.get(member=user)
            print(f"\n📋 Membership Details:")
            print(f"   Status: {membership.status}")
            print(f"   Type: {membership.membership_type}")
            print(f"   Registration Paid: {membership.registration_paid}")
            print(f"   Registration Date: {membership.registration_payment_date or 'Not set'}")
            print(f"   Annual Dues Year: {membership.annual_dues_paid_for_year or 'Not set'}")
            print(f"   Subscription Period: {membership.subscription_start_date} to {membership.subscription_end_date}")
            print(f"   Has Platform Access: {membership.has_platform_access}")
            print(f"   Access Suspended: {membership.access_suspended}")
            print(f"   Has Active Subscription: {membership.has_active_subscription}")

            # Check payments
            payments = membership.payments.all().order_by('-created_at')
            print(f"\n💳 Payment History ({payments.count()} total):")
            for payment in payments[:5]:  # Show last 5
                print(f"   - {payment.created_at.strftime('%Y-%m-%d %H:%M')} | "
                      f"{payment.payment_purpose} | "
                      f"₦{payment.amount:,.2f} | "
                      f"{payment.status}")

        except Membership.DoesNotExist:
            print("❌ NO MEMBERSHIP found for this user")

    except User.DoesNotExist:
        print(f"❌ User not found: {email}")

def suggest_fix(payment):
    """Suggest how to fix the issue"""
    print("\n" + "="*60)
    print("SUGGESTED FIX")
    print("="*60)

    if payment:
        if payment.status != 'successful':
            print(f"\n⚠️  Payment status is '{payment.status}' (should be 'successful')")
            print("\nManual Fix:")
            print("1. Go to Django Admin → Payments")
            print(f"2. Find payment: {payment.payment_id}")
            print("3. Change Status to 'Successful'")
            print("4. Save")
            print("5. If signals are deployed, membership will update automatically")
            print("6. If signals NOT deployed, update membership manually")

    print("\n📝 Checklist:")
    print("□ Is signals.py deployed?")
    print("□ Is signals imported in apps.py?")
    print("□ Has the application been restarted?")
    print("□ Is payment status 'successful'?")
    print("□ Is paystack_reference set?")

if __name__ == '__main__':
    print("\n" + "🔍 PAYMENT SYSTEM DIAGNOSTIC")
    print("="*60)

    # Check recent payments
    latest_payment = check_recent_payments()

    # Check signals
    check_signals_deployed()

    # If you know the user's email, check their membership
    if len(sys.argv) > 1:
        user_email = sys.argv[1]
        check_user_membership(user_email)

    # Suggest fix
    suggest_fix(latest_payment)

    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60 + "\n")
