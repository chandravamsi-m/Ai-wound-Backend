import os
import sys
import django

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wound_analysis_backend.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Drop old tables
    cursor.execute("DROP TABLE IF EXISTS staff_user CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS users_user CASCADE;")
    
    # Clear migration history
    cursor.execute("DELETE FROM django_migrations WHERE app IN ('staff', 'users');")
    
print("Database cleaned successfully!")
