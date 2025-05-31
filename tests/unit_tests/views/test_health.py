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
from unittest.mock import Mock, patch

from superset.views.health import health


class TestHealthEndpointView:
    """Test cases for the health endpoint view function"""

    @patch('superset.views.health.HealthChecker')
    @patch('superset.views.health.request')
    @patch('superset.views.health.app')
    def test_health_endpoint_basic_call(self, mock_app, mock_request, mock_health_checker_class):
        """Test that the health endpoint properly calls HealthChecker with correct parameters"""
        # Arrange
        mock_request.args.get.return_value = 'false'
        mock_stats_logger = Mock()
        mock_app.config = {"STATS_LOGGER": mock_stats_logger}
        
        mock_health_checker = Mock()
        mock_health_checker.get_health_status.return_value = ({"status": "healthy"}, 200)
        mock_health_checker_class.return_value = mock_health_checker
        
        # Act
        result = health()
        
        # Assert
        mock_health_checker_class.assert_called_once()
        mock_health_checker.get_health_status.assert_called_once_with(detailed=False)
        mock_stats_logger.incr.assert_called_once_with("health")

    @patch('superset.views.health.HealthChecker')
    @patch('superset.views.health.request')
    @patch('superset.views.health.app')
    def test_health_endpoint_detailed_call(self, mock_app, mock_request, mock_health_checker_class):
        """Test that the health endpoint properly calls HealthChecker with detailed=True"""
        # Arrange
        mock_request.args.get.return_value = 'true'
        mock_stats_logger = Mock()
        mock_app.config = {"STATS_LOGGER": mock_stats_logger}
        
        mock_health_checker = Mock()
        mock_health_checker.get_health_status.return_value = ({"status": "healthy"}, 200)
        mock_health_checker_class.return_value = mock_health_checker
        
        # Act
        result = health()
        
        # Assert
        mock_health_checker_class.assert_called_once()
        mock_health_checker.get_health_status.assert_called_once_with(detailed=True)

    @patch('superset.views.health.HealthChecker')
    @patch('superset.views.health.request')
    @patch('superset.views.health.app')
    def test_health_endpoint_detail_parameter_variations(self, mock_app, mock_request, mock_health_checker_class):
        """Test different detail parameter values"""
        # Arrange
        mock_stats_logger = Mock()
        mock_app.config = {"STATS_LOGGER": mock_stats_logger}
        
        mock_health_checker = Mock()
        mock_health_checker.get_health_status.return_value = ({"status": "healthy"}, 200)
        mock_health_checker_class.return_value = mock_health_checker
        
        # Test values that should result in detailed=True
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'on']
        for value in true_values:
            mock_request.args.get.return_value = value
            mock_health_checker.reset_mock()
            
            # Act
            result = health()
            
            # Assert
            mock_health_checker.get_health_status.assert_called_once_with(detailed=True)

        # Test values that should result in detailed=False
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'off', '']
        for value in false_values:
            mock_request.args.get.return_value = value
            mock_health_checker.reset_mock()
            
            # Act
            result = health()
            
            # Assert
            mock_health_checker.get_health_status.assert_called_once_with(detailed=False) 