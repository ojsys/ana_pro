from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.debug_logout_view, name='logout'),
    path('logout-alt/', views.custom_logout_view, name='logout_alt'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    
    # Main dashboard views
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('participants/', views.ParticipantsListView.as_view(), name='participants'),
    
    # Partner dashboard
    path('partner/', views.PartnerDashboardView.as_view(), name='partner_dashboard'),
    path('partner/data/', views.PartnerDataView.as_view(), name='partner_data'),
    path('partner/farmers/', views.PartnerFarmersView.as_view(), name='partner_farmers'),
    path('partner/extension-agents/', views.PartnerExtensionAgentsView.as_view(), name='partner_extension_agents'),
    
    # Membership and Certificate URLs
    path('membership/', views.membership_subscription, name='membership_subscription'),
    # path('certificate/download/', views.download_certificate, name='download_certificate'),
    # path('id-card/download/', views.download_id_card, name='download_id_card'),
    # path('verify/<uuid:qr_code>/', views.verify_membership, name='verify_membership'),
    
    # Payment URLs
    path('payment/selection/', views.payment_selection, name='payment_selection'),
    path('payment/renewal/', views.renewal, name='renewal'),
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    # path('payment/verify/', views.payment_verification, name='payment_verification'),
    # path('payment/mock/<uuid:payment_id>/', views.mock_payment_page, name='mock_payment'),
    
    # Debug URLs (commented out - functions need to be implemented)
    # path('test/', views.test_buttons, name='test_buttons'),
    # path('simple-test/', views.simple_test, name='simple_test'),
    
    # API endpoints
    path('api/participants/summary/', views.api_participants_summary, name='api_participants_summary'),
    path('api/yield/metrics/', views.api_yield_metrics, name='api_yield_metrics'),
    path('api/sync/data/', views.api_sync_data, name='api_sync_data'),
    path('api/partner/metrics/', views.api_partner_metrics, name='api_partner_metrics'),
]