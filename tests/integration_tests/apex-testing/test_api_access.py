#!/usr/bin/env python3
"""
Test script to demonstrate proper API access with JWT authentication.
This script shows how to:
1. Create a JWT token
2. Use it to access Superset APIs
3. Handle authentication properly
"""

import requests
import json
import sys
import os

# Add the superset directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

def test_api_access():
    """Test API access with proper authentication methods."""
    
    base_url = "http://localhost:8088"
    
    print("🧪 Testing Superset API Access\n")
    
    # Method 1: Test without authentication (should fail)
    print("1️⃣ Testing dashboard API without authentication:")
    try:
        response = requests.get(
            f"{base_url}/api/v1/dashboard/",
            headers={"accept": "application/json"},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   Error: {e}")
    
    print()
    
    # Method 2: Test login endpoint to get session
    print("2️⃣ Testing session-based login:")
    try:
        login_data = {
            "username": "admin",
            "password": "admin",
            "provider": "db"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/security/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token')
            if access_token:
                print(f"   ✅ Login successful, got access token")
                
                # Test API with access token
                print("\n3️⃣ Testing dashboard API with access token:")
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "accept": "application/json"
                }
                
                response = requests.get(
                    f"{base_url}/api/v1/dashboard/",
                    headers=headers,
                    timeout=5
                )
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    count = data.get('count', 0)
                    print(f"   ✅ Success! Found {count} dashboards")
                    
                    # Show first few dashboards
                    dashboards = data.get('result', [])
                    if dashboards:
                        print(f"   📊 Sample dashboards:")
                        for i, dashboard in enumerate(dashboards[:3]):
                            print(f"      {i+1}. {dashboard.get('dashboard_title', 'Untitled')}")
                else:
                    print(f"   ❌ Failed: {response.text}")
            else:
                print(f"   ❌ No access token in response")
        else:
            print(f"   ❌ Login failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   Error: {e}")
    
    print()
    
    # Method 3: Test JWT authentication (if available)
    print("4️⃣ Testing APEX JWT authentication:")
    try:
        # Try to import and use our JWT auth
        from superset.apex.jwt_auth import create_jwt_token
        
        # This would require proper Flask app context
        print("   📝 JWT auth module is available")
        print("   💡 To use JWT auth, you need:")
        print("      - Proper Flask application context")
        print("      - User ID or username")
        print("      - Configured JWT secret")
        
    except ImportError as e:
        print(f"   ⚠️  APEX JWT module not available: {e}")
    except Exception as e:
        print(f"   ⚠️  JWT auth requires app context: {e}")
    
    print()
    
    # Method 4: Test Swagger UI access
    print("5️⃣ Testing Swagger UI access:")
    try:
        response = requests.get(
            f"{base_url}/swagger/v1",
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Swagger UI is accessible")
            print("   💡 CORS issues in browser are common for localhost")
            print("   💡 Try using a proper HTTP client or Postman instead")
        else:
            print(f"   ❌ Swagger UI not accessible: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   Error: {e}")

def show_solutions():
    """Show solutions for common API access issues."""
    
    print("\n🔧 Solutions for API Access Issues:\n")
    
    print("🌐 CORS Issues in Browser:")
    print("   - CORS is a browser security feature")
    print("   - Swagger UI CORS issues are common for localhost")
    print("   - Solutions:")
    print("     • Use a proper HTTP client (Postman, Insomnia)")
    print("     • Use curl from command line")
    print("     • Use Python requests (like this script)")
    print("     • Configure CORS settings in superset_config.py")
    
    print("\n🔐 Authentication Methods:")
    print("   1. Session-based (traditional web login)")
    print("   2. JWT tokens (for API access)")
    print("   3. Bearer tokens from /api/v1/security/login")
    
    print("\n📝 Example CORS Configuration:")
    print("   Add to superset_config.py:")
    print("   ```python")
    print("   ENABLE_CORS = True")
    print("   CORS_OPTIONS = {")
    print("       'supports_credentials': True,")
    print("       'allow_headers': ['*'],")
    print("       'origins': ['http://localhost:8088']")
    print("   }")
    print("   ```")
    
    print("\n🚀 Recommended API Testing Tools:")
    print("   • Postman - GUI HTTP client")
    print("   • Insomnia - Modern API client") 
    print("   • curl - Command line tool")
    print("   • Python requests - Programmatic access")
    print("   • This test script - ./test_api_access.py")

if __name__ == "__main__":
    test_api_access()
    show_solutions() 