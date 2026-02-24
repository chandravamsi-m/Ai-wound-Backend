from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User
from core.firestore_service import FirestoreService
from firebase_admin import firestore
import uuid

class Command(BaseCommand):
    help = 'Seeds initial users to both Local SQLite and Firestore'

    def handle(self, *args, **options):
        # Sample user data
        users_data = [
            {"name": "chandravamsi", "email": "chandravamsi@gmail.com", "role": "Admin", "isActive": True},
            {"name": "Dr. Virat Kohli", "email": "viratkohli@gmail.com", "role": "Doctor", "isActive": True},
            {"name": "Nurse Mithali Raj", "email": "mithaliraj@gmail.com", "role": "Nurse", "isActive": True},
        ]
        
        password = "Vamsi123@"
        
        for item in users_data:
            # 1. Create/Update in Local SQLite (Use email as ID for consistency)
            user, created = User.objects.update_or_create(
                email=item['email'],
                defaults={
                    'id': item['email'], # Use email as primary key
                    'name': item['name'],
                    'role': item['role'],
                    'isActive': item['isActive'],
                    'status': 'ACTIVE' if item['isActive'] else 'DISABLED'
                }
            )
            
            if created or True: # Always reset password for seeding
                user.set_password(password)
                user.save()

            # 2. Sync to Firestore (Crucial for the new project)
            firestore_data = {
                'uid': str(user.id),
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'isActive': user.isActive,
                'status': user.status,
                'password': user.password, # Save the hash for self-healing/login
                'last_activity': timezone.now().isoformat(),
                'updated_at': firestore.SERVER_TIMESTAMP if hasattr(firestore, 'SERVER_TIMESTAMP') else None
            }
            
            # Using email as document ID in 'users' collection for clarity
            FirestoreService.create_document('users', firestore_data, doc_id=user.email)
            
            self.stdout.write(self.style.SUCCESS(f"Seeded: {user.email}"))
            
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(users_data)} users to SQLite and Firestore."))
