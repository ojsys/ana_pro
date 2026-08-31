from django.db import migrations, models


def bypass_to_registration_mode(apps, schema_editor):
    """Carry the old bypass_payment_requirements boolean over to registration_mode."""
    SiteSettings = apps.get_model('website', 'SiteSettings')
    for settings_obj in SiteSettings.objects.all():
        settings_obj.registration_mode = 'free' if settings_obj.bypass_payment_requirements else 'paid'
        settings_obj.save(update_fields=['registration_mode'])


def registration_mode_to_bypass(apps, schema_editor):
    SiteSettings = apps.get_model('website', 'SiteSettings')
    for settings_obj in SiteSettings.objects.all():
        settings_obj.bypass_payment_requirements = settings_obj.registration_mode == 'free'
        settings_obj.save(update_fields=['bypass_payment_requirements'])


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0008_add_gallery_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='registration_mode',
            field=models.CharField(
                choices=[
                    ('free', 'Free - membership is granted immediately, no payment required'),
                    ('paid', 'Paid - registration fee and annual dues must be paid'),
                ],
                default='free',
                help_text=(
                    'Free: new sign-ups get an active membership straight away (use this to grow the '
                    'member base). Paid: registration fees and annual dues are enforced before members '
                    'can access the platform.'
                ),
                max_length=10,
                verbose_name='Registration Mode',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='free_membership_banner',
            field=models.CharField(
                blank=True,
                default='Membership is currently free - enjoy full access to the platform.',
                help_text='Message shown to members while registration mode is Free. Leave blank to hide it.',
                max_length=255,
                verbose_name='Free Membership Message',
            ),
        ),
        migrations.RunPython(bypass_to_registration_mode, registration_mode_to_bypass),
        migrations.RemoveField(
            model_name='sitesettings',
            name='bypass_payment_requirements',
        ),
    ]
