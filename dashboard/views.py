from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Count, Q, Avg, F, Case, When, IntegerField
from datetime import datetime, timedelta
import logging

from .models import (ParticipantRecord, AkilimoParticipant, DashboardMetrics,
                    DataSyncLog, APIConfiguration, UserProfile, PartnerOrganization, Membership, MembershipPricing)
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .services import AkilimoDataService
from .decorators import require_active_subscription

logger = logging.getLogger(__name__)

@method_decorator(require_active_subscription, name='dispatch')
class DashboardHomeView(TemplateView):
    """Main dashboard view - requires active subscription"""
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get selected country from query parameters (default to Nigeria for AKILIMO Nigeria Association)
        selected_country = self.request.GET.get('country', 'nigeria').lower()
        
        # Get list of available countries
        available_countries = AkilimoParticipant.objects.exclude(
            country__isnull=True
        ).exclude(country='').values('country').annotate(
            count=Count('id')
        ).order_by('country')
        
        # Use the new AkilimoParticipant model with fallback to legacy
        if AkilimoParticipant.objects.exists():
            # Filter queryset by selected country (or show all if 'all' is selected)
            if selected_country == 'all':
                country_queryset = AkilimoParticipant.objects.all()
            else:
                country_queryset = AkilimoParticipant.objects.filter(country__iexact=selected_country)
            
            # Get basic metrics from new model (filtered by country)
            total_participants = country_queryset.count()
            
            # Gender distribution
            gender_stats = country_queryset.values('farmer_gender').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Calculate male/female counts
            male_count = country_queryset.filter(farmer_gender__icontains='male').exclude(farmer_gender__icontains='female').count()
            female_count = country_queryset.filter(farmer_gender__icontains='female').count()
            
            # Geographic distribution (admin_level1 = state)
            state_stats = country_queryset.exclude(
                admin_level1__isnull=True
            ).exclude(admin_level1='').values('admin_level1').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # City distribution
            city_stats = country_queryset.exclude(
                event_city__isnull=True
            ).exclude(event_city='').values('event_city').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Crop distribution
            crop_stats = country_queryset.exclude(
                crop__isnull=True
            ).exclude(crop='').values('crop').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Partner distribution
            partner_stats = country_queryset.exclude(
                partner__isnull=True
            ).exclude(partner='').values('partner').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Event types distribution
            event_type_stats = country_queryset.exclude(
                event_type__isnull=True
            ).exclude(event_type='').values('event_type').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            # Age category distribution
            age_category_stats = country_queryset.exclude(
                age_category__isnull=True
            ).exclude(age_category='').values('age_category').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            # Monthly participation trends (based on event dates)
            monthly_trend = []
            from django.utils import timezone
            from calendar import monthrange
            
            for i in range(12):
                # Calculate month boundaries properly
                today = timezone.now().date()
                target_date = today.replace(day=1) - timedelta(days=30*i)
                month_start = target_date.replace(day=1)
                month_end = target_date.replace(day=monthrange(target_date.year, target_date.month)[1])
                
                count = country_queryset.filter(
                    event_date__gte=month_start,
                    event_date__lte=month_end
                ).count()
                
                monthly_trend.append({
                    'month': month_start.strftime('%B %Y'),
                    'count': count
                })
            
            monthly_trend.reverse()
            
            # Recent training sessions
            recent_trainings = country_queryset.filter(
                event_date__isnull=False
            ).order_by('-event_date')[:10]
            
            # Count farmers with phone numbers
            farmers_with_phones = country_queryset.exclude(
                farmer_phone_no__isnull=True
            ).exclude(farmer_phone_no='').count()
            
            # Count unique events
            unique_events = country_queryset.values(
                'event_date', 'event_venue', 'event_type'
            ).distinct().count()
            
            # Count extension agents (organizational contacts)
            extension_agents = country_queryset.exclude(
                org_first_name__isnull=True
            ).exclude(org_first_name='').values(
                'org_first_name', 'org_surname', 'org_phone_no', 'partner'
            ).distinct().count()
            
            # Count unique partners
            unique_partners = country_queryset.exclude(
                partner__isnull=True
            ).exclude(partner='').values('partner').distinct().count()
            
            # Count unique states
            unique_states = country_queryset.exclude(
                admin_level1__isnull=True
            ).exclude(admin_level1='').values('admin_level1').distinct().count()
            
            # Count unique cities
            unique_cities = country_queryset.exclude(
                event_city__isnull=True
            ).exclude(event_city='').values('event_city').distinct().count()
            
            # Rename for template compatibility
            gender_stats = [{'gender': item['farmer_gender'], 'count': item['count']} for item in gender_stats]
            state_stats = [{'state': item['admin_level1'], 'count': item['count']} for item in state_stats]
            city_stats = [{'event_city': item['event_city'], 'count': item['count']} for item in city_stats]
            partner_stats = [{'partner': item['partner'], 'count': item['count']} for item in partner_stats]
            
            # No yield data in current model, so set to empty
            yield_improvement = {'avg_previous': None, 'avg_expected': None}
            
        else:
            # Fallback to legacy model
            total_participants = ParticipantRecord.objects.count()
            male_count = ParticipantRecord.objects.filter(gender__icontains='male').exclude(gender__icontains='female').count()
            female_count = ParticipantRecord.objects.filter(gender__icontains='female').count()
            farmers_with_phones = 0
            unique_events = ParticipantRecord.objects.values('training_date', 'facilitator').distinct().count()
            
            # Gender distribution
            gender_stats = ParticipantRecord.objects.values('gender').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # State distribution
            state_stats = ParticipantRecord.objects.values('state').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Recent training sessions
            recent_trainings = ParticipantRecord.objects.filter(
                training_date__isnull=False
            ).order_by('-training_date')[:10]
            
            # Empty data for features not available in legacy model
            city_stats = []
            crop_stats = []
            partner_stats = []
            event_type_stats = []
            age_category_stats = []
            monthly_trend = []
            
            # Yield improvement metrics
            yield_improvement = ParticipantRecord.objects.filter(
                previous_yield__isnull=False,
                expected_yield__isnull=False
            ).aggregate(
                avg_previous=Avg('previous_yield'),
                avg_expected=Avg('expected_yield')
            )
        
        context.update({
            'total_participants': total_participants,
            'male_count': male_count,
            'female_count': female_count,
            'farmers_with_phones': farmers_with_phones,
            'unique_events': unique_events,
            'extension_agents': locals().get('extension_agents', 0),
            'unique_partners': locals().get('unique_partners', 0),
            # Template expects these specific variable names
            'total_states_count': locals().get('unique_states', 0),
            'total_cities_count': locals().get('unique_cities', 0), 
            'total_partner_organizations': locals().get('unique_partners', 0),
            'gender_stats': list(gender_stats),
            'state_stats': list(state_stats),
            'city_stats': list(city_stats),
            'crop_stats': list(crop_stats),
            'partner_stats': list(partner_stats),
            'event_type_stats': list(event_type_stats),
            'age_category_stats': list(age_category_stats),
            'monthly_trend': monthly_trend,
            'recent_trainings': recent_trainings,
            'yield_improvement': yield_improvement,
            # Country filtering
            'selected_country': selected_country,
            'available_countries': list(available_countries),
        })
        
        return context

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_participants_summary(request):
    """API endpoint for participants summary data"""
    
    # Time filter
    days_filter = request.GET.get('days', 30)
    try:
        days_filter = int(days_filter)
        start_date = datetime.now().date() - timedelta(days=days_filter)
        participants_qs = ParticipantRecord.objects.filter(created_at__gte=start_date)
    except (ValueError, TypeError):
        participants_qs = ParticipantRecord.objects.all()
    
    # State filter
    state_filter = request.GET.get('state')
    if state_filter:
        participants_qs = participants_qs.filter(state__icontains=state_filter)
    
    # Gender filter
    gender_filter = request.GET.get('gender')
    if gender_filter:
        participants_qs = participants_qs.filter(gender__icontains=gender_filter)
    
    # Calculate metrics
    total_count = participants_qs.count()
    
    gender_distribution = participants_qs.values('gender').annotate(
        count=Count('id')
    ).order_by('-count')
    
    state_distribution = participants_qs.values('state').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Monthly trend (last 12 months)
    monthly_trend = []
    for i in range(12):
        month_start = (datetime.now().date().replace(day=1) - timedelta(days=30*i))
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end - timedelta(days=month_end.day)
        
        count = participants_qs.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        ).count()
        
        monthly_trend.append({
            'month': month_start.strftime('%B %Y'),
            'count': count
        })
    
    monthly_trend.reverse()
    
    return Response({
        'total_participants': total_count,
        'gender_distribution': list(gender_distribution),
        'state_distribution': list(state_distribution),
        'monthly_trend': monthly_trend,
        'filter_applied': {
            'days': days_filter,
            'state': state_filter,
            'gender': gender_filter
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_yield_metrics(request):
    """API endpoint for yield improvement metrics"""
    
    participants_with_yield = ParticipantRecord.objects.filter(
        previous_yield__isnull=False,
        expected_yield__isnull=False
    )
    
    # Calculate yield improvements
    yield_data = []
    total_improvement = 0
    improvement_count = 0
    
    for participant in participants_with_yield:
        if participant.previous_yield and participant.expected_yield:
            improvement = participant.expected_yield - participant.previous_yield
            improvement_percentage = (improvement / participant.previous_yield) * 100 if participant.previous_yield > 0 else 0
            
            yield_data.append({
                'participant_id': participant.external_id,
                'location': participant.location,
                'state': participant.state,
                'previous_yield': participant.previous_yield,
                'expected_yield': participant.expected_yield,
                'improvement': improvement,
                'improvement_percentage': round(improvement_percentage, 2)
            })
            
            total_improvement += improvement_percentage
            improvement_count += 1
    
    avg_improvement = total_improvement / improvement_count if improvement_count > 0 else 0
    
    # State-wise yield improvements
    state_yield_metrics = participants_with_yield.values('state').annotate(
        participant_count=Count('id'),
        avg_previous_yield=Avg('previous_yield'),
        avg_expected_yield=Avg('expected_yield')
    ).order_by('-participant_count')
    
    return Response({
        'total_participants_with_yield_data': improvement_count,
        'average_yield_improvement_percentage': round(avg_improvement, 2),
        'yield_improvements': yield_data[:50],  # Limit to 50 for performance
        'state_yield_metrics': list(state_yield_metrics)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_sync_data(request):
    """API endpoint to sync data from EiA MELIA API"""
    
    try:
        # Get API configuration
        api_config = APIConfiguration.objects.filter(is_active=True).first()
        if not api_config or not api_config.token:
            return Response({
                'error': 'API configuration not found or token missing'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create sync log entry
        sync_log = DataSyncLog.objects.create(
            sync_type='participants',
            status='started',
            initiated_by=request.user
        )
        
        try:
            # Initialize data service
            data_service = AkilimoDataService(api_config.token)
            
            # Get all participants data
            participants_data = data_service.get_all_akilimo_participants()
            
            created_count = 0
            updated_count = 0
            
            for participant_data in participants_data:
                external_id = participant_data.get('id', str(participant_data.get('participant_id', '')))
                
                if not external_id:
                    continue
                
                # Extract relevant fields from API response
                participant_record, created = ParticipantRecord.objects.update_or_create(
                    external_id=external_id,
                    defaults={
                        'gender': participant_data.get('gender'),
                        'age_group': participant_data.get('age_group'),
                        'location': participant_data.get('location'),
                        'state': participant_data.get('state'),
                        'lga': participant_data.get('lga'),
                        'event_type': participant_data.get('event_type'),
                        'facilitator': participant_data.get('facilitator'),
                        'farm_size': participant_data.get('farm_size'),
                        'previous_yield': participant_data.get('previous_yield'),
                        'expected_yield': participant_data.get('expected_yield'),
                        'raw_data': participant_data
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # Update sync log
            sync_log.records_processed = len(participants_data)
            sync_log.records_created = created_count
            sync_log.records_updated = updated_count
            sync_log.mark_completed('success')
            
            return Response({
                'message': 'Data sync completed successfully',
                'records_processed': len(participants_data),
                'records_created': created_count,
                'records_updated': updated_count
            })
            
        except Exception as e:
            logger.error(f"Data sync failed: {e}")
            sync_log.mark_completed('failed', str(e))
            
            return Response({
                'error': 'Data sync failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Sync API error: {e}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(require_active_subscription, name='dispatch')
class ParticipantsListView(TemplateView):
    """View for participants list page - requires active subscription"""
    template_name = 'dashboard/participants.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        state_filter = self.request.GET.get('state', '')
        gender_filter = self.request.GET.get('gender', '')
        search_query = self.request.GET.get('search', '')
        
        # Use new model if available, fallback to legacy
        if AkilimoParticipant.objects.exists():
            # Filter participants using new model
            participants = AkilimoParticipant.objects.all()
            
            if state_filter:
                participants = participants.filter(admin_level1__icontains=state_filter)
            
            if gender_filter:
                participants = participants.filter(farmer_gender__icontains=gender_filter)
            
            if search_query:
                participants = participants.filter(
                    Q(external_id__icontains=search_query) |
                    Q(farmer_first_name__icontains=search_query) |
                    Q(farmer_surname__icontains=search_query) |
                    Q(event_city__icontains=search_query) |
                    Q(admin_level1__icontains=search_query) |
                    Q(partner__icontains=search_query)
                )
            
            # Get unique values for filters
            unique_states = AkilimoParticipant.objects.values_list('admin_level1', flat=True).distinct()
            unique_genders = AkilimoParticipant.objects.values_list('farmer_gender', flat=True).distinct()
        
        else:
            # Fallback to legacy model
            participants = ParticipantRecord.objects.all()
            
            if state_filter:
                participants = participants.filter(state__icontains=state_filter)
            
            if gender_filter:
                participants = participants.filter(gender__icontains=gender_filter)
        
        if search_query:
            participants = participants.filter(
                Q(location__icontains=search_query) |
                Q(external_id__icontains=search_query) |
                Q(facilitator__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(participants, 25)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get unique values for filters
        unique_states = ParticipantRecord.objects.values_list('state', flat=True).distinct()
        unique_genders = ParticipantRecord.objects.values_list('gender', flat=True).distinct()
        
        context.update({
            'participants': page_obj,
            'unique_states': [s for s in unique_states if s],
            'unique_genders': [g for g in unique_genders if g],
            'current_filters': {
                'state': state_filter,
                'gender': gender_filter,
                'search': search_query
            }
        })
        
        return context


# Authentication Views

class CustomLoginView(LoginView):
    """Custom login view with enhanced styling"""
    form_class = CustomAuthenticationForm
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to appropriate dashboard after login"""
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.can_view_partner_data:
            return reverse('dashboard:partner_dashboard')
        return reverse('dashboard:home')
    
    def form_valid(self, form):
        """Add success message on successful login"""
        messages.success(self.request, f'Welcome back, {form.get_user().get_full_name() or form.get_user().username}!')
        return super().form_valid(form)


def debug_logout_view(request):
    """Production-ready logout view"""
    from django.contrib.auth import logout
    from django.http import HttpResponse
    from django.conf import settings
    
    try:
        # Log user out if authenticated
        if request.user.is_authenticated:
            user_info = f'Logging out user: {request.user.username}'
            logout(request)
            messages.success(request, 'You have been successfully logged out.')
        else:
            user_info = 'No user was logged in.'
        
        # In production, redirect to login page
        if not settings.DEBUG:
            return redirect('dashboard:login')
        
        # In debug mode, show information
        return HttpResponse(f'{user_info}<br><a href="/dashboard/login/">Go to Login</a>', content_type='text/html')
        
    except Exception as e:
        if not settings.DEBUG:
            # In production, always redirect to login even on error
            return redirect('dashboard:login')
        return HttpResponse(f'Logout error: {str(e)}<br>Type: {type(e).__name__}', status=500)


@csrf_exempt
def custom_logout_view(request):
    """Custom logout view that handles both GET and POST"""
    from django.contrib.auth import logout
    from django.http import HttpResponse
    
    try:
        if request.user.is_authenticated:
            messages.info(request, 'You have been successfully logged out.')
            logout(request)
        
        return redirect('dashboard:login')
    except Exception as e:
        # Debug: Return the error as text
        return HttpResponse(f'Logout error: {str(e)}', status=500)


# Keep the class-based view as backup
@method_decorator(csrf_exempt, name='dispatch')
class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('dashboard:login')
    http_method_names = ['get', 'post']  # Allow both GET and POST
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests for logout"""
        return self.post(request, *args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been successfully logged out.')
        return super().dispatch(request, *args, **kwargs)


class RegisterView(FormView):
    """User registration view"""
    form_class = CustomUserCreationForm
    template_name = 'auth/register.html'
    success_url = reverse_lazy('dashboard:profile_setup')
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users"""
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Create user and log them in"""
        user = form.save()
        # Specify the backend when logging in with multiple backends configured
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(
            self.request, 
            f'Welcome to AKILIMO Nigeria, {user.get_full_name()}! Your account has been created successfully.'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partner_organizations'] = PartnerOrganization.objects.filter(is_active=True)
        return context


@login_required
def profile_setup(request):
    """Profile setup page for new users"""
    profile = request.user.profile
    
    if profile.profile_completed:
        messages.info(request, 'Your profile is already completed.')
        return redirect('dashboard:profile')
    
    messages.info(
        request,
        'Please complete your profile setup. You can update this information later from your profile page.'
    )
    return redirect('dashboard:profile')


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view and edit"""
    template_name = 'auth/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get or create profile for current user
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        context['form'] = UserProfileForm(instance=profile, user=self.request.user)
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle profile update"""
        # Get or create profile for current user
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(
            request.POST,
            instance=profile,
            user=request.user
        )
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('dashboard:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)


@method_decorator(require_active_subscription, name='dispatch')
class PartnerDashboardView(LoginRequiredMixin, TemplateView):
    """Partner-specific dashboard view - requires active subscription"""
    template_name = 'dashboard/partner_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        """Check if user can access partner dashboard"""
        # Additional partner-specific check (subscription check happens via decorator)
        if not hasattr(request.user, 'profile') or not request.user.profile.partner_name:
            messages.error(request, 'You do not have access to partner-specific data. Please ensure you have a partner organization assigned.')
            return redirect('dashboard:home')

        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.request.user.profile
        partner_name = user_profile.partner_name
        
        # Get partner-specific farmers using partner_name
        partner_farmers = AkilimoParticipant.objects.filter(partner=partner_name)
        
        # Partner metrics
        total_partner_farmers = partner_farmers.count()
        
        # Gender distribution for partner
        partner_gender_stats = partner_farmers.values('farmer_gender').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Geographic distribution for partner
        partner_state_stats = partner_farmers.values('admin_level1').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # City distribution for partner
        partner_city_stats = partner_farmers.values('event_city').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Crop distribution for partner
        partner_crop_stats = partner_farmers.exclude(
            crop__isnull=True
        ).exclude(crop='').values('crop').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Recent events for partner
        recent_partner_events = partner_farmers.filter(
            event_date__isnull=False
        ).order_by('-event_date')[:10]
        
        # Event types for partner
        partner_event_types = partner_farmers.exclude(
            event_type__isnull=True
        ).exclude(event_type='').values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Monthly trends for partner (last 12 months)
        monthly_trend = []
        for i in range(12):
            month_start = (datetime.now().date().replace(day=1) - timedelta(days=30*i))
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end - timedelta(days=month_end.day)
            
            count = partner_farmers.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            
            monthly_trend.append({
                'month': month_start.strftime('%B %Y'),
                'count': count
            })
        
        monthly_trend.reverse()
        
        context.update({
            'partner_name': partner_name,
            'total_partner_farmers': total_partner_farmers,
            'partner_gender_stats': list(partner_gender_stats),
            'partner_state_stats': list(partner_state_stats),
            'partner_city_stats': list(partner_city_stats),
            'partner_crop_stats': list(partner_crop_stats),
            'recent_partner_events': recent_partner_events,
            'partner_event_types': list(partner_event_types),
            'monthly_trend': monthly_trend,
        })
        
        return context


@method_decorator(require_active_subscription, name='dispatch')
class PartnerDataView(LoginRequiredMixin, TemplateView):
    """Partner-specific data overview - requires active subscription"""
    template_name = 'dashboard/partner_data.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.partner_name:
            messages.error(request, 'You do not have access to partner-specific data.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.request.user.profile
        partner_name = user_profile.partner_name
        
        # Partner-specific data
        partner_farmers = AkilimoParticipant.objects.filter(partner=partner_name)
        
        # Basic statistics
        total_farmers = partner_farmers.count()
        
        # Events organized by partner
        partner_events = partner_farmers.filter(
            event_date__isnull=False
        ).values('event_date', 'event_venue', 'event_type', 'event_city').distinct()
        
        # Cities of influence
        cities_of_influence = partner_farmers.exclude(
            event_city__isnull=True
        ).exclude(event_city='').values('event_city').annotate(
            farmer_count=Count('id'),
            event_count=Count('event_date', distinct=True)
        ).order_by('-farmer_count')
        
        # States of influence
        states_of_influence = partner_farmers.exclude(
            admin_level1__isnull=True
        ).exclude(admin_level1='').values('admin_level1').annotate(
            farmer_count=Count('id'),
            city_count=Count('event_city', distinct=True)
        ).order_by('-farmer_count')
        
        # Crops promoted
        crops_promoted = partner_farmers.exclude(
            crop__isnull=True
        ).exclude(crop='').values('crop').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Training methods/event types
        training_methods = partner_farmers.exclude(
            event_type__isnull=True
        ).exclude(event_type='').values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Monthly activity (last 12 months)
        monthly_activity = []
        for i in range(12):
            month_start = (datetime.now().date().replace(day=1) - timedelta(days=30*i))
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end - timedelta(days=month_end.day)
            
            count = partner_farmers.filter(
                event_date__gte=month_start,
                event_date__lte=month_end
            ).count()
            
            monthly_activity.append({
                'month': month_start.strftime('%B %Y'),
                'count': count
            })
        
        monthly_activity.reverse()
        
        context.update({
            'partner_name': partner_name,
            'total_farmers': total_farmers,
            'partner_events': partner_events,
            'cities_of_influence': list(cities_of_influence),
            'states_of_influence': list(states_of_influence),
            'crops_promoted': list(crops_promoted),
            'training_methods': list(training_methods),
            'monthly_activity': monthly_activity,
        })
        
        return context


@method_decorator(require_active_subscription, name='dispatch')
class PartnerFarmersView(LoginRequiredMixin, TemplateView):
    """Partner-specific farmer demographics and details - requires active subscription"""
    template_name = 'dashboard/partner_farmers.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.partner_name:
            messages.error(request, 'You do not have access to partner-specific data.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.request.user.profile
        partner_name = user_profile.partner_name
        
        # Get filter parameters
        state_filter = self.request.GET.get('state', '')
        gender_filter = self.request.GET.get('gender', '')
        age_filter = self.request.GET.get('age_category', '')
        
        # Partner-specific farmers
        partner_farmers = AkilimoParticipant.objects.filter(partner=partner_name)
        
        # Apply filters
        if state_filter:
            partner_farmers = partner_farmers.filter(admin_level1__icontains=state_filter)
        if gender_filter:
            partner_farmers = partner_farmers.filter(farmer_gender__icontains=gender_filter)
        if age_filter:
            partner_farmers = partner_farmers.filter(age_category__icontains=age_filter)
        
        # Demographics
        gender_distribution = partner_farmers.values('farmer_gender').annotate(
            count=Count('id')
        ).order_by('-count')
        
        age_distribution = partner_farmers.exclude(
            age_category__isnull=True
        ).exclude(age_category='').values('age_category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Geographic distribution
        state_distribution = partner_farmers.exclude(
            admin_level1__isnull=True
        ).exclude(admin_level1='').values('admin_level1').annotate(
            count=Count('id')
        ).order_by('-count')
        
        city_distribution = partner_farmers.exclude(
            event_city__isnull=True
        ).exclude(event_city='').values('event_city').annotate(
            count=Count('id')
        ).order_by('-count')[:20]
        
        # Phone access
        farmers_with_phones = partner_farmers.exclude(
            farmer_phone_no__isnull=True
        ).exclude(farmer_phone_no='').count()
        
        farmers_own_phones = partner_farmers.filter(
            farmer_own_phone__icontains='yes'
        ).count()
        
        # Recent farmers (pagination)
        from django.core.paginator import Paginator
        paginator = Paginator(partner_farmers.order_by('-created_at'), 25)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Filter options for dropdowns
        unique_states = partner_farmers.exclude(
            admin_level1__isnull=True
        ).exclude(admin_level1='').values_list('admin_level1', flat=True).distinct()
        
        unique_genders = partner_farmers.exclude(
            farmer_gender__isnull=True
        ).exclude(farmer_gender='').values_list('farmer_gender', flat=True).distinct()
        
        unique_ages = partner_farmers.exclude(
            age_category__isnull=True
        ).exclude(age_category='').values_list('age_category', flat=True).distinct()
        
        # Calculate percentages
        total_count = partner_farmers.count()
        phone_percentage = (farmers_with_phones * 100 / total_count) if total_count > 0 else 0
        own_phone_percentage = (farmers_own_phones * 100 / total_count) if total_count > 0 else 0
        
        context.update({
            'partner_name': partner_name,
            'total_farmers': total_count,
            'gender_distribution': list(gender_distribution),
            'age_distribution': list(age_distribution),
            'state_distribution': list(state_distribution),
            'city_distribution': list(city_distribution),
            'farmers_with_phones': farmers_with_phones,
            'farmers_own_phones': farmers_own_phones,
            'phone_percentage': round(phone_percentage, 1),
            'own_phone_percentage': round(own_phone_percentage, 1),
            'farmers': page_obj,
            'unique_states': unique_states,
            'unique_genders': unique_genders,
            'unique_ages': unique_ages,
            'current_filters': {
                'state': state_filter,
                'gender': gender_filter,
                'age_category': age_filter
            }
        })
        
        return context


@method_decorator(require_active_subscription, name='dispatch')
class PartnerExtensionAgentsView(LoginRequiredMixin, TemplateView):
    """Partner-specific extension agents data - requires active subscription"""

    template_name = 'dashboard/partner_extension_agents.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.partner_name:
            messages.error(request, 'You do not have access to partner-specific data.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.request.user.profile
        partner_name = user_profile.partner_name
        
        # Partner-specific data
        partner_data = AkilimoParticipant.objects.filter(partner=partner_name)
        
        # Extension agents (org contacts) with their performance
        extension_agents = partner_data.exclude(
            org_first_name__isnull=True
        ).exclude(org_first_name='').values(
            'org_first_name', 'org_surname', 'org_phone_no'
        ).annotate(
            farmers_reached=Count('id'),
            events_conducted=Count('event_date', distinct=True),
            states_covered=Count('admin_level1', distinct=True),
            cities_covered=Count('event_city', distinct=True)
        ).order_by('-farmers_reached')
        
        # Extension agent performance by state
        ea_by_state = partner_data.exclude(
            org_first_name__isnull=True
        ).exclude(org_first_name='').exclude(
            admin_level1__isnull=True
        ).exclude(admin_level1='').values(
            'admin_level1'
        ).annotate(
            unique_agents=Count('org_first_name', distinct=True),
            farmers_reached=Count('id')
        ).order_by('-farmers_reached')
        
        # Monthly EA activity
        monthly_ea_activity = []
        for i in range(12):
            month_start = (datetime.now().date().replace(day=1) - timedelta(days=30*i))
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end - timedelta(days=month_end.day)
            
            agents_active = partner_data.exclude(
                org_first_name__isnull=True
            ).exclude(org_first_name='').filter(
                event_date__gte=month_start,
                event_date__lte=month_end
            ).values('org_first_name', 'org_surname').distinct().count()
            
            farmers_reached = partner_data.filter(
                event_date__gte=month_start,
                event_date__lte=month_end
            ).count()
            
            monthly_ea_activity.append({
                'month': month_start.strftime('%B %Y'),
                'agents_active': agents_active,
                'farmers_reached': farmers_reached
            })
        
        monthly_ea_activity.reverse()
        
        # Training effectiveness metrics
        training_effectiveness = partner_data.exclude(
            event_type__isnull=True
        ).exclude(event_type='').values('event_type').annotate(
            farmers_trained=Count('id'),
            agents_involved=Count('org_first_name', distinct=True),
            avg_farmers_per_agent=Count('id') / Count('org_first_name', distinct=True)
        ).order_by('-farmers_trained')
        
        # Calculate average farmers per agent
        total_agents = extension_agents.count()
        total_farmers_reached = partner_data.count()
        avg_farmers_per_agent = (total_farmers_reached / total_agents) if total_agents > 0 else 0
        
        context.update({
            'partner_name': partner_name,
            'extension_agents': list(extension_agents),
            'total_agents': total_agents,
            'ea_by_state': list(ea_by_state),
            'monthly_ea_activity': monthly_ea_activity,
            'training_effectiveness': list(training_effectiveness),
            'total_farmers_reached': total_farmers_reached,
            'avg_farmers_per_agent': avg_farmers_per_agent,
        })
        
        return context


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_partner_metrics(request):
    """API endpoint for partner-specific metrics"""
    if not hasattr(request.user, 'profile') or not request.user.profile.can_view_partner_data:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    user_profile = request.user.profile
    partner_farmers = user_profile.accessible_farmers
    
    # Time filter
    days_filter = request.GET.get('days', 30)
    try:
        days_filter = int(days_filter)
        start_date = datetime.now().date() - timedelta(days=days_filter)
        partner_farmers = partner_farmers.filter(created_at__gte=start_date)
    except (ValueError, TypeError):
        pass
    
    # Calculate metrics
    total_count = partner_farmers.count()
    
    gender_distribution = partner_farmers.values('farmer_gender').annotate(
        count=Count('id')
    ).order_by('-count')
    
    location_distribution = partner_farmers.values('admin_level1').annotate(
        count=Count('id')
    ).order_by('-count')
    
    crop_distribution = partner_farmers.exclude(
        crop__isnull=True
    ).exclude(crop='').values('crop').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return Response({
        'partner_name': user_profile.partner_organization.name,
        'total_farmers': total_count,
        'gender_distribution': list(gender_distribution),
        'location_distribution': list(location_distribution),
        'crop_distribution': list(crop_distribution),
        'filter_applied': {
            'days': days_filter
        }
    })


@login_required
def membership_subscription(request):
    """Membership subscription view - redirects to new payment selection"""
    # Redirect to the new payment selection page
    return redirect('dashboard:payment_selection')


@login_required
@csrf_exempt
def initiate_payment(request):
    """Initiate payment for membership subscription or annual dues"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        import json
        from django.conf import settings
        from decimal import Decimal
        import uuid
        from datetime import date

        # Parse request data
        data = json.loads(request.body)
        membership_type = data.get('membership_type', 'individual')

        # Clean amount - remove commas if present (from thousand separator formatting)
        amount_raw = data.get('amount', 10000)
        amount_str = str(amount_raw).replace(',', '').replace(' ', '').strip()
        amount = Decimal(amount_str)
        logger.info(f"Cleaned amount: {amount_raw} -> {amount}")

        payment_purpose = data.get('payment_purpose', 'registration')  # 'registration' or 'annual_dues'

        # Clean subscription_year - remove commas and convert to int
        subscription_year_raw = data.get('subscription_year')
        subscription_year = None
        if subscription_year_raw:
            try:
                # Convert to string, remove commas and any whitespace, then convert to int
                year_str = str(subscription_year_raw).replace(',', '').replace(' ', '').strip()
                subscription_year = int(year_str)
                logger.info(f"Cleaned subscription_year: {subscription_year_raw} -> {subscription_year}")
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to parse subscription_year '{subscription_year_raw}': {e}")
                subscription_year = None

        # Get or create membership for current user
        membership, created = Membership.objects.get_or_create(
            member=request.user,
            defaults={
                'membership_type': membership_type,
                'status': 'pending'
            }
        )

        # Update membership type if needed
        if membership.membership_type != membership_type:
            membership.membership_type = membership_type
            membership.save()

        # Set subscription year for annual dues
        if payment_purpose == 'annual_dues' and not subscription_year:
            subscription_year = date.today().year

        # Generate unique payment reference
        purpose_code = 'REG' if payment_purpose == 'registration' else 'DUES'
        payment_reference = f"ANA-{purpose_code}-{membership_type.upper()}-{uuid.uuid4().hex[:8].upper()}"

        # Get Paystack public key from settings
        paystack_public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', 'pk_test_96b9995fbf552beec8da11acbb821aa5c1d06341')

        # Create payment record
        from .models import Payment
        payment = Payment.objects.create(
            membership=membership,
            amount=amount,
            currency='NGN',
            payment_method='paystack',
            status='pending',
            paystack_reference=payment_reference,
            payment_purpose=payment_purpose,
            subscription_year=subscription_year if payment_purpose == 'annual_dues' else None,
            description=f'{payment_purpose.replace("_", " ").title()} - {membership_type.title()} Membership'
        )

        # Initialize Paystack transaction for checkout redirect
        from .paystack_service import PaystackService
        paystack = PaystackService()
        callback_url = request.build_absolute_uri('/dashboard/payment/verify/')

        metadata = {
            'membership_id': str(membership.membership_id),
            'payment_id': str(payment.payment_id),
            'payment_purpose': payment_purpose,
            'subscription_year': subscription_year,
            'membership_type': membership_type
        }

        paystack_response = paystack.initialize_transaction(
            email=request.user.email,
            amount=amount,
            reference=payment_reference,
            callback_url=callback_url,
            metadata=metadata
        )

        if paystack_response.get('status'):
            # Get checkout URL from Paystack response
            checkout_url = paystack_response['data']['authorization_url']
            logger.info(f"Payment initialized successfully. Checkout URL: {checkout_url}")

            return JsonResponse({
                'status': 'success',
                'checkout_url': checkout_url,
                'reference': payment_reference,
                'payment_id': str(payment.payment_id)
            })
        else:
            logger.error(f"Paystack initialization failed: {paystack_response.get('message')}")
            return JsonResponse({
                'error': paystack_response.get('message', 'Payment initialization failed')
            }, status=500)

    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        return JsonResponse({'error': f'Payment initiation failed: {str(e)}'}, status=500)


@login_required
def verify_payment(request):
    """Verify payment after Paystack checkout redirect"""
    from .paystack_service import PaystackService
    from .models import Payment
    from django.contrib import messages

    reference = request.GET.get('reference')

    if not reference:
        messages.error(request, 'Payment reference not provided.')
        return redirect('dashboard:index')

    try:
        # Get payment record
        payment = Payment.objects.get(paystack_reference=reference)

        # Verify with Paystack
        paystack = PaystackService()
        verification_response = paystack.verify_transaction(reference)

        if verification_response.get('status') and verification_response['data']['status'] == 'success':
            # Payment successful - update payment status
            # Note: Membership will be automatically updated by signals
            payment.status = 'successful'
            payment.paid_at = timezone.now()
            payment.save()

            logger.info(f"Payment verified successfully: {reference}")
            messages.success(request, 'Payment successful! Your membership has been updated.')
            return redirect('dashboard:index')
        else:
            # Payment failed
            payment.status = 'failed'
            payment.save()

            logger.error(f"Payment verification failed: {reference}")
            messages.error(request, 'Payment verification failed. Please try again or contact support.')
            return redirect('dashboard:payment_selection')

    except Payment.DoesNotExist:
        logger.error(f"Payment not found for reference: {reference}")
        messages.error(request, 'Payment record not found.')
        return redirect('dashboard:index')
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        messages.error(request, 'An error occurred while verifying payment.')
        return redirect('dashboard:index')


@login_required
def payment_selection(request):
    """
    Payment selection view for new registration or annual dues renewal.
    Shows appropriate pricing and allows user to choose payment type.
    """
    from datetime import date
    from .models import Membership, MembershipPricing

    # Get or create membership for current user
    membership, created = Membership.objects.get_or_create(
        member=request.user,
        defaults={'status': 'pending'}
    )

    # Determine what payment options to show
    show_registration = not membership.registration_paid
    show_annual_dues = membership.registration_paid or not created

    # Get current year for annual dues
    current_year = date.today().year

    # Check if user already paid annual dues for current year
    already_paid_current_year = (
        membership.annual_dues_paid_for_year == current_year and
        membership.has_active_subscription
    )

    # Get pricing information
    registration_pricing = MembershipPricing.objects.filter(
        payment_type='registration',
        is_active=True
    ).order_by('membership_type')

    annual_dues_pricing = MembershipPricing.objects.filter(
        payment_type='annual_dues',
        is_active=True
    ).first()

    context = {
        'membership': membership,
        'show_registration': show_registration,
        'show_annual_dues': show_annual_dues,
        'registration_pricing': registration_pricing,
        'annual_dues_pricing': annual_dues_pricing,
        'current_year': current_year,
        'already_paid_current_year': already_paid_current_year,
    }

    return render(request, 'dashboard/payment_selection.html', context)


@login_required
def renewal(request):
    """
    Annual membership renewal view.
    Allows members to renew their annual dues subscription.
    """
    from datetime import date
    from .models import Membership, MembershipPricing

    # Ensure user has a membership
    if not hasattr(request.user, 'membership'):
        messages.error(request, 'You need to complete membership registration first.')
        return redirect('dashboard:register')

    membership = request.user.membership

    # Check if registration is paid
    if not membership.registration_paid:
        messages.warning(request, 'Please complete your registration payment first.')
        return redirect('dashboard:payment_selection')

    # Get current year
    current_year = date.today().year

    # Check if already paid for current year
    already_paid = (
        membership.annual_dues_paid_for_year == current_year and
        membership.has_active_subscription
    )

    # Get annual dues pricing
    annual_dues_pricing = MembershipPricing.objects.filter(
        payment_type='annual_dues',
        is_active=True
    ).first()

    # Get subscription status
    subscription_expired = not membership.has_active_subscription
    days_until_expiry = None

    if membership.subscription_end_date:
        days_until_expiry = (membership.subscription_end_date - date.today()).days

    context = {
        'membership': membership,
        'current_year': current_year,
        'already_paid': already_paid,
        'subscription_expired': subscription_expired,
        'days_until_expiry': days_until_expiry,
        'annual_dues_pricing': annual_dues_pricing,
    }

    return render(request, 'dashboard/renewal.html', context)


@login_required
def download_certificate(request):
    """Generate and download membership certificate as PDF"""
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO
    import qrcode
    from datetime import date

    # Get membership
    try:
        membership = Membership.objects.get(member=request.user)
    except Membership.DoesNotExist:
        messages.error(request, 'No membership found.')
        return redirect('dashboard:profile')

    # Check if user can download certificate
    if not membership.can_download_certificate:
        messages.error(request, 'You do not have permission to download the certificate. Please ensure your annual dues are paid.')
        return redirect('dashboard:profile')

    # Create PDF buffer
    buffer = BytesIO()

    # Create the PDF document (landscape A4)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=0.5*cm,
        bottomMargin=0.5*cm
    )

    # Styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=colors.HexColor('#1a5f2a'),
        alignment=TA_CENTER,
        spaceAfter=25,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        alignment=TA_CENTER,
        spaceAfter=10,
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    name_style = ParagraphStyle(
        'Name',
        parent=styles['Heading2'],
        fontSize=24,
        textColor=colors.HexColor('#1a5f2a'),
        alignment=TA_CENTER,
        spaceAfter=10,
    )

    # Build content
    elements = []

    # Add logo at top center
    import os
    from django.conf import settings

    logo_path = os.path.join(settings.BASE_DIR, 'ana_logo.png')
    if not os.path.exists(logo_path):
        # Try media folder
        logo_path = os.path.join(settings.MEDIA_ROOT, 'site', 'ana_logo.png')

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.2*inch, height=1.2*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 0.3*cm))
    else:
        # Add spacing if no logo
        elements.append(Spacer(1, 0.5*cm))

    # Title
    elements.append(Paragraph("AKILIMO Nigeria Association", title_style))

    # Subtitle
    elements.append(Paragraph("Certificate of Membership", subtitle_style))

    # Decorative line
    elements.append(Spacer(1, 0.3*cm))

    # Certificate text
    elements.append(Paragraph("This is to certify that", body_style))
    elements.append(Spacer(1, 0.3*cm))

    # Member name
    full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    elements.append(Paragraph(f"<b>{full_name}</b>", name_style))

    elements.append(Spacer(1, 0.2*cm))

    # Membership details
    elements.append(Paragraph(
        f"is a registered member of AKILIMO Nigeria Association",
        body_style
    ))

    elements.append(Spacer(1, 0.2*cm))

    # Membership type and certificate number
    membership_type_display = membership.get_membership_type_display()
    elements.append(Paragraph(
        f"Membership Type: <b>{membership_type_display}</b>",
        body_style
    ))

    elements.append(Paragraph(
        f"Certificate Number: <b>{membership.certificate_number}</b>",
        body_style
    ))

    if membership.annual_dues_paid_for_year:
        elements.append(Paragraph(
            f"Valid for: <b>{membership.annual_dues_paid_for_year}</b>",
            body_style
        ))

    elements.append(Spacer(1, 0.5*cm))

    # Generate QR code for verification
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    verification_url = request.build_absolute_uri(f'/dashboard/verify/{membership.qr_code}/')
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Save QR to buffer
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    # Create table with QR code and date
    qr_image = Image(qr_buffer, width=1.2*inch, height=1.2*inch)

    footer_data = [
        [qr_image, Paragraph(f"Issue Date: {date.today().strftime('%B %d, %Y')}", body_style)],
        [Paragraph("Scan to verify", ParagraphStyle('Small', fontSize=8, alignment=TA_CENTER)), '']
    ]

    footer_table = Table(footer_data, colWidths=[1.5*inch, 4*inch])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(footer_table)

    # Build PDF
    doc.build(elements)

    # Mark certificate as generated
    if not membership.certificate_generated:
        membership.certificate_generated = True
        membership.save(update_fields=['certificate_generated'])

    # Get PDF content
    pdf = buffer.getvalue()
    buffer.close()

    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ANA_Certificate_{membership.certificate_number}.pdf"'
    response.write(pdf)

    logger.info(f"Certificate downloaded for member: {request.user.email}")

    return response


@login_required
def download_id_card(request):
    """Generate and download membership ID card as PDF"""
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm, mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.graphics.shapes import Drawing, Rect, String
    from io import BytesIO
    import qrcode
    from datetime import date

    # Get membership
    try:
        membership = Membership.objects.get(member=request.user)
    except Membership.DoesNotExist:
        messages.error(request, 'No membership found.')
        return redirect('dashboard:profile')

    # Check if user can download ID card
    if not membership.can_download_id_card:
        messages.error(request, 'You do not have permission to download the ID card. Please ensure your annual dues are paid.')
        return redirect('dashboard:profile')

    # Create PDF buffer
    buffer = BytesIO()

    # ID card size (credit card size: 85.6mm x 53.98mm, we'll make it slightly larger for printing)
    card_width = 9 * cm
    card_height = 5.5 * cm

    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Styles
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )

    name_style = ParagraphStyle(
        'Name',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1a5f2a'),
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
    )

    detail_style = ParagraphStyle(
        'Detail',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#333333'),
        alignment=TA_LEFT,
    )

    # Build content
    elements = []

    # Add logo at top
    import os
    from django.conf import settings

    logo_path = os.path.join(settings.BASE_DIR, 'ana_logo.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.MEDIA_ROOT, 'site', 'ana_logo.png')

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=0.8*inch, height=0.8*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 0.3*cm))

    # Instructions
    elements.append(Paragraph(
        "<b>AKILIMO Nigeria Association - Membership ID Card</b>",
        ParagraphStyle('Title', fontSize=14, alignment=TA_CENTER, spaceAfter=10)
    ))

    elements.append(Paragraph(
        "Print this page and cut along the dotted line to create your ID card.",
        ParagraphStyle('Instruction', fontSize=10, alignment=TA_CENTER, spaceAfter=20)
    ))

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    verification_url = request.build_absolute_uri(f'/dashboard/verify/{membership.qr_code}/')
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_image = Image(qr_buffer, width=1.2*inch, height=1.2*inch)

    # Member details
    full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    membership_type = membership.get_membership_type_display()

    # Get profile for additional info
    try:
        profile = request.user.profile
        organization = profile.partner_organization.name if profile.partner_organization else profile.partner_name or 'N/A'
    except:
        organization = 'N/A'

    # Create ID card as a table
    # Header row (green background)
    header = Paragraph("AKILIMO NIGERIA ASSOCIATION", header_style)

    # Member info
    name_para = Paragraph(f"<b>{full_name}</b>", name_style)
    type_para = Paragraph(f"Type: {membership_type}", detail_style)
    cert_para = Paragraph(f"ID: {membership.certificate_number}", detail_style)
    org_para = Paragraph(f"Org: {organization[:30]}", detail_style)

    if membership.annual_dues_paid_for_year:
        valid_para = Paragraph(f"Valid: {membership.annual_dues_paid_for_year}", detail_style)
    else:
        valid_para = Paragraph("", detail_style)

    # Create the card layout
    card_data = [
        # Header row
        [header, ''],
        # Content row
        [[name_para, Spacer(1, 3*mm), type_para, cert_para, org_para, valid_para], qr_image],
    ]

    card_table = Table(card_data, colWidths=[card_width - 3.5*cm, 3.5*cm], rowHeights=[0.8*cm, card_height - 0.8*cm])

    card_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f2a')),
        ('SPAN', (0, 0), (1, 0)),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

        # Content styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ALIGN', (0, 1), (0, 1), 'LEFT'),
        ('ALIGN', (1, 1), (1, 1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('PADDING', (0, 1), (0, 1), 8),
        ('PADDING', (1, 1), (1, 1), 5),

        # Border
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a5f2a')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#1a5f2a')),
    ]))

    elements.append(card_table)

    elements.append(Spacer(1, 1*cm))

    # Add cutting guide
    elements.append(Paragraph(
        "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -",
        ParagraphStyle('Cut', fontSize=8, alignment=TA_CENTER, textColor=colors.gray)
    ))

    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph(
        f"Scan QR code to verify membership • Issued: {date.today().strftime('%Y-%m-%d')}",
        ParagraphStyle('Footer', fontSize=8, alignment=TA_CENTER, textColor=colors.gray)
    ))

    # Build PDF
    doc.build(elements)

    # Mark ID card as generated
    if not membership.id_card_generated:
        membership.id_card_generated = True
        membership.save(update_fields=['id_card_generated'])

    # Get PDF content
    pdf = buffer.getvalue()
    buffer.close()

    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ANA_ID_Card_{membership.certificate_number}.pdf"'
    response.write(pdf)

    logger.info(f"ID card downloaded for member: {request.user.email}")

    return response


def verify_membership(request, qr_code):
    """
    Public view to verify membership via QR code.
    Anyone can access this to verify a member's status.
    """
    from datetime import date

    try:
        membership = Membership.objects.select_related('member').get(qr_code=qr_code)

        # Get member details
        member = membership.member
        full_name = f"{member.first_name} {member.last_name}".strip() or member.username

        # Get organization
        try:
            profile = member.profile
            organization = profile.partner_organization.name if profile.partner_organization else profile.partner_name or None
        except:
            organization = None

        # Determine verification status
        is_valid = False
        status_message = ""
        status_class = "danger"

        current_year = date.today().year

        if membership.access_suspended:
            status_message = "Membership Suspended"
            status_class = "warning"
        elif membership.has_active_subscription:
            is_valid = True
            status_message = f"Valid Member ({membership.annual_dues_paid_for_year})"
            status_class = "success"
        elif membership.annual_dues_paid_for_year and membership.annual_dues_paid_for_year < current_year:
            status_message = f"Expired ({membership.annual_dues_paid_for_year})"
            status_class = "danger"
        elif membership.registration_paid and not membership.annual_dues_paid_for_year:
            status_message = "Registered (Annual Dues Pending)"
            status_class = "warning"
        else:
            status_message = "Inactive"
            status_class = "secondary"

        context = {
            'membership': membership,
            'member_name': full_name,
            'organization': organization,
            'is_valid': is_valid,
            'status_message': status_message,
            'status_class': status_class,
            'current_year': current_year,
            'found': True,
        }

    except Membership.DoesNotExist:
        context = {
            'found': False,
            'status_message': 'Invalid QR Code',
            'status_class': 'danger',
        }

    return render(request, 'dashboard/verify_membership.html', context)
