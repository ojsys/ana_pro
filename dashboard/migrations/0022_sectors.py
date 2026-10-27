from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models

PRIVATE = 'Private Sector'
PUBLIC = 'Public Sector'
NGOS = 'NGOs'

# Existing types move under Private Sector with their new names (code -> name).
PRIVATE_RENAMES = [('corporate', 'Large Scale'), ('sme', 'Medium Scale'), ('msme', 'Small Scale')]

# New options: (sector, name, code, requires_details)
NEW_TYPES = [
    (PUBLIC, 'Research Institutes', 'research-institutes', False),
    (PUBLIC, 'FMARD', 'fmard', False),
    (PUBLIC, 'State Ministries of Agric (ADPs)', 'state-ministries-adps', False),
    (PUBLIC, 'Federal & State Universities', 'universities', False),
    (PUBLIC, 'Other', 'public-other', True),
    (NGOS, 'NGO', 'ngo', False),
]


def add_sectors(apps, schema_editor):
    """
    Create the sectors, file the existing membership types under Private Sector
    and add the Public Sector and NGO options.

    New options start with the Medium Scale fees so nobody can sign up for free
    by accident; set their real fees in Admin -> Membership Types.
    """
    Sector = apps.get_model('dashboard', 'Sector')
    MembershipType = apps.get_model('dashboard', 'MembershipType')

    sectors = {
        name: Sector.objects.create(name=name, display_order=order)
        for order, name in enumerate([PUBLIC, PRIVATE, NGOS])
    }

    for order, (code, name) in enumerate(PRIVATE_RENAMES):
        MembershipType.objects.filter(code=code).update(
            sector=sectors[PRIVATE], name=name, display_order=order,
        )
    # Any other type an admin already added stays under Private Sector to be moved if needed.
    MembershipType.objects.filter(sector__isnull=True).update(sector=sectors[PRIVATE])

    medium = MembershipType.objects.filter(code='sme').first()
    registration_fee = medium.registration_fee if medium else Decimal('50000.00')
    annual_dues = medium.annual_dues if medium else Decimal('20000.00')

    order_in = {}
    for sector_name, name, code, requires_details in NEW_TYPES:
        if MembershipType.objects.filter(code=code).exists():
            continue
        order = order_in.get(sector_name, 0)
        order_in[sector_name] = order + 1
        MembershipType.objects.create(
            sector=sectors[sector_name], name=name, code=code,
            requires_details=requires_details, display_order=order,
            registration_fee=registration_fee, annual_dues=annual_dues,
        )


def remove_sectors(apps, schema_editor):
    MembershipType = apps.get_model('dashboard', 'MembershipType')
    MembershipType.objects.filter(code__in=[code for _, _, code, _ in NEW_TYPES], organizations__isnull=True).delete()
    old_names = {'corporate': 'Corporate Organization', 'sme': 'SME', 'msme': 'MSME'}
    for code, name in old_names.items():
        MembershipType.objects.filter(code=code).update(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0021_membership_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text='Shown under the sector choice at sign-up.')),
                ('is_active', models.BooleanField(default=True, help_text="Inactive sectors aren't offered at sign-up.")),
                ('display_order', models.PositiveIntegerField(default=0, help_text='Lower numbers are listed first.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Sector',
                'verbose_name_plural': 'Sectors',
                'ordering': ['display_order', 'name'],
            },
        ),
        migrations.AlterField(
            model_name='membershiptype',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AddField(
            model_name='membershiptype',
            name='sector',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='membership_types', to='dashboard.sector'),
        ),
        migrations.AddField(
            model_name='membershiptype',
            name='requires_details',
            field=models.BooleanField(default=False, help_text="Ask the organization to specify (for an 'Other' option)."),
        ),
        migrations.AddField(
            model_name='partnerorganization',
            name='sector_details',
            field=models.CharField(blank=True, help_text="What the organization entered when its membership type asks to specify (e.g. 'Other').", max_length=200),
        ),
        migrations.RunPython(add_sectors, remove_sectors),
        migrations.AlterField(
            model_name='membershiptype',
            name='sector',
            field=models.ForeignKey(help_text='The sector this option is listed under at sign-up.',
                                    on_delete=django.db.models.deletion.PROTECT,
                                    related_name='membership_types', to='dashboard.sector'),
        ),
        migrations.AlterUniqueTogether(
            name='membershiptype',
            unique_together={('sector', 'name')},
        ),
        migrations.AlterModelOptions(
            name='membershiptype',
            options={'ordering': ['sector__display_order', 'display_order', 'name'],
                     'verbose_name': 'Membership Type', 'verbose_name_plural': 'Membership Types'},
        ),
    ]
