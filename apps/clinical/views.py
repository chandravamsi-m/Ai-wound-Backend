from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Patient, Alert, Wound, WoundAssessment, Task, ClinicalRecord
from .serializers import (
    PatientSerializer, AlertSerializer, WoundAssessmentSerializer, 
    WoundSerializer, TaskSerializer, ClinicalRecordSerializer
)
from core.firestore_service import FirestoreService
import random
import base64
import io
from PIL import Image

# --- Shared Viewsets ---

class PatientViewSet(viewsets.ModelViewSet):
    """
    Combined Patient Management.
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return []
            
        # For Firestore, we don't return a Django QuerySet. 
        # This will require updating the serializer or returning raw data.
        # For the sake of this migration, we will fetch data from Firestore.
        
        if self.request.query_params.get('all') == 'true':
            # Security Audit: Log if a Nurse accesses the full registry (Break-the-Glass)
            if hasattr(user, 'role') and user.role == 'Nurse':
                from users.utils import log_system_event, get_client_ip
                log_system_event(
                    user=user,
                    action="Accessed Global Patient Registry (Break-the-Glass Protocol)",
                    severity='Warning',
                    ip_address=get_client_ip(self.request)
                )
                
                # Create a formal Security Alert
                alert_data = {
                    'patient_id': 'SYSTEM',
                    'triggered_by_id': user.id,
                    'patient_name': 'Global Registry',
                    'alert_type': "Security Violation",
                    'description': f"Nurse {user.email} triggered Break-the-Glass protocol for global access.",
                    'severity': "Critical",
                    'timestamp': timezone.now().isoformat(),
                    'is_dismissed': False,
                    'is_resolved': False
                }
                FirestoreService.create_document('alerts', alert_data)
            
            docs = FirestoreService.collection('patients').stream()
            return [doc.to_dict() | {'id': doc.id} for doc in docs]

        # Nurses see patients assigned to them via tasks by default
        if user.role == 'Nurse':
            # This logic needs to be a bit more complex in Firestore (Join logic)
            # For now, we fetch all and filter in memory or via index if available
            tasks = FirestoreService.query('tasks', 'assigned_to_id', '==', user.id)
            patient_ids = list(set([t['patient_id'] for t in tasks]))
            patients = []
            for p_id in patient_ids:
                p = FirestoreService.get_document('patients', p_id)
                if p:
                    patients.append(p | {'id': p_id})
            return patients
        
        # Doctors and Admins see all
        docs = FirestoreService.collection('patients').stream()
        return [doc.to_dict() | {'id': doc.id} for doc in docs]

    def list(self, request, *args, **kwargs):
        # Override list to handle list of dicts instead of queryset
        queryset = self.get_queryset()
        return Response(queryset)

    def retrieve(self, request, *args, **kwargs):
        patient = FirestoreService.get_document('patients', kwargs['pk'])
        if patient:
            return Response(patient | {'id': kwargs['pk']})
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def perform_create(self, serializer):
        # Generate Firestore ID first so they match
        doc_ref = FirestoreService.collection('patients').document()
        firestore_id = doc_ref.id
        
        # Save the patient record with this ID
        patient = serializer.save(id=firestore_id)
        
        # Validation: Ensure MRN and name are present
        if not patient.name or not patient.mrn:
            return
            
        data = {
            'id': firestore_id,
            'name': patient.name,
            'mrn': patient.mrn,
            'age': patient.age,
            'gender': patient.gender,
            'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            'bed': patient.bed,
            'ward': patient.ward,
            'assigned_physician_id': patient.assigned_physician.id if patient.assigned_physician else None,
            'diagnosis': patient.diagnosis,
            'medical_history': patient.medical_history,
            'admission_date': patient.admission_date.isoformat(),
            'status': patient.status,
            'created_at': patient.created_at.isoformat(),
        }
        
        doc_ref.set(data)
        
        # Clinical Workflow: If a Nurse adds a patient, 
        # automatically assign an initial assessment task to them
        user = self.request.user
        from users.utils import log_system_event, get_client_ip
        log_system_event(
            user=user,
            action=f"PATIENT_INTAKE: {patient.name} ({patient.mrn}) admitted to {patient.ward} - Bed {patient.bed}",
            severity='Info',
            ip_address=get_client_ip(self.request)
        )
        
        if hasattr(user, 'role') and user.role == 'Nurse':
            # Format time as HH:MM string
            future_time = timezone.now() + timezone.timedelta(hours=2)
            time_str = future_time.strftime("%H:%M")
            
            task_data = {
                'patient_id': patient.id,
                'assigned_to_id': user.id,
                'title': "Initial Wound Assessment",
                'description': f"Auto-generated task for new patient intake: {patient.name}",
                'priority': 'Medium',
                'due_time': time_str,
                'status': 'PENDING',
                'assigned_at': timezone.now().isoformat()
            }
            FirestoreService.create_document('tasks', task_data)

class AlertViewSet(viewsets.ViewSet):
    def list(self, request):
        alerts_docs = FirestoreService.query('alerts', 'is_dismissed', '==', False)
        # Sort by timestamp descending
        alerts_docs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        patient_cache = {}
        for alert in alerts_docs:
            p_id = alert.get('patient_id')
            if not alert.get('patient_name') and p_id:
                if p_id in patient_cache:
                    p_data = patient_cache[p_id]
                else:
                    p_data = FirestoreService.get_document('patients', p_id)
                    patient_cache[p_id] = p_data
                
                if p_data:
                    alert['patient_name'] = p_data.get('name', 'Unknown')
                    alert['patient_mrn'] = p_data.get('mrn', 'Unknown')
                else:
                    alert['patient_name'] = 'System' # For system-level alerts without a patient
                    
        return Response(alerts_docs)

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        FirestoreService.update_document('alerts', pk, {'is_dismissed': True})
        return Response({'status': 'alert dismissed'})

# --- Doctor Specific Views ---
class DoctorDashboardSummaryView(APIView):
    def get(self, request):
        user_id = request.user.id
        
        # Get patients assigned to this doctor
        patients = FirestoreService.query('patients', 'assigned_physician_id', '==', user_id)
        active_count = len(patients)
        
        # Critical cases
        patient_ids = [p['id'] for p in patients]
        critical_cases = 0
        if patient_ids:
            # Firestore 'in' query supports up to 10 elements. For more, we might need multiple queries.
            # For simplicity, we filter in memory if patient_ids is large, or just fetch all active alerts.
            alerts = FirestoreService.query('alerts', 'severity', '==', 'Critical')
            critical_cases = sum(1 for a in alerts if a.get('patient_id') in patient_ids and not a.get('is_dismissed'))
        
        # Mocking healing rate for now as nested logic is complex in NoSQL
        healing_rate = "78%" if active_count > 0 else "0%"

        return Response({
            'active_patients': active_count,
            'active_patients_trend': '+5%' if active_count > 0 else '0%',
            'critical_cases': critical_cases,
            'critical_cases_trend': 'Stable',
            'healing_rate': healing_rate,
            'healing_rate_trend': '+2%',
            'avg_assessment_time': '4.2m',
            'avg_assessment_time_trend': '-10s',
            'greeting': f'Good Morning, Dr. {request.user.name.split()[-1]}',
            'status_message': f'You have {active_count} active patients and {critical_cases} critical notifications.',
            'my_patients': patients[:10]
        })

class DoctorDashboardStatsView(APIView):
    def get(self, request):
        user_id = request.user.id
        today = timezone.now().date().isoformat()
        
        patients = FirestoreService.query('patients', 'assigned_physician_id', '==', user_id)
        active_patients = len(patients)
        
        patient_ids = [p['id'] for p in patients]
        pending_tasks = 0
        scans = 0
        
        if patient_ids:
            tasks = FirestoreService.query('tasks', 'status', '==', 'PENDING')
            pending_tasks = sum(1 for t in tasks if t.get('patient_id') in patient_ids)
            
            assessments = FirestoreService.collection('assessments').stream()
            for a in assessments:
                data = a.to_dict()
                if data.get('patient_id') in patient_ids and data.get('created_at', '').startswith(today):
                    scans += 1

        return Response({
            'active_patients': active_patients,
            'pending_tasks': pending_tasks,
            'completed_today': 0, # Simpler to return 0 for now
            'scans': scans,
            'active_patients_trend': '+12%',
            'healing_rate': '84%',
            'greeting': f'Good Morning, Dr. {request.user.name}'
        })

class DoctorScheduledTasksView(APIView):
    def get(self, request):
        user_id = request.user.id
        # Get doctor's patients
        patients = FirestoreService.query('patients', 'assigned_physician_id', '==', user_id)
        patient_ids = [p['id'] for p in patients]
        
        if not patient_ids:
            return Response([])
            
        tasks = []
        all_tasks = FirestoreService.collection('tasks').stream()
        for doc in all_tasks:
            data = doc.to_dict()
            if data.get('patient_id') in patient_ids and data.get('status') == 'PENDING':
                patient = next((p for p in patients if p['id'] == data['patient_id']), None)
                tasks.append({
                    'id': doc.id,
                    'time': data.get('due_time'),
                    'title': data.get('title'),
                    'description': f"Patient: {patient.get('name') if patient else 'Unknown'} • Bed {patient.get('bed', 'N/A') if patient else 'N/A'}"
                })
        
        tasks.sort(key=lambda x: x['time'])
        return Response(tasks[:5])

class WoundStatsView(APIView):
    def get(self, request):
        user_id = request.user.id
        
        # Distribution
        wounds = FirestoreService.collection('wounds').stream()
        types_count = {}
        total = 0
        for w in wounds:
            # In a real app, we'd filter by doctor's patients first
            data = w.to_dict()
            total += 1
            w_type = data.get('wound_type', 'Other')
            types_count[w_type] = types_count.get(w_type, 0) + 1
            
        distribution = []
        for w_type, count in types_count.items():
            distribution.append({'category': w_type, 'percentage': round((count/total)*100)})
            
        if not distribution:
            distribution = [{'category': 'General', 'percentage': 100}]

        # Priority Cases
        alerts = FirestoreService.query('alerts', 'is_resolved', '==', False)
        priority_cases = []
        for a in alerts[:3]:
            patient = FirestoreService.get_document('patients', a.get('patient_id'))
            priority_cases.append({
                'id': a.get('id'),
                'patient_name': patient.get('name') if patient else "Unknown",
                'risk_level': 'HIGH RISK' if a.get('severity') == 'Critical' else 'MODERATE',
                'description': a.get('description')
            })

        return Response({
            'distribution': distribution,
            'healing_trend': [82, 85, 84, 88, 87, 89],
            'priority_cases': priority_cases
        })

class DoctorTaskViewSet(viewsets.ViewSet):
    def list(self, request):
        user_id = request.user.id
        # Get tasks for patients assigned to this doctor
        patients = FirestoreService.query('patients', 'assigned_physician_id', '==', user_id)
        patient_ids = [p['id'] for p in patients]
        
        if not patient_ids:
            return Response([])
            
        all_tasks = FirestoreService.collection('tasks').stream()
        doctor_tasks = []
        for doc in all_tasks:
            data = doc.to_dict()
            data['id'] = doc.id
            if data.get('patient_id') in patient_ids:
                doctor_tasks.append(data)
                
        return Response(doctor_tasks)

class AlertStatsView(APIView):
    def get(self, request):
        active_alerts = FirestoreService.query('alerts', 'is_dismissed', '==', False)
        total_active = len(active_alerts)
        
        critical_resolved = 0
        all_alerts = FirestoreService.collection('alerts').stream()
        for doc in all_alerts:
            data = doc.to_dict()
            if data.get('severity') == 'Critical' and data.get('is_resolved') == True:
                critical_resolved += 1

        return Response({
            'total_active': total_active,
            'avg_response_time': '42m',
            'critical_resolved': critical_resolved,
            'trend': '8% from yesterday'
        })

# --- Nurse Specific Views ---

class NurseDashboardStatsView(APIView):
    def get(self, request):
        user_id = request.user.id
        today = timezone.now().date().isoformat()
        
        # Fetching stats from Firestore
        tasks = FirestoreService.query('tasks', 'assigned_to_id', '==', user_id)
        doc_due = sum(1 for t in tasks if t.get('status') == 'PENDING')
        completed = sum(1 for t in tasks if t.get('status') == 'COMPLETED')
        
        patient_ids = list(set([t.get('patient_id') for t in tasks]))
        active_patients = len(patient_ids)
        
        scans = 0
        assessments = FirestoreService.collection('assessments').stream()
        for a in assessments:
            if a.to_dict().get('created_at', '').startswith(today):
                scans += 1

        return Response({
            'active_patients': active_patients,
            'doc_due': doc_due,
            'completed': completed,
            'scans': scans
        })

class NurseTaskViewSet(viewsets.ViewSet):
    def list(self, request):
        user_id = request.user.id
        tasks = FirestoreService.query('tasks', 'assigned_to_id', '==', user_id)
        return Response(tasks)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        update_data = {
            'status': 'COMPLETED',
            'is_completed': True,
            'completed_at': timezone.now().isoformat()
        }
        FirestoreService.update_document('tasks', pk, update_data)
        
        from users.utils import log_system_event, get_client_ip
        log_system_event(
            user=request.user,
            action=f"TASK_COMPLETED: Task {pk} marked as finished",
            severity='Success',
            ip_address=get_client_ip(request)
        )
        return Response({'status': 'task marked as completed'})

class NurseClinicalViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='upload-wound')
    def upload_wound(self, request):
        user_id = request.user.id
        patient_id = request.data.get('patient')
        image = request.FILES.get('image')
        notes = request.data.get('notes', '')
        
        # Check if patient exists in Firestore
        patient = FirestoreService.get_document('patients', patient_id)
        if not patient:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        # Advanced Image Processing Pipeline
        try:
            img = Image.open(image)
            max_size = (1200, 1200)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70, optimize=True)
            encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            base64_image_uri = f"data:image/jpeg;base64,{encoded_string}"
        except Exception as e:
            return Response({"error": f"Image processing failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Mock AI Analysis
        width = round(random.uniform(2.0, 10.0), 1)
        depth = round(random.uniform(0.5, 3.0), 1)
        stage = random.choice(['Stage 1', 'Stage 2', 'Stage 3'])
        
        # Save assessment to Firestore
        assessment_data = {
            'nurse_id': user_id,
            'patient_id': patient_id,
            'image': base64_image_uri,
            'notes': notes,
            'width': width,
            'depth': depth,
            'stage': stage,
            'is_escalated': stage in ['Stage 3', 'Stage 4', 'Unstageable'],
            'created_at': timezone.now().isoformat()
        }
        assessment_id = FirestoreService.create_document('assessments', assessment_data)
        
        # Audit Log for Wound Analysis
        from users.utils import log_system_event, get_client_ip
        log_system_event(
            user=request.user,
            action=f"WOUND_ANALYSIS: Patient {patient_id} assessment completed. Stage: {stage}, Dimensions: {width}x{depth}cm",
            severity='Warning' if assessment_data['is_escalated'] else 'Info',
            ip_address=get_client_ip(request)
        )
        
        # Handle Alerts in Firestore
        if assessment_data['is_escalated']:
            alert_data = {
                'patient_id': patient_id,
                'assessment_id': assessment_id,
                'triggered_by_id': user_id,
                'alert_type': "Critical Severity",
                'description': f"AI classified as {stage}. Immediate physician review required.",
                'severity': "Critical",
                'timestamp': timezone.now().isoformat(),
                'is_dismissed': False,
                'is_resolved': False
            }
            FirestoreService.create_document('alerts', alert_data)
        elif stage == 'Stage 2':
            alert_data = {
                'patient_id': patient_id,
                'assessment_id': assessment_id,
                'triggered_by_id': user_id,
                'alert_type': "Wound Progression Warning",
                'description': f"AI classified as {stage}. Monitoring frequency increase recommended.",
                'severity': "Warning",
                'timestamp': timezone.now().isoformat(),
                'is_dismissed': False,
                'is_resolved': False
            }
            FirestoreService.create_document('alerts', alert_data)

        return Response(assessment_data | {'id': assessment_id}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='record-vitals')
    def record_vitals(self, request):
        patient_id = request.data.get('patient')
        # Check if patient exists
        patient = FirestoreService.get_document('patients', patient_id)
        if not patient:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        data = {
            'patient_id': patient_id,
            'recorded_by_id': request.user.id,
            'heart_rate': request.data.get('heart_rate'),
            'respiratory_rate': request.data.get('respiratory_rate'),
            'oxygen_saturation': request.data.get('oxygen_saturation'),
            'perfusion_index': request.data.get('perfusion_index'), # New potential field
            'nurse_notes': request.data.get('nurse_notes', ''),
            'recorded_at': timezone.now().isoformat()
        }
        
        # Basic validation
        if not data['heart_rate'] or not data['oxygen_saturation']:
            return Response({"error": "Missing vital signs data"}, status=status.HTTP_400_BAD_REQUEST)

        record_id = FirestoreService.create_document('clinical_records', data)
        
        from users.utils import log_system_event, get_client_ip
        log_system_event(
            user=request.user,
            action=f"VITALS_RECORDED: Vitals updated for {patient.get('name')} (HR: {data['heart_rate']}, SpO2: {data['oxygen_saturation']}%)",
            severity='Info',
            ip_address=get_client_ip(request)
        )
        
        return Response(data | {'id': record_id}, status=status.HTTP_201_CREATED)
