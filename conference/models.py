import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify


class Conference(models.Model):
    """The main conference event"""
    name = models.CharField(max_length=200, default="AKILIMO International Conference 2026")
    slug = models.SlugField(unique=True, blank=True)
    theme = models.CharField(max_length=300)
    tagline = models.CharField(max_length=300, blank=True)
    edition = models.CharField(max_length=50, blank=True, help_text="e.g., '1st', '2nd'")

    start_date = models.DateField()
    end_date = models.DateField()
    venue = models.CharField(max_length=300)
    city = models.CharField(max_length=100, default="Abuja")
    state = models.CharField(max_length=100, default="FCT")
    country = models.CharField(max_length=100, default="Nigeria")

    description = models.TextField(help_text="Conference overview paragraph")
    objectives = models.TextField(blank=True, help_text="One objective per line")
    expected_outcomes = models.TextField(blank=True, help_text="One outcome per line")
    target_audience = models.TextField(blank=True, help_text="Who should attend")
    key_focus_areas = models.TextField(blank=True, help_text="One focus area per line")

    hero_image = models.ImageField(upload_to='conference/hero/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='conference/banners/', blank=True, null=True)
    organizer_logo = models.ImageField(upload_to='conference/logos/', blank=True, null=True)

    abstract_submission_open = models.BooleanField(default=True)
    abstract_deadline = models.DateField(null=True, blank=True)
    registration_open = models.BooleanField(default=True)
    registration_deadline = models.DateField(null=True, blank=True)
    early_bird_deadline = models.DateField(null=True, blank=True)
    notification_date = models.DateField(null=True, blank=True, help_text="Date authors are notified")
    final_paper_deadline = models.DateField(null=True, blank=True)

    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    website_url = models.URLField(blank=True)

    is_active = models.BooleanField(default=True, help_text="The currently featured conference")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Conference"
        verbose_name_plural = "Conferences"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_objectives_list(self):
        return [o.strip() for o in self.objectives.split('\n') if o.strip()]

    def get_outcomes_list(self):
        return [o.strip() for o in self.expected_outcomes.split('\n') if o.strip()]

    def get_focus_areas_list(self):
        return [f.strip() for f in self.key_focus_areas.split('\n') if f.strip()]

    @property
    def days_until(self):
        delta = self.start_date - timezone.now().date()
        return max(delta.days, 0)

    @property
    def is_upcoming(self):
        return self.start_date > timezone.now().date()

    @property
    def is_ongoing(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class SubTheme(models.Model):
    """Conference sub-themes"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='sub_themes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Sub-Theme"
        verbose_name_plural = "Sub-Themes"

    def __str__(self):
        return self.title


class Speaker(models.Model):
    """Conference speakers"""
    SPEAKER_TYPE_CHOICES = [
        ('keynote', 'Keynote Speaker'),
        ('invited', 'Invited Speaker'),
        ('panelist', 'Panelist'),
        ('presenter', 'Paper Presenter'),
        ('moderator', 'Moderator'),
    ]

    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='speakers')
    full_name = models.CharField(max_length=200)
    organization = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    speaker_type = models.CharField(max_length=20, choices=SPEAKER_TYPE_CHOICES, default='invited')
    topic = models.CharField(max_length=300, blank=True)
    bio = models.TextField(help_text="100–150 word professional bio")
    photo = models.ImageField(upload_to='conference/speakers/', blank=True, null=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    is_featured = models.BooleanField(default=False, help_text="Show on landing page preview")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-speaker_type', 'order', 'full_name']
        verbose_name = "Speaker"
        verbose_name_plural = "Speakers"

    def __str__(self):
        return f"{self.full_name} — {self.get_speaker_type_display()}"


class AbstractThematicArea(models.Model):
    """Thematic areas for abstract submissions"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='thematic_areas')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Thematic Area"
        verbose_name_plural = "Thematic Areas"

    def __str__(self):
        return self.name


class AbstractSubmission(models.Model):
    """Abstract submissions from authors"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('revision_required', 'Revision Required'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    PRESENTATION_FORMAT_CHOICES = [
        ('oral', 'Oral Presentation'),
        ('poster', 'Poster Presentation'),
        ('either', 'Either'),
    ]

    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='abstracts')
    reference_number = models.CharField(max_length=20, unique=True, blank=True)

    # Author information
    author_name = models.CharField(max_length=200, verbose_name="Presenting Author Full Name")
    co_authors = models.CharField(max_length=500, blank=True, verbose_name="Co-Author(s)", help_text="Separate names with semicolons")
    institution = models.CharField(max_length=300, verbose_name="Institution / Organization")
    email = models.EmailField(verbose_name="Email Address")
    phone = models.CharField(max_length=30, blank=True)

    # Abstract content
    title = models.CharField(max_length=400, verbose_name="Abstract Title")
    thematic_area = models.ForeignKey(AbstractThematicArea, on_delete=models.SET_NULL, null=True)
    abstract_text = models.TextField(verbose_name="Abstract Body", help_text="Max 300 words. Structure: Introduction, Methodology, Results/Findings, Conclusion.")
    keywords = models.CharField(max_length=300, help_text="3–5 keywords, comma-separated")
    presentation_format = models.CharField(max_length=10, choices=PRESENTATION_FORMAT_CHOICES, default='either')
    abstract_file = models.FileField(upload_to='conference/abstracts/', blank=True, null=True, help_text="Optional: upload Word/PDF version")

    # Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewer_notes = models.TextField(blank=True, help_text="Internal reviewer comments")
    score = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    # Consent
    declaration = models.BooleanField(default=False, verbose_name="I declare this is my original work and has not been submitted elsewhere")

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = "Abstract Submission"
        verbose_name_plural = "Abstract Submissions"

    def __str__(self):
        return f"[{self.reference_number}] {self.title[:60]}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            year = timezone.now().year
            count = AbstractSubmission.objects.filter(conference=self.conference).count() + 1
            self.reference_number = f"ANC{year}-{count:04d}"
        super().save(*args, **kwargs)

    def word_count(self):
        return len(self.abstract_text.split())


class RegistrationCategory(models.Model):
    """Participant registration tiers"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='registration_categories')
    name = models.CharField(max_length=100, help_text="e.g., Researcher, Farmer, Student")
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class")
    fee = models.DecimalField(max_digits=10, decimal_places=2, help_text="Regular fee in Naira")
    early_bird_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Early bird fee (if different)")
    includes = models.TextField(blank=True, help_text="What's included — one item per line")
    max_slots = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'fee']
        verbose_name = "Registration Category"
        verbose_name_plural = "Registration Categories"

    def __str__(self):
        return f"{self.name} — ₦{self.fee:,.0f}"

    def get_includes_list(self):
        return [i.strip() for i in self.includes.split('\n') if i.strip()]

    def current_fee(self, conference):
        """Return early bird fee if within deadline, else regular fee"""
        if self.early_bird_fee and conference.early_bird_deadline:
            if timezone.now().date() <= conference.early_bird_deadline:
                return self.early_bird_fee
        return self.fee

    @property
    def slots_available(self):
        if self.max_slots is None:
            return None
        taken = self.registrations.filter(payment_status='confirmed').count()
        return max(self.max_slots - taken, 0)


class Registration(models.Model):
    """Conference participant registration"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('processing', 'Processing'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Payment Failed'),
        ('cancelled', 'Cancelled'),
        ('waived', 'Fee Waived'),
    ]

    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='registrations')
    category = models.ForeignKey(RegistrationCategory, on_delete=models.PROTECT, related_name='registrations')

    # Ticket
    ticket_id = models.CharField(max_length=20, unique=True, blank=True)

    # Participant info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    organization = models.CharField(max_length=300)
    position = models.CharField(max_length=200, blank=True)
    state_of_origin = models.CharField(max_length=100, blank=True)
    dietary_requirements = models.CharField(max_length=200, blank=True, help_text="e.g., Vegetarian, Halal, None")
    t_shirt_size = models.CharField(max_length=5, blank=True, choices=[
        ('XS','XS'),('S','S'),('M','M'),('L','L'),('XL','XL'),
        ('XXL','XXL'),('XXXL','XXXL'),('X4L','X4L'),
    ])
    abstract_reference = models.CharField(max_length=20, blank=True, help_text="If you submitted an abstract, enter your reference number")

    # Payment
    PAYMENT_METHOD_CHOICES = [
        ('paystack', 'Pay Online (Paystack)'),
        ('manual', 'Bank Transfer'),
    ]
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='paystack')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    paystack_reference = models.CharField(max_length=100, blank=True)
    paystack_transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)

    # Consent
    terms_accepted = models.BooleanField(default=False)

    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-registered_at']
        verbose_name = "Registration"
        verbose_name_plural = "Registrations"

    def __str__(self):
        return f"[{self.ticket_id}] {self.full_name} — {self.category.name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            year = timezone.now().year
            count = Registration.objects.filter(conference=self.conference).count() + 1
            self.ticket_id = f"ANC{year}-T{count:05d}"
        super().save(*args, **kwargs)


class ProgramDay(models.Model):
    """A day within the conference program"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='program_days')
    date = models.DateField()
    title = models.CharField(max_length=200, help_text="e.g., 'Day 1 — Opening & Keynotes'")
    theme = models.CharField(max_length=300, blank=True, help_text="Focus theme for the day")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'date']
        verbose_name = "Program Day"
        verbose_name_plural = "Program Days"

    def __str__(self):
        return f"{self.title} ({self.date})"


