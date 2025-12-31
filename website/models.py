from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from dashboard.models import PartnerOrganization


class Page(models.Model):
    """Static pages like About, Services, etc."""
    title = models.CharField(max_length=200, help_text="Page title")
    slug = models.SlugField(unique=True, help_text="URL slug (auto-generated from title)")
    content = models.TextField(help_text="Main page content")
    meta_description = models.CharField(
        max_length=160, 
        blank=True,
        help_text="SEO meta description (max 160 characters)"
    )
    meta_keywords = models.CharField(
        max_length=200, 
        blank=True,
        help_text="SEO keywords, comma separated"
    )
    featured_image = models.ImageField(
        upload_to='pages/', 
        blank=True, 
        null=True,
        help_text="Featured image for the page"
    )
    is_published = models.BooleanField(default=True, help_text="Is this page published?")
    show_in_menu = models.BooleanField(default=False, help_text="Show in main navigation?")
    menu_order = models.IntegerField(default=0, help_text="Order in menu (0 = first)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['menu_order', 'title']
        verbose_name = "Page"
        verbose_name_plural = "Pages"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('website:page', kwargs={'slug': self.slug})


class NewsArticle(models.Model):
    """News articles and blog posts"""
    CATEGORY_CHOICES = [
        ('news', 'News'),
        ('events', 'Events'),
        ('success_stories', 'Success Stories'),
        ('announcements', 'Announcements'),
        ('research', 'Research'),
        ('training', 'Training'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    excerpt = models.TextField(max_length=300, help_text="Brief excerpt for listings")
    content = RichTextField(help_text="Full article content with rich text formatting")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='news')
    featured_image = models.ImageField(upload_to='news/', blank=True, null=True)
    
    # Publishing
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    published_date = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Feature on homepage?")
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    
    # Engagement
    views_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_date']
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('website:news_detail', kwargs={'slug': self.slug})


class HomePageSection(models.Model):
    """Configurable homepage sections"""
    SECTION_TYPES = [
        ('hero', 'Hero Banner'),
        ('about', 'About Section'),
        ('services', 'Services'),
        ('statistics', 'Statistics'),
        ('partners', 'Partners'),
        ('testimonials', 'Testimonials'),
        ('news', 'Latest News'),
        ('contact', 'Contact Info'),
        ('custom', 'Custom Content'),
    ]
    
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES)
    title = models.CharField(max_length=200, blank=True)
    subtitle = models.CharField(max_length=300, blank=True)
    content = models.TextField(blank=True, help_text="Section content")
    image = models.ImageField(upload_to='homepage/', blank=True, null=True)
    button_text = models.CharField(max_length=50, blank=True)
    button_url = models.URLField(blank=True)
    background_color = models.CharField(max_length=7, default="#ffffff", help_text="Hex color code")
    
    # Display
    order = models.IntegerField(default=0, help_text="Display order (0 = first)")
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Homepage Section"
        verbose_name_plural = "Homepage Sections"
    
    def __str__(self):
        return f"{self.get_section_type_display()} - {self.title}"


class TeamMember(models.Model):
    """Team and leadership profiles"""
    CATEGORY_CHOICES = [
        ('bot', 'Board of Trustees'),
        ('exco', 'Executive Committee'),
        ('staff', 'Staff'),
        ('advisory', 'Advisory Board'),
        ('regional', 'Regional Coordinators'),
    ]
    
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='staff',
        help_text="Team category for grouping"
    )
    bio = models.TextField(help_text="Biography and background")
    photo = models.ImageField(upload_to='team/', blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Social links
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    
    # Display
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', 'name']
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"
    
    def __str__(self):
        return f"{self.name} - {self.position} ({self.get_category_display()})"


class PartnerShowcase(models.Model):
    """Partner organization highlights for website"""
    partner = models.ForeignKey(
        PartnerOrganization, 
        on_delete=models.CASCADE,
        help_text="Link to partner organization"
    )
    description = models.TextField(
        help_text="Description of partnership and achievements"
    )
    logo = models.ImageField(
        upload_to='partners/', 
        blank=True, 
        null=True,
        help_text="Partner organization logo"
    )
    website_url = models.URLField(blank=True, help_text="Partner website")
    success_story = models.TextField(
        blank=True,
        help_text="Success story or case study"
    )
    
    # Display settings
    is_featured = models.BooleanField(
        default=False, 
        help_text="Feature on homepage?"
    )
    display_order = models.IntegerField(
        default=0, 
        help_text="Display order (0 = first)"
    )
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'partner__name']
        verbose_name = "Partner Showcase"
        verbose_name_plural = "Partner Showcases"
    
    def __str__(self):
        return f"{self.partner.name} - Showcase"


