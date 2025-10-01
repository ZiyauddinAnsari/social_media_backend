#!/usr/bin/env python3
"""
Simple API test script to verify the authentication endpoints work correctly.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("🚀 Testing Social Media API...")
    
    # Test registration
    print("\n1. Testing Registration...")
    register_data = {
        "email": "demo@example.com",
        "password": "demopass123",
        "password_confirm": "demopass123",
        "display_name": "Demo User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register/", json=register_data)
        if response.status_code == 201:
            print("✅ Registration successful!")
            data = response.json()
            access_token = data['tokens']['access']
            refresh_token = data['tokens']['refresh']
            user_id = data['user']['id']
            print(f"   User ID: {user_id}, Email: {data['user']['email']}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the Django server is running at http://127.0.0.1:8000")
        return
    
    # Test login
    print("\n2. Testing Login...")
    login_data = {
        "email": "demo@example.com",
        "password": "demopass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token/", json=login_data)
    if response.status_code == 200:
        print("✅ Login successful!")
        data = response.json()
        print(f"   Access token length: {len(data['access'])}")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Test protected endpoint
    print("\n3. Testing Protected Endpoint...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/api/users/{user_id}/", headers=headers)
    if response.status_code == 200:
        print("✅ Protected endpoint access successful!")
        data = response.json()
        print(f"   User: {data['email']}")
        if data['profile']:
            print(f"   Display name: {data['profile']['display_name']}")
    else:
        print(f"❌ Protected endpoint failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Test token refresh
    print("\n4. Testing Token Refresh...")
    response = requests.post(f"{BASE_URL}/api/auth/token/refresh/", json={"refresh": refresh_token})
    if response.status_code == 200:
        print("✅ Token refresh successful!")
        data = response.json()
        print(f"   New access token length: {len(data['access'])}")
    else:
        print(f"❌ Token refresh failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Test profile update
    print("\n5. Testing Profile Update...")
    profile_data = {
        "display_name": "Updated Demo User",
        "bio": "This is my updated bio"
    }
    response = requests.patch(f"{BASE_URL}/api/users/profile/", json=profile_data, headers=headers)
    if response.status_code == 200:
        print("✅ Profile update successful!")
        data = response.json()
        print(f"   Updated display name: {data['display_name']}")
        print(f"   Bio: {data['bio']}")
    else:
        print(f"❌ Profile update failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    print("\n🎉 API testing complete!")
    print(f"\n📚 View API docs at: {BASE_URL}/api/docs/")
    print(f"📖 View ReDoc at: {BASE_URL}/api/redoc/")

if __name__ == "__main__":
    test_api()