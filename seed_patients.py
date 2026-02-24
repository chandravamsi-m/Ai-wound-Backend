import os
import django
import sys
from datetime import date, timedelta
import random

# Setup Django environment
sys.path.insert(0, os.path.join(os.getcwd(), 'apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from clinical.models import Patient

def seed_patients():
    print("Seeding more clinical patient data...")
    
    # Existing patients check
    existing_count = Patient.objects.count()
    print(f"Current patient count: {existing_count}")

    more_patients = [
        {
            "name": "Sarah Jenkins",
            "age": 64,
            "gender": "Female",
            "bed": "301-A",
            "ward": "Medical-Surgical",
            "diagnosis": "Peripheral Artery Disease (PAD), Chronic Venous Insufficiency",
            "medical_history": "Type 2 Diabetes (15 years), Hypertension, Smoker",
            "status": "Observation"
        },
        {
            "name": "Robert Miller",
            "age": 72,
            "gender": "Male",
            "bed": "205-B",
            "ward": "Geriatric",
            "diagnosis": "Pressure Injury (Stage 3) - Sacral region",
            "medical_history": "Post-stroke immobility, Dementia, Frailty",
            "status": "Stable"
        },
        {
            "name": "Elena Rodriguez",
            "age": 45,
            "gender": "Female",
            "bed": "412-1",
            "ward": "Intensive Care Unit",
            "diagnosis": "Severe Diabetic Foot Ulcer (DFU) with Sepsis",
            "medical_history": "Type 1 Diabetes, Kidney Transplant (2020), Immunocompromised",
            "status": "Critical"
        },
        {
            "name": "David Thompson",
            "age": 58,
            "gender": "Male",
            "bed": "304-B",
            "ward": "Orthopedics",
            "diagnosis": "Post-operative surgical site infection",
            "medical_history": "Knee replacement surgery, Obesity (BMI 32)",
            "status": "Stable"
        },
        {
            "name": "Linda Wu",
            "age": 67,
            "gender": "Female",
            "bed": "210-A",
            "ward": "Medical-Surgical",
            "diagnosis": "Stasis Ulcer, Venous Insufficiency",
            "medical_history": "Varicose veins, Chronic lymphedema",
            "status": "Observation"
        },
        {
            "name": "James Wilson",
            "age": 81,
            "gender": "Male",
            "bed": "502-1",
            "ward": "Palliative Care",
            "diagnosis": "Complex non-healing wound, Malignant ulcer",
            "medical_history": "Metastatic Melanoma, Heart Failure",
            "status": "At Risk"
        },
        {
            "name": "Patricia Hall",
            "age": 53,
            "gender": "Female",
            "bed": "308-C",
            "ward": "Wound Care Unit",
            "diagnosis": "Neuropathic Foot Ulcer",
            "medical_history": "Type 2 Diabetes, Diabetic Retinopathy",
            "status": "Stable"
        },
        {
            "name": "Michael Brown",
            "age": 41,
            "gender": "Male",
            "bed": "105-B",
            "ward": "Emergency",
            "diagnosis": "Traumatic Laceration (Dehisced)",
            "medical_history": "No prior chronic illness",
            "status": "Stable"
        },
        {
            "name": "Susan Clark",
            "age": 79,
            "gender": "Female",
            "bed": "220-4",
            "ward": "Geriatric",
            "diagnosis": "Arterial Ulcer - Left Ankle",
            "medical_history": "Chronic Obstructive Pulmonary Disease (COPD), Atherosclerosis",
            "status": "Observation"
        },
        {
            "name": "Kevin Peterson",
            "age": 35,
            "gender": "Male",
            "bed": "401-2",
            "ward": "Burns Unit",
            "diagnosis": "Partial Thickness Burn - Right Leg",
            "medical_history": "Asthma",
            "status": "Stable"
        }
    ]

    for p_data in more_patients:
        # Check if already exists by name to avoid duplicates if re-run
        if not Patient.objects.filter(name=p_data['name']).exists():
            # Calculate a dummy DOB based on age
            dob = date.today() - timedelta(days=p_data['age'] * 365 + random.randint(0, 365))
            
            p = Patient(
                name=p_data['name'],
                age=p_data['age'],
                gender=p_data['gender'],
                date_of_birth=dob,
                bed=p_data['bed'],
                ward=p_data['ward'],
                diagnosis=p_data['diagnosis'],
                medical_history=p_data['medical_history'],
                status=p_data['status']
            )
            # MRN will be auto-generated in save()
            p.save()
            print(f"Added patient: {p.name} with auto-MRN: {p.mrn}")
        else:
            print(f"Patient {p_data['name']} already exists, skipping.")

    print(f"Seeding complete. Total patients: {Patient.objects.count()}")

if __name__ == "__main__":
    seed_patients()
