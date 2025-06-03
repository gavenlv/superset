#!/usr/bin/env python3
"""
Test script for JWT authentication in Superset
"""

import requests
import json
import sys
from datetime import datetime


def test_jwt_authentication(base_url="http://localhost:8088", username="admin", password="admin"):
    """Test JWT authentication flow"""
    
    print("=== Superset JWT Authentication Test ===\n")
    
    # 1. Test login endpoint
    print("1. Testing login endpoint...")
    login_url = f"{base_url}/api/v1/security/login/"
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        login_response = requests.post(
            login_url,
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            print("✓ Login successful")
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")
            
            print(f"  Access token: {access_token[:50]}...")
            print(f"  Refresh token: {refresh_token[:50]}...")
            print(f"  Expires in: {expires_in} seconds")
        else:
            print(f"✗ Login failed: {login_response.status_code}")
            print(f"  Response: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Login error: {e}")
        return False
    
    # 2. Test API access with JWT token
    print("\n2. Testing API access with JWT token...")
    api_url = f"{base_url}/api/v1/dashboard/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        api_response = requests.get(api_url, headers=headers)
        
        if api_response.status_code in [200, 201]:
            print("✓ API access successful with JWT token")
            result = api_response.json()
            print(f"  Response status: {api_response.status_code}")
            print(f"  Response has 'result' key: {'result' in result}")
        else:
            print(f"✗ API access failed: {api_response.status_code}")
            print(f"  Response: {api_response.text}")
            
    except Exception as e:
        print(f"✗ API access error: {e}")
    
    # 3. Test refresh token endpoint
    print("\n3. Testing refresh token endpoint...")
    refresh_url = f"{base_url}/api/v1/security/refresh/"
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    try:
        refresh_response = requests.post(
            refresh_url,
            json=refresh_data,
            headers={"Content-Type": "application/json"}
        )
        
        if refresh_response.status_code == 200:
            print("✓ Token refresh successful")
            new_token_data = refresh_response.json()
            new_access_token = new_token_data.get("access_token")
            new_expires_in = new_token_data.get("expires_in")
            
            print(f"  New access token: {new_access_token[:50]}...")
            print(f"  New expires in: {new_expires_in} seconds")
        else:
            print(f"✗ Token refresh failed: {refresh_response.status_code}")
            print(f"  Response: {refresh_response.text}")
            
    except Exception as e:
        print(f"✗ Token refresh error: {e}")
    
    # 4. Test API access with new token
    print("\n4. Testing API access with refreshed token...")
    new_headers = {
        "Authorization": f"Bearer {new_access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        new_api_response = requests.get(api_url, headers=new_headers)
        
        if new_api_response.status_code in [200, 201]:
            print("✓ API access successful with refreshed JWT token")
            print(f"  Response status: {new_api_response.status_code}")
        else:
            print(f"✗ API access with refreshed token failed: {new_api_response.status_code}")
            print(f"  Response: {new_api_response.text}")
            
    except Exception as e:
        print(f"✗ API access with refreshed token error: {e}")
    
    print("\n=== Test Complete ===")
    return True


def test_invalid_token(base_url="http://localhost:8088"):
    """Test API access with invalid token"""
    
    print("\n=== Testing Invalid Token ===")
    
    api_url = f"{base_url}/api/v1/dashboard/"
    invalid_headers = {
        "Authorization": "Bearer invalid_token_here",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(api_url, headers=invalid_headers)
        
        if response.status_code == 401:
            print("✓ Invalid token correctly rejected (401)")
        else:
            print(f"✗ Invalid token handling unexpected: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Invalid token test error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test JWT authentication in Superset")
    parser.add_argument("--url", default="http://localhost:8088", help="Superset base URL")
    parser.add_argument("--username", default="admin", help="Username for login")
    parser.add_argument("--password", default="admin", help="Password for login")
    
    args = parser.parse_args()
    
    print(f"Testing JWT authentication on {args.url}")
    print(f"Using credentials: {args.username} / {'*' * len(args.password)}")
    
    # Run main test
    success = test_jwt_authentication(args.url, args.username, args.password)
    
    # Run invalid token test
    test_invalid_token(args.url)
    
    if success:
        print("\n🎉 JWT authentication implementation appears to be working!")
    else:
        print("\n❌ JWT authentication test failed. Check configuration and logs.")
        sys.exit(1) 