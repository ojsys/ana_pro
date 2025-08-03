from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix database encoding issues for Unicode characters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check current database encoding without making changes',
        )

    def handle(self, *args, **options):
        check_only = options['check_only']
        
        if connection.vendor == 'mysql':
            self.handle_mysql(check_only)
        elif connection.vendor == 'sqlite':
            self.stdout.write(
                self.style.SUCCESS('SQLite databases handle UTF-8 encoding automatically.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Database vendor {connection.vendor} not specifically handled.')
            )

    def handle_mysql(self, check_only):
        with connection.cursor() as cursor:
            # Check current database encoding
            self.stdout.write("Checking current database encoding...")
            
            # Check database character set
            cursor.execute("SELECT @@character_set_database, @@collation_database;")
            db_charset, db_collation = cursor.fetchone()
            self.stdout.write(f"Database charset: {db_charset}, collation: {db_collation}")
            
            # Check connection character set
            cursor.execute("SHOW VARIABLES LIKE 'character_set_connection';")
            result = cursor.fetchone()
            if result:
                self.stdout.write(f"Connection charset: {result[1]}")
            
            # Check admin_log table specifically
            cursor.execute("""
                SELECT column_name, character_set_name, collation_name 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'django_admin_log' 
                AND column_name = 'object_repr';
            """)
            result = cursor.fetchone()
            if result:
                column_name, charset, collation = result
                self.stdout.write(f"django_admin_log.object_repr: charset={charset}, collation={collation}")
                
                if charset != 'utf8mb4':
                    if check_only:
                        self.stdout.write(
                            self.style.WARNING(
                                'The object_repr column is not using utf8mb4. '
                                'Run this command without --check-only to fix it.'
                            )
                        )
                    else:
                        self.stdout.write("Fixing object_repr column encoding...")
                        cursor.execute("""
                            ALTER TABLE django_admin_log 
                            MODIFY COLUMN object_repr VARCHAR(200) 
                            CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                        """)
                        self.stdout.write(
                            self.style.SUCCESS('Fixed django_admin_log.object_repr column encoding.')
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('django_admin_log.object_repr already has proper UTF-8 encoding.')
                    )
            
            if not check_only:
                # Set connection to use utf8mb4
                cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;")
                self.stdout.write("Set connection to use utf8mb4 encoding.")
                
        if not check_only:
            self.stdout.write(
                self.style.SUCCESS(
                    'Database encoding fix completed. '
                    'Consider updating your DATABASE_URL to include charset=utf8mb4'
                )
            )