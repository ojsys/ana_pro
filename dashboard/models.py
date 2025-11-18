from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from datetime import timedelta

class APIConfiguration(models.Model):
    """Store API configuration and tokens"""
    name = models.CharField(max_length=100, unique=True, default="EiA MELIA API")
    token = models.CharField(max_length=255, help_text="API Token for EiA MELIA API")
    base_url = models.URLField(default="https://my.eia.cgiar.org/api/v1/melia")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"

class PartnerOrganization(models.Model):
    """Partner organizations that participate in AKILIMO program"""

    # Status choices for approval workflow
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    name = models.CharField(max_length=200, unique=True, help_text="Organization name")
    code = models.CharField(max_length=50, unique=True, help_text="Organization code/abbreviation")
    description = models.TextField(blank=True, help_text="Organization description")

    # Approval workflow fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_APPROVED,
        help_text="Approval status of the organization"
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_organizations',
        help_text="User who requested this organization"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_organizations',
        help_text="Admin who approved/rejected this organization"
    )
    approved_at = models.DateTimeField(null=True, blank=True, help_text="When the organization was approved/rejected")
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection (if applicable)")

    # Contact information
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Visual branding
    logo = models.ImageField(upload_to='partner_logos/', blank=True, null=True, help_text="Partner organization logo")

    # Featured status
    is_featured = models.BooleanField(default=False, help_text="Display on homepage as featured partner")
    feature_order = models.PositiveIntegerField(default=0, help_text="Order in featured partners section (0=not featured)")

    # Success story
    success_story = models.TextField(blank=True, help_text="Success story or achievement highlight")

    # Location information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Nigeria")

    # Organization metadata
    organization_type = models.CharField(max_length=100, blank=True, help_text="NGO, Government, Private, etc.")
    established_date = models.DateField(null=True, blank=True)

    # Program participation
    is_active = models.BooleanField(default=True)
    joined_program_date = models.DateTimeField(auto_now_add=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Partner Organization"
        verbose_name_plural = "Partner Organizations"
    
    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def is_approved(self):
        """Check if organization is approved"""
        return self.status == self.STATUS_APPROVED

    @property
    def is_pending(self):
        """Check if organization is pending approval"""
        return self.status == self.STATUS_PENDING

    @property
    def status_badge(self):
        """Get HTML badge for status display in admin"""
        colors = {
            self.STATUS_PENDING: 'warning',
            self.STATUS_APPROVED: 'success',
            self.STATUS_REJECTED: 'danger',
        }
        color = colors.get(self.status, 'secondary')
        return f'<span class="badge bg-{color}">{self.get_status_display()}</span>'

    @property
    def total_farmers(self):
        """Get total number of farmers associated with this partner"""
        return AkilimoParticipant.objects.filter(partner__icontains=self.name).count()
    
    @property
    def total_events(self):
        """Get total number of events organized by this partner"""
        return AkilimoParticipant.objects.filter(partner__icontains=self.name).values('event_date', 'event_venue').distinct().count()

class UserProfile(models.Model):
    """Extended user profile for partner organization users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Partner association
    partner_organization = models.ForeignKey(PartnerOrganization, on_delete=models.CASCADE, null=True, blank=True)
    partner_name = models.CharField(max_length=200, blank=True, help_text="Partner organization name from registration")
    
    # Personal information
    phone_number = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True, help_text="Job title/position in organization")
    department = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True, help_text="Profile photo for ID card")
    
    # Profile status
    is_partner_verified = models.BooleanField(default=False, help_text="Has partner organization been verified?")
    profile_completed = models.BooleanField(default=False)
    profile_completion_date = models.DateTimeField(null=True, blank=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    dashboard_preferences = models.JSONField(default=dict, help_text="User dashboard preferences")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.partner_organization or 'No Partner'}"
    
    def save(self, *args, **kwargs):
        # Check if profile is completed based on essential fields
        was_completed = self.profile_completed
        
        # Core profile completion criteria
        has_basic_info = bool(self.user.first_name and self.user.last_name and self.user.email)
        has_contact = bool(self.phone_number)
        has_position = bool(self.position)
        has_partner = bool(self.partner_organization or self.partner_name)
        
        # Profile is completed if all essential fields are filled
        self.profile_completed = has_basic_info and has_contact and has_position and has_partner
        
        # Set completion date when profile becomes completed for the first time
        if self.profile_completed and not was_completed:
            self.profile_completion_date = timezone.now()
        elif not self.profile_completed and was_completed:
            # If profile becomes incomplete, clear the completion date
            self.profile_completion_date = None
        
        super().save(*args, **kwargs)
    
    @property
    def completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 6  # Basic info (3) + contact + position + partner
        completed_fields = 0
        
        # Basic info (first name, last name, email)
        if self.user.first_name and self.user.last_name and self.user.email:
            completed_fields += 3
        
        # Contact info
        if self.phone_number:
            completed_fields += 1
            
        # Position
        if self.position:
            completed_fields += 1
            
        # Partner info
        if self.partner_organization or self.partner_name:
            completed_fields += 1
            
        return int((completed_fields / total_fields) * 100)
    
    @property
    def profile_status_text(self):
        """Get human-readable profile status"""
        if self.profile_completed:
            return "Complete"
        else:
            percentage = self.completion_percentage
            if percentage >= 80:
                return "Almost Complete"
            elif percentage >= 50:
                return "In Progress"
            else:
                return "Incomplete"
    
    @property
    def partner_status_text(self):
        """Get human-readable partner verification status"""
        if self.is_partner_verified:
            return "Verified"
        elif self.partner_organization:
            return "Pending Verification"
        else:
            return "No Partner Organization"
    
    @property
    def missing_fields(self):
        """Get list of missing required fields"""
        missing = []
        
        if not (self.user.first_name and self.user.last_name):
            missing.append("Full Name")
        if not self.user.email:
            missing.append("Email")
        if not self.phone_number:
            missing.append("Phone Number")
        if not self.position:
            missing.append("Position/Title")
        if not (self.partner_organization or self.partner_name):
            missing.append("Partner Organization")
            
        return missing
    
    @property
    def can_view_partner_data(self):
        """Check if user can view partner-specific data"""
        return self.is_partner_verified and self.partner_organization
    
    @property
    def accessible_farmers(self):
        """Get farmers accessible to this user"""
        if not self.can_view_partner_data:
            return AkilimoParticipant.objects.none()
        
        return AkilimoParticipant.objects.filter(
            partner__icontains=self.partner_organization.name
        )

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    del sender, kwargs  # Unused parameters
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    del sender, kwargs  # Unused parameters
    if hasattr(instance, 'profile'):
        instance.profile.save()

class AkilimoParticipant(models.Model):
    """Updated model based on actual EiA MELIA API data structure"""
    
    # Primary identification
    external_id = models.BigIntegerField(unique=True, help_text="ID from EiA MELIA API")
    source_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Use case information
    usecase = models.CharField(max_length=50, default="AKILIMO")
    usecase_ref_id = models.CharField(max_length=50, null=True, blank=True)
    usecase_stage = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    
    # Event information
    event_date = models.DateField(null=True, blank=True)
    event_year = models.IntegerField(null=True, blank=True)
    event_month = models.IntegerField(null=True, blank=True)
    event_type = models.CharField(max_length=100, null=True, blank=True)
    event_format = models.CharField(max_length=50, null=True, blank=True)
    event_city = models.CharField(max_length=200, null=True, blank=True)
    event_venue = models.CharField(max_length=500, null=True, blank=True)
    event_geopoint = models.CharField(max_length=100, null=True, blank=True, help_text="GPS coordinates")
    
    # Participant/Farmer details
    farmer_first_name = models.CharField(max_length=100, null=True, blank=True)
    farmer_surname = models.CharField(max_length=100, null=True, blank=True)
    farmer_gender = models.CharField(max_length=20, null=True, blank=True)
    farmer_age = models.CharField(max_length=10, null=True, blank=True)
    age_category = models.CharField(max_length=20, null=True, blank=True)
    farmer_phone_no = models.CharField(max_length=20, null=True, blank=True)
    farmer_own_phone = models.CharField(max_length=10, null=True, blank=True)
    farmer_organization = models.CharField(max_length=200, null=True, blank=True)
    farmer_position = models.CharField(max_length=100, null=True, blank=True)
    farmer_relationship = models.CharField(max_length=100, null=True, blank=True)
    participants_type = models.CharField(max_length=50, null=True, blank=True)
    
    # Geographic information
    admin_level1 = models.CharField(max_length=100, null=True, blank=True, help_text="State/Region")
    admin_level2 = models.CharField(max_length=100, null=True, blank=True, help_text="LGA/District")
    
    # Organization/Partner information
    partner = models.CharField(max_length=100, null=True, blank=True)
    org_first_name = models.CharField(max_length=100, null=True, blank=True)
    org_surname = models.CharField(max_length=100, null=True, blank=True)
    org_phone_no = models.CharField(max_length=20, null=True, blank=True)
    
    # Technical/Agricultural information
    crop = models.CharField(max_length=50, null=True, blank=True)
    thematic_area = models.TextField(null=True, blank=True)
    thematic_area_overall = models.TextField(null=True, blank=True)
    
    # Data source tracking
    data_source = models.CharField(max_length=100, null=True, blank=True)
    source_submitted_on = models.DateTimeField(null=True, blank=True)
    api_created_on = models.DateTimeField(null=True, blank=True, help_text="Created timestamp from API")
    
    # Metadata
    raw_data = models.JSONField(default=dict, help_text="Complete raw data from API")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['country', 'admin_level1']),
            models.Index(fields=['event_date']),
            models.Index(fields=['farmer_gender']),
            models.Index(fields=['partner']),
            models.Index(fields=['event_type']),
            models.Index(fields=['age_category']),
        ]
    
    def __str__(self):
        name = f"{self.farmer_first_name} {self.farmer_surname}".strip()
        return f"{name or f'Participant {self.external_id}'} - {self.admin_level1 or 'Unknown'}"
    
    @property
    def full_name(self):
        """Return farmer's full name"""
        return f"{self.farmer_first_name or ''} {self.farmer_surname or ''}".strip()
    
    @property
    def location_display(self):
        """Return formatted location"""
        parts = [self.event_city, self.admin_level2, self.admin_level1, self.country]
        return ", ".join([p for p in parts if p])
    
    @property
    def coordinates(self):
        """Extract latitude and longitude from geopoint"""
        if self.event_geopoint:
            try:
                coords = self.event_geopoint.strip().split()
                if len(coords) >= 2:
                    return {
                        'latitude': float(coords[0]),
                        'longitude': float(coords[1])
                    }
            except (ValueError, IndexError):
                pass
        return None

class DashboardMetrics(models.Model):
    """Store computed dashboard metrics"""
    metric_type = models.CharField(max_length=50)
    metric_name = models.CharField(max_length=100)
    metric_value = models.JSONField()
    
    # Time period
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    
    # Metadata
    computed_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['metric_type', 'metric_name', 'period_start', 'period_end']
        ordering = ['-computed_at']
    
    def __str__(self):
        return f"{self.metric_type} - {self.metric_name}"

class DataSyncLog(models.Model):
    """Log data synchronization activities"""
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]
    
    sync_type = models.CharField(max_length=50, default="akilimo_participants")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    records_processed = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    
    # Error details
    error_message = models.TextField(null=True, blank=True)
    error_details = models.JSONField(default=dict)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    # User who initiated the sync
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.sync_type} sync - {self.status} ({self.started_at})"
    
    def mark_completed(self, status='success', error_message=None):
        """Mark sync as completed"""
        self.completed_at = timezone.now()
        self.status = status
        if error_message:
            self.error_message = error_message
        
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = duration.total_seconds()
        
        self.save()

