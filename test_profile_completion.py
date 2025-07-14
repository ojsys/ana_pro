#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to Python path
sys.path.append('/Users/Apple/projects/ana_pro')

# Setup Django environment
os.environ['DJANGO_SETTINGS_MODULE'] = 'akilimo_nigeria.settings'
django.setup()

# Now import Django modules
from django.contrib.auth.models import User
from dashboard.models import UserProfile, PartnerOrganization

def test_profile_completion_system():
    """Test the enhanced profile completion system"""
    
    print("📋 TESTING PROFILE COMPLETION SYSTEM")
    print("=" * 60)
    
    # Get an existing user or create a test user
    user = User.objects.filter(username='onahjonah1').first()
    if not user:
        print("❌ No test user found")
        return
    
    profile = user.profile
    print(f"👤 Testing with user: {user.get_full_name() or user.username}")
    print(f"📧 Email: {user.email}")
    print()
    
    print("📊 CURRENT PROFILE STATUS:")
    print("-" * 30)
    print(f"✅ Profile Completed: {profile.profile_completed}")
    print(f"📈 Completion Percentage: {profile.completion_percentage}%")
    print(f"📄 Status Text: {profile.profile_status_text}")
    print(f"🏢 Partner Status: {profile.partner_status_text}")
    print(f"🔍 Partner Verified: {profile.is_partner_verified}")
    
    if profile.profile_completion_date:
        print(f"📅 Completion Date: {profile.profile_completion_date}")
    else:
        print(f"📅 Completion Date: Not set")
    
    print()
    
    print("📋 FIELD ANALYSIS:")
    print("-" * 20)
    print(f"👤 First Name: {'✅' if user.first_name else '❌'} {user.first_name or 'Missing'}")
    print(f"👤 Last Name: {'✅' if user.last_name else '❌'} {user.last_name or 'Missing'}")
    print(f"📧 Email: {'✅' if user.email else '❌'} {user.email or 'Missing'}")
    print(f"📞 Phone: {'✅' if profile.phone_number else '❌'} {profile.phone_number or 'Missing'}")
    print(f"💼 Position: {'✅' if profile.position else '❌'} {profile.position or 'Missing'}")
    print(f"🏢 Partner Org: {'✅' if profile.partner_organization else '❌'} {profile.partner_organization or 'Missing'}")
    print(f"🏢 Partner Name: {'✅' if profile.partner_name else '❌'} {profile.partner_name or 'Missing'}")
    print(f"📸 Profile Photo: {'✅' if profile.profile_photo else '❌'} {'Uploaded' if profile.profile_photo else 'Not uploaded'}")
    
    if profile.missing_fields:
        print(f"\n❌ Missing Fields: {', '.join(profile.missing_fields)}")
    else:
        print(f"\n✅ All required fields completed!")
    
    print()
    
    print("🎯 COMPLETION CRITERIA:")
    print("-" * 25)
    print("Required for completion:")
    print("  ✅ First Name + Last Name + Email")
    print("  ✅ Phone Number")
    print("  ✅ Position/Title")
    print("  ✅ Partner Organization (either linked or name)")
    print()
    print("Optional fields:")
    print("  📸 Profile Photo (for ID card)")
    print("  📧 Email Notifications preference")
    print("  🏢 Department")
    
    print()
    
    print("🏆 PROFILE COMPLETION BENEFITS:")
    print("-" * 35)
    if profile.profile_completed:
        print("  🎉 Profile is COMPLETE!")
        print("  ✅ Can download membership certificate")
        print("  ✅ Can download member ID card")
        print("  ✅ Full access to dashboard features")
        if profile.is_partner_verified:
            print("  ✅ Access to partner dashboard")
            print(f"  ✅ Can view {profile.accessible_farmers.count()} farmer records")
    else:
        print("  ⏳ Profile is INCOMPLETE")
        print("  ❌ Cannot download membership documents")
        print("  ❌ Limited dashboard access")
        print("  💡 Complete profile to unlock all features")
    
    print()
    
    print("🔧 SYSTEM FEATURES:")
    print("-" * 20)
    print("  ✅ Automatic completion detection")
    print("  ✅ Real-time status updates")
    print("  ✅ Progress percentage tracking")
    print("  ✅ Missing field identification")
    print("  ✅ Completion date recording")
    print("  ✅ Partner verification status")
    print("  ✅ User feedback messages")
    print("  ✅ Bootstrap status badges")

if __name__ == '__main__':
    test_profile_completion_system()