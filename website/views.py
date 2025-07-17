from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, RedirectView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import Http404
from .models import (
    Page, NewsArticle, HomePageSection, TeamMember, 
    PartnerShowcase, Testimonial, FAQ, ContactInfo, SiteSettings, Statistic
)
from dashboard.models import PartnerOrganization


class HomeView(TemplateView):
    """Homepage view with dynamic sections"""
    template_name = 'website/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active homepage sections
        context['homepage_sections'] = HomePageSection.objects.filter(
            is_active=True
        ).order_by('order')
        
        # Get homepage statistics
        context['homepage_statistics'] = Statistic.objects.filter(
            is_active=True,
            show_on_homepage=True
        ).order_by('order')
        
        # Get featured content
        context['featured_news'] = NewsArticle.objects.filter(
            is_published=True, 
            is_featured=True
        )[:3]
        
        context['featured_testimonials'] = Testimonial.objects.filter(
            is_active=True, 
            is_featured=True
        )[:3]
        
        context['featured_partners'] = PartnerOrganization.objects.filter(
            is_active=True, 
            is_featured=True
        ).order_by('feature_order', 'name')[:10]
        
        # Get site settings
        try:
            context['site_settings'] = SiteSettings.objects.first()
        except SiteSettings.DoesNotExist:
            context['site_settings'] = None
            
        return context


class AboutView(TemplateView):
    """About page view"""
    template_name = 'website/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Try to get About page content from CMS
        try:
            context['about_page'] = Page.objects.get(
                slug='about',
                is_published=True
            )
        except Page.DoesNotExist:
            context['about_page'] = None
        
        # Get team members by category
        context['bot_members'] = TeamMember.objects.filter(
            is_active=True,
            category='bot'
        ).order_by('order', 'name')
        
        context['exco_members'] = TeamMember.objects.filter(
            is_active=True,
            category='exco'
        ).order_by('order', 'name')
        
        context['staff_members'] = TeamMember.objects.filter(
            is_active=True,
            category='staff'
        ).order_by('order', 'name')
        
        # Get all team members for backward compatibility
        context['team_members'] = TeamMember.objects.filter(
            is_active=True
        ).order_by('category', 'order', 'name')
        
        return context


class ProgramsView(TemplateView):
    """Programs and services page"""
    template_name = 'website/programs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Try to get Programs page content from CMS
        try:
            context['programs_page'] = Page.objects.get(
                slug='programs',
                is_published=True
            )
        except Page.DoesNotExist:
            context['programs_page'] = None
            
        return context


class PartnersView(TemplateView):
    """Partners page view"""
    template_name = 'website/partners.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all active partner organizations
        context['all_partners'] = PartnerOrganization.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Get featured partners
        context['featured_partners'] = PartnerOrganization.objects.filter(
            is_active=True, 
            is_featured=True
        ).order_by('feature_order', 'name')
        
        # Get partner showcases (legacy)
        context['partner_showcases'] = PartnerShowcase.objects.filter(
            is_active=True
        ).order_by('display_order', 'partner__name')
        
        # Try to get Partners page content from CMS
        try:
            context['partners_page'] = Page.objects.get(
                slug='partners',
                is_published=True
            )
        except Page.DoesNotExist:
            context['partners_page'] = None
            
        return context


class TeamView(TemplateView):
    """Team page view"""
    template_name = 'website/team.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all active team members
        context['team_members'] = TeamMember.objects.filter(
            is_active=True
        ).order_by('order', 'name')
        
        # Try to get Team page content from CMS
        try:
            context['team_page'] = Page.objects.get(
                slug='team',
                is_published=True
            )
        except Page.DoesNotExist:
            context['team_page'] = None
            
        return context


