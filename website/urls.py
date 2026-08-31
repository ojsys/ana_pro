from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    # Homepage
    path('', views.HomeView.as_view(), name='home'),

    # Public analytics (open to all visitors)
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),

    # API endpoints
    path('api/statistics/', views.get_live_statistics, name='live_statistics'),
    path('api/analytics/', views.analytics_api, name='analytics_api'),

    # Static pages
    path('about/', views.AboutView.as_view(), name='about'),
    path('programs/', views.ProgramsView.as_view(), name='programs'),
    path('partners/', views.PartnersView.as_view(), name='partners'),

    # Partner self-service (partner admins + staff). Declared before the
    # detail route so 'manage' paths are not swallowed by the slug pattern.
    path('partners/<slug:slug>/manage/', views.partner_manage, name='partner_manage'),
    path('partners/<slug:slug>/manage/services/', views.partner_manage_services, name='partner_manage_services'),
    path('partners/<slug:slug>/manage/gallery/', views.partner_manage_gallery, name='partner_manage_gallery'),
    path('partners/<slug:slug>/manage/analytics/', views.partner_manage_analytics, name='partner_manage_analytics'),

    # Public partner detail page
    path('partners/<slug:slug>/', views.PartnerDetailView.as_view(), name='partner_detail'),
    path('team/', views.TeamView.as_view(), name='team'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('faq/', views.FAQView.as_view(), name='faq'),

    # News and articles
    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('news/<slug:slug>/', views.NewsDetailView.as_view(), name='news_detail'),
    path('news/category/<str:category>/', views.NewsCategoryView.as_view(), name='news_category'),

    # Authentication redirects to dashboard
    path('login/', views.LoginRedirectView.as_view(), name='login_redirect'),
    path('register/', views.RegisterRedirectView.as_view(), name='register_redirect'),
    path('dashboard/', views.DashboardRedirectView.as_view(), name='dashboard_redirect'),

    # Dynamic pages (must be last)
    path('<slug:slug>/', views.PageDetailView.as_view(), name='page'),
]