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

logger = logging.getLogger(__name__)

class DashboardHomeView(TemplateView):
    """Main dashboard view"""
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

class ParticipantsListView(TemplateView):
    """View for participants list page"""
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


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('dashboard:login')
    
    def dispatch(self, request, *args, **kwargs):
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
        login(self.request, user)
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


class PartnerDashboardView(LoginRequiredMixin, TemplateView):
    """Partner-specific dashboard view"""
    template_name = 'dashboard/partner_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user can access partner dashboard"""
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


class PartnerDataView(LoginRequiredMixin, TemplateView):
    """Partner-specific data overview"""
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


class PartnerFarmersView(LoginRequiredMixin, TemplateView):
    """Partner-specific farmer demographics and details"""
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


class PartnerExtensionAgentsView(LoginRequiredMixin, TemplateView):
    """Partner-specific extension agents data"""
    
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
    """Membership subscription view"""
    # Get or create membership for current user
    membership, created = Membership.objects.get_or_create(
        member=request.user,
        defaults={
            'membership_type': 'individual',
            'status': 'pending'
        }
    )
    
    # Get pricing information
    pricing_data = {}
    try:
        individual_pricing = MembershipPricing.objects.get(membership_type='individual', is_active=True)
        pricing_data['individual'] = individual_pricing.price
    except MembershipPricing.DoesNotExist:
        pricing_data['individual'] = 10000  # Default fallback price
    
    try:
        organization_pricing = MembershipPricing.objects.get(membership_type='organization', is_active=True)
        pricing_data['organization'] = organization_pricing.price
    except MembershipPricing.DoesNotExist:
        pricing_data['organization'] = 50000  # Default fallback price
    
    context = {
        'membership': membership,
        'created': created,
        'pricing': pricing_data
    }
    
    return render(request, 'dashboard/membership_subscription.html', context)


@login_required
@csrf_exempt
def initiate_payment(request):
    """Initiate payment for membership subscription"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        from django.conf import settings
        from .paystack_service import PaystackService
        from decimal import Decimal
        import uuid
        
        # Parse request data
        data = json.loads(request.body)
        membership_type = data.get('membership_type', 'individual')
        amount = Decimal(str(data.get('amount', 10000)))
        
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
        
        # Generate unique payment reference
        payment_reference = f"ANA-{membership_type.upper()}-{uuid.uuid4().hex[:8].upper()}"
        
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
            description=f'{membership_type.title()} Membership Payment'
        )
        
        return JsonResponse({
            'status': 'success',
            'public_key': paystack_public_key,
            'reference': payment_reference,
            'membership_id': str(membership.membership_id),
            'payment_id': str(payment.payment_id),
            'amount': float(amount),
            'email': request.user.email
        })
        
    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        return JsonResponse({'error': f'Payment initiation failed: {str(e)}'}, status=500)
