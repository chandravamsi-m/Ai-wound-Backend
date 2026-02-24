import os
import sys
import django

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wound_analysis_backend.settings')
django.setup()

from users.models import User
from django.db import connection

# Delete all users
User.objects.all().delete()

# Reset the auto-increment sequence
with connection.cursor() as cursor:
    cursor.execute("ALTER SEQUENCE users_user_id_seq RESTART WITH 1")

print("All users deleted and ID sequence reset to 1")
