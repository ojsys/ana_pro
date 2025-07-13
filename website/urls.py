from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    # Homepage
    path('', views.HomeView.as_view(), name='home'),
    
    # Static pages
    path('about/', views.AboutView.as_view(), name='about'),
    path('programs/', views.ProgramsView.as_view(), name='programs'),
    path('partners/', views.PartnersView.as_view(), name='partners'),
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