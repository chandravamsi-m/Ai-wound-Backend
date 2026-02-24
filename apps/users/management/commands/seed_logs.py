import os
import sys
import django
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wound_analysis_backend.settings')
django.setup()

from users.models import User, SystemLog

def seed_logs():
    # Clear existing logs
    SystemLog.objects.all().delete()
    
    # Get some users
    users = list(User.objects.all())
    admin = User.objects.filter(role='Admin').first()
    doctor = User.objects.filter(role='Doctor').first()
    
    # Sample IP addresses
    sample_ips = [
        '192.168.1.104',
        '45.22.100.12',
        '10.0.0.42',
        '192.168.1.55',
        None  # For system-generated logs
    ]
    
    # Sample log data
    logs_data = [
        {
            "user": admin,
            "action": "Updated user permissions for 'nurse_jade'",
            "severity": "Info",
            "ip_address": "192.168.1.104",
            "hours_ago": 2
        },
        {
            "user": doctor,
            "action": "Failed login attempt (3x)",
            "severity": "Warning",
            "ip_address": "45.22.100.12",
            "hours_ago": 4
        },
        {
            "user": None,
            "action": "Daily database backup completed",
            "severity": "Success",
            "ip_address": None,
            "hours_ago": 24
        },
        {
            "user": None,
            "action": "Critical: High latency detected in API Gateway",
            "severity": "Error",
            "ip_address": "10.0.0.42",
            "hours_ago": 36
        },
        {
            "user": admin,
            "action": "Exported patient record summary (MRN: 8821)",
            "severity": "Info",
            "ip_address": "192.168.1.55",
            "hours_ago": 48
        },
        {
            "user": doctor,
            "action": "Accessed patient medical records",
            "severity": "Info",
            "ip_address": "192.168.1.104",
            "hours_ago": 6
        },
        {
            "user": None,
            "action": "System maintenance scheduled",
            "severity": "Info",
            "ip_address": None,
            "hours_ago": 12
        },
        {
            "user": admin,
            "action": "User account created: new_nurse",
            "severity": "Success",
            "ip_address": "192.168.1.104",
            "hours_ago": 18
        }
    ]
    
    for item in logs_data:
        log = SystemLog.objects.create(
            user=item['user'],
            action=item['action'],
            severity=item['severity'],
            ip_address=item['ip_address']
        )
        # Override auto_now_add timestamp for historical data
        log.timestamp = datetime.now() - timedelta(hours=item['hours_ago'])
        log.save()
        
    print(f"Successfully seeded {len(logs_data)} system logs.")

if __name__ == '__main__':
    seed_logs()
