"""
Management command to create and populate the AKILIMO-Lagos-2026 conference.
Run on the server: python manage.py setup_conference --settings=akilimo_nigeria.settings.production
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime


class Command(BaseCommand):
    help = 'Creates and populates the AKILIMO International Conference 2026 (AKILIMO-Lagos-2026)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing conference instead of skipping if it already exists',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be created without saving anything',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        update = options['update']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — nothing will be saved.\n'))

        # ── 1. Conference ─────────────────────────────────────────────────────
        from conference.models import (
            Conference, SubTheme, AbstractThematicArea,
            RegistrationCategory, KeyMessage
        )

        conf_data = dict(
            name='1st AKILIMO International Conference (AKILIMO-Lagos-2026)',
            slug='akilimo-lagos-2026',
            theme='Advancing Cassava, Rice and Maize Agronomy Through Digital Innovation',
            tagline='Science · Innovation · Impact',
            edition='1st',
            start_date=datetime.date(2026, 10, 27),
            end_date=datetime.date(2026, 10, 29),
            venue='Radisson Blu Hotel',
            city='Lagos',
            state='Lagos',
            country='Nigeria',
            description=(
                'AKILIMO Nigeria Association (ANA) was established by a network of dedicated partners '
                'when the Africa Cassava Agronomy Initiative (ACAI) project concluded. ACAI collaborated '
                'with research institutions, development organizations, government agencies, and the private '
                'sector to co-develop agronomic solutions for smallholder farmers. Building on this legacy, '
                'ANA ensures the sustained use and scaling of the AKILIMO decision-support tools, empowering '
                'farmers and value chain actors with data-driven advice.\n\n'
                'AKILIMO-Lagos-2026 will bring together leading scientists, academicians, industry practitioners, '
                'farmers, agro-processors and other experts along the various food value chains. The conference '
                'presents a unique opportunity for participants to explore speaking opportunities, present ideas, '
                'innovations, products and services, and create significant connections and collaborations.'
            ),
            objectives=(
                'Showcase the latest research and innovations in cassava, rice and maize agronomy\n'
                'Demonstrate the impact and reach of AKILIMO digital decision-support tools\n'
                'Strengthen partnerships across research institutions, government, and the private sector\n'
                'Explore pathways to scaling digital advisory tools for smallholder farmers\n'
                'Facilitate knowledge exchange between scientists, practitioners, and farmers\n'
                'Identify opportunities to improve access to markets, inputs, and credit along food value chains'
            ),
            expected_outcomes=(
                'New research collaborations and partnership agreements formed\n'
                'Published book of abstracts and conference proceedings\n'
                'Concrete recommendations for scaling AKILIMO tools nationally\n'
                'Strengthened ANA membership network\n'
                'Documented innovations and lessons shared across the value chain'
            ),
            target_audience=(
                'Researchers and scientists in cassava, rice and maize agronomy; ANA member organizations; '
                'agribusinesses and agro-processors; government agencies and policy makers; NGOs and development '
                'partners; extension agents; digital agriculture practitioners; students and early-career professionals'
            ),
            key_focus_areas=(
                'Cassava, rice and maize agronomy\n'
                'Digital advisory and decision-support tools\n'
                'Farm productivity and yield improvement\n'
                'Market access and value chain development\n'
                'Input supply and credit access for smallholders\n'
                'AKILIMO tool adoption and scaling\n'
                'Data-driven extension services'
            ),
            abstract_submission_open=True,
            abstract_deadline=datetime.date(2026, 5, 31),
            notification_date=datetime.date(2026, 6, 30),
            final_paper_deadline=datetime.date(2026, 7, 31),
            registration_open=True,
            early_bird_deadline=datetime.date(2026, 4, 30),
            contact_email='technicalpaper@akilimonigeria.org',
            website_url='https://www.akilimonigeria.org',
            is_active=True,
        )

        existing = Conference.objects.filter(slug='akilimo-lagos-2026').first()
        if existing and not update:
            self.stdout.write(self.style.WARNING(
                f'Conference already exists (id={existing.pk}). Use --update to overwrite.\n'
            ))
            conference = existing
        elif existing and update:
            if not dry_run:
                for k, v in conf_data.items():
                    setattr(existing, k, v)
                existing.save()
            conference = existing
            self.stdout.write(self.style.SUCCESS('✔ Conference updated'))
        else:
            if not dry_run:
                conference = Conference.objects.create(**conf_data)
            else:
                conference = type('obj', (object,), {'pk': 'DRY-RUN', **conf_data})()
            self.stdout.write(self.style.SUCCESS(f'✔ Conference created (id={conference.pk})'))

        # ── 2. Sub-Themes ─────────────────────────────────────────────────────
        sub_themes = [
            {
                'title': 'Cassava Agronomy and Value Chain Innovation',
                'description': 'Research and practices in cassava production, processing, market linkage, and value addition.',
                'icon': 'bi-diagram-3',
                'order': 1,
            },
            {
                'title': 'Rice and Maize Agronomy in the Digital Age',
                'description': 'Innovations in rice and maize production systems supported by data-driven agronomic tools.',
                'icon': 'bi-bar-chart-steps',
                'order': 2,
            },
            {
                'title': 'Digital Advisory and Decision-Support Tools',
                'description': 'Development, deployment, and impact of tools like AKILIMO for guiding farmer decisions.',
                'icon': 'bi-cpu',
                'order': 3,
            },
            {
                'title': 'Scaling Agricultural Technologies for Smallholders',
                'description': 'Strategies for expanding reach of proven technologies to millions of smallholder farmers.',
                'icon': 'bi-arrow-up-right-circle',
                'order': 4,
            },
            {
                'title': 'Markets, Inputs and Credit Access',
                'description': 'Connecting farmers to affordable inputs, credit facilities, and reliable market outlets.',
                'icon': 'bi-shop',
                'order': 5,
            },
            {
                'title': 'Partnerships and Institutional Sustainability',
                'description': 'Building lasting networks and institutional arrangements that sustain agricultural innovation.',
                'icon': 'bi-people',
                'order': 6,
            },
        ]

        themes_created = 0
        if not dry_run:
            SubTheme.objects.filter(conference=conference).delete()
            for t in sub_themes:
                SubTheme.objects.create(conference=conference, **t)
                themes_created += 1
        else:
            themes_created = len(sub_themes)
        self.stdout.write(self.style.SUCCESS(f'✔ {themes_created} sub-themes created'))

        # ── 3. Abstract Thematic Areas ────────────────────────────────────────
        thematic_areas = [
            {'name': 'Cassava Agronomy and Crop Management', 'order': 1},
            {'name': 'Rice Production Systems and Technology', 'order': 2},
            {'name': 'Maize Agronomy and Value Chain', 'order': 3},
            {'name': 'Digital Tools and Decision-Support Systems', 'order': 4},
            {'name': 'Soil Health, Fertility and Climate Adaptation', 'order': 5},
            {'name': 'Post-Harvest Management and Processing', 'order': 6},
            {'name': 'Market Access, Inputs and Agricultural Finance', 'order': 7},
            {'name': 'Extension Services and Capacity Building', 'order': 8},
            {'name': 'Gender, Youth and Inclusion in Agriculture', 'order': 9},
            {'name': 'Policy, Partnerships and Institutional Development', 'order': 10},
        ]

        areas_created = 0
        if not dry_run:
            AbstractThematicArea.objects.filter(conference=conference).delete()
            for a in thematic_areas:
                AbstractThematicArea.objects.create(conference=conference, **a)
                areas_created += 1
        else:
            areas_created = len(thematic_areas)
        self.stdout.write(self.style.SUCCESS(f'✔ {areas_created} thematic areas created'))

        # ── 4. Registration Categories ────────────────────────────────────────
        categories = [
            {
                'name': 'Student',
                'description': 'For registered students (valid student ID required).',
                'icon': 'bi-mortarboard',
                'fee': 5000,
                'early_bird_fee': None,   # No early bird for students
                'includes': (
                    'Full 3-day conference access\n'
                    'Conference bag and materials\n'
                    'Morning tea/coffee and lunch daily\n'
                    'Book of abstracts\n'
                    'Certificate of participation\n'
                    'Access to all plenary and technical sessions'
                ),
                'order': 1,
            },
            {
                'name': 'Regular',
                'description': 'Standard registration. Early bird rate available until 30th April 2026.',
                'icon': 'bi-person-badge',
                'fee': 15000,
                'early_bird_fee': 10000,
                'includes': (
                    'Full 3-day conference access\n'
                    'Conference bag and materials\n'
                    'Morning tea/coffee and lunch daily\n'
                    'Book of abstracts\n'
                    'Certificate of participation\n'
                    'Access to all plenary and technical sessions'
                ),
                'order': 2,
            },
            {
                'name': 'International',
                'description': 'For participants outside Nigeria. Early bird: $15 | Late: $20.',
                'icon': 'bi-globe',
                'fee': 30000,         # ₦30,000 (~$20) — update to exact naira equivalent
                'early_bird_fee': 22500,  # ₦22,500 (~$15) — update to exact naira equivalent
                'includes': (
                    'Full 3-day conference access\n'
                    'Conference bag and materials\n'
                    'Morning tea/coffee and lunch daily\n'
                    'Book of abstracts\n'
                    'Certificate of participation\n'
                    'Access to all plenary and technical sessions'
                ),
                'order': 3,
            },
        ]

        cats_created = 0
        if not dry_run:
            RegistrationCategory.objects.filter(conference=conference).delete()
            for c in categories:
                RegistrationCategory.objects.create(conference=conference, **c)
                cats_created += 1
        else:
            cats_created = len(categories)
        self.stdout.write(self.style.SUCCESS(f'✔ {cats_created} registration categories created'))

        # ── 5. Key Messages ───────────────────────────────────────────────────
        key_messages = [
            {
                'message': (
                    'ANA ensures the sustained use and scaling of the AKILIMO decision-support tools, '
                    'empowering farmers and value chain actors with data-driven advice across Nigeria.'
                ),
                'source': 'AKILIMO Nigeria Association',
                'is_quote': False,
                'order': 1,
            },
            {
                'message': (
                    'AKILIMO-Lagos-2026 presents a unique opportunity to explore speaking engagements, '
                    'present innovations, and create significant connections and collaborations with leading '
                    'scientists, practitioners, farmers and agro-processors.'
                ),
                'source': 'Conference Organizing Committee',
                'is_quote': False,
                'order': 2,
            },
            {
                'message': (
                    'Only those abstracts received by the deadline of 31st May 2026 and meeting the prescribed '
                    'standard will appear in the Book of Abstracts pre-printed before the conference. '
                    'Abstracts presented during the conference will be post-printed in the Book of Proceedings.'
                ),
                'source': 'Technical Committee',
                'is_quote': False,
                'order': 3,
            },
            {
                'message': (
                    'You are welcome to AKILIMO-Lagos-2026 to enhance your personal and professional '
                    'growth and development.'
                ),
                'source': 'Conference Chair',
                'is_quote': True,
                'order': 4,
            },
        ]

        msgs_created = 0
        if not dry_run:
            KeyMessage.objects.filter(conference=conference).delete()
            for m in key_messages:
                KeyMessage.objects.create(conference=conference, **m)
                msgs_created += 1
        else:
            msgs_created = len(key_messages)
        self.stdout.write(self.style.SUCCESS(f'✔ {msgs_created} key messages created'))

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN complete — no data was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\n{"─"*55}\n'
                f'AKILIMO-Lagos-2026 conference portal is ready.\n'
                f'Conference ID : {conference.pk}\n'
                f'Live at       : /conference/\n'
                f'Admin         : /admin/conference/conference/{conference.pk}/change/\n'
                f'{"─"*55}'
            ))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  1. Upload logo/favicon via Admin → Site Settings')
        self.stdout.write('  2. Add speakers via Admin → Conference → Speakers')
        self.stdout.write('  3. Add programme via Admin → Conference → Program Days')
        self.stdout.write('  4. Update bank/payment details in Admin → Conference → Registration Categories')
        self.stdout.write('  5. Fill in Organizing Committee contacts via Admin → Conference → Key Messages')
