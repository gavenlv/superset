# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
from unittest.mock import patch

from tests.integration_tests.base_tests import SupersetTestCase


class TestHealthEndpoint(SupersetTestCase):
    """Integration tests for the health endpoint"""

    def test_health_endpoint_basic(self):
        """Test that the health endpoint returns a valid response (basic check includes metadata DB and cache)"""
        response = self.client.get("/health")
        
        # Should return a JSON response
        assert response.content_type == "application/json"
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Should have the expected structure
        assert "status" in data
        assert "components" in data
        assert "metadata_database" in data["components"]
        assert "cache" in data["components"]
        assert "databases" in data["components"]
        
        # Metadata database should have status and message
        assert "status" in data["components"]["metadata_database"]
        assert "message" in data["components"]["metadata_database"]
        
        # Cache should now be checked in basic mode (not skipped)
        assert "status" in data["components"]["cache"]
        assert "message" in data["components"]["cache"]
        assert data["components"]["cache"]["status"] != "skipped"
        
        # Databases should be skipped in basic check
        assert data["components"]["databases"]["status"] == "skipped"
        assert "use ?detail=true" in data["components"]["databases"]["message"]

    def test_health_endpoint_detailed(self):
        """Test that the health endpoint returns detailed response when requested"""
        response = self.client.get("/health?detail=true")
        
        # Should return a JSON response
        assert response.content_type == "application/json"
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Should have the expected structure
        assert "status" in data
        assert "components" in data
        assert "metadata_database" in data["components"]
        assert "cache" in data["components"]
        assert "databases" in data["components"]
        
        # Each component should have status and message
        assert "status" in data["components"]["metadata_database"]
        assert "message" in data["components"]["metadata_database"]
        assert "status" in data["components"]["cache"]
        assert "message" in data["components"]["cache"]
        
        # Cache should not be skipped in detailed check
        assert data["components"]["cache"]["status"] != "skipped"
        
        # Databases should be a list (may be empty if no databases configured)
        assert isinstance(data["components"]["databases"], list)

    def test_health_endpoint_detail_parameter_variations(self):
        """Test different ways to specify the detail parameter"""
        detail_values = ["true", "True", "TRUE", "1", "yes", "on"]
        
        for detail_value in detail_values:
            response = self.client.get(f"/health?detail={detail_value}")
            data = json.loads(response.data)
            
            # Should perform detailed check
            assert data["components"]["cache"]["status"] != "skipped"
            assert isinstance(data["components"]["databases"], list)

    def test_health_endpoint_detail_false_variations(self):
        """Test different ways to specify detail=false"""
        detail_values = ["false", "False", "FALSE", "0", "no", "off", ""]
        
        for detail_value in detail_values:
            response = self.client.get(f"/health?detail={detail_value}")
            data = json.loads(response.data)
            
            # Should perform basic check (metadata DB and cache, but not databases)
            assert data["components"]["cache"]["status"] != "skipped"
            assert data["components"]["databases"]["status"] == "skipped"

    def test_health_endpoint_aliases(self):
        """Test that all health endpoint aliases work"""
        endpoints = ["/health", "/healthcheck", "/ping"]
        
        for endpoint in endpoints:
            # Test basic check
            response = self.client.get(endpoint)
            assert response.status_code in [200, 503]  # Either healthy or unhealthy
            
            data = json.loads(response.data)
            assert "status" in data
            assert data["status"] in ["healthy", "unhealthy"]
            assert data["components"]["cache"]["status"] != "skipped"
            assert data["components"]["databases"]["status"] == "skipped"
            
            # Test detailed check
            response = self.client.get(f"{endpoint}?detail=true")
            assert response.status_code in [200, 503]
            
            data = json.loads(response.data)
            assert data["components"]["cache"]["status"] != "skipped"
            assert isinstance(data["components"]["databases"], list)

    def test_health_endpoint_with_database_error_detailed(self):
        """Test health endpoint when database connections fail (detailed check)"""
        with patch('superset.views.health.HealthChecker.check_database_connections') as mock_db_check:
            mock_db_check.return_value = [
                {
                    "name": "test_db",
                    "status": "unhealthy",
                    "message": "Connection failed"
                }
            ]
            
            response = self.client.get("/health?detail=true")
            data = json.loads(response.data)
            
            # Should return unhealthy status
            assert response.status_code == 503
            assert data["status"] == "unhealthy"
            assert len(data["components"]["databases"]) == 1
            assert data["components"]["databases"][0]["status"] == "unhealthy"

    def test_health_endpoint_with_cache_error_detailed(self):
        """Test health endpoint when cache fails (detailed check)"""
        with patch('superset.views.health.HealthChecker.check_cache') as mock_cache_check:
            mock_cache_check.return_value = (False, "Cache connection failed")
            
            response = self.client.get("/health?detail=true")
            data = json.loads(response.data)
            
            # Should return unhealthy status
            assert response.status_code == 503
            assert data["status"] == "unhealthy"
            assert data["components"]["cache"]["status"] == "unhealthy"
            assert "Cache connection failed" in data["components"]["cache"]["message"]

    def test_health_endpoint_with_metadata_db_error(self):
        """Test health endpoint when metadata database fails"""
        with patch('superset.views.health.HealthChecker.check_metadata_db') as mock_metadata_check:
            mock_metadata_check.return_value = (False, "Metadata database connection failed")
            
            # Test both basic and detailed checks
            for detail in ["", "?detail=true"]:
                response = self.client.get(f"/health{detail}")
                data = json.loads(response.data)
                
                # Should return unhealthy status in both cases
                assert response.status_code == 503
                assert data["status"] == "unhealthy"
                assert data["components"]["metadata_database"]["status"] == "unhealthy"
                assert "Metadata database connection failed" in data["components"]["metadata_database"]["message"]

    def test_health_endpoint_basic_vs_detailed_performance(self):
        """Test that basic check calls metadata DB and cache, but not database connections"""
        with patch('superset.views.health.HealthChecker.check_cache') as mock_cache_check, \
             patch('superset.views.health.HealthChecker.check_database_connections') as mock_db_check:
            
            # Basic check should call cache check but not database connections check
            response = self.client.get("/health")
            data = json.loads(response.data)
            
            mock_cache_check.assert_called_once()
            mock_db_check.assert_not_called()
            assert data["components"]["cache"]["status"] != "skipped"
            assert data["components"]["databases"]["status"] == "skipped"
            
            # Reset mocks
            mock_cache_check.reset_mock()
            mock_db_check.reset_mock()
            
            # Detailed check should call all checks
            response = self.client.get("/health?detail=true")
            data = json.loads(response.data)
            
            mock_cache_check.assert_called_once()
            mock_db_check.assert_called_once() 