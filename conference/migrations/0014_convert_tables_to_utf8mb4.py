"""
Convert the conference tables to utf8mb4.

Production tables were created with the MySQL server default (latin1_swedish_ci)
while the connection uses utf8mb4_unicode_ci, so string lookups such as
``ticket_id__iexact`` fail with "Illegal mix of collations" (error 1267), and
non-Latin-1 characters can't be stored. No-op on non-MySQL databases.
"""

from django.db import migrations


def convert_to_utf8mb4(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != 'mysql':
        return

    tables = set()
    for model in apps.get_app_config('conference').get_models(include_auto_created=True):
        tables.add(model._meta.db_table)

    existing = set(connection.introspection.table_names())
    with connection.cursor() as cursor:
        for table in sorted(tables & existing):
            cursor.execute(
                f"ALTER TABLE {connection.ops.quote_name(table)} "
                "CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('conference', '0013_conference_display_abstracts_conference_display_days_and_more'),
    ]

    operations = [
        migrations.RunPython(convert_to_utf8mb4, migrations.RunPython.noop),
    ]
