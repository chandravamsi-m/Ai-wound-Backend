import os
import django
import sys

# Add the apps directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from clinical.models import Patient, Alert

def seed():
    # Create Patients
    p1, _ = Patient.objects.get_or_create(name="James Wilson", mrn="MRN-8821")
    p2, _ = Patient.objects.get_or_create(name="Elena Rodriguez", mrn="MRN-9932")
    p3, _ = Patient.objects.get_or_create(name="Robert Chen", mrn="MRN-4412")
    p4, _ = Patient.objects.get_or_create(name="Sarah Jenkins", mrn="MRN-2210")

    # Create Alerts
    Alert.objects.get_or_create(
        patient=p1,
        alert_type="Deteriorating Wound",
        description="15% increase in necrotic tissue",
        severity="Critical"
    )
    Alert.objects.get_or_create(
        patient=p2,
        alert_type="Missing Data",
        description="Depth measurement required",
        severity="Warning"
    )
    Alert.objects.get_or_create(
        patient=p3,
        alert_type="Late Assessment",
        description="Overdue by 12 hours",
        severity="Warning"
    )
    Alert.objects.get_or_create(
        patient=p4,
        alert_type="Suspected Infection",
        description="Purulent exudate noted",
        severity="Critical"
    )
    
    # Some resolved alerts for stats
    a5, _ = Alert.objects.get_or_create(
        patient=p1,
        alert_type="Resolved Infection",
        description="Antibiotics effective",
        severity="Critical",
        is_dismissed=True
    )

    print("Seeding complete!")

if __name__ == "__main__":
    seed()
