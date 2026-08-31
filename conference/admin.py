from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils import timezone
from ckeditor.widgets import CKEditorWidget
from import_export.admin import ExportMixin

from .resources import RegistrationResource
from .models import (
    Conference, SubTheme, Speaker, AbstractThematicArea, AbstractSubmission,
    RegistrationCategory, Registration, ProgramDay, ProgramSession, Sponsor,
    KeyMessage, ContentBlock, LOCMember, ExhibitorPackage, Exhibitor,
    ExhibitorShowcase, PaymentVerifier, AbstractReviewer,
    SponsorshipPackage, SponsorshipBenefit, SponsorshipPackageBenefit,
)

# Standard rich-text toolbar used across conference admin forms
_RICH = CKEditorWidget(attrs={'rows': 10}, config_name='default')
_RICH_SM = CKEditorWidget(attrs={'rows': 6}, config_name='default')


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
            'description':       CKEditorWidget(config_name='default'),
            'objectives':        CKEditorWidget(config_name='default'),
            'expected_outcomes': CKEditorWidget(config_name='default'),
            'target_audience':   CKEditorWidget(config_name='default'),
            'key_focus_areas':   CKEditorWidget(config_name='default'),
        }


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    form = ConferenceAdminForm
    list_display = ['name', 'theme', 'start_date', 'end_date', 'city', 'is_active', 'registration_open', 'abstract_submission_open']
    list_filter = ['is_active', 'registration_open', 'abstract_submission_open']
    search_fields = ['name', 'theme', 'city']
    list_editable = ['is_active', 'registration_open', 'abstract_submission_open']
    readonly_fields = ['stakeholder_link']
    actions = ['reset_stakeholder_link']

    def stakeholder_link(self, obj):
        if not obj.pk:
            return "Save the conference first to generate the stakeholder link."
        from django.urls import reverse
        url = reverse('conference:stakeholder_register', args=[obj.stakeholder_access_token])
        return format_html(
            '<a href="{0}" target="_blank">{0}</a>'
            '<p style="color:#888;margin-top:6px;">Private, fee-free registration link. '
            'Email it directly to stakeholders — it is not linked anywhere public. '
            'Use the “Reset stakeholder registration link” action to invalidate it.</p>',
            url,
        )
    stakeholder_link.short_description = "Stakeholder registration link"

    def reset_stakeholder_link(self, request, queryset):
        import uuid
        for conference in queryset:
            conference.stakeholder_access_token = uuid.uuid4()
            conference.save(update_fields=['stakeholder_access_token'])
        self.message_user(
            request,
            f"Stakeholder registration link reset for {queryset.count()} conference(s). "
            "Any previously shared link no longer works.",
        )
    reset_stakeholder_link.short_description = "Reset stakeholder registration link"

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'theme', 'tagline', 'edition'),
            'description': 'Core identity of the conference.',
        }),
        ('Status & Registration', {
            'fields': ('is_active', 'registration_open', 'abstract_submission_open', 'stakeholder_link'),
            'description': 'Toggle these to open or close the conference, registration, and abstract submission.',
        }),
        ('Dates & Venue', {
            'fields': ('start_date', 'end_date', 'venue', 'city', 'state', 'country'),
        }),
        ('Key Deadlines', {
            'fields': (
                'abstract_deadline', 'early_bird_deadline',
                'notification_date', 'registration_deadline', 'final_paper_deadline',
            ),
            'description': 'Leave blank any dates that do not apply.',
        }),
        ('Content (shown on the About section of the conference page)', {
            'fields': ('description', 'target_audience', 'objectives', 'expected_outcomes', 'key_focus_areas'),
            'description': (
                'description → main paragraph | '
                'objectives → one per line | '
                'expected_outcomes → one per line | '
                'target_audience → who should attend'
            ),
        }),
        ('Contact', {
            'fields': ('contact_email', 'contact_phone', 'website_url'),
        }),
        ('Media', {
            'fields': ('hero_image', 'banner_image', 'organizer_logo'),
        }),
    )


class SubThemeAdminForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=CKEditorWidget(config_name='default'))
    class Meta:
        model = SubTheme
        fields = '__all__'


@admin.register(SubTheme)
class SubThemeAdmin(admin.ModelAdmin):
    form = SubThemeAdminForm
    list_display = ['title', 'conference', 'order', 'is_active']
    list_filter = ['conference', 'is_active']
    list_editable = ['order', 'is_active']
    ordering = ['conference', 'order']


