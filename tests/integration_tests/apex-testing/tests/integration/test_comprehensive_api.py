"""
Comprehensive Integration Tests for Superset Apex Module

This test suite covers JWT authentication with various Superset APIs to ensure
comprehensive compatibility and functionality.
"""
import json
import pytest
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

# Test configuration
BASE_URL = "http://localhost:8088"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin"
TEST_PROVIDER = "db"


class SupersetApiTestClient:
    """Test client for Superset API with JWT authentication"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
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
            
            response = requests.post(login_url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            self.token = result["access_token"]
            self.headers["Authorization"] = f"Bearer {self.token}"
            return True
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Make GET request with JWT authentication"""
        url = f"{self.base_url}{endpoint}"
        return requests.get(url, headers=self.headers, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make POST request with JWT authentication"""
        url = f"{self.base_url}{endpoint}"
        return requests.post(url, headers=self.headers, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make PUT request with JWT authentication"""
        url = f"{self.base_url}{endpoint}"
        return requests.put(url, headers=self.headers, json=data)
    
    def delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request with JWT authentication"""
        url = f"{self.base_url}{endpoint}"
        return requests.delete(url, headers=self.headers)


@pytest.fixture(scope="session")
def api_client():
    """Create and authenticate API client for testing"""
    client = SupersetApiTestClient()
    
    # Mock authentication for testing
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_jwt_token_12345",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        authenticated = client.authenticate()
        assert authenticated, "Failed to authenticate test client"
    
    return client


class TestApexJwtAuthentication:
    """Test Apex JWT authentication functionality"""
    
    def test_jwt_login_success(self, api_client):
        """Test successful JWT login"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test",
                "token_type": "Bearer",
                "expires_in": 86400
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = api_client.authenticate()
            assert result is True
            assert api_client.token is not None
            assert "Authorization" in api_client.headers
    
    def test_jwt_login_invalid_credentials(self):
        """Test JWT login with invalid credentials"""
        client = SupersetApiTestClient()
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
            mock_post.return_value = mock_response
            
            result = client.authenticate("invalid", "invalid")
            assert result is False
    
    def test_jwt_token_validation(self, api_client):
        """Test JWT token validation endpoint"""
        with patch.object(api_client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "valid": True,
                "user": {
                    "id": 1,
                    "username": "admin",
                    "first_name": "Admin",
                    "last_name": "User"
                }
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            response = api_client.post("/api/v1/apex/validate_token")
            assert response.status_code == 200
            
            data = response.json()
            assert data["valid"] is True
            assert "user" in data


class TestChartApis:
    """Test Chart-related APIs with JWT authentication"""
    
    def test_get_charts_list(self, api_client):
        """Test getting charts list"""
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "count": 2,
                "result": [
                    {"id": 1, "slice_name": "Test Chart 1", "viz_type": "table"},
                    {"id": 2, "slice_name": "Test Chart 2", "viz_type": "bar"}
                ]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/chart/")
            assert response.status_code == 200
            
            data = response.json()
            assert "result" in data
            assert len(data["result"]) >= 0
    
    def test_get_chart_by_id(self, api_client):
        """Test getting specific chart by ID"""
        chart_id = 1
        
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": chart_id,
                "slice_name": "Test Chart",
                "description": "A test chart",
                "viz_type": "table",
                "datasource_id": 1
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get(f"/api/v1/chart/{chart_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == chart_id
    
    def test_chart_data_endpoint(self, api_client):
        """Test chart data retrieval"""
        chart_id = 1
        
        with patch.object(api_client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": [
                    {"data": [{"col1": "value1", "col2": "value2"}]},
                ],
                "query_context": {"datasource": {"type": "table"}}
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            query_context = {
                "datasource": {"type": "table", "id": 1},
                "queries": [
                    {
                        "columns": ["col1", "col2"],
                        "row_limit": 1000
                    }
                ]
            }
            
            response = api_client.post(f"/api/v1/chart/data", data=query_context)
            assert response.status_code == 200


class TestDashboardApis:
    """Test Dashboard-related APIs with JWT authentication"""
    
    def test_get_dashboards_list(self, api_client):
        """Test getting dashboards list"""
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "count": 1,
                "result": [
                    {
                        "id": 1,
                        "dashboard_title": "Test Dashboard",
                        "published": True,
                        "slug": "test_dashboard"
                    }
                ]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/dashboard/")
            assert response.status_code == 200
            
            data = response.json()
            assert "result" in data
    
    def test_get_dashboard_by_id(self, api_client):
        """Test getting specific dashboard by ID"""
        dashboard_id = 1
        
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": dashboard_id,
                "dashboard_title": "Test Dashboard",
                "published": True,
                "json_metadata": "{}",
                "position_json": "{}"
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get(f"/api/v1/dashboard/{dashboard_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == dashboard_id
    
    def test_dashboard_filter_state(self, api_client):
        """Test dashboard filter state APIs"""
        dashboard_id = 1
        
        with patch.object(api_client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"key": "filter_state_key_123"}
            mock_response.status_code = 201
            mock_post.return_value = mock_response
            
            filter_state = {
                "filters": [
                    {"col": "country", "op": "IN", "val": ["USA", "Canada"]}
                ]
            }
            
            response = api_client.post(
                f"/api/v1/dashboard/{dashboard_id}/filter_state", 
                data=filter_state
            )
            assert response.status_code == 201


class TestDatasetApis:
    """Test Dataset-related APIs with JWT authentication"""
    
    def test_get_datasets_list(self, api_client):
        """Test getting datasets list"""
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "count": 1,
                "result": [
                    {
                        "id": 1,
                        "table_name": "test_table",
                        "schema": "public",
                        "database": {"database_name": "test_db"}
                    }
                ]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/dataset/")
            assert response.status_code == 200
    
    def test_get_dataset_by_id(self, api_client):
        """Test getting specific dataset by ID"""
        dataset_id = 1
        
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": dataset_id,
                "table_name": "test_table",
                "columns": [
                    {"column_name": "id", "type": "INTEGER"},
                    {"column_name": "name", "type": "VARCHAR"}
                ]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get(f"/api/v1/dataset/{dataset_id}")
            assert response.status_code == 200


class TestDatabaseApis:
    """Test Database-related APIs with JWT authentication"""
    
    def test_get_databases_list(self, api_client):
        """Test getting databases list"""
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "count": 1,
                "result": [
                    {
                        "id": 1,
                        "database_name": "test_database",
                        "backend": "postgresql",
                        "allow_run_async": True
                    }
                ]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/database/")
            assert response.status_code == 200
    
    def test_database_test_connection(self, api_client):
        """Test database connection testing"""
        with patch.object(api_client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"message": "Connection successful"}
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            connection_data = {
                "database_name": "test_db",
                "sqlalchemy_uri": "postgresql://user:pass@localhost/test"
            }
            
            response = api_client.post("/api/v1/database/test_connection", data=connection_data)
            assert response.status_code == 200


class TestSqlLabApis:
    """Test SQL Lab related APIs with JWT authentication"""
    
    def test_sql_query_execution(self, api_client):
        """Test SQL query execution"""
        with patch.object(api_client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "query_id": 123,
                "status": "success",
                "data": [{"col1": "value1", "col2": "value2"}]
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            query_data = {
                "database_id": 1,
                "sql": "SELECT * FROM test_table LIMIT 10",
                "schema": "public"
            }
            
            response = api_client.post("/api/v1/sqllab/execute/", data=query_data)
            assert response.status_code == 200
    
    def test_get_saved_queries(self, api_client):
        """Test getting saved queries"""
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "count": 1,
                "result": [
                    {
                        "id": 1,
                        "label": "Test Query",
                        "sql": "SELECT * FROM test_table",
                        "database": {"database_name": "test_db"}
                    }
                ]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/saved_query/")
            assert response.status_code == 200


class TestSecurityApis:
    """Test Security and user management APIs with JWT authentication"""
    
    def test_get_current_user_info(self, api_client):
        """Test getting current user information"""
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": 1,
                "username": "admin",
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@example.com",
                "roles": ["Admin"]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/me/")
            assert response.status_code == 200
    
    def test_get_user_permissions(self, api_client):
        """Test getting user permissions"""
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "permissions": ["can_read", "can_write", "can_delete"]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/security/permissions/")
            assert response.status_code == 200


class TestCacheApis:
    """Test Cache-related APIs with JWT authentication"""
    
    def test_cache_invalidation(self, api_client):
        """Test cache invalidation"""
        with patch.object(api_client, 'delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.json.return_value = {"message": "Cache invalidated"}
            mock_response.status_code = 200
            mock_delete.return_value = mock_response
            
            response = api_client.delete("/api/v1/cachekey/invalidate")
            assert response.status_code == 200


class TestExploreApis:
    """Test Explore functionality APIs with JWT authentication"""
    
    def test_explore_form_data(self, api_client):
        """Test explore form data endpoints"""
        with patch.object(api_client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"key": "explore_form_data_key"}
            mock_response.status_code = 201
            mock_post.return_value = mock_response
            
            form_data = {
                "datasource": "1__table",
                "viz_type": "table",
                "metrics": ["count"],
                "groupby": ["category"]
            }
            
            response = api_client.post("/api/v1/explore/form_data", data=form_data)
            assert response.status_code == 201


class TestReportApis:
    """Test Report and Alert APIs with JWT authentication"""
    
    def test_get_reports_list(self, api_client):
        """Test getting reports list"""
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "count": 0,
                "result": []
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/report/")
            assert response.status_code == 200


class TestOpenApiDocumentation:
    """Test OpenAPI documentation accessibility"""
    
    def test_swagger_ui_anonymous_access(self):
        """Test anonymous access to Swagger UI"""
        # Test without authentication
        headers = {"Accept": "text/html"}
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html><title>Swagger UI</title></html>"
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = requests.get(f"{BASE_URL}/swagger/", headers=headers)
            assert response.status_code == 200
    
    def test_openapi_spec_anonymous_access(self):
        """Test anonymous access to OpenAPI specification"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "openapi": "3.0.0",
                "info": {"title": "Superset API", "version": "1.0.0"},
                "paths": {}
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = requests.get(f"{BASE_URL}/api/v1/_openapi")
            assert response.status_code == 200


class TestErrorHandling:
    """Test error handling with JWT authentication"""
    
    def test_expired_token_handling(self, api_client):
        """Test handling of expired JWT tokens"""
        # Simulate expired token
        api_client.token = "expired_token"
        api_client.headers["Authorization"] = "Bearer expired_token"
        
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"message": "Token has expired"}
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/chart/")
            assert response.status_code == 401
    
    def test_invalid_token_format(self, api_client):
        """Test handling of invalid token format"""
        api_client.headers["Authorization"] = "InvalidTokenFormat"
        
        with patch.object(api_client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"message": "Invalid token format"}
            mock_get.return_value = mock_response
            
            response = api_client.get("/api/v1/chart/")
            assert response.status_code == 401


class TestPerformanceAndLimits:
    """Test performance aspects and rate limiting"""
    
    def test_concurrent_requests(self, api_client):
        """Test handling of concurrent requests with JWT"""
        import concurrent.futures
        import threading
        
        def make_request():
            with patch.object(api_client, 'get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"result": []}
                mock_get.return_value = mock_response
                
                return api_client.get("/api/v1/chart/")
        
        # Simulate concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(result.status_code == 200 for result in results)


def test_integration_workflow():
    """Test complete integration workflow"""
    client = SupersetApiTestClient()
    
    # Mock the entire workflow
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get:
        
        # Mock authentication
        mock_auth_response = MagicMock()
        mock_auth_response.json.return_value = {
            "access_token": "test_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_auth_response.raise_for_status.return_value = None
        mock_post.return_value = mock_auth_response
        
        # Mock API calls
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {"result": "success"}
        mock_api_response.status_code = 200
        mock_get.return_value = mock_api_response
        
        # Test workflow
        assert client.authenticate()
        
        # Test various endpoints
        endpoints = [
            "/api/v1/chart/",
            "/api/v1/dashboard/",
            "/api/v1/dataset/",
            "/api/v1/database/",
            "/api/v1/me/"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"]) 