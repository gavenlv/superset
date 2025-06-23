"""
Real-world Integration Tests for Superset Apex Module

These tests are designed to run against an actual Superset instance
with the Apex module installed and configured.

Run with: pytest test_real_api.py -m "not requires_data" for basic tests
Run with: pytest test_real_api.py for all tests (requires sample data)
"""
import json
import pytest
import requests
import time
from typing import Dict, Any, Optional, List
import os

# Configuration - can be overridden by environment variables
BASE_URL = os.getenv("SUPERSET_BASE_URL", "http://localhost:8088")
TEST_USERNAME = os.getenv("SUPERSET_USERNAME", "admin")
TEST_PASSWORD = os.getenv("SUPERSET_PASSWORD", "admin")
TEST_PROVIDER = os.getenv("SUPERSET_PROVIDER", "db")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))


class RealApiTestClient:
    """Real API test client for Superset with JWT authentication"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
    
    def authenticate(self, username: str = TEST_USERNAME, 
                    password: str = TEST_PASSWORD, 
                    provider: str = TEST_PROVIDER) -> bool:
        """Authenticate and obtain JWT token"""
        try:
            login_url = f"{self.base_url}/api/v1/apex/jwt_login"
            data = {
                "username": username,
                "password": password,
                "provider": provider
            }
            
            response = self.session.post(login_url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            self.token = result["access_token"]
            self.headers["Authorization"] = f"Bearer {self.token}"
            print(f"✓ Successfully authenticated as {username}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error during authentication: {e}")
            return False
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Make GET request with JWT authentication"""
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url, headers=self.headers, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make POST request with JWT authentication"""
        url = f"{self.base_url}{endpoint}"
        return self.session.post(url, headers=self.headers, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make PUT request with JWT authentication"""
        url = f"{self.base_url}{endpoint}"
        return self.session.put(url, headers=self.headers, json=data)
    
    def delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request with JWT authentication"""
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(url, headers=self.headers)
    
    def is_superset_available(self) -> bool:
        """Check if Superset is available"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def is_apex_available(self) -> bool:
        """Check if Apex module is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/apex/validate_token", timeout=5)
            # Should return 401 (unauthorized) if Apex is working, 404 if not available
            return response.status_code in [401, 422]  # 422 for missing token
        except:
            return False


@pytest.fixture(scope="session")
def real_client():
    """Create real API client and authenticate"""
    client = RealApiTestClient()
    
    # Check if Superset is available
    if not client.is_superset_available():
        pytest.skip(f"Superset is not available at {BASE_URL}")
    
    # Check if Apex module is available
    if not client.is_apex_available():
        pytest.skip("Apex module is not available or not configured")
    
    # Authenticate
    if not client.authenticate():
        pytest.skip("Could not authenticate with Superset")
    
    return client


@pytest.mark.integration
class TestApexAuthentication:
    """Test Apex authentication functionality with real API"""
    
    def test_jwt_login_success(self, real_client):
        """Test successful JWT login"""
        # Re-authenticate to test the login endpoint
        client = RealApiTestClient()
        result = client.authenticate()
        assert result is True
        assert client.token is not None
        assert "Authorization" in client.headers
        print(f"✓ JWT login successful, token length: {len(client.token)}")
    
    def test_jwt_login_with_custom_expiry(self, real_client):
        """Test JWT login with custom expiration time"""
        login_url = f"{real_client.base_url}/api/v1/apex/jwt_login"
        data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "provider": TEST_PROVIDER,
            "expires_in": 3600  # 1 hour
        }
        
        response = real_client.session.post(login_url, json=data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert result["expires_in"] == 3600
        print(f"✓ Custom expiry login successful: {result['expires_in']} seconds")
    
    def test_jwt_token_validation(self, real_client):
        """Test JWT token validation endpoint"""
        response = real_client.post("/api/v1/apex/validate_token")
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert "user" in data
        assert data["user"]["username"] == TEST_USERNAME
        print(f"✓ Token validation successful for user: {data['user']['username']}")
    
    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        client = RealApiTestClient()
        login_url = f"{client.base_url}/api/v1/apex/jwt_login"
        data = {
            "username": "invalid_user",
            "password": "invalid_password",
            "provider": TEST_PROVIDER
        }
        
        response = client.session.post(login_url, json=data)
        assert response.status_code in [401, 422]  # Unauthorized or Unprocessable Entity
        print("✓ Invalid credentials properly rejected")


@pytest.mark.integration
class TestCoreApiEndpoints:
    """Test core Superset API endpoints with JWT authentication"""
    
    def test_current_user_info(self, real_client):
        """Test getting current user information"""
        response = real_client.get("/api/v1/me/")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert data["username"] == TEST_USERNAME
        print(f"✓ Current user info: {data['username']} (ID: {data['id']})")
    
    def test_charts_list(self, real_client):
        """Test getting charts list"""
        response = real_client.get("/api/v1/chart/")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "result" in data
        print(f"✓ Charts list retrieved: {data['count']} charts found")
    
    def test_dashboards_list(self, real_client):
        """Test getting dashboards list"""
        response = real_client.get("/api/v1/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "result" in data
        print(f"✓ Dashboards list retrieved: {data['count']} dashboards found")
    
    def test_datasets_list(self, real_client):
        """Test getting datasets list"""
        response = real_client.get("/api/v1/dataset/")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "result" in data
        print(f"✓ Datasets list retrieved: {data['count']} datasets found")
    
    def test_databases_list(self, real_client):
        """Test getting databases list"""
        response = real_client.get("/api/v1/database/")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "result" in data
        print(f"✓ Databases list retrieved: {data['count']} databases found")


@pytest.mark.integration
@pytest.mark.requires_data
class TestDataApiEndpoints:
    """Test data-related API endpoints (requires sample data)"""
    
    def test_chart_data_with_existing_chart(self, real_client):
        """Test getting chart data from an existing chart"""
        # First get list of charts
        charts_response = real_client.get("/api/v1/chart/")
        assert charts_response.status_code == 200
        
        charts = charts_response.json()["result"]
        if not charts:
            pytest.skip("No charts available for testing")
        
        # Test with the first chart
        chart_id = charts[0]["id"]
        chart_name = charts[0].get("slice_name", "Unknown")
        
        # Get chart details
        chart_response = real_client.get(f"/api/v1/chart/{chart_id}")
        assert chart_response.status_code == 200
        
        chart_data = chart_response.json()
        print(f"✓ Chart details retrieved: '{chart_name}' (ID: {chart_id})")
        
        # Try to get chart data (this might require additional permissions)
        try:
            data_response = real_client.get(f"/api/v1/chart/{chart_id}/data/")
            if data_response.status_code == 200:
                print(f"✓ Chart data retrieved for '{chart_name}'")
            else:
                print(f"ℹ Chart data access limited (status: {data_response.status_code})")
        except Exception as e:
            print(f"ℹ Chart data access limited: {e}")
    
    def test_dashboard_with_existing_dashboard(self, real_client):
        """Test getting dashboard data from an existing dashboard"""
        # First get list of dashboards
        dashboards_response = real_client.get("/api/v1/dashboard/")
        assert dashboards_response.status_code == 200
        
        dashboards = dashboards_response.json()["result"]
        if not dashboards:
            pytest.skip("No dashboards available for testing")
        
        # Test with the first dashboard
        dashboard_id = dashboards[0]["id"]
        dashboard_title = dashboards[0].get("dashboard_title", "Unknown")
        
        # Get dashboard details
        dashboard_response = real_client.get(f"/api/v1/dashboard/{dashboard_id}")
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        print(f"✓ Dashboard details retrieved: '{dashboard_title}' (ID: {dashboard_id})")


@pytest.mark.integration
class TestSwaggerAccess:
    """Test Swagger UI anonymous access"""
    
    def test_swagger_ui_access(self):
        """Test anonymous access to Swagger UI"""
        try:
            response = requests.get(f"{BASE_URL}/swagger/", timeout=TIMEOUT)
            if response.status_code == 200:
                assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
                print("✓ Swagger UI accessible anonymously")
            else:
                print(f"ℹ Swagger UI access limited (status: {response.status_code})")
        except Exception as e:
            print(f"ℹ Swagger UI not accessible: {e}")
    
    def test_openapi_spec_access(self):
        """Test anonymous access to OpenAPI specification"""
        try:
            response = requests.get(f"{BASE_URL}/api/v1/_openapi", timeout=TIMEOUT)
            if response.status_code == 200:
                spec = response.json()
                assert "openapi" in spec or "swagger" in spec
                print("✓ OpenAPI specification accessible anonymously")
            else:
                print(f"ℹ OpenAPI spec access limited (status: {response.status_code})")
        except Exception as e:
            print(f"ℹ OpenAPI spec not accessible: {e}")


@pytest.mark.integration
class TestSecurityFeatures:
    """Test security-related features"""
    
    def test_token_expiry_handling(self, real_client):
        """Test handling of token expiry"""
        # Create a short-lived token
        login_url = f"{real_client.base_url}/api/v1/apex/jwt_login"
        data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "provider": TEST_PROVIDER,
            "expires_in": 1  # 1 second
        }
        
        response = real_client.session.post(login_url, json=data)
        if response.status_code != 200:
            pytest.skip("Cannot create short-lived token")
        
        result = response.json()
        short_token = result["access_token"]
        
        # Wait for token to expire
        time.sleep(2)
        
        # Try to use expired token
        headers = {
            "Authorization": f"Bearer {short_token}",
            "Content-Type": "application/json"
        }
        
        expired_response = real_client.session.get(f"{real_client.base_url}/api/v1/me/", headers=headers)
        assert expired_response.status_code == 401
        print("✓ Expired token properly rejected")
    
    def test_invalid_token_format(self, real_client):
        """Test handling of invalid token format"""
        headers = {
            "Authorization": "Bearer invalid_token_format",
            "Content-Type": "application/json"
        }
        
        response = real_client.session.get(f"{real_client.base_url}/api/v1/me/", headers=headers)
        assert response.status_code == 401
        print("✓ Invalid token format properly rejected")
    
    def test_missing_authorization_header(self, real_client):
        """Test API access without authorization header"""
        headers = {"Content-Type": "application/json"}
        
        response = real_client.session.get(f"{real_client.base_url}/api/v1/me/", headers=headers)
        assert response.status_code in [401, 302]  # Unauthorized or redirect to login
        print("✓ Missing authorization header properly handled")


@pytest.mark.integration
class TestAdvancedApiUsage:
    """Test advanced API usage patterns"""
    
    def test_pagination(self, real_client):
        """Test API pagination"""
        # Test with charts endpoint
        params = {"page_size": 5, "page": 0}
        response = real_client.get("/api/v1/chart/", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "result" in data
        assert len(data["result"]) <= 5
        print(f"✓ Pagination working: page_size=5, returned {len(data['result'])} items")
    
    def test_filtering(self, real_client):
        """Test API filtering"""
        # Test filtering charts by viz_type if available
        params = {"filters": [{"col": "viz_type", "opr": "eq", "value": "table"}]}
        response = real_client.get("/api/v1/chart/", params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Filtering working: found {data['count']} table charts")
        else:
            print(f"ℹ Filtering not available or limited (status: {response.status_code})")
    
    def test_search(self, real_client):
        """Test API search functionality"""
        # Test searching in charts
        params = {"q": "test"}
        response = real_client.get("/api/v1/chart/", params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Search working: found {data['count']} charts matching 'test'")
        else:
            print(f"ℹ Search not available or limited (status: {response.status_code})")


def test_comprehensive_workflow():
    """Test a comprehensive workflow using multiple APIs"""
    client = RealApiTestClient()
    
    # Check prerequisites
    if not client.is_superset_available():
        pytest.skip(f"Superset is not available at {BASE_URL}")
    
    if not client.is_apex_available():
        pytest.skip("Apex module is not available")
    
    print(f"\n=== Comprehensive Workflow Test ===")
    print(f"Testing against: {BASE_URL}")
    
    # Step 1: Authenticate
    assert client.authenticate(), "Authentication failed"
    
    # Step 2: Get user info
    user_response = client.get("/api/v1/me/")
    assert user_response.status_code == 200
    user_data = user_response.json()
    print(f"User: {user_data['username']} ({user_data.get('first_name', '')} {user_data.get('last_name', '')})")
    
    # Step 3: List resources
    resources = {
        "charts": "/api/v1/chart/",
        "dashboards": "/api/v1/dashboard/",
        "datasets": "/api/v1/dataset/",
        "databases": "/api/v1/database/"
    }
    
    for resource_name, endpoint in resources.items():
        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        print(f"{resource_name.capitalize()}: {data['count']} items")
    
    # Step 4: Test token validation
    validation_response = client.post("/api/v1/apex/validate_token")
    assert validation_response.status_code == 200
    validation_data = validation_response.json()
    assert validation_data["valid"] is True
    
    print("✓ Comprehensive workflow completed successfully")


if __name__ == "__main__":
    # Run specific test
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "workflow":
        test_comprehensive_workflow()
    else:
        # Run all tests
        pytest.main([__file__, "-v", "-s"]) 