class SpeakerAdminForm(forms.ModelForm):
    bio = forms.CharField(required=False, widget=CKEditorWidget(config_name='default'))
    class Meta:
        model = Speaker
        fields = '__all__'


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    form = SpeakerAdminForm
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


class AbstractSubmissionAdminForm(forms.ModelForm):
    reviewer_notes = forms.CharField(required=False, widget=CKEditorWidget(config_name='default'))
    class Meta:
        model = AbstractSubmission
        fields = '__all__'


@admin.register(AbstractSubmission)
class AbstractSubmissionAdmin(admin.ModelAdmin):
    form = AbstractSubmissionAdminForm
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
class RegistrationAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = RegistrationResource
    list_display = ['ticket_id', 'full_name', 'email', 'category', 'amount', 'payment_method', 'payment_status', 'is_stakeholder', 'checked_in', 'registered_at']
    list_filter = ['conference', 'is_stakeholder', 'payment_method', 'payment_status', 'category', 'checked_in']
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
            'fields': ('is_stakeholder', 'amount', 'payment_method', 'payment_status', 'paystack_reference', 'paystack_transaction_id', 'payment_date')
        }),
        ('Check-in', {
            'fields': ('checked_in', 'checked_in_at')
        }),
    )

    actions = ['export_selected_to_csv', 'confirm_registration',
               'resend_confirmation_emails', 'resend_payment_receipt',
               'mark_checked_in']

    @admin.action(description='⬇ Export selected registrations to CSV')
    def export_selected_to_csv(self, request, queryset):
        """Download the selected registrations as a CSV file.

        The 'Export' button above exports the whole (filtered) list and offers
        other formats; this action is the quick path for a hand-picked set.
        """
        import csv
        from django.http import HttpResponse

        resource = self.resource_class()
        dataset = resource.export(queryset)

        response = HttpResponse(content_type='text/csv')
        filename = f"conference-registrations-{timezone.now():%Y%m%d-%H%M}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(dataset.headers)
        for row in dataset:
            writer.writerow(row)
        return response

    def confirm_registration(self, request, queryset):
        from django.utils import timezone
        # Save each instance individually (instead of queryset.update) so the
        # post_save signal fires and the receipt + welcome emails are sent.
        confirmed = 0
        for registration in queryset.exclude(payment_status='confirmed'):
            registration.payment_status = 'confirmed'
            if not registration.payment_date:
                registration.payment_date = timezone.now()
            registration.save()
            confirmed += 1
        self.message_user(
            request,
            f"{confirmed} registration(s) confirmed. Receipt and welcome emails sent.",
        )
    confirm_registration.short_description = "Confirm selected registrations"

    def resend_confirmation_emails(self, request, queryset):
        """(Re)send the receipt + welcome email to selected confirmed registrations."""
        from conference.emails import send_registration_confirmation
        confirmed = queryset.filter(payment_status='confirmed')
        sent = 0
        failed = 0
        for registration in confirmed:
            try:
                send_registration_confirmation(registration)
            except Exception:
                failed += 1
                continue
            Registration.objects.filter(pk=registration.pk).update(
                confirmation_email_sent=True, receipt_email_sent=True,
            )
            sent += 1

        skipped = queryset.count() - confirmed.count()
        msg = f"Receipt + welcome email sent to {sent} registration(s)."
        if skipped:
            msg += f" {skipped} skipped (payment not confirmed)."
        if failed:
            msg += f" {failed} failed — check the logs."
        self.message_user(request, msg, level=messages.WARNING if failed else messages.INFO)
    resend_confirmation_emails.short_description = "Resend receipt + welcome email"

    def resend_payment_receipt(self, request, queryset):
        """Send only the payment receipt to selected confirmed registrations."""
        from conference.emails import send_payment_receipt
        confirmed = queryset.filter(payment_status='confirmed')
        sent = 0
        failed = 0
        for registration in confirmed:
            try:
                send_payment_receipt(registration)
            except Exception:
                failed += 1
                continue
            Registration.objects.filter(pk=registration.pk).update(receipt_email_sent=True)
            sent += 1

        skipped = queryset.count() - confirmed.count()
        msg = f"Payment receipt sent to {sent} registration(s)."
        if skipped:
            msg += f" {skipped} skipped (payment not confirmed)."
        if failed:
            msg += f" {failed} failed — check the logs."
        self.message_user(request, msg, level=messages.WARNING if failed else messages.INFO)
    resend_payment_receipt.short_description = "Resend payment receipt only"

    def mark_checked_in(self, request, queryset):
        from django.utils import timezone
        queryset.update(checked_in=True, checked_in_at=timezone.now())
    mark_checked_in.short_description = "Mark selected as Checked In"

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = "Name"


class ProgramSessionAdminForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=CKEditorWidget(config_name='default'))
    class Meta:
        model = ProgramSession
        fields = '__all__'


class ProgramSessionInline(admin.StackedInline):
    model = ProgramSession
    form = ProgramSessionAdminForm
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
    form = ProgramSessionAdminForm
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


class KeyMessageAdminForm(forms.ModelForm):
    message = forms.CharField(widget=CKEditorWidget(config_name='default'))
    class Meta:
        model = KeyMessage
        fields = '__all__'


@admin.register(KeyMessage)
class KeyMessageAdmin(admin.ModelAdmin):
    form = KeyMessageAdminForm
    list_display = ['message_short', 'conference', 'source', 'is_quote', 'order', 'is_active']
    list_filter = ['conference', 'is_quote', 'is_active']
    list_editable = ['order', 'is_active']

    def message_short(self, obj):
        from django.utils.html import strip_tags
        return strip_tags(obj.message)[:80]
    message_short.short_description = "Message"


@admin.register(LOCMember)
class LOCMemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'email', 'phone', 'conference', 'order', 'is_active']
    list_filter = ['conference', 'is_active']
    search_fields = ['full_name', 'position', 'email']
    list_editable = ['order', 'is_active']
    ordering = ['conference', 'order']


@admin.register(ExhibitorPackage)
class ExhibitorPackageAdmin(admin.ModelAdmin):
    """Standalone exhibition booths that can be booked and paid for."""
    list_display = ['name', 'conference', 'price', 'space_structure', 'max_slots', 'order', 'is_active']
    list_filter = ['conference', 'is_active']
    search_fields = ['name', 'space_structure', 'perks']
    list_editable = ['price', 'order', 'is_active']
    ordering = ['conference', 'order']

    fieldsets = (
        ('Booth', {
            'fields': ('conference', 'name', 'description', 'icon')
        }),
        ('Price & space', {
            'fields': ('price', 'space_structure'),
            'description': 'Space/structure appears beside the price on the Exhibition page.'
        }),
        ('What is included', {
            'fields': ('perks',),
            'description': 'One item per line. Each line becomes a ticked bullet on the booth card.'
        }),
        ('Availability', {
            'fields': ('max_slots', 'order', 'is_active')
        }),
    )


class ExhibitorShowcaseInline(admin.TabularInline):
    model = ExhibitorShowcase
    extra = 0
    fields = ['image_preview', 'title', 'price', 'is_approved', 'is_active', 'created_at']
    readonly_fields = ['image_preview', 'created_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:8px;">', obj.image.url)
        return "—"
    image_preview.short_description = "Image"


@admin.register(Exhibitor)
class ExhibitorAdmin(admin.ModelAdmin):
    list_display = ['reference', 'company_name', 'contact_name', 'email', 'package', 'amount', 'payment_method', 'payment_status', 'registered_at']
    list_filter = ['conference', 'payment_method', 'payment_status', 'package']
    search_fields = ['reference', 'company_name', 'contact_name', 'email']
    list_editable = ['payment_status']
    readonly_fields = ['reference', 'access_token', 'registered_at', 'updated_at', 'paystack_reference', 'paystack_transaction_id', 'showcase_link']
    ordering = ['-registered_at']
    inlines = [ExhibitorShowcaseInline]

    fieldsets = (
        ('Reference', {
            'fields': ('reference', 'conference', 'package', 'access_token', 'showcase_link', 'registered_at')
        }),
        ('Exhibitor', {
            'fields': ('company_name', 'contact_name', 'email', 'phone', 'website', 'logo')
        }),
        ('Payment', {
            'fields': ('amount', 'payment_method', 'payment_status', 'paystack_reference', 'paystack_transaction_id', 'payment_date')
        }),
    )

    actions = ['confirm_exhibitor']

    def confirm_exhibitor(self, request, queryset):
        queryset.update(payment_status='confirmed', payment_date=timezone.now())
    confirm_exhibitor.short_description = "Confirm selected exhibitors (payment)"

    def showcase_link(self, obj):
        if obj.pk:
            from django.urls import reverse
            url = reverse('conference:exhibitor_showcase', args=[obj.access_token])
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "—"
    showcase_link.short_description = "Private showcase link"


