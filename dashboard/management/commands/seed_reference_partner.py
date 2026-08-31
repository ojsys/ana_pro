"""
Create (or refresh) the "Afri Farm Sync" reference partner.

Afri Farm Sync is a real ANA partner whose page is filled in here with clearly
labelled SAMPLE content - about text, mission, areas of work, services, a gallery
and a success story - so there is one worked example of a complete partner page
to look at, and a template for briefing real partners on what to write.

The organization's real contact details are left untouched. Everything written
here is placeholder copy and says so; replace it with the partner's own words
before treating the page as published.

  python manage.py seed_reference_partner            # create / refresh
  python manage.py seed_reference_partner --with-admin   # also make a demo login
  python manage.py seed_reference_partner --remove       # delete it again

Note: the "Reach in Nigeria" panel on a partner page is generated from synced
AKILIMO participant records, not from anything entered by hand. It stays empty
for AfriFarm Sync because inventing participant rows would inflate the public
analytics totals with farmers who do not exist.

NOTE ON ENCODING
----------------
All seeded text here is deliberately plain ASCII. The production MySQL database
still stores several columns in a pre-utf8mb4 charset, which rejects characters
like an em dash or an arrow with:

    DataError (1366, "Incorrect string value ...")

Run ``manage.py fix_mysql_charset --apply`` to convert the database to utf8mb4;
until that is done, any partner typing a curly quote or an accented character
into the Manage form will hit the same error.
"""
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from dashboard.models import (
    ANANigeriaPartner, PartnerGalleryImage, PartnerOrganization,
    PartnerService, UserProfile,
)

# The existing ANA partner record this content is attached to.
NAME = 'Afri Farm Sync'
SLUG = 'afri-farm-sync'

ABOUT = (
    "SAMPLE CONTENT - this page is filled in as a worked example of a complete partner "
    "profile. Afri Farm Sync has not written any of the text below; it is placeholder copy "
    "showing what belongs in each section.\n\n"
    "This first section is where a partner introduces itself: who it is, where it works, and "
    "what it does for smallholder farmers. Two or three short paragraphs work best. Partners "
    "write this themselves from Manage -> About.\n\n"
    "For example: \"We work with cassava-growing households across the South West and North "
    "Central, pairing agronomic advice with the logistics that get harvested roots to a buyer "
    "before they spoil. Our field officers use the AKILIMO advisory to build fertiliser and "
    "planting plans with each farmer group at the start of every season.\""
)

MISSION = (
    "Sample mission statement - one or two sentences on what the organization is for. "
    "For example: \"To put site-specific agronomic advice, and a reliable route to market, "
    "within reach of every smallholder cassava household in Nigeria.\""
)

AREAS = "\n".join([
    "Cassava agronomy",
    "Site-specific fertiliser advice",
    "Farmer group training",
    "Harvest scheduling",
    "Market linkage",
    "Women and youth inclusion",
])

SUCCESS_STORY = (
    "SAMPLE CONTENT - this is where a partner tells one story well.\n\n"
    "An example of the shape it should take: \"In the 2025 season we ran AKILIMO fertiliser "
    "planning with 42 farmer groups in Oyo and Benue. Groups that followed the site-specific "
    "plan reported better root yields than their own previous season, and scheduled "
    "harvesting cut the volume lost to delayed collection.\"\n\n"
    "A good success story names the place, the season, what was actually done, and what "
    "changed - and it is honest about which figures are estimates."
)

SERVICES = [
    ('Agronomic Advisory',
     'Season-long, site-specific fertiliser and planting guidance for cassava, built with '
     'each farmer group using the AKILIMO advisory tool.',
     'bi-clipboard2-data'),
    ('Farmer Group Training',
     'Hands-on training days covering land preparation, spacing, weed control and the '
     'timing decisions that most affect root yield.',
     'bi-people'),
    ('Demonstration Plots',
     'Managed demonstration fields where AKILIMO recommendations run side by side with '
     'usual farmer practice, so groups can judge the difference themselves.',
     'bi-flower1'),
    ('Input Access',
     'Aggregated ordering of fertiliser and improved planting material, so smallholders buy '
     'at a price normally available only to large farms.',
     'bi-basket'),
    ('Harvest Scheduling',
     'Coordinating harvest dates across a cluster of farms so roots reach a processor while '
     'still fresh, cutting post-harvest loss.',
     'bi-calendar-check'),
    ('Market Linkage',
     'Standing offtake arrangements with processors and aggregators, negotiated on behalf of '
     'the farmer groups.',
     'bi-shop'),
]

