import requests
import json

# Test JWT Login
url = "http://127.0.0.1:8000/api/auth/login/"
data = {
    "email": "chandravamsi@gmail.com",
    "password": "Vamsi123@"
}

print("Testing JWT Login Endpoint...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print("-" * 50)

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
    except:
        print(f"Response (raw): {response.text}")
    
    if response.status_code == 200:
        print("\n✅ JWT Login successful!")
        tokens = response_data
        if 'access' in tokens:
            print(f"\nAccess Token (first 50 chars): {tokens.get('access', '')[:50]}...")
            print(f"Refresh Token (first 50 chars): {tokens.get('refresh', '')[:50]}...")
        print(f"User: {tokens.get('user', {})}")
    else:
        print("\n❌ JWT Login failed!")
        print(f"Error details: {response_data}")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
