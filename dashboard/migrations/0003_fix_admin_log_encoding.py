# Generated migration to fix django_admin_log encoding issue

from django.db import migrations, connection


def fix_admin_log_encoding(apps, schema_editor):
    """Fix the encoding of django_admin_log.object_repr column for MySQL databases"""
    if connection.vendor == 'mysql':
        with connection.cursor() as cursor:
            try:
                # Fix the django_admin_log.object_repr column encoding
                cursor.execute("""
                    ALTER TABLE django_admin_log 
                    MODIFY COLUMN object_repr VARCHAR(200) 
                    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                """)
                print("Successfully updated django_admin_log.object_repr column encoding to utf8mb4")
            except Exception as e:
                print(f"Warning: Could not update django_admin_log encoding: {e}")
                # Don't fail the migration if this doesn't work
                pass


def reverse_admin_log_encoding(apps, schema_editor):
    """Reverse the encoding fix (not recommended)"""
    # We don't reverse this as it would break Unicode support
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_membershippricing'),
    ]

    operations = [
        migrations.RunPython(
            fix_admin_log_encoding,
            reverse_admin_log_encoding,
            elidable=True,
        ),
    ]