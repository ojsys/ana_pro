from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Conference, SubTheme, Speaker, AbstractThematicArea, AbstractSubmission,
    RegistrationCategory, Registration, ProgramDay, ProgramSession, Sponsor,
    KeyMessage, ContentBlock,
)


class DatePickerInput(forms.DateInput):
    input_type = 'date'


class ConferenceAdminForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = '__all__'
        widgets = {
            # Core dates
            'start_date': DatePickerInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            'end_date': DatePickerInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            # Key deadlines
            'abstract_deadline': DatePickerInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            'early_bird_deadline': DatePickerInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            'registration_deadline': DatePickerInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            'notification_date': DatePickerInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            'final_paper_deadline': DatePickerInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            # Text fields
            'name': forms.TextInput(attrs={'placeholder': 'e.g. AKILIMO International Conference 2026'}),
            'theme': forms.TextInput(attrs={'placeholder': 'e.g. Transforming Cassava Systems for Food Security in Nigeria'}),
            'tagline': forms.TextInput(attrs={'placeholder': 'Short catchy tagline (optional)'}),
            'edition': forms.TextInput(attrs={'placeholder': 'e.g. 1st, 2nd, Inaugural'}),
            'venue': forms.TextInput(attrs={'placeholder': 'e.g. International Conference Centre'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g. Abuja'}),
            'state': forms.TextInput(attrs={'placeholder': 'e.g. FCT'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'conference@akilimo-nigeria.org'}),
            'contact_phone': forms.TextInput(attrs={'placeholder': '+234 800 000 0000'}),
            'website_url': forms.URLInput(attrs={'placeholder': 'https://conference.akilimo-nigeria.org'}),
            'description': forms.Textarea(attrs={'placeholder': 'Overview paragraph about the conference — shown on the landing page.', 'rows': 4}),
            'objectives': forms.Textarea(attrs={'placeholder': 'One objective per line, e.g.:\nShare innovations in cassava value chain\nShowcase AKILIMO tool impact\nStrengthen stakeholder partnerships', 'rows': 5}),
            'expected_outcomes': forms.Textarea(attrs={'placeholder': 'One outcome per line, e.g.:\nNew partnerships formed\nPolicy recommendations documented', 'rows': 4}),
            'target_audience': forms.Textarea(attrs={'placeholder': 'e.g. Researchers, farmers, agribusinesses, government agencies, NGOs, students', 'rows': 2}),
            'key_focus_areas': forms.Textarea(attrs={'placeholder': 'One focus area per line, e.g.:\nCassava value chain innovation\nAKILIMO advisory tools\nDigital agriculture', 'rows': 4}),
        }


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    form = ConferenceAdminForm
    list_display = ['name', 'theme', 'start_date', 'end_date', 'city', 'is_active', 'registration_open', 'abstract_submission_open']
    list_filter = ['is_active', 'registration_open', 'abstract_submission_open']
    search_fields = ['name', 'theme', 'city']
    list_editable = ['is_active', 'registration_open', 'abstract_submission_open']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'theme', 'tagline', 'edition')
        }),
        ('Dates & Venue', {
            'fields': ('start_date', 'end_date', 'venue', 'city', 'state', 'country')
        }),
        ('Content', {
            'fields': ('description', 'objectives', 'expected_outcomes', 'target_audience', 'key_focus_areas'),
            'classes': ('collapse',),
        }),
        ('Media', {
            'fields': ('hero_image', 'banner_image', 'organizer_logo'),
            'classes': ('collapse',),
        }),
        ('Key Dates', {
            'fields': (
                'abstract_deadline', 'notification_date', 'final_paper_deadline',
                'early_bird_deadline', 'registration_deadline',
            ),
        }),
        ('Status', {
            'fields': ('is_active', 'registration_open', 'abstract_submission_open')
        }),
        ('Contact', {
            'fields': ('contact_email', 'contact_phone', 'website_url'),
            'classes': ('collapse',),
        }),
    )


@admin.register(SubTheme)
class SubThemeAdmin(admin.ModelAdmin):
    list_display = ['title', 'conference', 'order', 'is_active']
    list_filter = ['conference', 'is_active']
    list_editable = ['order', 'is_active']
    ordering = ['conference', 'order']


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'organization', 'speaker_type', 'topic', 'is_featured', 'is_active', 'photo_preview']
    list_filter = ['conference', 'speaker_type', 'is_featured', 'is_active']
    search_fields = ['full_name', 'organization', 'topic']
    list_editable = ['speaker_type', 'is_featured', 'is_active']
    ordering = ['conference', 'order']

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;">', obj.photo.url)
        return "—"
    photo_preview.short_description = "Photo"


