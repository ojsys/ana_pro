from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
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


@admin.register(Membership)
class MembershipAdmin(ImportExportModelAdmin):
    resource_class = MembershipResource
    list_display = [
        'certificate_number', 'member', 'membership_type', 'subscription_status_display',
        'registration_status', 'subscription_year_display', 'access_status', 'created_at'
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
    actions = ['activate_subscription', 'suspend_access', 'restore_access']

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
            'description': 'Annual membership dues tracking (Jan 1 - Dec 31)'
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
        """Display subscription status with color coding"""
        status_colors = {
            'Active': 'success',
            'Expired': 'danger',
            'Suspended': 'warning',
            'No Active Subscription': 'secondary',
        }
        status_text = obj.subscription_status_text
        color = status_colors.get(status_text, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, status_text)
    subscription_status_display.short_description = 'Subscription Status'

    def registration_status(self, obj):
        """Display registration payment status"""
        if obj.registration_paid:
            return format_html('<span class="badge bg-success">✓ Paid</span>')
        return format_html('<span class="badge bg-warning">Pending</span>')
    registration_status.short_description = 'Registration'

    def subscription_year_display(self, obj):
        """Display subscription year without thousand separator"""
        if obj.subscription_year:
            # Format as string to prevent comma formatting from USE_THOUSAND_SEPARATOR
            year_str = str(obj.subscription_year).replace(',', '')
            return format_html('<strong>{}</strong>', year_str)
        return '-'
    subscription_year_display.short_description = 'Year'

    def access_status(self, obj):
        """Display access status"""
        if obj.access_suspended:
            return format_html('<span class="badge bg-danger">Suspended</span>')
        elif obj.has_platform_access:
            return format_html('<span class="badge bg-success">✓ Active</span>')
        return format_html('<span class="badge bg-secondary">No Access</span>')
    access_status.short_description = 'Access'

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
            'fields': ('membership', 'payment_purpose', 'subscription_year', 'amount', 'currency', 'payment_method', 'status')
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
        return format_html('<strong>₦{:,.2f}</strong>', obj.amount)
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
    list_display = ['payment_type_display', 'membership_type_display', 'price_display', 'is_active', 'created_at']
    list_filter = ['payment_type', 'membership_type', 'is_active', 'created_at']
    search_fields = ['description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']

    fieldsets = (
        ('Pricing Configuration', {
            'fields': ('payment_type', 'membership_type', 'price', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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
        return format_html('<strong>₦{:,.2f}</strong>', obj.price)
    price_display.short_description = 'Price'
