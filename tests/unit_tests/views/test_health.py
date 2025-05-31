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

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from contextlib import closing

from superset.views.health import HealthChecker
from superset.models.core import Database


class TestHealthChecker:
    """Test cases for HealthChecker class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_cache = Mock()
        self.health_checker = HealthChecker(
            db_session=self.mock_db_session,
            cache=self.mock_cache
        )

    def test_check_metadata_db_healthy(self):
        """Test metadata database health check when database is healthy"""
        # Arrange
        self.mock_db_session.execute.return_value = None

        # Act
        is_healthy, message = self.health_checker.check_metadata_db()

        # Assert
        assert is_healthy is True
        assert message == "Metadata database is healthy"
        self.mock_db_session.execute.assert_called_once_with("SELECT 1")

    def test_check_metadata_db_unhealthy(self):
        """Test metadata database health check when database is unhealthy"""
        # Arrange
        error_message = "Connection failed"
        self.mock_db_session.execute.side_effect = SQLAlchemyError(error_message)

        # Act
        is_healthy, message = self.health_checker.check_metadata_db()

        # Assert
        assert is_healthy is False
        assert "Metadata database error:" in message
        assert error_message in message

    def test_check_cache_healthy(self):
        """Test cache health check when cache is healthy"""
        # Arrange
        self.mock_cache.set.return_value = None
        self.mock_cache.get.return_value = "ok"

        # Act
        is_healthy, message = self.health_checker.check_cache()

        # Assert
        assert is_healthy is True
        assert message == "Cache system is healthy"
        self.mock_cache.set.assert_called_once_with("health_check", "ok", timeout=10)
        self.mock_cache.get.assert_called_once_with("health_check")

    def test_check_cache_not_responding(self):
        """Test cache health check when cache is not responding correctly"""
        # Arrange
        self.mock_cache.set.return_value = None
        self.mock_cache.get.return_value = "wrong_value"

        # Act
        is_healthy, message = self.health_checker.check_cache()

        # Assert
        assert is_healthy is False
        assert message == "Cache system is not responding correctly"

    def test_check_cache_exception(self):
        """Test cache health check when cache raises an exception"""
        # Arrange
        error_message = "Cache connection failed"
        self.mock_cache.set.side_effect = Exception(error_message)

        # Act
        is_healthy, message = self.health_checker.check_cache()

        # Assert
        assert is_healthy is False
        assert "Cache system error:" in message
        assert error_message in message

    def test_check_database_connections_all_healthy(self):
        """Test database connections check when all databases are healthy"""
        # Arrange
        mock_db1 = Mock(spec=Database)
        mock_db1.database_name = "db1"
        mock_db2 = Mock(spec=Database)
        mock_db2.database_name = "db2"
        
        self.mock_db_session.query.return_value.all.return_value = [mock_db1, mock_db2]
        
        # Mock engine and connection
        mock_engine = Mock()
        mock_engine.dialect.do_ping.return_value = True
        mock_connection = Mock()
        
        # Create proper context manager mocks
        mock_engine_context = Mock()
        mock_engine_context.__enter__ = Mock(return_value=mock_engine)
        mock_engine_context.__exit__ = Mock(return_value=None)
        
        mock_db1.get_sqla_engine.return_value = mock_engine_context
        mock_db2.get_sqla_engine.return_value = mock_engine_context
        
        with patch('superset.views.health.closing') as mock_closing:
            mock_closing.return_value.__enter__.return_value = mock_connection
            mock_closing.return_value.__exit__.return_value = None
            
            # Act
            results = self.health_checker.check_database_connections()

        # Assert
        assert len(results) == 2
        assert all(result["status"] == "healthy" for result in results)
        assert results[0]["name"] == "db1"
        assert results[1]["name"] == "db2"
        assert all(result["message"] == "Database is accessible" for result in results)

    def test_check_database_connections_some_unhealthy(self):
        """Test database connections check when some databases are unhealthy"""
        # Arrange
        mock_db1 = Mock(spec=Database)
        mock_db1.database_name = "healthy_db"
        mock_db2 = Mock(spec=Database)
        mock_db2.database_name = "unhealthy_db"
        
        self.mock_db_session.query.return_value.all.return_value = [mock_db1, mock_db2]
        
        # Mock engines
        mock_engine1 = Mock()
        mock_engine1.dialect.do_ping.return_value = True
        mock_engine2 = Mock()
        mock_engine2.dialect.do_ping.return_value = False
        
        mock_connection = Mock()
        
        # Create proper context manager mocks
        mock_engine_context1 = Mock()
        mock_engine_context1.__enter__ = Mock(return_value=mock_engine1)
        mock_engine_context1.__exit__ = Mock(return_value=None)
        
        mock_engine_context2 = Mock()
        mock_engine_context2.__enter__ = Mock(return_value=mock_engine2)
        mock_engine_context2.__exit__ = Mock(return_value=None)
        
        mock_db1.get_sqla_engine.return_value = mock_engine_context1
        mock_db2.get_sqla_engine.return_value = mock_engine_context2
        
        with patch('superset.views.health.closing') as mock_closing:
            mock_closing.return_value.__enter__.return_value = mock_connection
            mock_closing.return_value.__exit__.return_value = None
            
            # Act
            results = self.health_checker.check_database_connections()

        # Assert
        assert len(results) == 2
        assert results[0]["status"] == "healthy"
        assert results[0]["name"] == "healthy_db"
        assert results[1]["status"] == "unhealthy"
        assert results[1]["name"] == "unhealthy_db"
        assert results[1]["message"] == "Database is not responding"

    def test_check_database_connections_with_exception(self):
        """Test database connections check when an exception occurs"""
        # Arrange
        mock_db = Mock(spec=Database)
        mock_db.database_name = "error_db"
        
        self.mock_db_session.query.return_value.all.return_value = [mock_db]
        
        error_message = "Connection timeout"
        mock_db.get_sqla_engine.side_effect = Exception(error_message)
        
        # Act
        results = self.health_checker.check_database_connections()

        # Assert
        assert len(results) == 1
        assert results[0]["status"] == "unhealthy"
        assert results[0]["name"] == "error_db"
        assert f"Error: {error_message}" in results[0]["message"]

    def test_get_health_status_all_healthy(self):
        """Test get_health_status when all components are healthy"""
        # Arrange
        with patch.object(self.health_checker, 'check_metadata_db') as mock_metadata, \
             patch.object(self.health_checker, 'check_cache') as mock_cache, \
             patch.object(self.health_checker, 'check_database_connections') as mock_db_connections:
            
            mock_metadata.return_value = (True, "Metadata database is healthy")
            mock_cache.return_value = (True, "Cache system is healthy")
            mock_db_connections.return_value = [
                {"name": "db1", "status": "healthy", "message": "Database is accessible"}
            ]
            
            # Act
            response, status_code = self.health_checker.get_health_status(detailed=True)

        # Assert
        assert status_code == 200
        assert response["status"] == "healthy"
        assert response["components"]["metadata_database"]["status"] == "healthy"
        assert response["components"]["cache"]["status"] == "healthy"
        assert len(response["components"]["databases"]) == 1
        assert response["components"]["databases"][0]["status"] == "healthy"

    def test_get_health_status_metadata_db_unhealthy(self):
        """Test get_health_status when metadata database is unhealthy"""
        # Arrange
        with patch.object(self.health_checker, 'check_metadata_db') as mock_metadata, \
             patch.object(self.health_checker, 'check_cache') as mock_cache, \
             patch.object(self.health_checker, 'check_database_connections') as mock_db_connections:
            
            mock_metadata.return_value = (False, "Metadata database error")
            mock_cache.return_value = (True, "Cache system is healthy")
            mock_db_connections.return_value = [
                {"name": "db1", "status": "healthy", "message": "Database is accessible"}
            ]
            
            # Act
            response, status_code = self.health_checker.get_health_status(detailed=True)

        # Assert
        assert status_code == 503
        assert response["status"] == "unhealthy"
        assert response["components"]["metadata_database"]["status"] == "unhealthy"
        assert response["components"]["cache"]["status"] == "healthy"

    def test_get_health_status_cache_unhealthy(self):
        """Test get_health_status when cache is unhealthy"""
        # Arrange
        with patch.object(self.health_checker, 'check_metadata_db') as mock_metadata, \
             patch.object(self.health_checker, 'check_cache') as mock_cache, \
             patch.object(self.health_checker, 'check_database_connections') as mock_db_connections:
            
            mock_metadata.return_value = (True, "Metadata database is healthy")
            mock_cache.return_value = (False, "Cache system error")
            mock_db_connections.return_value = [
                {"name": "db1", "status": "healthy", "message": "Database is accessible"}
            ]
            
            # Act
            response, status_code = self.health_checker.get_health_status(detailed=True)

        # Assert
        assert status_code == 503
        assert response["status"] == "unhealthy"
        assert response["components"]["metadata_database"]["status"] == "healthy"
        assert response["components"]["cache"]["status"] == "unhealthy"

    def test_get_health_status_database_unhealthy(self):
        """Test get_health_status when a database is unhealthy"""
        # Arrange
        with patch.object(self.health_checker, 'check_metadata_db') as mock_metadata, \
             patch.object(self.health_checker, 'check_cache') as mock_cache, \
             patch.object(self.health_checker, 'check_database_connections') as mock_db_connections:
            
            mock_metadata.return_value = (True, "Metadata database is healthy")
            mock_cache.return_value = (True, "Cache system is healthy")
            mock_db_connections.return_value = [
                {"name": "db1", "status": "healthy", "message": "Database is accessible"},
                {"name": "db2", "status": "unhealthy", "message": "Database is not responding"}
            ]
            
            # Act
            response, status_code = self.health_checker.get_health_status(detailed=True)

        # Assert
        assert status_code == 503
        assert response["status"] == "unhealthy"
        assert response["components"]["metadata_database"]["status"] == "healthy"
        assert response["components"]["cache"]["status"] == "healthy"
        assert len(response["components"]["databases"]) == 2
        assert response["components"]["databases"][0]["status"] == "healthy"
        assert response["components"]["databases"][1]["status"] == "unhealthy"

    def test_get_health_status_basic_check_only(self):
        """Test get_health_status with detailed=False (basic check includes metadata DB and cache)"""
        # Arrange
        with patch.object(self.health_checker, 'check_metadata_db') as mock_metadata, \
             patch.object(self.health_checker, 'check_cache') as mock_cache, \
             patch.object(self.health_checker, 'check_database_connections') as mock_db_connections:
            
            mock_metadata.return_value = (True, "Metadata database is healthy")
            mock_cache.return_value = (True, "Cache system is healthy")
            
            # Act
            response, status_code = self.health_checker.get_health_status(detailed=False)

        # Assert
        assert status_code == 200
        assert response["status"] == "healthy"
        assert response["components"]["metadata_database"]["status"] == "healthy"
        assert response["components"]["cache"]["status"] == "healthy"
        assert response["components"]["databases"]["status"] == "skipped"
        assert "use ?detail=true" in response["components"]["databases"]["message"]
        
        # Verify that cache check was called (now part of basic check)
        mock_cache.assert_called_once()
        # Verify that database check was not called
        mock_db_connections.assert_not_called()

    def test_get_health_status_basic_check_metadata_unhealthy(self):
        """Test get_health_status with detailed=False when metadata DB is unhealthy"""
        # Arrange
        with patch.object(self.health_checker, 'check_metadata_db') as mock_metadata, \
             patch.object(self.health_checker, 'check_cache') as mock_cache, \
             patch.object(self.health_checker, 'check_database_connections') as mock_db_connections:
            
            mock_metadata.return_value = (False, "Metadata database connection failed")
            mock_cache.return_value = (True, "Cache system is healthy")
            
            # Act
            response, status_code = self.health_checker.get_health_status(detailed=False)

        # Assert
        assert status_code == 503
        assert response["status"] == "unhealthy"
        assert response["components"]["metadata_database"]["status"] == "unhealthy"
        assert response["components"]["cache"]["status"] == "healthy"
        assert response["components"]["databases"]["status"] == "skipped"
        
        # Verify that cache check was called (now part of basic check)
        mock_cache.assert_called_once()
        # Verify that database check was not called
        mock_db_connections.assert_not_called()

    def test_get_health_status_basic_check_cache_unhealthy(self):
        """Test get_health_status with detailed=False when cache is unhealthy"""
        # Arrange
        with patch.object(self.health_checker, 'check_metadata_db') as mock_metadata, \
             patch.object(self.health_checker, 'check_cache') as mock_cache, \
             patch.object(self.health_checker, 'check_database_connections') as mock_db_connections:
            
            mock_metadata.return_value = (True, "Metadata database is healthy")
            mock_cache.return_value = (False, "Cache system error")
            
            # Act
            response, status_code = self.health_checker.get_health_status(detailed=False)

        # Assert
        assert status_code == 503
        assert response["status"] == "unhealthy"
        assert response["components"]["metadata_database"]["status"] == "healthy"
        assert response["components"]["cache"]["status"] == "unhealthy"
        assert response["components"]["databases"]["status"] == "skipped"
        
        # Verify that cache check was called (now part of basic check)
        mock_cache.assert_called_once()
        # Verify that database check was not called
        mock_db_connections.assert_not_called()

    def test_health_checker_with_default_dependencies(self):
        """Test HealthChecker initialization with default dependencies"""
        # Act
        health_checker = HealthChecker()
        
        # Assert
        assert health_checker.db_session is not None
        assert health_checker.cache is not None 