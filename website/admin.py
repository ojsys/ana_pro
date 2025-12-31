from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.forms import Textarea
from import_export.admin import ImportExportModelAdmin
from .models import (
    Page, NewsArticle, HomePageSection, TeamMember, PartnerShowcase,
    Testimonial, FAQ, ContactInfo, SiteSettings, Statistic, HeroSlide,
    MissionVision, OperationalPillar, PlatformFeature, TrainingProgram,
    SupportTeam, CallToAction, PageContent
)
from .resources import (
    PageResource, NewsArticleResource, HomePageSectionResource,
    TeamMemberResource, PartnerShowcaseResource, TestimonialResource,
    FAQResource, ContactInfoResource, StatisticResource, SiteSettingsResource
)


class RichTextAdmin(ImportExportModelAdmin):
    """Base admin class with rich text editing and export functionality"""
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 80})},
    }


@admin.register(Page)
class PageAdmin(RichTextAdmin):
    resource_class = PageResource
    list_display = ['title', 'slug', 'is_published', 'show_in_menu', 'menu_order', 'created_at']
    list_filter = ['is_published', 'show_in_menu', 'created_at']
    search_fields = ['title', 'content', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Page Content', {
            'fields': ('title', 'slug', 'content', 'featured_image')
        }),
        ('Navigation', {
            'fields': ('show_in_menu', 'menu_order')
        }),
        ('SEO & Meta', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('is_published', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new page
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(NewsArticle)
class NewsArticleAdmin(ImportExportModelAdmin):
    resource_class = NewsArticleResource
    list_display = ['title', 'category', 'author', 'published_date', 'is_published', 'is_featured', 'views_count']
    list_filter = ['category', 'is_published', 'is_featured', 'published_date', 'author']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'views_count']
    date_hierarchy = 'published_date'
    
    fieldsets = (
        ('Article Content', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'featured_image')
        }),
        ('Classification', {
            'fields': ('category', 'author')
        }),
        ('Publishing', {
            'fields': ('published_date', 'is_published', 'is_featured')
        }),
        ('SEO & Meta', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('views_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new article
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(HomePageSection)
class HomePageSectionAdmin(ImportExportModelAdmin):
    resource_class = HomePageSectionResource
    list_display = ['section_type', 'title', 'order', 'is_active', 'created_at']
    list_filter = ['section_type', 'is_active', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['order']
    
    fieldsets = (
        ('Section Details', {
            'fields': ('section_type', 'title', 'subtitle', 'content')
        }),
        ('Visual Elements', {
            'fields': ('image', 'background_color')
        }),
        ('Call to Action', {
            'fields': ('button_text', 'button_url'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TeamMember)
class TeamMemberAdmin(ImportExportModelAdmin):
    resource_class = TeamMemberResource
    list_display = ['name', 'position', 'category', 'order', 'is_active', 'photo_preview']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'position', 'bio']
    ordering = ['category', 'order', 'name']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'position', 'category', 'bio', 'photo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Social Media', {
            'fields': ('linkedin_url', 'twitter_url'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.photo.url
            )
        return "No photo"
    photo_preview.short_description = 'Photo'


@admin.register(PartnerShowcase)
class PartnerShowcaseAdmin(ImportExportModelAdmin):
    resource_class = PartnerShowcaseResource
    list_display = ['partner', 'is_featured', 'is_active', 'display_order', 'logo_preview']
    list_filter = ['is_featured', 'is_active', 'partner', 'created_at']
    search_fields = ['partner__name', 'description', 'success_story']
    ordering = ['display_order', 'partner__name']
    
    fieldsets = (
        ('Partner Information', {
            'fields': ('partner', 'description', 'logo', 'website_url')
        }),
        ('Success Story', {
            'fields': ('success_story',),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: contain;" />',
                obj.logo.url
            )
        return "No logo"
    logo_preview.short_description = 'Logo'


@admin.register(Testimonial)
class TestimonialAdmin(ImportExportModelAdmin):
    resource_class = TestimonialResource
    list_display = ['name', 'organization', 'testimonial_type', 'rating', 'is_featured', 'is_active']
    list_filter = ['testimonial_type', 'rating', 'is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'organization', 'content']
    ordering = ['order', '-created_at']
    
    fieldsets = (
        ('Person Information', {
            'fields': ('name', 'position', 'organization', 'photo')
        }),
        ('Testimonial Content', {
            'fields': ('content', 'testimonial_type', 'rating')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FAQ)
class FAQAdmin(ImportExportModelAdmin):
    resource_class = FAQResource
    list_display = ['question_preview', 'category', 'order', 'is_active', 'helpful_count']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['question', 'answer']
    ordering = ['category', 'order']
    
    fieldsets = (
        ('FAQ Content', {
            'fields': ('question', 'answer', 'category')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Engagement', {
            'fields': ('helpful_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'helpful_count']
    
    def question_preview(self, obj):
        return f"{obj.question[:60]}..." if len(obj.question) > 60 else obj.question
    question_preview.short_description = 'Question'


@admin.register(ContactInfo)
class ContactInfoAdmin(ImportExportModelAdmin):
    resource_class = ContactInfoResource
    list_display = ['office_name', 'city', 'state', 'is_primary', 'is_active', 'phone', 'email']
    list_filter = ['is_primary', 'is_active', 'state', 'country']
    search_fields = ['office_name', 'city', 'address', 'phone', 'email']
    ordering = ['order', 'office_name']
    
    fieldsets = (
        ('Office Information', {
            'fields': ('office_name', 'address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Contact Details', {
            'fields': ('phone', 'email', 'fax', 'hours')
        }),
        ('Map Location', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_primary', 'order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Statistic)
class StatisticAdmin(ImportExportModelAdmin):
    resource_class = StatisticResource
    list_display = ['label', 'value', 'icon', 'order', 'show_on_homepage', 'is_active']
    list_filter = ['show_on_homepage', 'is_active', 'created_at']
    search_fields = ['label', 'value', 'description']
    ordering = ['order', 'label']
    
    fieldsets = (
        ('Statistic Information', {
            'fields': ('label', 'value', 'icon', 'description')
        }),
        ('Display Settings', {
            'fields': ('order', 'show_on_homepage', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SiteSettings)
class SiteSettingsAdmin(ImportExportModelAdmin):
    resource_class = SiteSettingsResource
    list_display = ['site_title', 'site_tagline', 'bypass_payment_requirements', 'primary_email', 'primary_phone']
    
    fieldsets = (
        ('Site Information', {
            'fields': ('site_title', 'site_tagline', 'site_description')
        }),
        ('Payment Settings', {
            'fields': ('bypass_payment_requirements',),
            'description': '<div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin-bottom: 15px; border-radius: 4px;"><strong>⚠️ Important:</strong> When "Bypass Payment Requirements" is <strong>enabled</strong>, users can register and access the dashboard <strong>without any payment</strong>. Disable this setting to enforce payment requirements.</div>'
        }),
        ('Contact Information', {
            'fields': ('primary_email', 'primary_phone')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'youtube_url'),
            'classes': ('collapse',)
        }),
        ('SEO & Analytics', {
            'fields': ('meta_keywords', 'google_analytics_id'),
            'classes': ('collapse',)
        }),
        ('Site Images', {
            'fields': ('logo', 'favicon'),
            'classes': ('collapse',)
        }),
        ('Footer Settings', {
            'fields': ('footer_copyright_text', 'footer_tagline'),
            'description': 'Customize the footer text displayed at the bottom of every page. The current year is automatically added to the copyright text.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one SiteSettings instance
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of SiteSettings
        return False


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'subtitle', 'description']
    ordering = ['order']

    fieldsets = (
        ('Slide Content', {
            'fields': ('title', 'subtitle', 'description')
        }),
        ('Visual Elements', {
            'fields': ('background_image', 'background_color')
        }),
        ('Button 1', {
            'fields': ('button_1_text', 'button_1_url', 'button_1_icon'),
            'classes': ('collapse',)
        }),
        ('Button 2', {
            'fields': ('button_2_text', 'button_2_url', 'button_2_icon'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(MissionVision)
class MissionVisionAdmin(admin.ModelAdmin):
    list_display = ['mission_title', 'vision_title', 'is_active', 'updated_at']

    fieldsets = (
        ('Mission', {
            'fields': ('mission_title', 'mission_content', 'mission_icon')
        }),
        ('Vision', {
            'fields': ('vision_title', 'vision_content', 'vision_icon')
        }),
        ('Display Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def has_add_permission(self, request):
        # Only allow one MissionVision instance
        return not MissionVision.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False


@admin.register(OperationalPillar)
class OperationalPillarAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['order']

    fieldsets = (
        ('Pillar Information', {
            'fields': ('title', 'description', 'icon')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(PlatformFeature)
class PlatformFeatureAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['order']

    fieldsets = (
        ('Feature Information', {
            'fields': ('title', 'description', 'icon')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['order']

    fieldsets = (
        ('Program Information', {
            'fields': ('title', 'description', 'icon')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(SupportTeam)
class SupportTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'responsibilities']
    ordering = ['order']

    fieldsets = (
        ('Team Information', {
            'fields': ('name', 'description', 'icon', 'responsibilities'),
            'description': 'Enter responsibilities one per line'
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(CallToAction)
class CallToActionAdmin(admin.ModelAdmin):
    list_display = ['title', 'placement', 'is_active', 'created_at']
    list_filter = ['placement', 'is_active', 'created_at']
    search_fields = ['title', 'description']

    fieldsets = (
        ('CTA Content', {
            'fields': ('title', 'description')
        }),
        ('Button 1 (Primary)', {
            'fields': ('button_1_text', 'button_1_url', 'button_1_icon')
        }),
        ('Button 2 (Secondary)', {
            'fields': ('button_2_text', 'button_2_url', 'button_2_icon'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('placement', 'background_style', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ['page_section', 'title', 'is_active', 'updated_at']
    list_filter = ['page_section', 'is_active']
    search_fields = ['title', 'content']

    fieldsets = (
        ('Page Section', {
            'fields': ('page_section',)
        }),
        ('Content', {
            'fields': ('title', 'subtitle', 'content', 'badge_text')
        }),
        ('Key Highlights', {
            'fields': ('highlight_1', 'highlight_2', 'highlight_3'),
            'classes': ('collapse',),
            'description': 'For About page key highlights'
        }),
        ('Display Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


# Admin site customization
admin.site.site_header = "AKILIMO Nigeria Association - CMS Admin"
admin.site.site_title = "AKILIMO CMS"
admin.site.index_title = "Content Management System"
