from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django import forms
from decimal import Decimal
from datetime import date, datetime
from import_export.admin import ImportExportModelAdmin
from .models import (
    APIConfiguration, ParticipantRecord, AkilimoParticipant, DashboardMetrics,
    DataSyncLog, PartnerOrganization, UserProfile, Membership, Payment, MembershipPricing
)
from .resources import (
    APIConfigurationResource, PartnerOrganizationResource, UserProfileResource,
    AkilimoParticipantResource, ParticipantRecordResource, DataSyncLogResource,
    DashboardMetricsResource, MembershipResource, PaymentResource,
    MembershipPricingResource, UserResource
)


# Customize Admin Site
class AkilimoAdminSite(admin.AdminSite):
    site_header = 'AKILIMO Nigeria Administration'
    site_title = 'AKILIMO Admin'
    index_title = 'Welcome to AKILIMO Nigeria Administration'

    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps with custom ordering.
        """
        app_list = super().get_app_list(request)

        # Define custom ordering for models within the Dashboard app
        model_order = {
            'Membership Pricing': 1,  # Put pricing first for easy access
            'Memberships': 2,
            'Payments': 3,
            'Partner Organizations': 4,
            'User Profiles': 5,
            'AKILIMO Participants': 6,
            'Participant Records': 7,
            'Dashboard Metrics': 8,
            'Data Sync Logs': 9,
            'API Configurations': 10,
        }

        # Sort models within each app
        for app in app_list:
            if app['app_label'] == 'dashboard':
                app['models'].sort(
                    key=lambda x: model_order.get(x['name'], 999)
                )

        return app_list


# Use custom admin site (comment out if you want to use default)
# admin_site = AkilimoAdminSite(name='akilimo_admin')

@admin.register(APIConfiguration)
class APIConfigurationAdmin(ImportExportModelAdmin):
    resource_class = APIConfigurationResource
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('base_url', 'token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ParticipantRecord)
class ParticipantRecordAdmin(ImportExportModelAdmin):
    resource_class = ParticipantRecordResource
    list_display = ['external_id', 'gender', 'state', 'location', 'training_date', 'created_at']
    list_filter = ['gender', 'state', 'usecase', 'event_type', 'training_date', 'created_at']
    search_fields = ['external_id', 'location', 'facilitator', 'state', 'lga']
    readonly_fields = ['external_id', 'created_at', 'updated_at']
    date_hierarchy = 'training_date'
    
    fieldsets = (
        ('Participant Information', {
            'fields': ('external_id', 'usecase', 'gender', 'age_group')
        }),
        ('Location Details', {
            'fields': ('location', 'state', 'lga')
        }),
        ('Training Information', {
            'fields': ('event_type', 'training_date', 'facilitator')
        }),
        ('Cassava Production', {
            'fields': ('farm_size', 'previous_yield', 'expected_yield')
        }),
        ('Metadata', {
            'fields': ('raw_data', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(DashboardMetrics)
class DashboardMetricsAdmin(ImportExportModelAdmin):
    resource_class = DashboardMetricsResource
    list_display = ['metric_type', 'metric_name', 'period_start', 'period_end', 'is_current', 'computed_at']
    list_filter = ['metric_type', 'is_current', 'computed_at']
    search_fields = ['metric_name', 'metric_type']
    readonly_fields = ['computed_at']
    date_hierarchy = 'computed_at'
    
    fieldsets = (
        ('Metric Information', {
            'fields': ('metric_type', 'metric_name', 'metric_value')
        }),
        ('Time Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Status', {
            'fields': ('is_current', 'computed_at')
        }),
    )

@admin.register(DataSyncLog)
class DataSyncLogAdmin(ImportExportModelAdmin):
    resource_class = DataSyncLogResource
    list_display = ['sync_type', 'status', 'records_processed', 'records_created', 'records_updated', 'started_at', 'duration_seconds']
    list_filter = ['sync_type', 'status', 'started_at']
    search_fields = ['sync_type', 'error_message']
    readonly_fields = ['started_at', 'completed_at', 'duration_seconds']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Sync Information', {
            'fields': ('sync_type', 'status', 'initiated_by')
        }),
        ('Results', {
            'fields': ('records_processed', 'records_created', 'records_updated')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Error Details', {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('initiated_by')


@admin.register(PartnerOrganization)
class PartnerOrganizationAdmin(ImportExportModelAdmin):
    resource_class = PartnerOrganizationResource
    list_display = ['name', 'code', 'status_display', 'organization_type', 'city', 'state', 'requested_by', 'is_featured', 'feature_order', 'is_active', 'total_farmers', 'created_at']
    list_filter = ['status', 'organization_type', 'state', 'country', 'is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'contact_person', 'email', 'city']
    readonly_fields = ['created_at', 'updated_at', 'joined_program_date', 'requested_by', 'approved_by', 'approved_at']
    list_editable = ['is_featured', 'feature_order']
    actions = ['approve_organizations', 'reject_organizations']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'organization_type', 'is_active')
        }),
        ('Approval Status', {
            'fields': ('status', 'requested_by', 'approved_by', 'approved_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'email', 'phone_number', 'website')
        }),
        ('Visual Branding', {
            'fields': ('logo', 'is_featured', 'feature_order', 'success_story')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'country')
        }),
        ('Dates', {
            'fields': ('established_date', 'joined_program_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):
        """Display status as a colored badge"""
        return obj.status_badge
    status_display.short_description = 'Status'
    status_display.allow_tags = True

    def total_farmers(self, obj):
        return obj.total_farmers
    total_farmers.short_description = 'Total Farmers'

    @admin.action(description='Approve selected organizations')
    def approve_organizations(self, request, queryset):
        """Approve selected pending organizations"""
        from django.utils import timezone
        from django.contrib import messages

        pending_orgs = queryset.filter(status=PartnerOrganization.STATUS_PENDING)
        count = pending_orgs.count()

        if count == 0:
            messages.warning(request, 'No pending organizations selected.')
            return

        # Update organizations
        pending_orgs.update(
            status=PartnerOrganization.STATUS_APPROVED,
            approved_by=request.user,
            approved_at=timezone.now(),
            is_active=True
        )

        # Send notifications to requesting users
        for org in pending_orgs:
            if org.requested_by and org.requested_by.email:
                # You can implement email notification here
                pass

        messages.success(request, f'Successfully approved {count} organization(s).')

    @admin.action(description='Reject selected organizations')
    def reject_organizations(self, request, queryset):
        """Reject selected pending organizations"""
        from django.utils import timezone
        from django.contrib import messages

        pending_orgs = queryset.filter(status=PartnerOrganization.STATUS_PENDING)
        count = pending_orgs.count()

        if count == 0:
            messages.warning(request, 'No pending organizations selected.')
            return

        # Update organizations
        pending_orgs.update(
            status=PartnerOrganization.STATUS_REJECTED,
            approved_by=request.user,
            approved_at=timezone.now(),
            is_active=False
        )

        # Send notifications to requesting users
        for org in pending_orgs:
            if org.requested_by and org.requested_by.email:
                # You can implement email notification here
                pass

        messages.warning(request, f'Rejected {count} organization(s). You can add rejection reasons in the individual organization details.')


@admin.register(AkilimoParticipant)
class AkilimoParticipantAdmin(ImportExportModelAdmin):
    resource_class = AkilimoParticipantResource
    list_display = ['external_id', 'full_name', 'farmer_gender', 'admin_level1', 'partner', 'event_date', 'crop']
    list_filter = ['farmer_gender', 'admin_level1', 'partner', 'crop', 'event_type', 'age_category', 'country']
    search_fields = ['external_id', 'farmer_first_name', 'farmer_surname', 'event_city', 'partner']
    readonly_fields = ['external_id', 'created_at', 'updated_at', 'api_created_on', 'source_submitted_on']
    date_hierarchy = 'event_date'
    
    fieldsets = (
        ('Identification', {
            'fields': ('external_id', 'source_id', 'usecase', 'usecase_ref_id')
        }),
        ('Farmer Information', {
            'fields': ('farmer_first_name', 'farmer_surname', 'farmer_gender', 'farmer_age', 'age_category', 'farmer_phone_no', 'farmer_own_phone')
        }),
        ('Organization Details', {
            'fields': ('farmer_organization', 'farmer_position', 'farmer_relationship', 'participants_type')
        }),
        ('Event Information', {
            'fields': ('event_date', 'event_year', 'event_month', 'event_type', 'event_format', 'event_city', 'event_venue', 'event_geopoint')
        }),
        ('Geographic Information', {
            'fields': ('country', 'admin_level1', 'admin_level2')
        }),
        ('Partner Information', {
            'fields': ('partner', 'org_first_name', 'org_surname', 'org_phone_no')
        }),
        ('Agricultural Information', {
            'fields': ('crop', 'thematic_area', 'thematic_area_overall')
        }),
        ('Data Source', {
            'fields': ('data_source', 'source_submitted_on', 'api_created_on')
        }),
        ('Metadata', {
            'fields': ('raw_data', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)


# Inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = True  # Allow deletion when user is deleted
    verbose_name_plural = 'Profile'
    max_num = 1  # Only one profile per user
    extra = 0  # Don't show extra empty forms
    
    fieldsets = (
        ('Partner Information', {
            'fields': ('partner_organization', 'partner_name', 'position', 'department')
        }),
        ('Contact Information', {
            'fields': ('phone_number',)
        }),
        ('Status', {
            'fields': ('is_partner_verified', 'profile_completed', 'profile_completion_date')
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'dashboard_preferences'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('profile_completion_date', 'created_at', 'updated_at')


# Extend User Admin with Import/Export functionality
class UserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    resource_class = UserResource
    inlines = (UserProfileInline,)

    # Ensure list_display includes all necessary fields
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    resource_class = UserProfileResource
    list_display = ['user', 'partner_name', 'partner_organization', 'position', 'is_partner_verified', 'profile_completed', 'created_at']
    list_filter = ['partner_organization', 'is_partner_verified', 'profile_completed', 'email_notifications', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone_number', 'position']
    readonly_fields = ['profile_completion_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Partner Information', {
            'fields': ('partner_organization', 'partner_name', 'position', 'department')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'profile_photo')
        }),
        ('Status', {
            'fields': ('is_partner_verified', 'profile_completed', 'profile_completion_date')
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'dashboard_preferences'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'partner_organization')


# Inline for showing payments in Membership admin
class PaymentInline(admin.TabularInline):
    """Show all payments for this membership"""
    model = Payment
    extra = 0
    can_delete = False
    readonly_fields = [
        'payment_id_short', 'payment_purpose_display', 'amount_with_currency',
        'status_badge', 'subscription_year', 'paid_at', 'created_at'
    ]
    fields = [
        'payment_id_short', 'payment_purpose_display', 'subscription_year',
        'amount_with_currency', 'status_badge', 'payment_method', 'paid_at'
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def payment_id_short(self, obj):
        """Display shortened payment ID with link"""
        if obj.pk:
            url = f'/admin/dashboard/payment/{obj.pk}/change/'
            return format_html('<a href="{}">{}</a>', url, str(obj.payment_id)[:8].upper())
        return '-'
    payment_id_short.short_description = 'Payment ID'

    def payment_purpose_display(self, obj):
        """Display payment purpose with badge"""
        colors = {'registration': 'primary', 'annual_dues': 'success'}
        color = colors.get(obj.payment_purpose, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_payment_purpose_display() if obj.pk else '-'
        )
    payment_purpose_display.short_description = 'Purpose'

    def amount_with_currency(self, obj):
        """Display amount with currency symbol"""
        if obj.pk:
            return f'₦{obj.amount:,.2f}'
        return '-'
    amount_with_currency.short_description = 'Amount'

    def status_badge(self, obj):
        """Display status with color coding"""
        if not obj.pk:
            return '-'
        status_colors = {
            'successful': 'success',
            'pending': 'warning',
            'processing': 'info',
            'failed': 'danger',
        }
        color = status_colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Status'


# Custom Form for Membership with better date/time widgets
class MembershipAdminForm(forms.ModelForm):
    """Custom form for Membership admin with date/time pickers"""

    class Meta:
        model = Membership
        fields = '__all__'
        widgets = {
            'subscription_start_date': forms.DateInput(attrs={'type': 'date'}),
            'subscription_end_date': forms.DateInput(attrs={'type': 'date'}),
            'registration_payment_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'last_annual_dues_payment_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


@admin.register(Membership)
class MembershipAdmin(ImportExportModelAdmin):
    resource_class = MembershipResource
    form = MembershipAdminForm  # Use custom form with date/time pickers
    inlines = [PaymentInline]  # Show payment history inline

    list_display = [
        'certificate_number', 'member', 'membership_type', 'subscription_status_display',
        'registration_status', 'subscription_year_display', 'recent_payment_info', 'access_status', 'created_at'
    ]
    list_filter = [
        'membership_type', 'status', 'registration_paid', 'has_platform_access',
        'access_suspended', 'subscription_year', 'created_at'
    ]
    search_fields = ['certificate_number', 'member__username', 'member__first_name', 'member__last_name', 'member__email']
    readonly_fields = [
        'membership_id', 'certificate_number', 'qr_code', 'created_at', 'updated_at',
        'subscription_status_text', 'has_active_subscription', 'days_until_expiry', 'needs_renewal'
    ]
    date_hierarchy = 'created_at'
    actions = [
        'activate_subscription', 'suspend_access', 'restore_access',
        'mark_annual_dues_paid_current_year', 'mark_annual_dues_paid_next_year'
    ]

    fieldsets = (
        ('Member Information', {
            'fields': ('member', 'membership_type', 'status')
        }),
        ('Registration Payment', {
            'fields': ('registration_paid', 'registration_payment_date'),
            'description': 'One-time registration fee tracking'
        }),
        ('Annual Dues Subscription', {
            'fields': (
                'subscription_year', 'annual_dues_paid_for_year',
                'subscription_start_date', 'subscription_end_date',
                'last_annual_dues_payment_date'
            ),
            'description': (
                'Annual membership dues tracking. '
                '<strong>Automatic:</strong> When a Paystack payment is successful, these fields update automatically. '
                '<strong>Manual:</strong> Use date pickers for custom periods, or use admin actions to mark as paid. '
                'See payment history below.'
            )
        }),
        ('Access Control', {
            'fields': (
                'has_platform_access', 'can_download_certificate', 'can_download_id_card',
                'access_suspended', 'access_suspended_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Subscription Status (Read-Only)', {
            'fields': ('subscription_status_text', 'has_active_subscription', 'days_until_expiry', 'needs_renewal'),
            'classes': ('collapse',)
        }),
        ('Legacy Fields', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',),
            'description': 'Kept for backward compatibility'
        }),
        ('Certificate & ID Card', {
            'fields': ('certificate_generated', 'id_card_generated', 'certificate_number')
        }),
        ('Verification', {
            'fields': ('qr_code',)
        }),
        ('Metadata', {
            'fields': ('membership_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def subscription_status_display(self, obj):
        """Display subscription status with color coding based on current status"""
        from datetime import date

        # Get real-time subscription status
        current_year = date.today().year

        if obj.access_suspended:
            status_text = "Suspended"
            color = "warning"
            icon = "⚠"
        elif obj.has_active_subscription:
            # Has active annual dues for current year
            status_text = "Active"
            color = "success"
            icon = "✓"
            if obj.annual_dues_paid_for_year:
                status_text = f"Active ({obj.annual_dues_paid_for_year})"
        elif obj.annual_dues_paid_for_year and obj.annual_dues_paid_for_year < current_year:
            # Paid for previous year but expired
            status_text = f"Expired ({obj.annual_dues_paid_for_year})"
            color = "danger"
            icon = "✗"
        elif obj.registration_paid and not obj.annual_dues_paid_for_year:
            # Registered but no annual dues paid yet
            status_text = "Registered (No Annual Dues)"
            color = "info"
            icon = "ℹ"
        else:
            # No active subscription
            status_text = "Inactive"
            color = "secondary"
            icon = "○"

        return format_html('<span class="badge bg-{}">{} {}</span>', color, icon, status_text)
    subscription_status_display.short_description = 'Subscription Status'

    def registration_status(self, obj):
        """Display registration payment status with date"""
        if obj.registration_paid:
            if obj.registration_payment_date:
                date_str = obj.registration_payment_date.strftime('%Y-%m-%d')
                return format_html(
                    '<span class="badge bg-success" title="Paid on {}">✓ Paid</span>',
                    date_str
                )
            return format_html('<span class="badge bg-success">✓ Paid</span>')
        return format_html('<span class="badge bg-warning">⚠ Pending</span>')
    registration_status.short_description = 'Registration'

    def recent_payment_info(self, obj):
        """Display most recent successful payment from Paystack"""
        recent_payment = obj.payments.filter(status='successful').order_by('-paid_at').first()

        if recent_payment:
            purpose_icons = {
                'registration': '🎫',
                'annual_dues': '💳'
            }
            icon = purpose_icons.get(recent_payment.payment_purpose, '💰')

            if recent_payment.paid_at:
                # Show relative time (e.g., "2 days ago")
                from django.utils.timesince import timesince
                time_ago = timesince(recent_payment.paid_at)

                return format_html(
                    '<span title="₦{:,.2f} - {}">{} {} ago</span>',
                    recent_payment.amount,
                    recent_payment.get_payment_purpose_display(),
                    icon,
                    time_ago.split(',')[0]  # Show only the first part (e.g., "2 days" not "2 days, 3 hours")
                )

        return format_html('<span style="color: #999;">No payments</span>')
    recent_payment_info.short_description = 'Last Payment'

    def subscription_year_display(self, obj):
        """Display subscription year with status indicator"""
        from datetime import date
        current_year = date.today().year

        if obj.annual_dues_paid_for_year:
            # Format as string to prevent comma formatting from USE_THOUSAND_SEPARATOR
            year_str = str(obj.annual_dues_paid_for_year).replace(',', '')

            if obj.annual_dues_paid_for_year == current_year and obj.has_active_subscription:
                # Current year and active
                return format_html('<strong class="text-success">{} ✓</strong>', year_str)
            elif obj.annual_dues_paid_for_year < current_year:
                # Previous year - expired
                return format_html('<span class="text-danger">{} (Expired)</span>', year_str)
            else:
                return format_html('<strong>{}</strong>', year_str)
        return format_html('<span class="text-muted">-</span>')
    subscription_year_display.short_description = 'Annual Dues Year'

    def access_status(self, obj):
        """Display platform access status with clear indicators"""
        if obj.access_suspended:
            return format_html('<span class="badge bg-danger">🚫 Suspended</span>')
        elif obj.has_platform_access and obj.has_active_subscription:
            # Has both registration and active annual dues
            return format_html('<span class="badge bg-success">✓ Full Access</span>')
        elif obj.registration_paid and not obj.has_active_subscription:
            # Has registration but no active annual dues
            return format_html('<span class="badge bg-warning">⚠ Limited (No Annual Dues)</span>')
        else:
            # No access
            return format_html('<span class="badge bg-secondary">○ No Access</span>')
    access_status.short_description = 'Platform Access'

    @admin.action(description='Activate subscription for selected memberships')
    def activate_subscription(self, request, queryset):
        """Manually activate subscription for current year"""
        from datetime import date
        from django.contrib import messages

        current_year = date.today().year
        count = 0

        for membership in queryset:
            membership.subscription_year = current_year
            membership.annual_dues_paid_for_year = current_year
            membership.subscription_start_date = date(current_year, 1, 1)
            membership.subscription_end_date = date(current_year, 12, 31)
            membership.access_suspended = False
            membership.save()
            count += 1

        messages.success(request, f'Activated subscription for {count} membership(s) for year {current_year}.')

    @admin.action(description='Suspend access for selected memberships')
    def suspend_access(self, request, queryset):
        """Suspend access for selected memberships"""
        from django.contrib import messages

        count = queryset.update(access_suspended=True, has_platform_access=False)
        messages.warning(request, f'Suspended access for {count} membership(s).')

    @admin.action(description='Restore access for selected memberships')
    def restore_access(self, request, queryset):
        """Restore access for selected memberships"""
        from django.contrib import messages

        count = 0
        for membership in queryset:
            membership.access_suspended = False
            membership.save()  # This will trigger update_access_permissions
            count += 1

        messages.success(request, f'Restored access for {count} membership(s).')

    def mark_annual_dues_paid_current_year(self, request, queryset):
        """Mark selected members as having paid annual dues for current year"""
        from django.contrib import messages
        from django.utils import timezone

        current_year = date.today().year
        count = 0

        for membership in queryset:
            membership.annual_dues_paid_for_year = current_year
            membership.subscription_start_date = date(current_year, 1, 1)
            membership.subscription_end_date = date(current_year, 12, 31)
            membership.last_annual_dues_payment_date = timezone.now()
            membership.status = 'active'
            membership.access_suspended = False
            membership.save()
            count += 1

        messages.success(
            request,
            f'Marked {count} member(s) as paid for {current_year}. '
            f'Subscription dates set to Jan 1 - Dec 31, {current_year}.'
        )
    mark_annual_dues_paid_current_year.short_description = f'✓ Mark annual dues PAID for {date.today().year}'

    def mark_annual_dues_paid_next_year(self, request, queryset):
        """Mark selected members as having paid annual dues for next year"""
        from django.contrib import messages
        from django.utils import timezone

        current_year = date.today().year
        next_year = current_year + 1
        count = 0

        for membership in queryset:
            membership.annual_dues_paid_for_year = next_year
            membership.subscription_start_date = date(next_year, 1, 1)
            membership.subscription_end_date = date(next_year, 12, 31)
            membership.last_annual_dues_payment_date = timezone.now()
            membership.status = 'active'
            membership.access_suspended = False
            membership.save()
            count += 1

        messages.success(
            request,
            f'Marked {count} member(s) as paid for {next_year}. '
            f'Subscription dates set to Jan 1 - Dec 31, {next_year}.'
        )
    mark_annual_dues_paid_next_year.short_description = f'✓ Mark annual dues PAID for {date.today().year + 1}'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member')


@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    resource_class = PaymentResource
    list_display = [
        'payment_id_short', 'membership', 'payment_purpose_display', 'amount_display',
        'payment_method', 'status_display', 'subscription_year', 'paid_at', 'created_at'
    ]
    list_filter = ['payment_purpose', 'payment_method', 'status', 'currency', 'subscription_year', 'paid_at', 'created_at']
    search_fields = ['payment_id', 'paystack_reference', 'membership__member__username', 'membership__member__email']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'paid_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Payment Information', {
            'fields': ('membership', 'payment_purpose', 'subscription_year', 'amount', 'currency', 'payment_method', 'status'),
            'description': 'Note: Changing payment status to "Successful" will automatically update the associated membership.'
        }),
        ('Payment Gateway', {
            'fields': ('paystack_reference', 'paystack_access_code', 'gateway_response')
        }),
        ('Transaction Details', {
            'fields': ('description', 'paid_at')
        }),
        ('Metadata', {
            'fields': ('payment_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def payment_id_short(self, obj):
        """Display shortened payment ID"""
        return str(obj.payment_id)[:8].upper()
    payment_id_short.short_description = 'Payment ID'

    def payment_purpose_display(self, obj):
        """Display payment purpose with color coding"""
        colors = {
            'registration': 'primary',
            'annual_dues': 'success',
        }
        color = colors.get(obj.payment_purpose, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_payment_purpose_display()
        )
    payment_purpose_display.short_description = 'Purpose'

    def amount_display(self, obj):
        """Display amount with currency"""
        from decimal import Decimal
        # Convert to Decimal to avoid SafeString formatting issues
        amount_value = Decimal(str(obj.amount))
        formatted_amount = f'{amount_value:,.2f}'
        return format_html('<strong>₦{}</strong>', formatted_amount)
    amount_display.short_description = 'Amount'

    def status_display(self, obj):
        """Display status with color coding"""
        status_colors = {
            'successful': 'success',
            'pending': 'warning',
            'processing': 'info',
            'failed': 'danger',
            'cancelled': 'secondary',
            'refunded': 'warning',
        }
        color = status_colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_display.short_description = 'Status'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('membership__member')


@admin.register(MembershipPricing)
class MembershipPricingAdmin(ImportExportModelAdmin):
    resource_class = MembershipPricingResource
    list_display = ['payment_type_display', 'membership_type_display', 'price', 'is_active', 'description', 'created_at']
    list_filter = ['payment_type', 'membership_type', 'is_active', 'created_at']
    search_fields = ['description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['price', 'is_active']
    ordering = ['payment_type', 'membership_type']

    fieldsets = (
        ('Pricing Configuration', {
            'fields': ('payment_type', 'membership_type', 'price', 'description', 'is_active'),
            'description': 'Configure membership pricing. Prices are in Nigerian Naira (₦).'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_list_display_links(self, request, list_display):
        """Make payment_type_display and membership_type_display clickable"""
        return ['payment_type_display', 'membership_type_display']

    def payment_type_display(self, obj):
        """Display payment type with color coding"""
        colors = {
            'registration': 'primary',
            'annual_dues': 'success',
        }
        color = colors.get(obj.payment_type, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_payment_type_display()
        )
    payment_type_display.short_description = 'Payment Type'

    def membership_type_display(self, obj):
        """Display membership type"""
        return obj.get_membership_type_display()
    membership_type_display.short_description = 'Membership Type'

    def price_display(self, obj):
        """Display price with currency formatting"""
        return format_html('<strong>₦{:,.2f}</strong>', Decimal(obj.price))
    price_display.short_description = 'Price'

    actions = ['activate_pricing', 'deactivate_pricing']

    def activate_pricing(self, request, queryset):
        """Activate selected pricing items"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} pricing item(s) activated successfully.')
    activate_pricing.short_description = 'Activate selected pricing'

    def deactivate_pricing(self, request, queryset):
        """Deactivate selected pricing items"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} pricing item(s) deactivated successfully.')
    deactivate_pricing.short_description = 'Deactivate selected pricing'
