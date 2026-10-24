from django.db import migrations, models


def switch_to_paid(apps, schema_editor):
    """Membership is no longer free: new sign-ups must pay. Existing free
    memberships are left alone and run until they expire on 31 December."""
    SiteSettings = apps.get_model('website', 'SiteSettings')
    SiteSettings.objects.update(registration_mode='paid')


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0010_socialmedialink_socialpost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='registration_mode',
            field=models.CharField(
                choices=[
                    ('free', 'Free - membership is granted immediately, no payment required'),
                    ('paid', 'Paid - registration fee and annual dues must be paid'),
                ],
                default='paid',
                help_text=(
                    'Free: new sign-ups get an active membership straight away (use this to grow the '
                    'member base). Paid: registration fees and annual dues are enforced before members '
                    'can access the platform.'
                ),
                max_length=10,
                verbose_name='Registration Mode',
            ),
        ),
        migrations.RunPython(switch_to_paid, migrations.RunPython.noop),
    ]