# Keep the old model for backwards compatibility during migration
class ParticipantRecord(models.Model):
    """Legacy model - will be migrated to AkilimoParticipant"""
    external_id = models.CharField(max_length=100, unique=True, help_text="ID from external API")
    usecase = models.CharField(max_length=50, default="akilimo")
    
    # Participant details
    gender = models.CharField(max_length=20, null=True, blank=True)
    age_group = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    lga = models.CharField(max_length=100, null=True, blank=True, help_text="Local Government Area")
    
    # Training/Event details
    event_type = models.CharField(max_length=100, null=True, blank=True)
    training_date = models.DateField(null=True, blank=True)
    facilitator = models.CharField(max_length=200, null=True, blank=True)
    
    # Cassava production details
    farm_size = models.FloatField(null=True, blank=True, help_text="Farm size in hectares")
    previous_yield = models.FloatField(null=True, blank=True, help_text="Previous yield in tons/hectare")
    expected_yield = models.FloatField(null=True, blank=True, help_text="Expected yield after recommendations")
    
    # Metadata
    raw_data = models.JSONField(default=dict, help_text="Raw data from API")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Legacy Participant {self.external_id} - {self.location}"


class MembershipPricing(models.Model):
    """Membership pricing configuration"""
    MEMBERSHIP_TYPES = [
        ('individual', 'Individual Membership'),
        ('organization', 'Partner Organization Membership'),
    ]
    
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_TYPES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in Naira")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Membership Pricing"
        verbose_name_plural = "Membership Pricing"
    
    def __str__(self):
        return f"{self.get_membership_type_display()} - NGN {self.price}"


