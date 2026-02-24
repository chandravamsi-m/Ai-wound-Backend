from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView as BaseTokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.db import models
from .models import User, SystemLog
from clinical.models import Alert
from .serializers import UserSerializer, SystemLogSerializer, CustomTokenObtainPairSerializer, ChangePasswordSerializer
from .permissions import IsAdmin, IsAdminOrDoctor
from .utils import get_storage_metrics, get_database_size, log_system_event, get_client_ip, get_uptime, format_activity_status, format_size_smart
from django.utils import timezone
from datetime import timedelta
from core.firestore_service import FirestoreService
from django.contrib.auth.hashers import check_password

class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        users_docs = FirestoreService.collection('users').stream()
        users = []
        for doc in users_docs:
            user_data = doc.to_dict() | {'id': doc.id}
            # Use the dedicated last_activity field from the user document
            user_data['activity'] = format_activity_status(user_data.get('last_activity'))
            users.append(user_data)
            
        return Response(users)

    def retrieve(self, request, pk=None):
        user = FirestoreService.get_document('users', pk)
        if user:
            return Response(user | {'id': pk})
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        try:
            if request.user.role != 'Admin':
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
            data = dict(request.data) # Convert to real dict if it's a QueryDict
            # Flatten lists if it was a QueryDict
            for k, v in data.items():
                if isinstance(v, list) and len(v) == 1:
                    data[k] = v[0]

            # Hash password if provided
            if 'password' in data:
                from django.contrib.auth.hashers import make_password
                data['password'] = make_password(data['password'])
            
            # Ensure isActive is set based on status
            if 'isActive' not in data:
                data['isActive'] = (data.get('status') == 'ACTIVE')
            
            data['created_at'] = timezone.now().isoformat()
            user_id = FirestoreService.create_document('users', data)
            
            log_system_event(
                user=request.user,
                action=f"ADMIN_USER_CREATE: User {user_id} ({data.get('email')}) created with role {data.get('role')}",
                severity='Success',
                ip_address=get_client_ip(request)
            )
            return Response(data | {'id': user_id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return Response({"error": str(e), "traceback": traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        try:
            if request.user.role != 'Admin':
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
            # Protection: Prevent disabling your own account
            if str(pk) == str(request.user.id) and request.data.get('isActive') is False:
                return Response({"detail": "Security Protection: You cannot disable your own admin account."}, status=status.HTTP_400_BAD_REQUEST)

            data = request.data.copy()
            # Hash password if provided and not empty
            if data.get('password'):
                from django.contrib.auth.hashers import make_password
                data['password'] = make_password(data['password'])
            else:
                data.pop('password', None) # Don't update password if empty

            # 1. Update Firestore
            FirestoreService.update_document('users', pk, data)
            
            # 2. Sync to local SQLite (Auth Mirror)
            User.objects.filter(id=pk).update(**{k: v for k, v in data.items() if hasattr(User, k)})
            
            # 3. Fetch full updated document for frontend consistency
            updated_user = FirestoreService.get_document('users', pk)
            user_email = updated_user.get('email', pk)
            
            # Skip logging if it's an account deactivation to reduce noise
            if data.get('isActive') is not False:
                log_system_event(
                    user=request.user,
                    action=f"ADMIN_USER_UPDATE: User {user_email} updated.",
                    severity='Info',
                    ip_address=get_client_ip(request)
                )
            return Response(updated_user | {'id': pk})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        try:
            if request.user.role != 'Admin':
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
            # 0. Get user email before deletion for logging
            user_to_delete = FirestoreService.get_document('users', pk)
            user_email = user_to_delete.get('email', pk) if user_to_delete else pk

            # 1. Delete from Firestore
            FirestoreService.delete_document('users', pk)
            
            # 2. Delete from local SQLite
            User.objects.filter(id=pk).delete()
            
            log_system_event(
                user=request.user,
                action=f"ADMIN_USER_DELETE: User {user_email} deleted permanentely.",
                severity='Warning',
                ip_address=get_client_ip(request)
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SystemLogViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminOrDoctor]
    
    def list(self, request):
        docs = FirestoreService.collection('logs').order_by('timestamp', direction='DESCENDING').limit(150).stream()
        logs_list = []
        user_cache = {} # N+1 fix: Cache user details
        
        for doc in docs:
            log_data = doc.to_dict() | {'id': doc.id}
            
            # Enrich with user display name (Prefer Email as requested)
            u_id = log_data.get('user_id')
            u_email = log_data.get('user_email')
            
            if not u_id:
                log_data['user_name'] = 'System'
            elif u_email:
                # Use the stored email directly (very fast)
                log_data['user_name'] = u_email
            elif u_id in user_cache:
                log_data['user_name'] = user_cache[u_id]
            else:
                user_doc = FirestoreService.get_document('users', u_id)
                # Fallback to email if name is missing, else 'System'
                display_name = user_doc.get('email', user_doc.get('name', 'System')) if user_doc else 'System'
                user_cache[u_id] = display_name
                log_data['user_name'] = display_name
            
            logs_list.append(log_data)
            
        return Response(logs_list)

class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Firestore count aggregation (for small datasets, stream() is fine, for large use aggregation queries)
            users_docs = FirestoreService.collection('users').where('isActive', '==', True).stream()
            active_users = sum(1 for _ in users_docs)
            
            logs_docs = FirestoreService.collection('logs').stream()
            total_logs = sum(1 for _ in logs_docs)
            
            alerts_docs = FirestoreService.collection('alerts').where('is_dismissed', '==', False).stream()
            clinical_alerts = sum(1 for _ in alerts_docs)
            
            sec_alerts_docs = FirestoreService.collection('logs').where('severity', 'in', ['Error', 'Warning']).stream()
            security_alerts = sum(1 for _ in sec_alerts_docs)
            
            display_alerts = clinical_alerts + security_alerts
            
            security_status = "Healthy"
            if security_alerts > 10:
                security_status = "Critical"
            elif security_alerts > 0:
                security_status = "Action Required"

            # Real document counts for storage estimation
            patients_all = FirestoreService.collection('patients').stream()
            patient_count = sum(1 for _ in patients_all)
            
            assessments_all = FirestoreService.collection('assessments').stream()
            assessment_count = sum(1 for _ in assessments_all)
            
            logs_all = FirestoreService.collection('logs').stream()
            logs_count = sum(1 for _ in logs_all)
            
            # Estimating Firestore usage (Wound images are the main bulk)
            # Average assessment with base64 image: ~200KB
            est_clinical_gb = (assessment_count * 200) / (1024 * 1024) 
            # Average patient doc: ~1KB
            est_patient_gb = (patient_count * 1) / (1024 * 1024)
            # Average log: ~0.5KB
            est_log_gb = (logs_count * 0.5) / (1024 * 1024)
            
            db_stats = get_database_size()
            sq_size_gb = db_stats['size_gb']
            
            total_est_used_gb = est_clinical_gb + est_patient_gb + est_log_gb + sq_size_gb
            FREE_TIER_LIMIT = 1.0 # 1GB
            
            used_pct = round((total_est_used_gb / FREE_TIER_LIMIT) * 100, 2)

            storage_stats = {
                'used_percentage': used_pct,
                'patient_records_size': format_size_smart(est_patient_gb),
                'imaging_data_size': format_size_smart(est_clinical_gb),
                'free_space': format_size_smart(max(0, FREE_TIER_LIMIT - total_est_used_gb)),
                'total_capacity_tb': 0.001,
                'used_capacity_tb': round(total_est_used_gb / 1024, 6)
            }
            
            return Response({
                'active_users': active_users,
                'user_trend': "+5% healthy",
                'system_uptime': get_uptime(),
                'security_alerts': display_alerts,
                'security_status': security_status,
                'storage_stats': storage_stats
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Failed to fetch dashboard summary',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StorageStatsView(APIView):
    permission_classes = [IsAdminOrDoctor]
    
    def get(self, request):
        metrics = get_storage_metrics()
        
        # Get real counts for breakdown
        patient_count = sum(1 for _ in FirestoreService.collection('patients').stream())
        assessment_count = sum(1 for _ in FirestoreService.collection('assessments').stream())
        logs_count = sum(1 for _ in FirestoreService.collection('logs').stream())
        
        est_pat_mb = (patient_count * 1) / 1024
        est_img_mb = (assessment_count * 200) / 1024
        est_log_mb = (logs_count * 0.5) / 1024
        
        total_used_gb = metrics['used_capacity_gb'] + (est_pat_mb + est_img_mb + est_log_mb) / 1024
        
        data = {
            'total_capacity': metrics['total_capacity_gb'],
            'total_capacity_display': f"{metrics['total_capacity_gb']} GB",
            'used_capacity': round(total_used_gb, 4),
            'used_capacity_display': format_size_smart(total_used_gb),
            'used_percentage': round((total_used_gb / metrics['total_capacity_gb']) * 100, 2) if metrics['total_capacity_gb'] > 0 else 0,
            'database_usage_gb': metrics['used_capacity_gb'], # SQLite size
            'database_usage_display': format_size_smart(metrics['used_capacity_gb']),
            'database_percentage': round((metrics['used_capacity_gb'] / metrics['total_capacity_gb']) * 100, 1) if metrics['total_capacity_gb'] > 0 else 0,
            'file_storage_gb': round(est_img_mb / 1024, 4),
            'file_storage_display': format_size_smart(est_img_mb / 1024),
            'file_storage_percentage': round((est_img_mb / (metrics['total_capacity_gb'] * 1024)) * 100, 1),
            'breakdown': [
                {
                    'id': 1,
                    'category': 'Patient Profiles',
                    'description': f'{patient_count} Documents in Firestore',
                    'size': f"{round(est_pat_mb, 2)} MB",
                    'growth': '+0.0%',
                    'lastBackup': 'Real-time',
                    'status': 'SECURE',
                    'statusType': 'secure'
                },
                {
                    'id': 2,
                    'category': 'Wound Imaging',
                    'description': f'{assessment_count} Assessments with Images',
                    'size': f"{round(est_img_mb, 2)} MB",
                    'growth': '+0.0%',
                    'lastBackup': 'Real-time',
                    'status': 'SECURE',
                    'statusType': 'secure'
                },
                {
                    'id': 3,
                    'category': 'System Activity Logs',
                    'description': f'{logs_count} Audit Documents',
                    'size': f"{round(est_log_mb, 2)} MB",
                    'growth': 'Active',
                    'lastBackup': 'Instant',
                    'status': 'SECURE',
                    'statusType': 'secure'
                },
                {
                    'id': 4,
                    'category': 'Local Auth Cache',
                    'description': 'SQLite Mirror for Login Speed',
                    'size': f"{round(metrics['used_capacity_gb'] * 1024, 2)} MB",
                    'growth': 'Stable',
                    'lastBackup': 'Synced',
                    'status': 'HEALTHY',
                    'statusType': 'secure'
                }
            ]
        }
        return Response(data, status=status.HTTP_200_OK)

class CustomTokenObtainPairView(APIView):
    """
    Custom JWT login view with rate limiting and activity tracking.
    """
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='5/15m', method='POST', block=True))
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get user from Firestore
            users = FirestoreService.query('users', 'email', '==', email)
            
            if not users:
                # Removed logging for failed login attempts to reduce noise
                # log_system_event(...)
                return Response(
                    {'error': 'Invalid email or password'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user_data = users[0]
            user_id = user_data['id']
            
            # Check if user is active
            if not user_data.get('isActive', True):
                # Removed logging for deactivated account access to reduce noise
                # log_system_event(...)
                return Response(
                    {'error': 'Your account has been deactivated. Please contact administrator.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verify password using django's check_password on the hash from Firestore
            if not check_password(password, user_data['password']):
                # Removed logging for incorrect password attempts to reduce noise
                # log_system_event(...)
                return Response(
                    {'error': 'Invalid email or password'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # SELF-HEALING SYNC:
            # Check for email collisions (e.g., legacy numeric ID vs new Firestore UID)
            existing_email_user = User.objects.filter(email=user_data['email']).first()
            if existing_email_user and existing_email_user.id != user_id:
                existing_email_user.delete()
            
            local_user, created = User.objects.update_or_create(
                id=user_id,
                defaults={
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'role': user_data['role'],
                    'status': user_data.get('status', 'ACTIVE'),
                    'isActive': user_data.get('isActive', True),
                    'password': user_data['password']
                }
            )
            
            # Update last activity in Firestore
            FirestoreService.update_document('users', user_id, {
                'last_activity': timezone.now().isoformat()
            })
            
            # Generate JWT tokens using the local user object
            refresh = RefreshToken.for_user(local_user)
            refresh['email'] = user_data['email']
            refresh['role'] = user_data['role']
            refresh['name'] = user_data['name']
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user_id,
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'role': user_data['role'],
                    'status': user_data.get('status', 'ACTIVE'),
                    'isActive': user_data.get('isActive', True),
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Login error: {e}")
            return Response(
                {'error': 'An internal error occurred during login'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(APIView):
    """
    Logout view that blacklists the refresh token.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Removed redundant logout logging
            # log_system_event(...)
            
            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class CustomTokenRefreshView(BaseTokenRefreshView):
    """
    Custom token refresh view.
    """
    permission_classes = [AllowAny]


class ChangePasswordView(APIView):
    """
    Change password for authenticated user.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Verify old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': 'Old password is incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password in Django (Postgres)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Sync to Firestore
            from django.contrib.auth.hashers import make_password
            FirestoreService.update_document('users', user.id, {
                'password': make_password(serializer.validated_data['new_password'])
            })
            
            log_system_event(
                user=user,
                action="SECURITY_EVENT: Password changed successfully",
                severity='Success',
                ip_address=get_client_ip(request)
            )
            
            return Response(
                {'message': 'Password changed successfully'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Keep old LoginView for backward compatibility during migration
class LoginView(APIView):
    """
    Legacy login view - deprecated, use CustomTokenObtainPairView instead.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user is active
            if not user.isActive:
                return Response(
                    {'error': 'Your account has been disabled. Please contact administrator.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verify password
            if user.verify_password(password):
                # Update last activity
                user.update_activity()
                
                # Removed successful login logging to reduce noise
                # log_system_event(...)
                
                # Serialize user data (password won't be included due to write_only)
                serializer = UserSerializer(user)
                return Response({
                    'message': 'Login successful',
                    'user': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Log failed login attempt
                # log_system_event(...)
                return Response(
                    {'error': 'Invalid email or password'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
        except User.DoesNotExist:
            # Log failed login attempt (non-existent user)
            # log_system_event(...)
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