@admin.register(AbstractThematicArea)
class AbstractThematicAreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'conference', 'order', 'is_active']
    list_filter = ['conference', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(AbstractSubmission)
class AbstractSubmissionAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'title_short', 'author_name', 'institution', 'thematic_area', 'presentation_format', 'status', 'word_count_display', 'submitted_at']
    list_filter = ['conference', 'status', 'thematic_area', 'presentation_format']
    search_fields = ['reference_number', 'title', 'author_name', 'institution', 'email']
    list_editable = ['status']
    readonly_fields = ['reference_number', 'submitted_at', 'updated_at', 'word_count_display']
    ordering = ['-submitted_at']

    fieldsets = (
        ('Reference', {
            'fields': ('reference_number', 'conference', 'submitted_at')
        }),
        ('Author', {
            'fields': ('author_name', 'co_authors', 'institution', 'email', 'phone')
        }),
        ('Abstract', {
            'fields': ('title', 'thematic_area', 'abstract_text', 'keywords', 'presentation_format', 'abstract_file')
        }),
        ('Review', {
            'fields': ('status', 'score', 'reviewer_notes')
        }),
    )

    def title_short(self, obj):
        return obj.title[:60] + ('…' if len(obj.title) > 60 else '')
    title_short.short_description = "Title"

    def word_count_display(self, obj):
        wc = obj.word_count()
        color = 'green' if wc <= 300 else 'red'
        return format_html('<span style="color:{}">{} words</span>', color, wc)
    word_count_display.short_description = "Word Count"

    actions = ['mark_under_review', 'mark_accepted', 'mark_rejected']

    def mark_under_review(self, request, queryset):
        queryset.update(status='under_review')
    mark_under_review.short_description = "Mark selected as Under Review"

    def mark_accepted(self, request, queryset):
        queryset.update(status='accepted')
    mark_accepted.short_description = "Mark selected as Accepted"

    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected')
    mark_rejected.short_description = "Mark selected as Rejected"


@admin.register(RegistrationCategory)
class RegistrationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'conference', 'fee', 'early_bird_fee', 'max_slots', 'order', 'is_active']
    list_filter = ['conference', 'is_active']
    list_editable = ['fee', 'early_bird_fee', 'order', 'is_active']


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'full_name', 'email', 'category', 'amount', 'payment_status', 'checked_in', 'registered_at']
    list_filter = ['conference', 'payment_status', 'category', 'checked_in']
    search_fields = ['ticket_id', 'first_name', 'last_name', 'email', 'organization']
    list_editable = ['payment_status', 'checked_in']
    readonly_fields = ['ticket_id', 'registered_at', 'updated_at', 'paystack_reference', 'paystack_transaction_id']
    ordering = ['-registered_at']

    fieldsets = (
        ('Ticket', {
            'fields': ('ticket_id', 'conference', 'category', 'registered_at')
        }),
        ('Participant', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'organization', 'position', 'state_of_origin')
        }),
        ('Preferences', {
            'fields': ('dietary_requirements', 't_shirt_size', 'abstract_reference'),
            'classes': ('collapse',),
        }),
        ('Payment', {
            'fields': ('amount', 'payment_status', 'paystack_reference', 'paystack_transaction_id', 'payment_date')
        }),
        ('Check-in', {
            'fields': ('checked_in', 'checked_in_at')
        }),
    )

    actions = ['confirm_registration', 'mark_checked_in']

    def confirm_registration(self, request, queryset):
        from django.utils import timezone
        queryset.update(payment_status='confirmed', payment_date=timezone.now())
    confirm_registration.short_description = "Confirm selected registrations"

    def mark_checked_in(self, request, queryset):
        from django.utils import timezone
        queryset.update(checked_in=True, checked_in_at=timezone.now())
    mark_checked_in.short_description = "Mark selected as Checked In"

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = "Name"


class ProgramSessionInline(admin.StackedInline):
    model = ProgramSession
    extra = 1
    fields = ['title', 'session_type', 'start_time', 'end_time', 'venue', 'speakers', 'moderator', 'description', 'order', 'is_active']
    filter_horizontal = ['speakers']


@admin.register(ProgramDay)
class ProgramDayAdmin(admin.ModelAdmin):
    list_display = ['title', 'conference', 'date', 'theme', 'order', 'is_active']
    list_filter = ['conference', 'is_active']
    list_editable = ['order', 'is_active']
    inlines = [ProgramSessionInline]


@admin.register(ProgramSession)
class ProgramSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'day', 'session_type', 'start_time', 'end_time', 'venue', 'order']
    list_filter = ['day__conference', 'session_type']
    search_fields = ['title', 'moderator']
    filter_horizontal = ['speakers']
    ordering = ['day', 'order', 'start_time']


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'conference', 'tier', 'order', 'is_active']
    list_filter = ['conference', 'tier', 'is_active']
    list_editable = ['tier', 'order', 'is_active']


@admin.register(KeyMessage)
class KeyMessageAdmin(admin.ModelAdmin):
    list_display = ['message_short', 'conference', 'source', 'is_quote', 'order', 'is_active']
    list_filter = ['conference', 'is_quote', 'is_active']
    list_editable = ['order', 'is_active']

    def message_short(self, obj):
        return obj.message[:80]
    message_short.short_description = "Message"


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ['key', 'content_preview', 'updated_by', 'updated_at']
    search_fields = ['key', 'content']
    readonly_fields = ['updated_by', 'updated_at']

    def content_preview(self, obj):
        from django.utils.html import strip_tags
        return strip_tags(obj.content)[:80]
    content_preview.short_description = "Content"
