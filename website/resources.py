"""
Export resource classes for website models
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.contrib.auth.models import User
from dashboard.models import PartnerOrganization
from .models import (
    Page,
    NewsArticle,
    HomePageSection,
    TeamMember,
    PartnerShowcase,
    Testimonial,
    FAQ,
    ContactInfo,
    Statistic,
    SiteSettings,
)


class PageResource(resources.ModelResource):
    """Export resource for Pages"""
    created_by = fields.Field(
        column_name='created_by',
        attribute='created_by',
        widget=ForeignKeyWidget(User, 'username')
    )

    class Meta:
        model = Page
        fields = (
            'id', 'title', 'slug', 'content', 'meta_description', 'meta_keywords',
            'is_published', 'show_in_menu', 'menu_order',
            'created_by', 'created_at', 'updated_at'
        )
        export_order = fields


class NewsArticleResource(resources.ModelResource):
    """Export resource for News Articles"""
    author = fields.Field(
        column_name='author',
        attribute='author',
        widget=ForeignKeyWidget(User, 'username')
    )
    category_display = fields.Field(column_name='category_display')

    class Meta:
        model = NewsArticle
        fields = (
            'id', 'title', 'slug', 'excerpt', 'content', 'category', 'category_display',
            'author', 'published_date', 'is_published', 'is_featured',
            'meta_description', 'meta_keywords', 'views_count',
            'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_category_display(self, article):
        """Convert category to human-readable format"""
        return article.get_category_display()


class HomePageSectionResource(resources.ModelResource):
    """Export resource for Homepage Sections"""
    section_type_display = fields.Field(column_name='section_type_display')

    class Meta:
        model = HomePageSection
        fields = (
            'id', 'section_type', 'section_type_display', 'title', 'subtitle',
            'content', 'button_text', 'button_url', 'background_color',
            'order', 'is_active', 'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_section_type_display(self, section):
        """Convert section type to human-readable format"""
        return section.get_section_type_display()


class TeamMemberResource(resources.ModelResource):
    """Export resource for Team Members"""
    category_display = fields.Field(column_name='category_display')

    class Meta:
        model = TeamMember
        fields = (
            'id', 'name', 'position', 'category', 'category_display', 'bio',
            'email', 'phone', 'linkedin_url', 'twitter_url',
            'order', 'is_active', 'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_category_display(self, member):
        """Convert category to human-readable format"""
        return member.get_category_display()


class PartnerShowcaseResource(resources.ModelResource):
    """Export resource for Partner Showcases"""
    partner = fields.Field(
        column_name='partner',
        attribute='partner',
        widget=ForeignKeyWidget(PartnerOrganization, 'name')
    )
    partner_code = fields.Field(column_name='partner_code')

    class Meta:
        model = PartnerShowcase
        fields = (
            'id', 'partner', 'partner_code', 'description', 'website_url',
            'success_story', 'is_featured', 'display_order', 'is_active',
            'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_partner_code(self, showcase):
        """Get partner organization code"""
        return showcase.partner.code if showcase.partner else ''


class TestimonialResource(resources.ModelResource):
    """Export resource for Testimonials"""
    testimonial_type_display = fields.Field(column_name='testimonial_type_display')

    class Meta:
        model = Testimonial
        fields = (
            'id', 'name', 'position', 'organization', 'content',
            'testimonial_type', 'testimonial_type_display', 'is_featured',
            'rating', 'order', 'is_active', 'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_testimonial_type_display(self, testimonial):
        """Convert testimonial type to human-readable format"""
        return testimonial.get_testimonial_type_display()


class FAQResource(resources.ModelResource):
    """Export resource for FAQs"""
    category_display = fields.Field(column_name='category_display')

    class Meta:
        model = FAQ
        fields = (
            'id', 'question', 'answer', 'category', 'category_display',
            'order', 'is_active', 'helpful_count',
            'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_category_display(self, faq):
        """Convert category to human-readable format"""
        return faq.get_category_display()


class ContactInfoResource(resources.ModelResource):
    """Export resource for Contact Information"""

    class Meta:
        model = ContactInfo
        fields = (
            'id', 'office_name', 'address', 'city', 'state', 'postal_code', 'country',
            'phone', 'email', 'fax', 'hours',
            'latitude', 'longitude', 'is_primary', 'order', 'is_active',
            'created_at', 'updated_at'
        )
        export_order = fields


class StatisticResource(resources.ModelResource):
    """Export resource for Statistics"""

    class Meta:
        model = Statistic
        fields = (
            'id', 'label', 'value', 'icon', 'description',
            'order', 'is_active', 'show_on_homepage',
            'created_at', 'updated_at'
        )
        export_order = fields


class SiteSettingsResource(resources.ModelResource):
    """Export resource for Site Settings"""

    class Meta:
        model = SiteSettings
        fields = (
            'id', 'site_title', 'site_tagline', 'site_description',
            'primary_email', 'primary_phone',
            'facebook_url', 'twitter_url', 'linkedin_url', 'youtube_url',
            'google_analytics_id', 'meta_keywords',
            'created_at', 'updated_at'
        )
        export_order = fields