class Testimonial(models.Model):
    """Success stories and testimonials"""
    name = models.CharField(max_length=100, help_text="Person's name")
    position = models.CharField(max_length=100, blank=True, help_text="Job title or role")
    organization = models.CharField(max_length=100, blank=True)
    content = models.TextField(help_text="Testimonial content")
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    
    # Classification
    testimonial_type = models.CharField(
        max_length=20,
        choices=[
            ('farmer', 'Farmer'),
            ('partner', 'Partner Organization'),
            ('staff', 'Staff Member'),
            ('researcher', 'Researcher'),
            ('other', 'Other'),
        ],
        default='farmer'
    )
    
    # Display
    is_featured = models.BooleanField(default=False, help_text="Feature on homepage?")
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)], 
        default=5,
        help_text="Rating out of 5 stars"
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
    
    def __str__(self):
        return f"{self.name} - {self.organization}"


class FAQ(models.Model):
    """Frequently Asked Questions"""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('programs', 'Programs & Services'),
        ('partnerships', 'Partnerships'),
        ('technical', 'Technical Support'),
        ('registration', 'Registration'),
        ('dashboard', 'Dashboard'),
    ]
    
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    
    # Display
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Engagement
    helpful_count = models.PositiveIntegerField(default=0, help_text="How many found this helpful")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return f"{self.question[:50]}..."


class ContactInfo(models.Model):
    """Contact details and office locations"""
    office_name = models.CharField(max_length=100, help_text="Office or location name")
    address = models.TextField(help_text="Full address")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="Nigeria")
    
    # Contact details
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    fax = models.CharField(max_length=20, blank=True)
    
    # Hours
    hours = models.TextField(
        blank=True,
        help_text="Operating hours (e.g., Mon-Fri: 9:00 AM - 5:00 PM)"
    )
    
    # Map integration
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=8, 
        blank=True, 
        null=True,
        help_text="Latitude for map display"
    )
    longitude = models.DecimalField(
        max_digits=11, 
        decimal_places=8, 
        blank=True, 
        null=True,
        help_text="Longitude for map display"
    )
    
    # Display
    is_primary = models.BooleanField(default=False, help_text="Primary contact location?")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'office_name']
        verbose_name = "Contact Information"
        verbose_name_plural = "Contact Information"
    
    def __str__(self):
        return f"{self.office_name} - {self.city}"


class Statistic(models.Model):
    """Site statistics for homepage display"""
    label = models.CharField(max_length=100, help_text="Statistic label (e.g., 'Active Farmers')")
    value = models.CharField(max_length=20, help_text="Statistic value (e.g., '500+', '25')")
    icon = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Bootstrap icon class (e.g., 'bi-people', 'bi-geo-alt')"
    )
    description = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Optional description or additional context"
    )
    
    # Display
    order = models.IntegerField(default=0, help_text="Display order (0 = first)")
    is_active = models.BooleanField(default=True)
    show_on_homepage = models.BooleanField(default=True, help_text="Display on homepage?")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'label']
        verbose_name = "Statistic"
        verbose_name_plural = "Statistics"
    
    def __str__(self):
        return f"{self.value} {self.label}"


