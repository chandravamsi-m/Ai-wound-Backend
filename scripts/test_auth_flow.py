import requests
import json

# Test JWT authentication flow
base_url = "http://127.0.0.1:8000/api"

# Step 1: Login
print("Step 1: Logging in...")
login_response = requests.post(f"{base_url}/auth/login/", json={
    "email": "chandravamsi@gmail.com",
    "password": "Vamsi123@"
})

print(f"Login Status: {login_response.status_code}")
if login_response.status_code == 200:
    tokens = login_response.json()
    access_token = tokens['access']
    user = tokens['user']
    print(f"✅ Login successful!")
    print(f"User: {user['name']} ({user['role']})")
    print(f"Access Token (first 50 chars): {access_token[:50]}...")
    
    # Step 2: Test Dashboard Summary with token
    print("\nStep 2: Testing Dashboard Summary...")
    headers = {"Authorization": f"Bearer {access_token}"}
    dashboard_response = requests.get(f"{base_url}/dashboard/summary/", headers=headers)
    print(f"Dashboard Status: {dashboard_response.status_code}")
    if dashboard_response.status_code == 200:
        print("✅ Dashboard summary fetched successfully!")
        print(json.dumps(dashboard_response.json(), indent=2))
    else:
        print(f"❌ Dashboard error: {dashboard_response.text}")
    
    # Step 3: Test Logs with token
    print("\nStep 3: Testing Logs...")
    logs_response = requests.get(f"{base_url}/logs/", headers=headers)
    print(f"Logs Status: {logs_response.status_code}")
    if logs_response.status_code == 200:
        print("✅ Logs fetched successfully!")
        logs_data = logs_response.json()
        print(f"Total logs: {len(logs_data)}")
    else:
        print(f"❌ Logs error: {logs_response.text}")
else:
    print(f"❌ Login failed: {login_response.text}")
