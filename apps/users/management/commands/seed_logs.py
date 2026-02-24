from django.core.management.base import BaseCommand
from users.models import User, SystemLog
from core.firestore_service import FirestoreService
from django.utils import timezone
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Seeds initial logs to both Local SQLite and Firestore'

    def handle(self, *args, **options):
        # Clear existing logs locally for a fresh start
        SystemLog.objects.all().delete()
        
        # Get users for attribution
        admin = User.objects.filter(role='Admin').first()
        doctor = User.objects.filter(role='Doctor').first()
        nurse = User.objects.filter(role='Nurse').first()
        
        # Sample log data
        logs_data = [
            {"user": admin, "action": "ADMIN_LOGIN_SUCCESS: Authorized access to panel", "severity": "Success", "hours_ago": 1},
            {"user": doctor, "action": "WOUND_ANALYSIS: Processed scan for Patient ID: PAT-101", "severity": "Info", "hours_ago": 2},
            {"user": nurse, "action": "PATIENT_INTAKE: Admitted new patient 'John Doe'", "severity": "Success", "hours_ago": 5},
            {"user": None, "action": "SYSTEM_CRON: Automated database optimization", "severity": "Info", "hours_ago": 12},
            {"user": admin, "action": "SECURITY_WARNING: Multiple failed login attempts from 45.22.100.12", "severity": "Warning", "hours_ago": 24},
            {"user": doctor, "action": "CRITICAL_ESCALATION: Stage 4 Pressure Injury detected", "severity": "Error", "hours_ago": 48},
        ]
        
        for item in logs_data:
            user = item['user']
            timestamp = timezone.now() - timedelta(hours=item['hours_ago'])
            
            # 1. Create locally (for history)
            log = SystemLog.objects.create(
                user=user,
                action=item['action'],
                severity=item['severity'],
                ip_address="127.0.0.1" if user else None
            )
            # Override auto-add timestamp
            log.timestamp = timestamp
            log.save()
            
            # 2. Sync to Firestore (Crucial for the new project)
            firestore_data = {
                'id': str(log.id),
                'user_id': user.id if user else None,
                'user_email': user.email if user else 'system@mediwound.ai',
                'action': item['action'],
                'severity': item['severity'],
                'ip_address': log.ip_address,
                'timestamp': timestamp.isoformat()
            }
            
            # The 'logs' viewset uses auto-generated IDs from Firestore typically
            FirestoreService.create_document('logs', firestore_data)
            
            self.stdout.write(self.style.SUCCESS(f"Logged action: {item['action']}"))
            
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(logs_data)} logs to SQLite and Firestore."))