class SiteSettings(models.Model):
    """Global site settings"""
    site_title = models.CharField(max_length=100, default="AKILIMO Nigeria Association")
    site_tagline = models.CharField(
        max_length=200, 
        default="Advancing Cassava Production Through Innovation"
    )
    site_description = models.TextField(
        default="AKILIMO Nigeria Association promotes sustainable cassava production and agricultural innovation across Nigeria."
    )

    # Payment Settings
    bypass_payment_requirements = models.BooleanField(
        default=True,
        verbose_name="Bypass Payment Requirements",
        help_text="When enabled, users can register and access the dashboard without payment. Disable to enforce payment requirements."
    )

    # Contact
    primary_email = models.EmailField(blank=True)
    primary_phone = models.CharField(max_length=20, blank=True)
    
    # Social media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    
    # SEO
    google_analytics_id = models.CharField(max_length=20, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    
    # Images
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.site_title
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            self.pk = SiteSettings.objects.first().pk
        super().save(*args, **kwargs)


class HeroSlide(models.Model):
    """Hero slider slides for homepage"""
    title = models.CharField(max_length=200, help_text="Main slide title")
    subtitle = models.CharField(max_length=300, blank=True, help_text="Slide subtitle")
    description = models.TextField(blank=True, help_text="Slide description text")
    background_image = models.ImageField(
        upload_to='hero_slides/',
        blank=True,
        null=True,
        help_text="Background image for the slide"
    )
    background_color = models.CharField(
        max_length=50,
        default="linear-gradient(135deg, #1C4523 0%, #4CAF50 100%)",
        help_text="CSS background color or gradient"
    )

    # Buttons
    button_1_text = models.CharField(max_length=50, blank=True, help_text="First button text")
    button_1_url = models.CharField(max_length=200, blank=True, help_text="First button URL")
    button_1_icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class")

    button_2_text = models.CharField(max_length=50, blank=True, help_text="Second button text")
    button_2_url = models.CharField(max_length=200, blank=True, help_text="Second button URL")
    button_2_icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class")

    # Display
    order = models.IntegerField(default=0, help_text="Slide order (0 = first)")
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Hero Slide"
        verbose_name_plural = "Hero Slides"

    def __str__(self):
        return self.title


class MissionVision(models.Model):
    """Mission and Vision statements"""
    mission_title = models.CharField(max_length=100, default="Our Mission")
    mission_content = models.TextField(
        help_text="Mission statement content",
        default="To promote and scale the use of AKILIMO's evidence-based agronomic advisory services across Nigeria."
    )
    mission_icon = models.CharField(
        max_length=50,
        default="bi-crosshair",
        help_text="Bootstrap icon class for mission"
    )

    vision_title = models.CharField(max_length=100, default="Our Vision")
    vision_content = models.TextField(
        help_text="Vision statement content",
        default="A thriving agricultural sector in Nigeria where every smallholder farmer has access to data-driven decision support tools."
    )
    vision_icon = models.CharField(
        max_length=50,
        default="bi-lightbulb",
        help_text="Bootstrap icon class for vision"
    )

    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mission & Vision"
        verbose_name_plural = "Mission & Vision"

    def __str__(self):
        return "Mission & Vision Statements"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and MissionVision.objects.exists():
            self.pk = MissionVision.objects.first().pk
        super().save(*args, **kwargs)


class OperationalPillar(models.Model):
    """AKILIMO's Four Operational Pillars"""
    title = models.CharField(max_length=100, help_text="Pillar title")
    description = models.TextField(help_text="Pillar description")
    icon = models.CharField(
        max_length=50,
        help_text="Bootstrap icon class (e.g., 'bi-clipboard-data')"
    )

    # Display
    order = models.IntegerField(default=0, help_text="Display order (0 = first)")
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Operational Pillar"
        verbose_name_plural = "Operational Pillars"

    def __str__(self):
        return self.title


class PlatformFeature(models.Model):
    """AKILIMO Platform Features"""
    title = models.CharField(max_length=100, help_text="Feature title")
    description = models.TextField(help_text="Feature description")
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Bootstrap icon class (e.g., 'bi-check-circle-fill')"
    )

    # Display
    order = models.IntegerField(default=0, help_text="Display order (0 = first)")
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Platform Feature"
        verbose_name_plural = "Platform Features"

    def __str__(self):
        return self.title