class ContactView(TemplateView):
    """Contact page view"""
    template_name = 'website/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get contact information
        context['contact_offices'] = ContactInfo.objects.filter(
            is_active=True
        ).order_by('order', 'office_name')
        
        # Get primary contact
        try:
            context['primary_contact'] = ContactInfo.objects.get(
                is_primary=True,
                is_active=True
            )
        except ContactInfo.DoesNotExist:
            context['primary_contact'] = context['contact_offices'].first()
        
        # Try to get Contact page content from CMS
        try:
            context['contact_page'] = Page.objects.get(
                slug='contact',
                is_published=True
            )
        except Page.DoesNotExist:
            context['contact_page'] = None
            
        return context


class FAQView(TemplateView):
    """FAQ page view"""
    template_name = 'website/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get FAQs organized by category
        faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order')
        
        # Group FAQs by category
        faq_categories = {}
        for faq in faqs:
            category = faq.get_category_display()
            if category not in faq_categories:
                faq_categories[category] = []
            faq_categories[category].append(faq)
        
        context['faq_categories'] = faq_categories
        
        return context


class NewsListView(ListView):
    """News articles listing view"""
    model = NewsArticle
    template_name = 'website/news_list.html'
    context_object_name = 'articles'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = NewsArticle.objects.filter(is_published=True)
        
        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        return queryset.order_by('-published_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add category choices for filtering
        context['categories'] = NewsArticle.CATEGORY_CHOICES
        context['current_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Get featured articles for sidebar
        context['featured_articles'] = NewsArticle.objects.filter(
            is_published=True,
            is_featured=True
        ).exclude(
            id__in=[article.id for article in context['articles']]
        )[:3]
        
        return context


class NewsDetailView(DetailView):
    """Individual news article view"""
    model = NewsArticle
    template_name = 'website/news_detail.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return NewsArticle.objects.filter(is_published=True)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Increment views count
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related articles
        context['related_articles'] = NewsArticle.objects.filter(
            is_published=True,
            category=self.object.category
        ).exclude(id=self.object.id)[:3]
        
        return context


class NewsCategoryView(NewsListView):
    """News articles filtered by category"""
    
    def get_queryset(self):
        category = self.kwargs.get('category')
        return NewsArticle.objects.filter(
            is_published=True,
            category=category
        ).order_by('-published_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        category = self.kwargs.get('category')
        # Get category display name
        category_dict = dict(NewsArticle.CATEGORY_CHOICES)
        context['category_name'] = category_dict.get(category, category)
        context['current_category'] = category
        
        return context


class PageDetailView(DetailView):
    """Dynamic page view for CMS pages"""
    model = Page
    template_name = 'website/page_detail.html'
    context_object_name = 'page'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Page.objects.filter(is_published=True)


class LoginRedirectView(RedirectView):
    """Redirect to dashboard login"""
    permanent = False
    
    def get_redirect_url(self, *args, **kwargs):
        # Redirect to dashboard login URL
        from django.urls import reverse
        return reverse('dashboard:login')


class RegisterRedirectView(RedirectView):
    """Redirect to dashboard registration"""
    permanent = False
    
    def get_redirect_url(self, *args, **kwargs):
        # Redirect to dashboard registration URL
        from django.urls import reverse
        return reverse('dashboard:register')


class DashboardRedirectView(RedirectView):
    """Redirect to dashboard"""
    permanent = False
    
    def get_redirect_url(self, *args, **kwargs):
        # Redirect to dashboard home
        from django.urls import reverse
        return reverse('dashboard:home')


# Context processor for global template variables
def website_context(request):
    """Global context processor for website templates"""
    context = {}
    
    try:
        site_settings = SiteSettings.objects.first()
        context['site_settings'] = site_settings
    except SiteSettings.DoesNotExist:
        context['site_settings'] = None
    
    # Get menu pages
    context['menu_pages'] = Page.objects.filter(
        is_published=True,
        show_in_menu=True
    ).order_by('menu_order', 'title')
    
    # Get primary contact info
    try:
        context['primary_contact'] = ContactInfo.objects.get(
            is_primary=True,
            is_active=True
        )
    except ContactInfo.DoesNotExist:
        context['primary_contact'] = ContactInfo.objects.filter(
            is_active=True
        ).first()
    
    return context
