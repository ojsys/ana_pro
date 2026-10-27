from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models

# The categories that used to be fixed in code.
OLD_CATEGORIES = [('msme', 'MSME'), ('sme', 'SME'), ('corporate', 'Corporate Organization')]


def categories_to_types(apps, schema_editor):
    """
    Turn the fixed categories into MembershipType rows, carrying over the fees
    from Membership Pricing, and point each organization at its new type.
    """
    MembershipType = apps.get_model('dashboard', 'MembershipType')
    MembershipPricing = apps.get_model('dashboard', 'MembershipPricing')
    PartnerOrganization = apps.get_model('dashboard', 'PartnerOrganization')

    for order, (code, name) in enumerate(OLD_CATEGORIES):
        prices = dict(
            MembershipPricing.objects.filter(membership_type=code)
            .values_list('payment_type', 'price')
        )
        membership_type = MembershipType.objects.create(
            name=name,
            code=code,
            registration_fee=prices.get('registration', Decimal('0')),
            annual_dues=prices.get('annual_dues', Decimal('0')),
            display_order=order,
        )
        PartnerOrganization.objects.filter(membership_category=code).update(
            membership_type_link=membership_type
        )

    MembershipPricing.objects.filter(membership_type__in=[c for c, _ in OLD_CATEGORIES]).delete()


def types_to_categories(apps, schema_editor):
    MembershipType = apps.get_model('dashboard', 'MembershipType')
    MembershipPricing = apps.get_model('dashboard', 'MembershipPricing')
    PartnerOrganization = apps.get_model('dashboard', 'PartnerOrganization')

    codes = {c for c, _ in OLD_CATEGORIES}
    for membership_type in MembershipType.objects.filter(code__in=codes):
        for payment_type, price in (('registration', membership_type.registration_fee),
                                    ('annual_dues', membership_type.annual_dues)):
            MembershipPricing.objects.update_or_create(
                membership_type=membership_type.code, payment_type=payment_type,
                defaults={'price': price, 'is_active': True},
            )
        PartnerOrganization.objects.filter(membership_type_link=membership_type).update(
            membership_category=membership_type.code
        )


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0020_organization_membership_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='MembershipType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('code', models.SlugField(help_text="Short identifier used in payment references, e.g. 'sme'. Filled in from the name if left blank.", max_length=30, unique=True)),
                ('description', models.TextField(blank=True, help_text='Shown to organizations choosing a membership type at sign-up.')),
                ('registration_fee', models.DecimalField(decimal_places=2, help_text='One-time registration fee in Naira', max_digits=12)),
                ('annual_dues', models.DecimalField(decimal_places=2, help_text='Yearly dues (Jan 1 - Dec 31) in Naira', max_digits=12)),
                ('is_active', models.BooleanField(default=True, help_text="Inactive types can't be chosen at sign-up. Organizations already on one keep it.")),
                ('display_order', models.PositiveIntegerField(default=0, help_text='Lower numbers are listed first.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Membership Type',
                'verbose_name_plural': 'Membership Types',
                'ordering': ['display_order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='partnerorganization',
            name='membership_type_link',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='+', to='dashboard.membershiptype'),
        ),
        migrations.RunPython(categories_to_types, types_to_categories),
        migrations.RemoveField(
            model_name='partnerorganization',
            name='membership_category',
        ),
        migrations.RenameField(
            model_name='partnerorganization',
            old_name='membership_type_link',
            new_name='membership_category',
        ),
        migrations.AlterField(
            model_name='partnerorganization',
            name='membership_category',
            field=models.ForeignKey(blank=True, help_text='Sets the registration fee and annual dues this organization pays. Organizations without a type are legacy records billed per person.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='organizations', to='dashboard.membershiptype', verbose_name='Membership type'),
        ),
        migrations.AlterField(
            model_name='membershippricing',
            name='membership_type',
            field=models.CharField(choices=[('individual', 'Individual Membership (legacy)'), ('organization', 'Partner Organization Membership (legacy)')], max_length=20),
        ),
    ]
