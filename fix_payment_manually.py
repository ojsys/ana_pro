#!/usr/bin/env python
"""
Manual fix script for payment issues
Use this to manually update membership when payment is stuck
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/home/akilimon/ana_pro')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akilimo_nigeria.settings.production')
django.setup()

from dashboard.models import Payment, Membership
from django.utils import timezone
from datetime import date

def fix_payment_by_id(payment_id):
    """Fix a specific payment by ID"""
    try:
        payment = Payment.objects.get(payment_id=payment_id)
        print(f"Found payment: {payment.payment_id}")
        print(f"Current status: {payment.status}")
        print(f"Member: {payment.membership.member.email}")

        # Update payment status
        if payment.status != 'successful':
            payment.status = 'successful'
            if not payment.paid_at:
                payment.paid_at = timezone.now()
            payment.save()
            print("✓ Payment status updated to 'successful'")

        # Update membership
        membership = payment.membership

        if payment.payment_purpose == 'registration':
            membership.registration_paid = True
            membership.registration_payment_date = payment.paid_at or timezone.now()
            membership.status = 'active'
            print("✓ Registration marked as paid")

        elif payment.payment_purpose == 'annual_dues':
            if payment.subscription_year:
                membership.annual_dues_paid_for_year = payment.subscription_year
                membership.subscription_start_date = date(payment.subscription_year, 1, 1)
                membership.subscription_end_date = date(payment.subscription_year, 12, 31)
                membership.last_annual_dues_payment_date = payment.paid_at or timezone.now()
                membership.status = 'active'
                membership.access_suspended = False
                print(f"✓ Annual dues marked as paid for {payment.subscription_year}")
            else:
                print("⚠️  No subscription_year set on payment")

        membership.save()
        print("✓ Membership updated successfully")
        print(f"\nMembership Status: {membership.status}")
        print(f"Has Platform Access: {membership.has_platform_access}")
        print(f"Annual Dues Year: {membership.annual_dues_paid_for_year}")

    except Payment.DoesNotExist:
        print(f"❌ Payment not found: {payment_id}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def fix_latest_payment_for_user(email):
    """Fix the latest payment for a specific user"""
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(email=email)
        membership = Membership.objects.get(member=user)

        latest_payment = membership.payments.order_by('-created_at').first()

        if latest_payment:
            print(f"Found latest payment for {email}")
            fix_payment_by_id(str(latest_payment.payment_id))
        else:
            print(f"❌ No payments found for {email}")

    except User.DoesNotExist:
        print(f"❌ User not found: {email}")
    except Membership.DoesNotExist:
        print(f"❌ Membership not found for {email}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    print("\n🔧 MANUAL PAYMENT FIX SCRIPT")
    print("="*60)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_payment_manually.py <payment_id>")
        print("  python fix_payment_manually.py email@example.com")
        print("\nExample:")
        print("  python fix_payment_manually.py abc123-def456")
        print("  python fix_payment_manually.py user@example.com")
        sys.exit(1)

    arg = sys.argv[1]

    if '@' in arg:
        # Email provided
        fix_latest_payment_for_user(arg)
    else:
        # Payment ID provided
        fix_payment_by_id(arg)

    print("="*60 + "\n")
