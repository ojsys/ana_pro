from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Fix production database encoding issues immediately'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migration',
            action='store_true',
            help='Skip running migrations (only fix database encoding)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Starting production database encoding fix...')
        )
        
        # Step 1: Run migrations first (unless skipped)
        if not options['skip_migration']:
            self.stdout.write("📦 Running database migrations...")
            try:
                call_command('migrate', verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS('✅ Migrations completed successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Migration failed: {e}')
                )
                self.stdout.write(
                    self.style.WARNING('🔧 Continuing with direct database fix...')
                )
        
        # Step 2: Fix database encoding
        if connection.vendor == 'mysql':
            self.fix_mysql_encoding()
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Database vendor {connection.vendor} - no encoding fix needed')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Production database encoding fix completed!')
        )

    def fix_mysql_encoding(self):
        self.stdout.write("🛠️  Fixing MySQL database encoding...")
        
        with connection.cursor() as cursor:
            try:
                # Check current encoding
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
                    self.stdout.write(f"📊 Current django_admin_log.object_repr: {charset}/{collation}")
                    
                    if charset != 'utf8mb4':
                        self.stdout.write("🔄 Updating column encoding to utf8mb4...")
                        
                        # Fix the column encoding
                        cursor.execute("""
                            ALTER TABLE django_admin_log 
                            MODIFY COLUMN object_repr VARCHAR(200) 
                            CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                        """)
                        
                        self.stdout.write(
                            self.style.SUCCESS('✅ django_admin_log.object_repr encoding fixed!')
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS('✅ django_admin_log.object_repr already has utf8mb4 encoding')
                        )
                
                # Set connection encoding
                cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;")
                self.stdout.write("✅ Connection encoding set to utf8mb4")
                
                # Also fix any other admin log columns that might have encoding issues
                cursor.execute("""
                    ALTER TABLE django_admin_log 
                    MODIFY COLUMN change_message LONGTEXT 
                    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                """)
                self.stdout.write("✅ django_admin_log.change_message encoding fixed")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error fixing database encoding: {e}')
                )
                self.stdout.write(
                    self.style.WARNING('💡 You may need to run this command with database admin privileges')
                )
                raise