GALLERY = [
    ('Fertiliser planning session', 'Ibadan, Oyo State', (46, 125, 50),
     'Field officers building a site-specific fertiliser plan with a farmer group at the start of the season.'),
    ('Demonstration plot at 8 weeks', 'Makurdi, Benue State', (27, 94, 32),
     'AKILIMO recommendation on the left, usual farmer practice on the right.'),
    ('Farmer group training day', 'Iseyin, Oyo State', (76, 175, 80),
     'Training on spacing and weed control ahead of planting.'),
    ('Harvest and collection', 'Gboko, Benue State', (56, 142, 60),
     'Scheduled harvesting so roots reach the processor while still fresh.'),
    ('Women farmers cooperative', 'Ogbomosho, Oyo State', (102, 187, 106),
     'A cooperative of 60 women growers planning the coming season together.'),
    ('Input distribution day', 'Otukpo, Benue State', (34, 110, 40),
     'Aggregated fertiliser order being shared out across member farms.'),
]


def placeholder_image(text, subtitle, size, rgb, show_text=True):
    """
    Generate a captioned placeholder so the gallery renders without shipping
    binary assets into the repository.

    ``show_text=False`` produces the pattern only - used for the cover banner,
    where the page draws its own heading over the image and baked-in text would
    ghost through the gradient overlay.
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new('RGB', size, rgb)
    draw = ImageDraw.Draw(img)
    w, h = size

    # Soft diagonal banding so the tiles are not flat blocks of colour.
    lighter = tuple(min(255, c + 18) for c in rgb)
    for offset in range(-h, w, 90):
        draw.polygon(
            [(offset, h), (offset + 45, h), (offset + 45 + h, 0), (offset + h, 0)],
            fill=lighter,
        )

    if not show_text:
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=88)
        return ContentFile(buf.getvalue())

    # Size the type to the image so it stays legible once the tile is scaled down.
    def font(px):
        try:
            return ImageFont.load_default(size=px)
        except TypeError:      # Pillow < 10.1 has no size argument
            return ImageFont.load_default()

    title_font = font(max(22, int(h * 0.075)))
    sub_font = font(max(16, int(h * 0.048)))
    note_font = font(max(12, int(h * 0.032)))

    def centered(msg, y, fill, f):
        box = draw.textbbox((0, 0), msg, font=f)
        draw.text(((w - (box[2] - box[0])) / 2, y), msg, fill=fill, font=f)

    centered(text, h * 0.38, (255, 255, 255), title_font)
    centered(subtitle, h * 0.52, (226, 242, 226), sub_font)
    centered('DEMO IMAGE', h * 0.84, (210, 232, 210), note_font)

    buf = BytesIO()
    img.save(buf, format='JPEG', quality=88)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = 'Create or refresh the fictional "AfriFarm Sync" reference partner'

    def add_arguments(self, parser):
        parser.add_argument('--remove', action='store_true',
                            help='Clear the sample content (the partner record itself is kept)')
        parser.add_argument('--with-admin', action='store_true',
                            help='Also create a demo partner-admin login for it')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['remove']:
            return self._remove()

        org = PartnerOrganization.objects.filter(slug=SLUG).first()
        if not org:
            self.stderr.write(f'No partner organization with slug "{SLUG}" - run link_ana_partners first.')
            return
        created = False

        org.description = org.description or 'Sample partner profile used as a reference example.'
        org.about = ABOUT
        org.mission = MISSION
        org.areas_of_work = AREAS
        org.success_story = SUCCESS_STORY
        org.organization_type = 'Digital Advisory'
        # Contact details belong to a real organization - never overwritten here.
        # Where the organization record has none, the partner's own details are
        # copied across from its ANA Nigeria Partner row: real data already held
        # in this system, not anything invented.
        ana_row = ANANigeriaPartner.objects.filter(organization__iexact=NAME).first()
        if ana_row:
            org.contact_person = org.contact_person or ana_row.contact_person or ''
            org.email = org.email or ana_row.email or ''
            org.phone_number = org.phone_number or (ana_row.phone_number or '')[:20]

        org.country = org.country or 'Nigeria'
        if not org.city:
            org.city = 'Ibadan'
        if not org.state:
            org.state = 'Oyo'
        if not org.address:
            org.address = 'Sample address - replace with the partner\'s own'
        org.status = PartnerOrganization.STATUS_APPROVED
        org.is_active = True
        org.has_public_page = True
        org.is_featured = True
        org.feature_order = 1

        if not org.logo:
            org.logo.save('afrifarm-sync-logo.jpg',
                          placeholder_image('', '', (400, 400), (46, 125, 50), show_text=False),
                          save=False)
        if not org.cover_image:
            org.cover_image.save('afrifarm-sync-cover.jpg',
                                 placeholder_image('', '', (1600, 500), (27, 94, 32),
                                                   show_text=False),
                                 save=False)
        org.save()
        self.stdout.write(self.style.SUCCESS(
            f'Filled in sample content for: {org.name}  (/partners/{org.slug}/)'
        ))

        # Services
        org.services.all().delete()
        for i, (title, desc, icon) in enumerate(SERVICES, 1):
            PartnerService.objects.create(
                partner=org, title=title, description=desc, icon=icon, order=i, is_active=True,
            )
        self.stdout.write(f'  services: {len(SERVICES)}')

        # Gallery
        for image in org.gallery_images.all():
            image.image.delete(save=False)
            image.delete()
        for i, (caption, location, rgb, desc) in enumerate(GALLERY, 1):
            entry = PartnerGalleryImage(
                partner=org, caption=caption, description=desc,
                location=location, order=i, is_active=True,
            )
            entry.image.save(
                f'afrifarm-sync-{i}.jpg',
                placeholder_image(caption, location, (1200, 800), rgb),
                save=False,
            )
            entry.save()
        self.stdout.write(f'  gallery photos: {len(GALLERY)}')

        # ANA listing, so the card shows on /partners/
        ana = ANANigeriaPartner.objects.filter(organization__iexact=NAME).first()
        if ana:
            ana.partner_organization = org
            ana.is_active = True
            ana.save(update_fields=['partner_organization', 'is_active'])
            self.stdout.write(f'  ANA listing: {ana.organization} ({ana.primary_category})')
        else:
            self.stdout.write(self.style.WARNING(
                f'  no ANA Nigeria Partner row named "{NAME}" - the card will not '
                f'appear in the ANA grid, only in the Partner Directory.'
            ))

        if options['with_admin']:
            self._demo_admin(org)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. View it at /partners/{org.slug}/'
            f'\nNote: the "Reach in Nigeria" panel stays empty - it is generated from synced'
            f'\nAKILIMO participant records, and inventing those would inflate the public'
            f'\nanalytics totals with farmers who do not exist.'
        ))

    def _demo_admin(self, org):
        username = 'afrifarm.demo'
        password = 'AfriFarmDemo!2026'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': 'demo@afrifarmsync.example',
                      'first_name': 'Amara', 'last_name': 'Okafor'},
        )
        user.set_password(password)
        user.is_active = True
        user.save()
        UserProfile.objects.update_or_create(
            user=user,
            defaults={'partner_organization': org, 'is_partner_admin': True,
                      'partner_name': org.name, 'position': 'Programme Manager (demo)'},
        )
        self.stdout.write(self.style.WARNING(
            f'\n  demo partner-admin login'
            f'\n    username : {username}'
            f'\n    email    : demo@afrifarmsync.example'
            f'\n    password : {password}'
            f'\n    manage   : /partners/{org.slug}/manage/'
            f'\n  Change or remove this account before going live.'
        ))

    def _remove(self):
        org = PartnerOrganization.objects.filter(slug=SLUG).first()
        if not org:
            self.stdout.write(self.style.WARNING(f'{NAME} not found - nothing to remove.'))
            return

        for image in org.gallery_images.all():
            image.image.delete(save=False)
        if org.logo:
            org.logo.delete(save=False)
        if org.cover_image:
            org.cover_image.delete(save=False)

        # This is a real partner: strip the sample content, keep the organization.
        for image in org.gallery_images.all():
            image.delete()
        org.services.all().delete()
        org.about = ''
        org.mission = ''
        org.areas_of_work = ''
        org.success_story = ''
        org.logo = None
        org.cover_image = None
        org.save()

        User.objects.filter(username='afrifarm.demo').delete()
        self.stdout.write(self.style.SUCCESS(
            f'Cleared the sample content from {org.name}. The partner record itself was kept.'
        ))