class TrainingProgram(models.Model):
    """Training Programs and Capacity Building"""
    title = models.CharField(max_length=100, help_text="Program title")
    description = models.TextField(help_text="Program description")
    icon = models.CharField(
        max_length=50,
        help_text="Bootstrap icon class (e.g., 'bi-people-fill')"
    )

    # Display
    order = models.IntegerField(default=0, help_text="Display order (0 = first)")
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Training Program"
        verbose_name_plural = "Training Programs"

    def __str__(self):
        return self.title


class SupportTeam(models.Model):
    """AKILIMO Support Teams (Content, Tech, Business)"""
    name = models.CharField(max_length=100, help_text="Team name (e.g., 'CONTENT Team')")
    description = models.TextField(blank=True, help_text="Brief team description")
    icon = models.CharField(
        max_length=50,
        help_text="Bootstrap icon class (e.g., 'bi-file-text')"
    )
    responsibilities = models.TextField(
        help_text="Team responsibilities (one per line)",
        blank=True
    )

    # Display
    order = models.IntegerField(default=0, help_text="Display order (0 = first)")
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Support Team"
        verbose_name_plural = "Support Teams"

    def __str__(self):
        return self.name

    def get_responsibilities_list(self):
        """Return responsibilities as a list"""
        if self.responsibilities:
            return [r.strip() for r in self.responsibilities.split('\n') if r.strip()]
        return []


class CallToAction(models.Model):
    """Call to Action sections"""
    PLACEMENT_CHOICES = [
        ('home', 'Home Page'),
        ('about', 'About Page'),
        ('programs', 'Programs Page'),
        ('news', 'News Detail'),
        ('page', 'Page Detail'),
        ('partners', 'Partners Page'),
        ('all', 'All Pages'),
    ]

    title = models.CharField(max_length=200, help_text="CTA heading")
    description = models.TextField(help_text="CTA description text")

    button_1_text = models.CharField(max_length=50, help_text="First button text")
    button_1_url = models.CharField(max_length=200, help_text="First button URL")
    button_1_icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class")

    button_2_text = models.CharField(max_length=50, blank=True, help_text="Second button text")
    button_2_url = models.CharField(max_length=200, blank=True, help_text="Second button URL")
    button_2_icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class")

    background_style = models.CharField(
        max_length=200,
        default="background: linear-gradient(135deg, var(--primary-accent), var(--dark-accent));",
        help_text="CSS background style"
    )

    placement = models.CharField(
        max_length=20,
        choices=PLACEMENT_CHOICES,
        default='all',
        help_text="Where to display this CTA"
    )

    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Call to Action"
        verbose_name_plural = "Call to Actions"

    def __str__(self):
        return f"{self.title} ({self.get_placement_display()})"


class PageContent(models.Model):
    """Editable page content sections"""
    PAGE_CHOICES = [
        ('home_hero', 'Home - Hero Section'),
        ('home_about', 'Home - About Section'),
        ('about_hero', 'About - Hero Section'),
        ('about_highlights', 'About - Key Highlights'),
        ('about_org_structure', 'About - Organizational Structure'),
        ('programs_hero', 'Programs - Hero Section'),
        ('programs_platform', 'Programs - Platform Description'),
        ('partners_hero', 'Partners - Hero Section'),
    ]

    page_section = models.CharField(
        max_length=50,
        choices=PAGE_CHOICES,
        unique=True,
        help_text="Page section identifier"
    )
    title = models.CharField(max_length=200, blank=True, help_text="Section title")
    subtitle = models.CharField(max_length=300, blank=True, help_text="Section subtitle")
    content = models.TextField(blank=True, help_text="Section content")

    # Additional fields for flexibility
    badge_text = models.CharField(max_length=100, blank=True, help_text="Badge or label text")
    highlight_1 = models.CharField(max_length=100, blank=True)
    highlight_2 = models.CharField(max_length=100, blank=True)
    highlight_3 = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Page Content"
        verbose_name_plural = "Page Contents"

    def __str__(self):
        return f"{self.get_page_section_display()}"
