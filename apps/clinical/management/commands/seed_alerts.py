from django.core.management.base import BaseCommand
from users.models import User
from core.firestore_service import FirestoreService
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Seeds initial alerts to Firestore'

    def handle(self, *args, **options):
        # Sample patients to link alerts
        patients = [
            {"name": "Alice Johnson", "mrn": "MRN-101"},
            {"name": "Bob Smith", "mrn": "MRN-102"},
            {"name": "Charlie Brown", "mrn": "MRN-103"},
        ]
        
        # Alert types
        alert_types = [
            {"type": "Clinical Escalation", "severity": "Critical", "short": "Stage 4 Wound detected"},
            {"type": "Security Violation", "severity": "Warning", "short": "Unauthorized access attempt (Break-the-Glass)"},
            {"type": "Clinical Escalation", "severity": "Critical", "short": "Unstageable Pressure Injury"},
        ]

        for i, patient in enumerate(patients):
            alert_config = alert_types[i % len(alert_types)]
            timestamp = timezone.now() - timedelta(hours=random.randint(1, 48))
            
            alert_data = {
                'patient_id': patient['mrn'],
                'patient_name': patient['name'],
                'type': alert_config['type'],
                'severity': alert_config['severity'],
                'message': f"{alert_config['short']} for patient {patient['name']}",
                'timestamp': timestamp.isoformat(),
                'is_dismissed': False,
                'is_resolved': False,
                'created_at': timestamp.isoformat()
            }
            
            doc_id = FirestoreService.create_document('alerts', alert_data)
            self.stdout.write(self.style.SUCCESS(f"Created alert {doc_id} for {patient['name']}"))

        self.stdout.write(self.style.SUCCESS("Successfully seeded clinical alerts to Firestore."))
