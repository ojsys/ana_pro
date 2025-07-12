from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    name = models.CharField(max_length=200, unique=True, help_text="Organization name")
    code = models.CharField(max_length=50, unique=True, help_text="Organization code/abbreviation")
    description = models.TextField(blank=True, help_text="Organization description")
    
    # Contact information
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
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
    
    # Personal information
    phone_number = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True, help_text="Job title/position in organization")
    department = models.CharField(max_length=100, blank=True)
    
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
        # Check if profile is completed
        if (self.partner_organization and self.phone_number and 
            self.position and not self.profile_completed):
            self.profile_completed = True
            self.profile_completion_date = timezone.now()
        
        super().save(*args, **kwargs)
    
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