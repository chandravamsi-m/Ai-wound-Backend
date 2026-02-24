import os
import sys
import django

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.firestore_service import FirestoreService
from users.models import User

def recover_user(email):
    print(f"🚀 Attempting recovery for: {email}")
    
    # 1. Update Firestore
    users = FirestoreService.query('users', 'email', '==', email)
    if not users:
        print(f"❌ User with email {email} not found in Firestore.")
        return
    
    user_data = users[0]
    user_id = user_data['id']
    
    FirestoreService.update_document('users', user_id, {
        'isActive': True,
        'status': 'ACTIVE'
    })
    print(f"✅ Firestore updated: isActive=True, status=ACTIVE")
    
    # 2. Update Local SQLite
    affected = User.objects.filter(email=email).update(isActive=True, status='ACTIVE')
    if affected:
        print(f"✅ Local SQLite updated.")
    else:
        # If user doesn't exist locally, the next login will sync them anyway
        print(f"ℹ️ User not found in local SQLite (will sync on next login).")

    print(f"\n✨ Recovery complete! Please try logging in again.")

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else 'admin@woundtool.com'
    recover_user(email)
