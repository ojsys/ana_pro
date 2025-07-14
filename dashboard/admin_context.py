from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry
from .models import (
    UserProfile, PartnerOrganization, Membership, 
    Payment, AkilimoParticipant, DataSyncLog
)


def admin_context_processor(request):
    """Add dashboard statistics to admin templates"""
    
    if not request.path.startswith('/admin/'):
        return {}
    
    try:
        # Get basic statistics
        total_users = User.objects.count()
        total_partners = PartnerOrganization.objects.filter(is_active=True).count()
        total_memberships = Membership.objects.filter(status='active').count()
        total_participants = AkilimoParticipant.objects.count()
        
        # Get recent users (last 5)
        recent_users = User.objects.order_by('-date_joined')[:5]
        
        # Get recent memberships (last 5)
        recent_memberships = Membership.objects.order_by('-created_at')[:5]
        
        # Get recent activity (last 10 admin actions)
        recent_activity = LogEntry.objects.select_related('user').order_by('-action_time')[:10]
        
        # Get active sessions count (approximate)
        try:
            from django.contrib.sessions.models import Session
            from django.utils import timezone
            active_sessions = Session.objects.filter(expire_date__gte=timezone.now()).count()
        except:
            active_sessions = 0
        
        # Get last sync time (if any)
        last_sync = DataSyncLog.objects.filter(status='success').order_by('-completed_at').first()
        
        return {
            'total_users': total_users,
            'total_partners': total_partners,
            'total_memberships': total_memberships,
            'total_participants': total_participants,
            'recent_users': recent_users,
            'recent_memberships': recent_memberships,
            'recent_activity': recent_activity,
            'active_sessions': active_sessions,
            'last_sync': last_sync.completed_at if last_sync else None,
        }
    except:
        # Return empty context if there are any errors
        return {}