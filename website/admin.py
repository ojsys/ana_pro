from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.forms import Textarea
from .models import (
    Page, NewsArticle, HomePageSection, TeamMember, PartnerShowcase,
    Testimonial, FAQ, ContactInfo, SiteSettings, Statistic
)


class RichTextAdmin(admin.ModelAdmin):
    """Base admin class with rich text editing"""
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 80})},
    }
    
    class Media:
        css = {
            'all': (
                'https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js',
            )
        }
        js = (
            'admin/js/tinymce_setup.js',
        )


@admin.register(Page)
class PageAdmin(RichTextAdmin):
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
class NewsArticleAdmin(RichTextAdmin):
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
class HomePageSectionAdmin(admin.ModelAdmin):
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
class TeamMemberAdmin(admin.ModelAdmin):
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
class PartnerShowcaseAdmin(admin.ModelAdmin):
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
class TestimonialAdmin(admin.ModelAdmin):
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
class FAQAdmin(admin.ModelAdmin):
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
class ContactInfoAdmin(admin.ModelAdmin):
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
class StatisticAdmin(admin.ModelAdmin):
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
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_title', 'site_tagline', 'primary_email', 'primary_phone']
    
    fieldsets = (
        ('Site Information', {
            'fields': ('site_title', 'site_tagline', 'site_description')
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


# Admin site customization
admin.site.site_header = "AKILIMO Nigeria Association - CMS Admin"
admin.site.site_title = "AKILIMO CMS"
admin.site.index_title = "Content Management System"
