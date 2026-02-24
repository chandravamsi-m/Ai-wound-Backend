import shutil
import os
from django.db import connection
from .models import SystemLog
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# Record server start time
START_TIME = timezone.now()

def get_uptime():
    """
    Returns the server uptime as a human-readable string.
    """
    now = timezone.now()
    diff = now - START_TIME
    
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def format_size_smart(size_gb):
    """
    Formats a GB value into a human-readable string (MB or GB).
    """
    if size_gb < 0.1: # Less than 100MB
        mb = round(size_gb * 1024, 2)
        return f"{mb} MB"
    return f"{round(size_gb, 4)} GB"

def get_storage_metrics():
    """
    Returns application-specific storage metrics.
    Firestore Free Tier is 1 GiB.
    """
    # 1. Measure SQLite Mirror
    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    db_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    db_size_gb = db_size_bytes / (1024**3)
    
    # 2. Get Global Disk (for system health) - Optional but good for awareness
    try:
        total, used, free = shutil.disk_usage("/")
    except:
        total, used, free = 0, 0, 0
    
    # We set a "Virtual Limit" of 1GB for the Firestore Free Tier
    FREE_TIER_LIMIT_GB = 1.0
    
    return {
        'total_capacity_gb': FREE_TIER_LIMIT_GB,
        'used_capacity_gb': round(db_size_gb, 6), # High precision for calculations
        'used_capacity_formatted': format_size_smart(db_size_gb),
        'free_space_gb': round(max(0, FREE_TIER_LIMIT_GB - db_size_gb), 6),
        'used_percentage': round((db_size_gb / FREE_TIER_LIMIT_GB) * 100, 2) if FREE_TIER_LIMIT_GB > 0 else 0,
        'total_capacity_tb': 0.001,
        'used_capacity_tb': 0.0
    }

def get_database_size():
    """
    Returns the size of the local SQLite mirror.
    """
    try:
        from django.conf import settings
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            return {
                'size_bytes': size_bytes,
                'size_mb': round(size_bytes / (1024**2), 2),
                'size_gb': round(size_bytes / (1024**3), 4)
            }
    except Exception as e:
        print(f"Error calculating SQLite size: {e}")
    
    return {'size_bytes': 0, 'size_mb': 0, 'size_gb': 0}

def log_system_event(user, action, severity='Info', ip_address=None):
    """
    Helper to log system events to Firestore.
    """
    try:
        from core.firestore_service import FirestoreService
        data = {
            'user_id': user.id if user and hasattr(user, 'id') else (user.get('id') if isinstance(user, dict) else None),
            'user_email': user.email if user and hasattr(user, 'email') else (user.get('email') if isinstance(user, dict) else 'System'),
            'action': action,
            'severity': severity,
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat()
        }
        FirestoreService.create_document('logs', data)
    except Exception as e:
        print(f"Failed to log event: {e}")

def get_client_ip(request):
    """
    Extracts IP address from the request object.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def format_activity_status(last_activity_iso):
    """
    Converts an ISO timestamp to a human-readable activity string.
    """
    if not last_activity_iso:
        return "Never logged in"
    
    try:
        from datetime import datetime
        last_activity = datetime.fromisoformat(last_activity_iso.replace('Z', '+00:00'))
        now = timezone.now()
        
        # Ensure both are offset-aware if needed, but fromisoformat handles +00:00
        time_diff = now - last_activity
        
        if time_diff < timedelta(minutes=5):
            return "Active now"
        
        if time_diff < timedelta(hours=1):
            minutes = int(time_diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        
        if time_diff < timedelta(days=1):
            hours = int(time_diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        
        if time_diff < timedelta(days=7):
            days = time_diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
            
        return "Last seen: " + last_activity.strftime('%b %d')
    except Exception as e:
        print(f"Error formatting activity: {e}")
        return "Unknown"
