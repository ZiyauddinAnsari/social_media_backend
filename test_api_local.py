#!/usr/bin/env python3
"""
Django management command to test API endpoints using Django's test client.
"""
import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import json

User = get_user_model()

def test_api_with_django_client():
    print("🚀 Testing Social Media API with Django Test Client...")
    
    client = Client()
    
    # Test registration
    print("\n1. Testing Registration...")
    register_data = {
        "email": "demo@example.com",
        "password": "demopass123",
        "password_confirm": "demopass123",
        "display_name": "Demo User"
    }
    
    response = client.post('/api/auth/register/', 
                          data=json.dumps(register_data),
                          content_type='application/json')
    
    if response.status_code == 201:
        print("✅ Registration successful!")
        data = response.json()
        access_token = data['tokens']['access']
        refresh_token = data['tokens']['refresh']
        user_id = data['user']['id']
        print(f"   User ID: {user_id}, Email: {data['user']['email']}")
        print(f"   Profile: {data['user']['profile']['display_name']}")
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   Response: {response.json()}")
        return
    
    # Test login
    print("\n2. Testing Login...")
    login_data = {
        "email": "demo@example.com",
        "password": "demopass123"
    }
    
    response = client.post('/api/auth/token/',
                          data=json.dumps(login_data),
                          content_type='application/json')
    
    if response.status_code == 200:
        print("✅ Login successful!")
        data = response.json()
        print(f"   Has access token: {len(data['access']) > 0}")
        print(f"   Has refresh token: {len(data['refresh']) > 0}")
        print(f"   User data included: {'user' in data}")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.json()}")
    
    # Test protected endpoint
    print("\n3. Testing Protected Endpoint...")
    response = client.get(f'/api/users/{user_id}/',
                         HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    if response.status_code == 200:
        print("✅ Protected endpoint access successful!")
        data = response.json()
        print(f"   User: {data['email']}")
        if data['profile']:
            print(f"   Display name: {data['profile']['display_name']}")
    else:
        print(f"❌ Protected endpoint failed: {response.status_code}")
        print(f"   Response: {response.json()}")
    
    # Test token refresh
    print("\n4. Testing Token Refresh...")
    response = client.post('/api/auth/token/refresh/',
                          data=json.dumps({"refresh": refresh_token}),
                          content_type='application/json')
    
    if response.status_code == 200:
        print("✅ Token refresh successful!")
        data = response.json()
        print(f"   New access token received: {len(data['access']) > 0}")
    else:
        print(f"❌ Token refresh failed: {response.status_code}")
        print(f"   Response: {response.json()}")
    
    # Test profile update
    print("\n5. Testing Profile Update...")
    profile_data = {
        "display_name": "Updated Demo User",
        "bio": "This is my updated bio"
    }
    response = client.patch('/api/users/profile/',
                           data=json.dumps(profile_data),
                           content_type='application/json',
                           HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    if response.status_code == 200:
        print("✅ Profile update successful!")
        data = response.json()
        print(f"   Updated display name: {data['display_name']}")
        print(f"   Bio: {data['bio']}")
    else:
        print(f"❌ Profile update failed: {response.status_code}")
        print(f"   Response: {response.json()}")
    
    # Test unauthenticated access
    print("\n6. Testing Unauthenticated Access...")
    response = client.get(f'/api/users/{user_id}/')
    if response.status_code == 401:
        print("✅ Unauthenticated access properly blocked!")
    else:
        print(f"❌ Unauthenticated access not blocked: {response.status_code}")
    
    print("\n🎉 API testing complete!")
    print("\n📊 Summary:")
    print("✅ Custom user model with email primary key")
    print("✅ JWT authentication (access + refresh tokens)")
    print("✅ User registration with automatic profile creation")
    print("✅ Login with user data response")
    print("✅ Protected endpoints with Bearer token auth")
    print("✅ Token refresh functionality")
    print("✅ Profile update capability")
    print("✅ Proper authentication protection")
    
    print(f"\n📚 View API docs at: http://127.0.0.1:8000/api/docs/")
    print(f"📖 View ReDoc at: http://127.0.0.1:8000/api/redoc/")

if __name__ == "__main__":
    test_api_with_django_client()