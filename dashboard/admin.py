from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    APIConfiguration, ParticipantRecord, AkilimoParticipant, DashboardMetrics, 
    DataSyncLog, PartnerOrganization, UserProfile, Membership, Payment
)

@admin.register(APIConfiguration)
class APIConfigurationAdmin(admin.ModelAdmin):
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
class ParticipantRecordAdmin(admin.ModelAdmin):
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
class DashboardMetricsAdmin(admin.ModelAdmin):
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
class DataSyncLogAdmin(admin.ModelAdmin):
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
class PartnerOrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization_type', 'city', 'state', 'is_active', 'total_farmers', 'created_at']
    list_filter = ['organization_type', 'state', 'country', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'contact_person', 'email', 'city']
    readonly_fields = ['created_at', 'updated_at', 'joined_program_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'organization_type', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'email', 'phone_number', 'website')
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
    
    def total_farmers(self, obj):
        return obj.total_farmers
    total_farmers.short_description = 'Total Farmers'


@admin.register(AkilimoParticipant)
class AkilimoParticipantAdmin(admin.ModelAdmin):
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
    can_delete = False
    verbose_name_plural = 'Profile'
    
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


# Extend User Admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
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
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'member', 'membership_type', 'status', 'start_date', 'end_date', 'is_active']
    list_filter = ['membership_type', 'status', 'start_date', 'end_date', 'created_at']
    search_fields = ['certificate_number', 'member__username', 'member__first_name', 'member__last_name', 'member__email']
    readonly_fields = ['membership_id', 'certificate_number', 'qr_code', 'created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Member Information', {
            'fields': ('member', 'membership_type', 'status')
        }),
        ('Subscription Period', {
            'fields': ('start_date', 'end_date')
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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'membership', 'amount', 'currency', 'payment_method', 'status', 'paid_at', 'created_at']
    list_filter = ['payment_method', 'status', 'currency', 'paid_at', 'created_at']
    search_fields = ['payment_id', 'paystack_reference', 'membership__member__username', 'membership__member__email']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'paid_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('membership', 'amount', 'currency', 'payment_method', 'status')
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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('membership__member')