class Membership(models.Model):
    """Membership subscription model for AKILIMO Nigeria Association"""
    MEMBERSHIP_TYPES = [
        ('individual', 'Individual Membership'),
        ('organization', 'Partner Organization Membership'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Payment'),
    ]
    
    # Membership identification
    membership_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    member = models.OneToOneField(User, on_delete=models.CASCADE, related_name='membership')
    
    # Membership details
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_TYPES, default='basic')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Subscription period
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    
    # Certificate and ID card
    certificate_generated = models.BooleanField(default=False)
    id_card_generated = models.BooleanField(default=False)
    certificate_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # QR Code for verification
    qr_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
    
    def __str__(self):
        return f"{self.member.get_full_name()} - {self.get_membership_type_display()} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Generate certificate number if not exists
        if not self.certificate_number:
            self.certificate_number = f"ANA-{timezone.now().year}-{str(self.membership_id)[:8].upper()}"
        
        # Set end date to 1 year from start date for all memberships
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=365)  # 1 year for all types
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if membership is currently active"""
        return (self.status == 'active' and 
                self.start_date <= timezone.now() <= self.end_date)
    
    @property
    def is_expired(self):
        """Check if membership has expired"""
        return timezone.now() > self.end_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining in membership"""
        if self.is_expired:
            return 0
        return (self.end_date - timezone.now()).days
    
    @property
    def verification_url(self):
        """Generate verification URL for QR code"""
        from django.urls import reverse
        return reverse('dashboard:verify_membership', kwargs={'qr_code': self.qr_code})


class Payment(models.Model):
    """Payment tracking for membership subscriptions"""
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('paystack', 'Paystack'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card Payment'),
        ('ussd', 'USSD'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    # Payment identification
    payment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='paystack')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Gateway integration
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    paystack_access_code = models.CharField(max_length=100, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Transaction details
    description = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.membership.member.get_full_name()} - ₦{self.amount} ({self.status})"
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'successful'
    
    @property
    def formatted_amount(self):
        """Return formatted amount with currency"""
        return f"₦{self.amount:,.2f}"


@receiver(post_save, sender=User)
def create_user_membership(sender, instance, created, **kwargs):
    """Create basic membership when User is created"""
    if created:
        Membership.objects.get_or_create(
            member=instance,
            defaults={
                'membership_type': 'individual',
                'status': 'pending'
            }
        )