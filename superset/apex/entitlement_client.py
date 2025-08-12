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

"""Entitlement service client for Apex integration."""

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import requests
from flask import current_app

logger = logging.getLogger(__name__)


@dataclass
class UserEntitlements:
    """User entitlements data structure."""
    user_id: str
    roles: List[str]
    permissions: Dict[str, Dict[str, List[str]]]
    row_level_filters: Dict[str, Any]
    cache_ttl: int = 300


class EntitlementServiceClient:
    """
    Client for communicating with Apex Entitlement Service.
    
    Handles fetching user permissions, roles, and hierarchical access controls.
    """
    
    def __init__(self, base_url: str = None, api_key: str = None, timeout: int = 30):
        """
        Initialize the entitlement service client.
        
        Args:
            base_url: Base URL for the entitlement service
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or current_app.config.get('ENTITLEMENT_SERVICE_BASE_URL')
        self.api_key = api_key or current_app.config.get('ENTITLEMENT_SERVICE_API_KEY')
        self.timeout = timeout
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def fetch_user_entitlements(self, user_id: str) -> Optional[UserEntitlements]:
        """
        Fetch user entitlements from the service.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserEntitlements object if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/entitlements"
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            return UserEntitlements(
                user_id=data['user_id'],
                roles=data.get('roles', []),
                permissions=data.get('permissions', {}),
                row_level_filters=data.get('row_level_filters', {}),
                cache_ttl=data.get('cache_ttl', 300)
            )
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch entitlements for user {user_id}: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid entitlement response for user {user_id}: {e}")
            return None
    
    def fetch_role_permissions(self, role_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch role permissions from the service.
        
        Args:
            role_name: Role name
            
        Returns:
            Role permissions dict if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/roles/{role_name}/permissions"
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch role permissions for {role_name}: {e}")
            return None
    
    def check_permission(self, user_id: str, resource_type: str, resource_id: str, action: str) -> bool:
        """
        Check if user has permission for a specific action on a resource.
        
        Args:
            user_id: User identifier
            resource_type: Type of resource (dashboard, chart, dataset)
            resource_id: Resource identifier
            action: Action to check (create, read, update, delete)
            
        Returns:
            True if permission granted, False otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/permissions/check"
            
            payload = {
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action
            }
            
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get('allowed', False)
            
        except requests.RequestException as e:
            logger.error(f"Failed to check permission for user {user_id}: {e}")
            return False
    
    def bulk_check_permissions(self, user_id: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check permissions for multiple resources at once.
        
        Args:
            user_id: User identifier
            resources: List of resource permission checks
            
        Returns:
            Bulk permission check results
        """
        try:
            url = f"{self.base_url}/api/v1/permissions/bulk-check"
            
            payload = {
                'user_id': user_id,
                'resources': resources
            }
            
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to bulk check permissions for user {user_id}: {e}")
            return {'results': []}
    
    def validate_entitlement(self, user_id: str, resource_type: str, resource_id: str, 
                           action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate user entitlement with context and get effective filters.
        
        Args:
            user_id: User identifier
            resource_type: Type of resource
            resource_id: Resource identifier
            action: Action to validate
            context: Additional context for validation
            
        Returns:
            Validation result with effective filters
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/entitlements/validate"
            
            payload = {
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action,
                'context': context or {}
            }
            
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to validate entitlement for user {user_id}: {e}")
            return {'allowed': False, 'reason': 'Service unavailable'}
    
    def get_hierarchies(self) -> List[Dict[str, Any]]:
        """
        Get all available hierarchies from the service.
        
        Returns:
            List of hierarchy definitions
        """
        try:
            url = f"{self.base_url}/api/v1/hierarchies"
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return data.get('hierarchies', [])
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch hierarchies: {e}")
            return []
    
    def get_hierarchy_children(self, hierarchy_name: str, parent_level: str, 
                             parent_values: List[str], child_level: str) -> List[str]:
        """
        Get children for parent values in a hierarchy.
        
        Args:
            hierarchy_name: Name of the hierarchy
            parent_level: Parent level name
            parent_values: List of parent values
            child_level: Child level name
            
        Returns:
            List of child values
        """
        try:
            # For multiple parent values, we'll make multiple requests and combine results
            all_children = set()
            
            for parent_value in parent_values:
                url = f"{self.base_url}/api/v1/hierarchies/{hierarchy_name}/lookup/{parent_level}/{parent_value}"
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                children = data.get('children', {}).get(child_level, [])
                all_children.update(children)
            
            return list(all_children)
            
        except requests.RequestException as e:
            logger.error(f"Failed to get hierarchy children: {e}")
            return []


# Global instance to be used throughout the application
entitlement_client = EntitlementServiceClient()


def init_entitlement_client(app):
    """Initialize the entitlement client with app configuration."""
    global entitlement_client
    
    base_url = app.config.get('ENTITLEMENT_SERVICE_BASE_URL')
    api_key = app.config.get('ENTITLEMENT_SERVICE_API_KEY')
    timeout = app.config.get('ENTITLEMENT_SERVICE_TIMEOUT', 30)
    
    if base_url and api_key:
        entitlement_client = EntitlementServiceClient(base_url, api_key, timeout)
        logger.info("Entitlement service client initialized")
    else:
        logger.warning("Entitlement service configuration missing") 