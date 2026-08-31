from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_alter_userprofile_dashboard_preferences'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='is_free_membership',
            field=models.BooleanField(
                default=False,
                help_text='Membership was granted free of charge (no payment was made).',
            ),
        ),
        migrations.AddField(
            model_name='membership',
            name='free_membership_granted_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When the free membership was last granted or renewed.',
            ),
        ),
    ]
