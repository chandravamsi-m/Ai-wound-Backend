from django.db import models
from django.conf import settings
from django.utils import timezone

class Patient(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    # Core identification
    name = models.CharField(max_length=100)
    mrn = models.CharField(max_length=50, unique=True, verbose_name="Medical Record Number", blank=True)
    
    # Demographic / Clinical details
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bed = models.CharField(max_length=20, null=True, blank=True)
    ward = models.CharField(max_length=50, null=True, blank=True)
    
    # Medical Context
    assigned_physician = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='patients_under_care'
    )
    assigned_nurse = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='patients_under_nurse_care'
    )
    diagnosis = models.TextField(null=True, blank=True)
    medical_history = models.TextField(null=True, blank=True)
    admission_date = models.DateTimeField(default=timezone.now)
    
    # [NEW] Contact & Clinical Details
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=20, blank=True, null=True)
    
    diabetes_type = models.CharField(max_length=100, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    blood_group = models.CharField(max_length=10, blank=True, null=True)

    STATUS_CHOICES = [
        ('Stable', 'Stable'),
        ('Observation', 'Observation'),
        ('Critical', 'Critical'),
        ('At Risk', 'At Risk'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Stable')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.mrn:
            # Sequential MRN generation (Stateless via Firestore lookup)
            from core.firestore_service import FirestoreService
            patients_count = len(list(FirestoreService.collection('patients').stream()))
            new_seq = patients_count + 1
            self.mrn = f"MRN{new_seq:04d}"
        
        super(Patient, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.mrn})"

class Wound(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    WOUND_TYPES = [
        ('Venous Ulcer', 'Venous Ulcer'),
        ('Pressure Ulcer', 'Pressure Ulcer'),
        ('Diabetic Foot', 'Diabetic Foot'),
        ('Surgical', 'Surgical'),
        ('Other', 'Other'),
    ]
    patient = models.ForeignKey(Patient, related_name='wounds', on_delete=models.CASCADE)
    location = models.CharField(max_length=200, default="General")
    wound_type = models.CharField(max_length=50, choices=WOUND_TYPES, default='Other')
    onset_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Wound for {self.patient.name}"

class WoundAssessment(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    wound = models.ForeignKey(Wound, related_name='assessments', on_delete=models.CASCADE)
    nurse = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    image = models.TextField(help_text="Base64 encoded image data") # Stores image directly in DB
    
    width = models.FloatField(help_text="Width in cm")
    depth = models.FloatField(help_text="Depth in cm")
    length = models.FloatField(null=True, blank=True, help_text="Length in cm")
    stage = models.CharField(max_length=50) # e.g. "Stage 2"
    
    exudate_amount = models.CharField(max_length=100, blank=True, null=True)
    pain_level = models.IntegerField(default=0)
    
    # AI/ML Analysis Results
    ml_analysis_result = models.JSONField(null=True, blank=True)
    cure_recommendation = models.TextField(blank=True, null=True)
    reduction_rate = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    healing_index = models.FloatField(null=True, blank=True)
    algorithm_analysis = models.JSONField(null=True, blank=True)

    notes = models.TextField(blank=True)
    is_escalated = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Assessment {self.id} for {self.wound.patient.name}"

class Task(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('MISSED', 'Missed'),
        ('CANCELLED', 'Cancelled')
    ]
    
    patient = models.ForeignKey(Patient, related_name='tasks', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assigned_tasks', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_time = models.CharField(max_length=10) # e.g., "14:00"
    priority = models.CharField(max_length=20, choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], default='medium')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"[{self.status}] {self.title} for {self.patient.name}"

class ClinicalRecord(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    patient = models.ForeignKey(Patient, related_name='clinical_records', on_delete=models.CASCADE)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Core Vitals
    heart_rate = models.IntegerField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    oxygen_saturation = models.IntegerField(null=True, blank=True)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    
    # Morphology
    weight = models.FloatField(null=True, blank=True) # in kg
    height = models.FloatField(null=True, blank=True) # in cm
    bmi = models.FloatField(null=True, blank=True)
    
    nurse_notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)

class Alert(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    PRIORITY_CHOICES = [
        ('Critical', 'Critical'),
        ('Warning', 'Warning'),
        ('Info', 'Info'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='alerts')
    assessment = models.ForeignKey(WoundAssessment, on_delete=models.CASCADE, null=True, blank=True)
    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    alert_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Info')
    
    timestamp = models.DateTimeField(default=timezone.now)
    is_dismissed = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.severity}: {self.alert_type} - {self.patient.name}"