@admin.register(ExhibitorShowcase)
class ExhibitorShowcaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'exhibitor', 'price', 'is_approved', 'is_active', 'image_preview', 'created_at']
    list_filter = ['is_approved', 'is_active', 'exhibitor__conference']
    search_fields = ['title', 'exhibitor__company_name']
    list_editable = ['is_approved', 'is_active']
    readonly_fields = ['created_at', 'image_preview']
    ordering = ['-created_at']

    actions = ['approve_items', 'unapprove_items']

    def approve_items(self, request, queryset):
        queryset.update(is_approved=True)
    approve_items.short_description = "Approve selected items for public display"

    def unapprove_items(self, request, queryset):
        queryset.update(is_approved=False)
    unapprove_items.short_description = "Unapprove selected items"

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:8px;">', obj.image.url)
        return "—"
    image_preview.short_description = "Image"


@admin.register(PaymentVerifier)
class PaymentVerifierAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'last_login_at', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'email']
    list_editable = ['is_active']
    readonly_fields = ['last_login_at', 'created_at']
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'is_active'),
            'description': (
                'People listed here can access the Payment Verification page without being '
                'staff. They visit /conference/payment/verification/, enter this email, and '
                'receive a 2-hour sign-in link. Untick "is active" to revoke access immediately.'
            ),
        }),
        ('Activity', {
            'fields': ('last_login_at', 'created_at'),
        }),
    )