class ProgramSession(models.Model):
    """A session within a program day"""
    SESSION_TYPE_CHOICES = [
        ('opening', 'Opening Ceremony'),
        ('keynote', 'Keynote Address'),
        ('panel', 'Panel Discussion'),
        ('technical', 'Technical Session'),
        ('workshop', 'Workshop'),
        ('poster', 'Poster Session'),
        ('networking', 'Networking / Exhibition'),
        ('break', 'Break / Refreshment'),
        ('lunch', 'Lunch'),
        ('closing', 'Closing Ceremony'),
        ('cultural', 'Cultural Programme'),
        ('excursion', 'Field Excursion'),
    ]

    day = models.ForeignKey(ProgramDay, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=300)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='technical')
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=200, blank=True, help_text="Room / hall name")
    description = models.TextField(blank=True)
    speakers = models.ManyToManyField(Speaker, blank=True, related_name='sessions')
    moderator = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'start_time']
        verbose_name = "Program Session"
        verbose_name_plural = "Program Sessions"

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} — {self.title}"

    @property
    def is_break(self):
        return self.session_type in ('break', 'lunch')


class Sponsor(models.Model):
    """Conference sponsors"""
    TIER_CHOICES = [
        ('platinum', 'Platinum'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('bronze', 'Bronze'),
        ('partner', 'Supporting Partner'),
        ('media', 'Media Partner'),
    ]

    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='sponsors')
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='conference/sponsors/', blank=True, null=True)
    website_url = models.URLField(blank=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['tier', 'order']
        verbose_name = "Sponsor"
        verbose_name_plural = "Sponsors"

    def __str__(self):
        return f"{self.name} ({self.get_tier_display()})"


class KeyMessage(models.Model):
    """Key messages and talking points"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='key_messages')
    message = models.TextField()
    source = models.CharField(max_length=200, blank=True, help_text="Attribution e.g. 'Executive Director'")
    is_quote = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Key Message"
        verbose_name_plural = "Key Messages"

    def __str__(self):
        return self.message[:80]


class ContentBlock(models.Model):
    """Stores inline-editable text blocks for frontend editing."""
    key = models.CharField(max_length=200, unique=True, db_index=True)
    content = models.TextField()
    updated_by = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']
        verbose_name = "Content Block"
        verbose_name_plural = "Content Blocks"

    def __str__(self):
        return self.key
