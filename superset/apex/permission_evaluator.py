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

"""Permission evaluator for Apex integration."""

import logging
from typing import Any, Dict, List, Optional
from flask import current_app

from .entitlement_client import entitlement_client, UserEntitlements
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)


class ApexPermissionEvaluator:
    """
    Permission evaluator for CRUD operations on BI resources.
    
    Evaluates user permissions for dashboards, charts, and datasets
    with support for fine-grained CRUD actions.
    """
    
    def __init__(self, entitlement_client=None, cache_manager=None):
        self.entitlement_client = entitlement_client or globals()['entitlement_client']
        self.cache_manager = cache_manager or globals()['cache_manager']
    
    def can_access_dashboard(self, user_id: str, dashboard_id: str, action: str = "read") -> bool:
        """
        Check if user can access a dashboard with specific action.
        
        Args:
            user_id: User identifier
            dashboard_id: Dashboard identifier
            action: Action to check (create, read, update, delete)
            
        Returns:
            True if access granted, False otherwise
        """
        try:
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if not entitlements:
                return False
            
            dashboard_permissions = entitlements.permissions.get('dashboards', {}).get(dashboard_id, [])
            return action.lower() in [perm.lower() for perm in dashboard_permissions]
            
        except Exception as e:
            logger.error(f"Error checking dashboard access for user {user_id}: {e}")
            return False
    
    def can_access_chart(self, user_id: str, chart_id: str, action: str = "read") -> bool:
        """
        Check if user can access a chart with specific action.
        
        Args:
            user_id: User identifier
            chart_id: Chart identifier
            action: Action to check (create, read, update, delete)
            
        Returns:
            True if access granted, False otherwise
        """
        try:
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if not entitlements:
                return False
            
            chart_permissions = entitlements.permissions.get('charts', {}).get(chart_id, [])
            return action.lower() in [perm.lower() for perm in chart_permissions]
            
        except Exception as e:
            logger.error(f"Error checking chart access for user {user_id}: {e}")
            return False
    
    def can_access_dataset(self, user_id: str, dataset_id: str, action: str = "read") -> bool:
        """
        Check if user can access a dataset with specific action.
        
        Args:
            user_id: User identifier
            dataset_id: Dataset identifier
            action: Action to check (create, read, update, delete)
            
        Returns:
            True if access granted, False otherwise
        """
        try:
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if not entitlements:
                return False
            
            dataset_permissions = entitlements.permissions.get('datasets', {}).get(dataset_id, [])
            return action.lower() in [perm.lower() for perm in dataset_permissions]
            
        except Exception as e:
            logger.error(f"Error checking dataset access for user {user_id}: {e}")
            return False
    
    def check_crud_permission(self, user_id: str, resource_type: str, resource_id: str, action: str) -> bool:
        """
        Generic CRUD permission checker.
        
        Args:
            user_id: User identifier
            resource_type: Type of resource (dashboard, chart, dataset)
            resource_id: Resource identifier
            action: Action to check (create, read, update, delete)
            
        Returns:
            True if permission granted, False otherwise
        """
        try:
            resource_type = resource_type.lower()
            action = action.lower()
            
            if resource_type == "dashboard":
                return self.can_access_dashboard(user_id, resource_id, action)
            elif resource_type == "chart":
                return self.can_access_chart(user_id, resource_id, action)
            elif resource_type == "dataset":
                return self.can_access_dataset(user_id, resource_id, action)
            else:
                logger.warning(f"Unknown resource type: {resource_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking CRUD permission: {e}")
            return False
    
    def get_user_permissions(self, user_id: str, resource_type: str, resource_id: str) -> List[str]:
        """
        Get all permissions for a user on a specific resource.
        
        Args:
            user_id: User identifier
            resource_type: Type of resource
            resource_id: Resource identifier
            
        Returns:
            List of permitted actions
        """
        try:
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if not entitlements:
                return []
            
            resource_type = resource_type.lower()
            if resource_type in entitlements.permissions:
                return entitlements.permissions[resource_type].get(resource_id, [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return []
    
    def bulk_check_permissions(self, user_id: str, resources: List[Dict[str, Any]]) -> Dict[str, Dict[str, bool]]:
        """
        Check permissions for multiple resources at once.
        
        Args:
            user_id: User identifier
            resources: List of resource permission checks
            
        Returns:
            Dictionary mapping resource IDs to permission results
        """
        results = {}
        
        try:
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if not entitlements:
                # Return all false if no entitlements
                for resource in resources:
                    resource_id = resource.get('resource_id')
                    actions = resource.get('actions', [])
                    results[resource_id] = {action: False for action in actions}
                return results
            
            for resource in resources:
                resource_type = resource.get('resource_type', '').lower()
                resource_id = resource.get('resource_id')
                actions = resource.get('actions', [])
                
                if not resource_id:
                    continue
                
                resource_permissions = entitlements.permissions.get(resource_type, {}).get(resource_id, [])
                
                results[resource_id] = {}
                for action in actions:
                    results[resource_id][action] = action.lower() in [perm.lower() for perm in resource_permissions]
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk permission check: {e}")
            return results
    
    def get_row_level_filters(self, user_id: str, dataset_id: str = None) -> Dict[str, Any]:
        """
        Get row-level security filters for a user.
        
        Args:
            user_id: User identifier
            dataset_id: Optional dataset identifier for context
            
        Returns:
            Dictionary of RLS filters
        """
        try:
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if not entitlements:
                return {}
            
            return entitlements.row_level_filters
            
        except Exception as e:
            logger.error(f"Error getting RLS filters for user {user_id}: {e}")
            return {}
    
    def has_role(self, user_id: str, role_name: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            user_id: User identifier
            role_name: Role name to check
            
        Returns:
            True if user has the role, False otherwise
        """
        try:
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if not entitlements:
                return False
            
            return role_name in entitlements.roles
            
        except Exception as e:
            logger.error(f"Error checking role for user {user_id}: {e}")
            return False
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get all roles for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of role names
        """
        try:
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if not entitlements:
                return []
            
            return entitlements.roles
            
        except Exception as e:
            logger.error(f"Error getting roles for user {user_id}: {e}")
            return []
    
    def get_accessible_resources(self, user_id: str, resource_type: str, action: str = "read") -> List[str]:
        """
        Get all resources of a type that user can access with specified action.
        
        Args:
            user_id: User identifier
            resource_type: Type of resource
            action: Action to check
            
        Returns:
            List of accessible resource IDs
        """
        try:
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if not entitlements:
                return []
            
            resource_type = resource_type.lower()
            if resource_type not in entitlements.permissions:
                return []
            
            accessible_resources = []
            for resource_id, permissions in entitlements.permissions[resource_type].items():
                if action.lower() in [perm.lower() for perm in permissions]:
                    accessible_resources.append(resource_id)
            
            return accessible_resources
            
        except Exception as e:
            logger.error(f"Error getting accessible resources: {e}")
            return []
    
    def validate_permission_context(self, user_id: str, resource_type: str, resource_id: str, 
                                  action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate permission with additional context and get effective filters.
        
        Args:
            user_id: User identifier
            resource_type: Type of resource
            resource_id: Resource identifier
            action: Action to validate
            context: Additional validation context
            
        Returns:
            Validation result with effective filters
        """
        try:
            # Use entitlement service for context-aware validation
            result = self.entitlement_client.validate_entitlement(
                user_id, resource_type, resource_id, action, context
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating permission context: {e}")
            return {
                'allowed': False,
                'reason': 'Validation error',
                'effective_filters': {}
            }
    
    def check_hierarchical_access(self, user_id: str, hierarchy_name: str, 
                                level: str, value: str) -> bool:
        """
        Check if user has access to a specific value in a hierarchy.
        
        Args:
            user_id: User identifier
            hierarchy_name: Name of hierarchy
            level: Hierarchy level
            value: Value to check
            
        Returns:
            True if access granted, False otherwise
        """
        try:
            rls_filters = self.get_row_level_filters(user_id)
            
            if hierarchy_name not in rls_filters:
                return False
            
            hierarchy_data = rls_filters[hierarchy_name]
            user_access = hierarchy_data.get('user_access', {})
            
            return value in user_access.get(level, [])
            
        except Exception as e:
            logger.error(f"Error checking hierarchical access: {e}")
            return False


# Global permission evaluator instance
permission_evaluator = ApexPermissionEvaluator()


def get_permission_evaluator() -> ApexPermissionEvaluator:
    """Get the global permission evaluator instance."""
    return permission_evaluator


def check_user_permission(user_id: str, resource_type: str, resource_id: str, action: str) -> bool:
    """
    Helper function to check user permission.
    
    Args:
        user_id: User identifier
        resource_type: Type of resource
        resource_id: Resource identifier
        action: Action to check
        
    Returns:
        True if permission granted, False otherwise
    """
    return permission_evaluator.check_crud_permission(user_id, resource_type, resource_id, action)


def get_user_accessible_resources(user_id: str, resource_type: str, action: str = "read") -> List[str]:
    """
    Helper function to get accessible resources for a user.
    
    Args:
        user_id: User identifier
        resource_type: Type of resource
        action: Action to check
        
    Returns:
        List of accessible resource IDs
    """
    return permission_evaluator.get_accessible_resources(user_id, resource_type, action)


def init_permission_evaluator(app):
    """
    Initialize the permission evaluator.
    
    Args:
        app: Flask application instance
    """
    global permission_evaluator
    
    try:
        # Re-initialize with proper dependencies
        permission_evaluator = ApexPermissionEvaluator()
        logger.info("Permission evaluator initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize permission evaluator: {e}")


# Decorators for permission checking

def require_permission(resource_type: str, resource_id_param: str, action: str):
    """
    Decorator to require specific permission for a view.
    
    Args:
        resource_type: Type of resource
        resource_id_param: Parameter name containing resource ID
        action: Required action
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask import g, request, abort
            
            # Get user ID from session/context
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                abort(401, "User not authenticated")
            
            # Get resource ID from parameters
            resource_id = kwargs.get(resource_id_param) or request.args.get(resource_id_param)
            if not resource_id:
                abort(400, f"Missing {resource_id_param}")
            
            # Check permission
            if not check_user_permission(user_id, resource_type, resource_id, action):
                abort(403, f"Permission denied for {action} on {resource_type}")
            
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    
    return decorator


def require_role(role_name: str):
    """
    Decorator to require specific role for a view.
    
    Args:
        role_name: Required role name
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask import g, abort
            
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                abort(401, "User not authenticated")
            
            if not permission_evaluator.has_role(user_id, role_name):
                abort(403, f"Role {role_name} required")
            
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    
    return decorator 