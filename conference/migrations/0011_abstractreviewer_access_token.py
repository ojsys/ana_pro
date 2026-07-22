import uuid
from django.db import migrations, models


def gen_tokens(apps, schema_editor):
    """Give every existing reviewer a unique access token."""
    AbstractReviewer = apps.get_model('conference', 'AbstractReviewer')
    for reviewer in AbstractReviewer.objects.all():
        reviewer.access_token = uuid.uuid4()
        reviewer.save(update_fields=['access_token'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('conference', '0010_abstractreviewer'),
    ]

    operations = [
        # 1. Add nullable, non-unique first so existing rows don't collide.
        migrations.AddField(
            model_name='abstractreviewer',
            name='access_token',
            field=models.UUIDField(null=True, editable=False),
        ),
        # 2. Backfill a unique token per existing row.
        migrations.RunPython(gen_tokens, noop),
        # 3. Tighten to the final field definition (unique, default, help_text).
        migrations.AlterField(
            model_name='abstractreviewer',
            name='access_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True,
                                   help_text="Permanent token embedded in this reviewer's access link"),
        ),
        # 4. Match the model's updated email help_text (state only).
        migrations.AlterField(
            model_name='abstractreviewer',
            name='email',
            field=models.EmailField(help_text='The access link is emailed here', max_length=254, unique=True),
        ),
    ]
