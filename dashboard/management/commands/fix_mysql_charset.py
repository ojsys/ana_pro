"""
Convert the MySQL database to utf8mb4.

The production database was created with an older default charset (latin1 or
utf8mb3), so text columns reject any character outside that set even though the
connection itself is utf8mb4. A partner typing an em dash, a curly quote pasted
from Word, an accented name or an emoji into a form gets:

    DataError (1366, "Incorrect string value: '\\xE2\\x80\\x94...' for column ...")

This converts the database default, then every table and text column, to
utf8mb4 / utf8mb4_unicode_ci. Existing rows are converted in place by MySQL.

    python manage.py fix_mysql_charset                    # report only (default)
    python manage.py fix_mysql_charset --apply            # convert everything
    python manage.py fix_mysql_charset --apply --table dashboard_partnerorganization

Take a database backup first. On a large table the ALTER rewrites the table and
holds a lock for the duration.
"""
from django.core.management.base import BaseCommand
from django.db import connection

TARGET_CHARSET = 'utf8mb4'
TARGET_COLLATION = 'utf8mb4_unicode_ci'


class Command(BaseCommand):
    help = 'Convert MySQL tables and text columns to utf8mb4 (report-only unless --apply)'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Actually run the ALTER statements (default is a dry report)')
        parser.add_argument('--table', action='append', dest='tables',
                            help='Limit to this table; repeatable')

    def handle(self, *args, **options):
        if connection.vendor != 'mysql':
            self.stdout.write(self.style.WARNING(
                f'Database vendor is "{connection.vendor}", not mysql - nothing to do.'
            ))
            return

        apply_changes = options['apply']
        only = set(options['tables'] or [])

        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]

            cursor.execute("""
                SELECT default_character_set_name, default_collation_name
                FROM information_schema.schemata WHERE schema_name = %s
            """, [db_name])
            db_charset, db_collation = cursor.fetchone()
            self.stdout.write(f'Database "{db_name}": {db_charset} / {db_collation}')

            # Columns still on the wrong charset.
            cursor.execute("""
                SELECT table_name, column_name, column_type, character_set_name,
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND character_set_name IS NOT NULL
                  AND character_set_name <> %s
                ORDER BY table_name, ordinal_position
            """, [db_name, TARGET_CHARSET])
            columns = [row for row in cursor.fetchall() if not only or row[0] in only]

            cursor.execute("""
                SELECT t.table_name, c.character_set_name
                FROM information_schema.tables t
                JOIN information_schema.collation_character_set_applicability c
                  ON c.collation_name = t.table_collation
                WHERE t.table_schema = %s AND t.table_type = 'BASE TABLE'
                  AND c.character_set_name <> %s
                ORDER BY t.table_name
            """, [db_name, TARGET_CHARSET])
            tables = [row for row in cursor.fetchall() if not only or row[0] in only]

            if not columns and not tables and db_charset == TARGET_CHARSET:
                self.stdout.write(self.style.SUCCESS(
                    f'Everything is already {TARGET_CHARSET}. Nothing to do.'
                ))
                return

            self.stdout.write(
                f'\n{len(tables)} table(s) and {len(columns)} column(s) are not {TARGET_CHARSET}.'
            )

            by_table = {}
            for table, column, coltype, charset, *_ in columns:
                by_table.setdefault(table, []).append((column, coltype, charset))
            for table in sorted(by_table)[:15]:
                cols = by_table[table]
                shown = ', '.join(f'{c} ({cs})' for c, _, cs in cols[:4])
                more = f' +{len(cols) - 4} more' if len(cols) > 4 else ''
                self.stdout.write(f'  {table}: {shown}{more}')
            if len(by_table) > 15:
                self.stdout.write(f'  ... and {len(by_table) - 15} more table(s)')

            if not apply_changes:
                self.stdout.write(self.style.WARNING(
                    '\nReport only - nothing was changed.\n'
                    'Back up the database, then re-run with --apply to convert.'
                ))
                return

            self.stdout.write(self.style.WARNING('\nApplying changes...'))

            # 1. Database default, so new tables inherit utf8mb4.
            if db_charset != TARGET_CHARSET and not only:
                cursor.execute(
                    f'ALTER DATABASE `{db_name}` '
                    f'CHARACTER SET {TARGET_CHARSET} COLLATE {TARGET_COLLATION}'
                )
                self.stdout.write(f'  database default -> {TARGET_CHARSET}')

            # 2. Each table, which converts its columns and existing rows.
            converted = failed = 0
            for table, _charset in tables:
                try:
                    cursor.execute(
                        f'ALTER TABLE `{table}` '
                        f'CONVERT TO CHARACTER SET {TARGET_CHARSET} COLLATE {TARGET_COLLATION}'
                    )
                    converted += 1
                    self.stdout.write(f'  {table} -> {TARGET_CHARSET}')
                except Exception as exc:
                    failed += 1
                    self.stdout.write(self.style.ERROR(f'  {table} FAILED: {exc}'))

            # 3. Anything CONVERT TO left behind (columns with an explicit charset).
            cursor.execute("""
                SELECT table_name, column_name, character_set_name
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND character_set_name IS NOT NULL
                  AND character_set_name <> %s
            """, [db_name, TARGET_CHARSET])
            remaining = [r for r in cursor.fetchall() if not only or r[0] in only]

            if remaining:
                self.stdout.write(self.style.WARNING(
                    f'\n{len(remaining)} column(s) still not {TARGET_CHARSET}:'
                ))
                for table, column, charset in remaining[:20]:
                    self.stdout.write(f'  {table}.{column} ({charset})')

            self.stdout.write(self.style.SUCCESS(
                f'\nConverted {converted} table(s)'
                + (f', {failed} failed' if failed else '')
                + f'. {len(remaining)} column(s) still need attention.'
            ))
            self.stdout.write(
                'Restart the application so existing database connections pick this up.'
            )
