from rest_framework import serializers
from .models import Patient, Alert, Wound, WoundAssessment, Task, ClinicalRecord

class ClinicalRecordSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    nurse_name = serializers.ReadOnlyField(source='recorded_by.name')

    class Meta:
        model = ClinicalRecord
        fields = [
            'id', 'patient', 'patient_name', 'recorded_by', 'nurse_name',
            'heart_rate', 'respiratory_rate', 'oxygen_saturation', 
            'nurse_notes', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'recorded_at']

class WoundAssessmentSerializer(serializers.ModelSerializer):
    nurse_name = serializers.ReadOnlyField(source='nurse.name')
    wound_location = serializers.ReadOnlyField(source='wound.location')
    patient_name = serializers.ReadOnlyField(source='wound.patient.name')

    class Meta:
        model = WoundAssessment
        fields = [
            'id', 'wound', 'wound_location', 'patient_name', 
            'nurse', 'nurse_name', 'image', 'width', 'depth', 
            'stage', 'notes', 'is_escalated', 'created_at'
        ]
        read_only_fields = ['id', 'nurse', 'created_at', 'is_escalated']

class WoundSerializer(serializers.ModelSerializer):
    assessments = WoundAssessmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Wound
        fields = ['id', 'patient', 'location', 'created_at', 'assessments']
        read_only_fields = ['id']

class PatientSerializer(serializers.ModelSerializer):
    clinical_history = ClinicalRecordSerializer(source='clinical_records', many=True, read_only=True)
    wounds = WoundSerializer(many=True, read_only=True)
    physician_name = serializers.ReadOnlyField(source='assigned_physician.name')
    
    class Meta:
        model = Patient
        fields = [
            'id', 'name', 'mrn', 'age', 'gender', 'date_of_birth', 
            'bed', 'ward', 'assigned_physician', 'physician_name', 
            'diagnosis', 'medical_history', 'admission_date', 
            'clinical_history', 'wounds'
        ]
        read_only_fields = ['id', 'mrn']

class TaskSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    assigned_to_name = serializers.ReadOnlyField(source='assigned_to.name')

    class Meta:
        model = Task
        fields = [
            'id', 'patient', 'patient_name', 'assigned_to', 
            'assigned_to_name', 'title', 'description', 'due_time', 'priority', 
            'status', 'is_completed', 'completed_at', 'assigned_at'
        ]
        read_only_fields = ['id', 'assigned_at']

class AlertSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    patient_mrn = serializers.ReadOnlyField(source='patient.mrn')
    triggered_by_name = serializers.ReadOnlyField(source='triggered_by.name')
    
    class Meta:
        model = Alert
        fields = [
            'id', 'patient', 'patient_name', 'patient_mrn', 'assessment',
            'triggered_by', 'triggered_by_name', 'alert_type', 'description', 
            'severity', 'timestamp', 'is_dismissed', 'is_resolved', 'resolved_at'
        ]
        read_only_fields = ['id', 'timestamp', 'is_dismissed', 'is_resolved', 'resolved_at']
