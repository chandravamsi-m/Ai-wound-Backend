import os
import sys
import django
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wound_analysis_backend.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def test_apis():
    client = Client()
    
    # Test Dashboard Summary
    print("Testing Dashboard Summary API...")
    url_summary = reverse('dashboard-summary')
    response_summary = client.get(url_summary)
    print(f"Status Code: {response_summary.status_code}")
    if response_summary.status_code == 200:
        print("Data:", json.dumps(response_summary.json(), indent=2))
    
    # Test Logs List
    print("\nTesting Logs API...")
    url_logs = '/api/logs/'  # Using direct path since viewset urls are dynamic
    response_logs = client.get(url_logs)
    print(f"Status Code: {response_logs.status_code}")
    if response_logs.status_code == 200:
        print(f"Count: {len(response_logs.json())}")
        print("First 2 logs:", json.dumps(response_logs.json()[:2], indent=2))

if __name__ == '__main__':
    test_apis()
