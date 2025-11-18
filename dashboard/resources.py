"""
Export resource classes for dashboard models
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateTimeWidget, DateWidget
from django.contrib.auth.models import User
from .models import (
    APIConfiguration,
    PartnerOrganization,
    UserProfile,
    AkilimoParticipant,
    ParticipantRecord,
    DataSyncLog,
    DashboardMetrics,
    Membership,
    Payment,
    MembershipPricing,
)


class APIConfigurationResource(resources.ModelResource):
    """Export resource for API Configuration"""

    class Meta:
        model = APIConfiguration
        fields = ('id', 'name', 'token', 'base_url', 'is_active', 'created_at', 'updated_at')
        export_order = fields


class PartnerOrganizationResource(resources.ModelResource):
    """Export resource for Partner Organizations"""
    status = fields.Field(column_name='status')
    requested_by = fields.Field(
        column_name='requested_by',
        attribute='requested_by',
        widget=ForeignKeyWidget(User, 'username')
    )
    approved_by = fields.Field(
        column_name='approved_by',
        attribute='approved_by',
        widget=ForeignKeyWidget(User, 'username')
    )

    class Meta:
        model = PartnerOrganization
        fields = (
            'id', 'name', 'code', 'status', 'description', 'organization_type',
            'contact_person', 'email', 'phone_number', 'website',
            'address', 'city', 'state', 'country',
            'is_featured', 'feature_order', 'success_story',
            'established_date', 'is_active', 'joined_program_date',
            'requested_by', 'approved_by', 'approved_at', 'rejection_reason',
            'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_status(self, partner_org):
        """Convert status to human-readable format"""
        return partner_org.get_status_display()


class UserProfileResource(resources.ModelResource):
    """Export resource for User Profiles"""
    username = fields.Field(column_name='username')
    email = fields.Field(column_name='email')
    first_name = fields.Field(column_name='first_name')
    last_name = fields.Field(column_name='last_name')
    partner_organization = fields.Field(
        column_name='partner_organization',
        attribute='partner_organization',
        widget=ForeignKeyWidget(PartnerOrganization, 'name')
    )

    class Meta:
        model = UserProfile
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'partner_organization', 'partner_name', 'phone_number', 'position',
            'department', 'is_partner_verified', 'profile_completed',
            'profile_completion_date', 'email_notifications', 'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_username(self, profile):
        return profile.user.username

    def dehydrate_email(self, profile):
        return profile.user.email

    def dehydrate_first_name(self, profile):
        return profile.user.first_name

    def dehydrate_last_name(self, profile):
        return profile.user.last_name


class AkilimoParticipantResource(resources.ModelResource):
    """Export resource for AKILIMO Participants (Farmers)"""

    class Meta:
        model = AkilimoParticipant
        fields = (
            'id', 'external_id', 'source_id', 'usecase', 'usecase_ref_id',
            'farmer_first_name', 'farmer_surname', 'farmer_gender', 'farmer_age',
            'age_category', 'farmer_phone_no', 'farmer_own_phone',
            'event_date', 'event_venue', 'event_city', 'event_type', 'organizer',
            'partner', 'admin_level1', 'admin_level2', 'admin_level3',
            'country', 'crop', 'variety', 'area_farm', 'area_cassava',
            'plot_label', 'user_location_latitude', 'user_location_longitude',
            'api_created_on', 'source_submitted_on', 'created_at', 'updated_at'
        )
        export_order = fields


class ParticipantRecordResource(resources.ModelResource):
    """Export resource for Participant Records"""

    class Meta:
        model = ParticipantRecord
        fields = (
            'id', 'external_id', 'source_id', 'usecase', 'usecase_ref_id',
            'farmer_first_name', 'farmer_surname', 'farmer_gender', 'farmer_age',
            'age_category', 'farmer_phone_no', 'farmer_own_phone',
            'event_date', 'event_venue', 'event_city', 'event_type', 'organizer',
            'partner', 'admin_level1', 'admin_level2', 'admin_level3',
            'country', 'crop', 'variety', 'area_farm', 'area_cassava',
            'plot_label', 'user_location_latitude', 'user_location_longitude',
            'api_created_on', 'source_submitted_on', 'created_at', 'updated_at'
        )
        export_order = fields


class DataSyncLogResource(resources.ModelResource):
    """Export resource for Data Sync Logs"""
    initiated_by = fields.Field(
        column_name='initiated_by',
        attribute='initiated_by',
        widget=ForeignKeyWidget(User, 'username')
    )

    class Meta:
        model = DataSyncLog
        fields = (
            'id', 'sync_type', 'status', 'started_at', 'completed_at',
            'duration_seconds', 'records_fetched', 'records_created',
            'records_updated', 'error_message', 'initiated_by', 'created_at'
        )
        export_order = fields


class DashboardMetricsResource(resources.ModelResource):
    """Export resource for Dashboard Metrics"""

    class Meta:
        model = DashboardMetrics
        fields = (
            'id', 'metric_name', 'metric_value', 'metric_type',
            'description', 'created_at', 'updated_at'
        )
        export_order = fields


class MembershipResource(resources.ModelResource):
    """Export resource for Memberships"""
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )
    pricing = fields.Field(
        column_name='pricing_tier',
        attribute='pricing'
    )

    class Meta:
        model = Membership
        fields = (
            'id', 'membership_id', 'user', 'pricing_tier', 'status',
            'start_date', 'end_date', 'auto_renew', 'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_pricing_tier(self, membership):
        return str(membership.pricing) if membership.pricing else ''


class PaymentResource(resources.ModelResource):
    """Export resource for Payments"""
    membership = fields.Field(column_name='membership_id')
    user = fields.Field(column_name='user')

    class Meta:
        model = Payment
        fields = (
            'id', 'payment_id', 'membership_id', 'user', 'amount', 'currency',
            'payment_method', 'status', 'transaction_id', 'payment_date',
            'created_at', 'updated_at'
        )
        export_order = fields

    def dehydrate_membership_id(self, payment):
        return payment.membership.membership_id if payment.membership else ''

    def dehydrate_user(self, payment):
        return payment.membership.user.username if payment.membership and payment.membership.user else ''


class MembershipPricingResource(resources.ModelResource):
    """Export resource for Membership Pricing"""

    class Meta:
        model = MembershipPricing
        fields = (
            'id', 'tier_name', 'description', 'price', 'currency',
            'duration_days', 'features', 'is_active', 'created_at', 'updated_at'
        )
        export_order = fields


class UserResource(resources.ModelResource):
    """Export resource for Users"""

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_active', 'is_superuser', 'date_joined', 'last_login'
        )
        export_order = fields
