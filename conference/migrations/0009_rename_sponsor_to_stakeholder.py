# Rename the private "sponsor" registration flow to "stakeholder".

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conference', '0008_conference_sponsor_access_token_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='conference',
            old_name='sponsor_access_token',
            new_name='stakeholder_access_token',
        ),
        migrations.RenameField(
            model_name='registration',
            old_name='is_sponsor',
            new_name='is_stakeholder',
        ),
        migrations.AlterField(
            model_name='registration',
            name='is_stakeholder',
            field=models.BooleanField(default=False, help_text='Complimentary stakeholder registration — captured via the private stakeholder link, with no fee charged.'),
        ),
    ]
