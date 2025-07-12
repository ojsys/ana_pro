from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    
    # Main dashboard views
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('participants/', views.ParticipantsListView.as_view(), name='participants'),
    
    # Partner dashboard
    path('partner/', views.PartnerDashboardView.as_view(), name='partner_dashboard'),
    
    # API endpoints
    path('api/participants/summary/', views.api_participants_summary, name='api_participants_summary'),
    path('api/yield/metrics/', views.api_yield_metrics, name='api_yield_metrics'),
    path('api/sync/data/', views.api_sync_data, name='api_sync_data'),
    path('api/partner/metrics/', views.api_partner_metrics, name='api_partner_metrics'),
]