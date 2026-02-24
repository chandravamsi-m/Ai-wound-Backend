import os
import sys
import django

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from core.firestore_service import FirestoreService
from users.models import User, SystemLog
from clinical.models import Patient, Wound, WoundAssessment, Task, ClinicalRecord, Alert
from django.contrib.auth.hashers import make_password

def clear_all_data():
    print("🚀 Starting Fresh: Clearing all databases...")
    
    # 1. Clear Firestore Collections
    collections = ['users', 'patients', 'wounds', 'assessments', 'tasks', 'clinical_records', 'alerts', 'logs']
    for coll_name in collections:
        print(f"Clearing Firestore collection: {coll_name}...")
        docs = FirestoreService.collection(coll_name).stream()
        count = 0
        for doc in docs:
            FirestoreService.delete_document(coll_name, doc.id)
            count += 1
        print(f"✅ Deleted {count} documents from {coll_name}.")

    # 2. Clear PostgreSQL Tables
    print("\nClearing local PostgreSQL tables...")
    Alert.objects.all().delete()
    Task.objects.all().delete()
    ClinicalRecord.objects.all().delete()
    WoundAssessment.objects.all().delete()
    Wound.objects.all().delete()
    Patient.objects.all().delete()
    SystemLog.objects.all().delete()
    # Delete all users except superusers if you want to keep them, but here we wipe all
    User.objects.all().delete()
    print("✅ Local database tables truncated.")

    # 3. Create Bootstrap Admin
    print("\nCreating bootstrap Admin user in Firestore...")
    from django.contrib.auth.hashers import make_password
    
    # First, let Firestore generate a UID
    coll_ref = FirestoreService.collection('users')
    doc_ref = coll_ref.document() # Generates a new unique reference
    firestore_id = doc_ref.id
    
    admin_data = {
        'id': firestore_id,
        'name': 'Root Admin',
        'email': 'admin@woundtool.com',
        'password': make_password('adminpassword123'),
        'role': 'Admin',
        'status': 'ACTIVE',
        'isActive': True,
        'created_at': timezone.now().isoformat()
    }
    
    # Save to Firestore
    doc_ref.set(admin_data)
    
    # Now, sync to the internal SQLite (only for the Django login engine)
    admin_user = User.objects.create(
        id=firestore_id,
        email=admin_data['email'],
        name=admin_data['name'],
        role=admin_data['role'],
        status=admin_data['status'],
        isActive=admin_data['isActive']
    )
    admin_user.password = admin_data['password']
    admin_user.save()
    
    print(f"\n✨ Ready! All clinical data is now 100% Firestore-Only.")
    print(f"Admin Firestore UID: {firestore_id}")
    print(f"Credentials for testing:")
    print(f"Email: {admin_data['email']}")
    print(f"Password: adminpassword123")

if __name__ == "__main__":
    confirm = input("⚠️ WARNING: This will DELETE ALL DATA from Firestore and Local DB. Type 'YES' to confirm: ")
    if confirm == "YES":
        clear_all_data()
    else:
        print("Aborted.")