@admin.register(AbstractReviewer)
class AbstractReviewerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'link_sent_at', 'last_login_at', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'email']
    list_editable = ['is_active']
    readonly_fields = ['access_link', 'link_sent_at', 'last_login_at', 'created_at']
    actions = ['resend_access_link']
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'is_active'),
            'description': (
                'People listed here can view the Abstract Review page without being staff. '
                'When you add an active email and save, their permanent access link is emailed '
                'to them automatically. The link never expires — they can bookmark it and return '
                'any time while active. Copy it from "Access link" below to share it another way, '
                'use the "Resend access link" action to email it again, or untick "is active" to '
                'revoke access immediately.'
            ),
        }),
        ('Access', {
            'fields': ('access_link', 'link_sent_at', 'last_login_at', 'created_at'),
        }),
    )

    def changeform_view(self, request, *args, **kwargs):
        # Stash the request so access_link can build an absolute URL.
        self._request = request
        return super().changeform_view(request, *args, **kwargs)

    def access_link(self, obj):
        if not obj or not obj.pk:
            return "— saved after you add the reviewer —"
        from .views import abstract_reviewer_access_url
        request = getattr(self, '_request', None)
        if request is not None:
            url = abstract_reviewer_access_url(request, obj)
        else:
            from django.urls import reverse
            url = reverse('conference:abstract_reviewer_login', args=[str(obj.access_token)])
        return format_html(
            '<a href="{}" target="_blank" style="word-break:break-all;">{}</a>'
            '<br><span style="color:#888;font-size:0.85em;">Permanent — share only with this reviewer.</span>',
            url, url,
        )
    access_link.short_description = "Access link"

    def _send_link(self, request, reviewer):
        """Send a magic link to one reviewer; report success/failure via messages.
        Returns True on success."""
        from .views import issue_abstract_reviewer_link
        if not reviewer.is_active:
            messages.warning(
                request,
                f"Skipped {reviewer.email}: access is deactivated (tick “is active” first).",
            )
            return False
        try:
            issue_abstract_reviewer_link(request, reviewer)
        except Exception as exc:
            messages.error(request, f"Could not email {reviewer.email}: {exc}")
            return False
        messages.success(request, f"Access link sent to {reviewer.email}.")
        return True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Email an access link when a reviewer is first added (or when an
        # existing entry is (re)activated and has never received one).
        newly_active = 'is_active' in form.changed_data and obj.is_active
        if obj.is_active and (not change or newly_active) and not obj.link_sent_at:
            self._send_link(request, obj)

    @admin.action(description="Resend access link")
    def resend_access_link(self, request, queryset):
        for reviewer in queryset:
            self._send_link(request, reviewer)


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ['key', 'content_preview', 'updated_by', 'updated_at']
    search_fields = ['key', 'content']
    readonly_fields = ['updated_by', 'updated_at']

    def content_preview(self, obj):
        from django.utils.html import strip_tags
        return strip_tags(obj.content)[:80]
    content_preview.short_description = "Content"


# ─── Sponsorship packages & benefits ──────────────────────────────────────────

@admin.register(SponsorshipBenefit)
class SponsorshipBenefitAdmin(admin.ModelAdmin):
    """The rows of the sponsorship comparison table."""
    list_display = ['label', 'conference', 'order', 'packages_filled', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['conference', 'is_active']
    search_fields = ['label', 'description']
    ordering = ['conference', 'order']

    fieldsets = (
        (None, {
            'fields': ('conference', 'label', 'description', 'order', 'is_active'),
            'description': (
                'Each benefit is one <strong>row</strong> of the comparison table on the '
                'Exhibition page. What each package offers for this row is set on the '
                'package itself, under Sponsorship Packages.'
            )
        }),
    )

    @admin.display(description='Filled in for')
    def packages_filled(self, obj):
        total = SponsorshipPackage.objects.filter(conference=obj.conference, is_active=True).count()
        filled = obj.package_values.exclude(value='').count()
        colour = '#0a7d2b' if filled >= total else '#b45309'
        return format_html('<span style="color:{};">{} of {} package(s)</span>', colour, filled, total)


class SponsorshipPackageBenefitInline(admin.TabularInline):
    """Edit every benefit value for a package on one screen."""
    model = SponsorshipPackageBenefit
    extra = 0
    fields = ['benefit', 'value']
    autocomplete_fields = ['benefit']
    verbose_name = "Benefit"
    verbose_name_plural = "What this package includes (one row per benefit)"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            # Only offer benefits belonging to this package's conference.
            formset.form.base_fields['benefit'].queryset = SponsorshipBenefit.objects.filter(
                conference=obj.conference, is_active=True
            )
        return formset


@admin.register(SponsorshipPackage)
class SponsorshipPackageAdmin(admin.ModelAdmin):
    """The columns of the sponsorship comparison table."""
    list_display = ['name', 'conference', 'price_column', 'position', 'benefits_filled',
                    'is_featured', 'order', 'is_active']
    list_editable = ['is_featured', 'order', 'is_active']
    list_filter = ['conference', 'is_active', 'is_featured']
    search_fields = ['name', 'position']
    ordering = ['conference', 'order']
    inlines = [SponsorshipPackageBenefitInline]

    fieldsets = (
        ('Package', {
            'fields': ('conference', 'name', 'position'),
        }),
        ('Price', {
            'fields': ('price', 'price_display'),
            'description': (
                'Enter the amount in <strong>Price</strong> for a fixed tier. For a range '
                '(such as the Supporting Partner tier) leave Price blank and type the range '
                'into <strong>Price display</strong> instead.'
            )
        }),
        ('Display', {
            'fields': ('accent_color', 'is_featured', 'order', 'is_active'),
        }),
    )

    @admin.display(description='Price', ordering='price')
    def price_column(self, obj):
        return obj.display_price

    @admin.display(description='Benefits filled')
    def benefits_filled(self, obj):
        total = SponsorshipBenefit.objects.filter(conference=obj.conference, is_active=True).count()
        filled = obj.benefit_values.exclude(value='').count()
        if not total:
            return format_html('<span style="color:#b45309;">no benefit rows defined</span>')
        colour = '#0a7d2b' if filled >= total else '#b45309'
        return format_html('<span style="color:{};">{} of {}</span>', colour, filled, total)


@admin.register(SponsorshipPackageBenefit)
class SponsorshipPackageBenefitAdmin(admin.ModelAdmin):
    """Direct access to individual cells, for bulk edits across packages."""
    list_display = ['benefit', 'package', 'short_value']
    list_filter = ['package__conference', 'benefit', 'package']
    search_fields = ['value', 'benefit__label', 'package__name']
    autocomplete_fields = ['package', 'benefit']
    ordering = ['benefit__order', 'package__order']

    @admin.display(description='Value')
    def short_value(self, obj):
        if not obj.is_included:
            return format_html('<span style="color:#999;">not included</span>')
        return obj.value[:80] + ('…' if len(obj.value) > 80 else '')
