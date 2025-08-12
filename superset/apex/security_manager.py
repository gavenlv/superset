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

"""Enhanced security manager for Apex integration."""

import logging
from typing import Any, Dict, List, Optional
from flask import current_app, g, request
from flask_appbuilder.security.sqla.manager import SecurityManager
from flask_appbuilder.security.sqla.models import User

from .jwt_auth import JwtHeaderAuthenticator
from .entitlement_client import entitlement_client
from .cache_manager import cache_manager
from .permission_evaluator import permission_evaluator
from .hierarchy_registry import get_hierarchy_registry
from .rls_builder import apply_rls_to_query

logger = logging.getLogger(__name__)


class ApexSecurityManager(SecurityManager):
    """
    Enhanced security manager with Apex entitlement integration.
    
    Extends Superset's security manager to integrate with:
    - Apex DSP for SSO authentication
    - Apex entitlement service for permissions
    - Dynamic hierarchy support for RLS
    - Multi-level caching for performance
    """
    
    def __init__(self, appbuilder):
        super().__init__(appbuilder)
        self.jwt_authenticator = JwtHeaderAuthenticator()
        self.entitlement_client = entitlement_client
        self.cache_manager = cache_manager
        self.permission_evaluator = permission_evaluator
        self.hierarchy_registry = get_hierarchy_registry()
        self._apex_config = current_app.config.get('APEX_CONFIG', {})
    
    def auth_user_jwt(self, token: str) -> Optional[User]:
        """
        Authenticate user via JWT token from Apex DSP.
        
        Args:
            token: JWT token from Apex DSP
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # Decode and validate JWT token
            payload = self.jwt_authenticator.decode_jwt_token(token)
            if not payload:
                return None
            
            # Extract user information from token
            user_info = {
                'user_id': payload.get('user_id') or payload.get('sub'),
                'username': payload.get('username') or payload.get('preferred_username'),
                'email': payload.get('email'),
                'first_name': payload.get('first_name') or payload.get('given_name'),
                'last_name': payload.get('last_name') or payload.get('family_name'),
                'roles': payload.get('roles', [])
            }
            
            if not user_info['user_id']:
                logger.error("No user_id in JWT token")
                return None
            
            # Get or create user
            user = self.get_or_create_apex_user(user_info)
            
            if user:
                # Fetch and cache user entitlements
                self._fetch_and_cache_entitlements(user_info['user_id'])
                
                # Set user context
                g.user_id = user_info['user_id']
                g.apex_user_info = user_info
            
            return user
            
        except Exception as e:
            logger.error(f"JWT authentication failed: {e}")
            return None
    
    def get_or_create_apex_user(self, user_info: Dict[str, Any]) -> Optional[User]:
        """
        Get or create user from Apex user information.
        
        Args:
            user_info: User information from Apex
            
        Returns:
            User object or None
        """
        try:
            username = user_info.get('username')
            email = user_info.get('email')
            
            if not username:
                logger.error("No username in user info")
                return None
            
            # Try to find existing user by username or email
            user = self.find_user(username=username)
            if not user and email:
                user = self.find_user(email=email)
            
            if user:
                # Update existing user if needed
                self._update_user_from_apex(user, user_info)
            else:
                # Create new user
                user = self._create_user_from_apex(user_info)
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to get/create user: {e}")
            return None
    
    def _update_user_from_apex(self, user: User, user_info: Dict[str, Any]) -> None:
        """Update existing user with Apex information."""
        try:
            updated = False
            
            # Update basic information
            if user_info.get('email') and user.email != user_info['email']:
                user.email = user_info['email']
                updated = True
            
            if user_info.get('first_name') and user.first_name != user_info['first_name']:
                user.first_name = user_info['first_name']
                updated = True
            
            if user_info.get('last_name') and user.last_name != user_info['last_name']:
                user.last_name = user_info['last_name']
                updated = True
            
            if updated:
                self.get_session.commit()
                logger.debug(f"Updated user {user.username}")
            
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            self.get_session.rollback()
    
    def _create_user_from_apex(self, user_info: Dict[str, Any]) -> Optional[User]:
        """Create new user from Apex information."""
        try:
            # Create user with minimal Superset role
            user = self.add_user(
                username=user_info['username'],
                first_name=user_info.get('first_name', ''),
                last_name=user_info.get('last_name', ''),
                email=user_info.get('email', ''),
                role=self.find_role('Public'),  # Minimal role, permissions come from Apex
                password='',  # No password needed for SSO users
            )
            
            if user:
                logger.info(f"Created new user {user.username}")
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def _fetch_and_cache_entitlements(self, user_id: str) -> None:
        """Fetch and cache user entitlements."""
        try:
            # This will use the cache manager to fetch/cache entitlements
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            if entitlements:
                logger.debug(f"Cached entitlements for user {user_id}")
            else:
                logger.warning(f"No entitlements found for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to fetch entitlements for user {user_id}: {e}")
    
    def has_access(self, permission_name: str, view_name: str, user: User = None) -> bool:
        """
        Override has_access to use Apex entitlements.
        
        Args:
            permission_name: Permission name (create, read, update, delete)
            view_name: View/resource name
            user: User object
            
        Returns:
            True if access granted, False otherwise
        """
        try:
            # Get current user if not provided
            if not user:
                user = g.user
            
            if not user:
                return False
            
            # Get user ID from context
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                return False
            
            # Map Superset view names to resource types
            resource_type = self._map_view_to_resource_type(view_name)
            if not resource_type:
                # Fallback to original Superset logic for unmapped views
                return super().has_access(permission_name, view_name, user)
            
            # For resource-level permissions, we need resource ID
            # This is a simplified check - real implementation would need resource context
            return self._check_general_resource_access(user_id, resource_type, permission_name)
            
        except Exception as e:
            logger.error(f"Error checking access: {e}")
            return False
    
    def can_access_dashboard(self, dashboard_id: str, action: str = "read", user: User = None) -> bool:
        """
        Check if user can access a specific dashboard.
        
        Args:
            dashboard_id: Dashboard identifier
            action: Action to check
            user: User object
            
        Returns:
            True if access granted, False otherwise
        """
        try:
            user_id = self._get_user_id(user)
            if not user_id:
                return False
            
            return self.permission_evaluator.can_access_dashboard(user_id, dashboard_id, action)
            
        except Exception as e:
            logger.error(f"Error checking dashboard access: {e}")
            return False
    
    def can_access_chart(self, chart_id: str, action: str = "read", user: User = None) -> bool:
        """
        Check if user can access a specific chart.
        
        Args:
            chart_id: Chart identifier
            action: Action to check
            user: User object
            
        Returns:
            True if access granted, False otherwise
        """
        try:
            user_id = self._get_user_id(user)
            if not user_id:
                return False
            
            return self.permission_evaluator.can_access_chart(user_id, chart_id, action)
            
        except Exception as e:
            logger.error(f"Error checking chart access: {e}")
            return False
    
    def can_access_dataset(self, dataset_id: str, action: str = "read", user: User = None) -> bool:
        """
        Check if user can access a specific dataset.
        
        Args:
            dataset_id: Dataset identifier
            action: Action to check
            user: User object
            
        Returns:
            True if access granted, False otherwise
        """
        try:
            user_id = self._get_user_id(user)
            if not user_id:
                return False
            
            return self.permission_evaluator.can_access_dataset(user_id, dataset_id, action)
            
        except Exception as e:
            logger.error(f"Error checking dataset access: {e}")
            return False
    
    def apply_rls_filters(self, query: Any, dataset: Any, user: User = None) -> Any:
        """
        Apply row-level security filters to a query.
        
        Args:
            query: SQL query
            dataset: Dataset object
            user: User object
            
        Returns:
            Modified query with RLS filters
        """
        try:
            user_id = self._get_user_id(user)
            if not user_id:
                return query
            
            return apply_rls_to_query(query, user_id, dataset)
            
        except Exception as e:
            logger.error(f"Error applying RLS filters: {e}")
            return query
    
    def get_user_entitlements(self, user: User = None) -> Optional[Dict[str, Any]]:
        """
        Get user entitlements.
        
        Args:
            user: User object
            
        Returns:
            User entitlements dictionary or None
        """
        try:
            user_id = self._get_user_id(user)
            if not user_id:
                return None
            
            entitlements = self.cache_manager.get_user_entitlements(user_id)
            return entitlements.__dict__ if entitlements else None
            
        except Exception as e:
            logger.error(f"Error getting user entitlements: {e}")
            return None
    
    def _get_user_id(self, user: User = None) -> Optional[str]:
        """Get user ID from user object or context."""
        if hasattr(g, 'user_id'):
            return g.user_id
        
        if user and hasattr(user, 'username'):
            # For users created through Apex, username should be the user_id
            return user.username
        
        return None
    
    def _map_view_to_resource_type(self, view_name: str) -> Optional[str]:
        """Map Superset view name to resource type."""
        view_mapping = {
            'DashboardModelView': 'dashboard',
            'SliceModelView': 'chart',
            'TableModelView': 'dataset',
            'DashboardApi': 'dashboard',
            'ChartApi': 'chart',
            'DatasetApi': 'dataset',
        }
        
        return view_mapping.get(view_name)
    
    def _check_general_resource_access(self, user_id: str, resource_type: str, action: str) -> bool:
        """
        Check general access to a resource type.
        
        This is used when we don't have a specific resource ID.
        """
        try:
            # Get all accessible resources for this user and action
            accessible_resources = self.permission_evaluator.get_accessible_resources(
                user_id, resource_type, action
            )
            
            # If user has access to any resources of this type, grant general access
            return len(accessible_resources) > 0
            
        except Exception as e:
            logger.error(f"Error checking general resource access: {e}")
            return False
    
    def invalidate_user_cache(self, user_id: str) -> bool:
        """
        Invalidate cache for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache_manager.invalidate_user_cache(user_id)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {e}")
            return False
    
    def refresh_user_entitlements(self, user_id: str) -> bool:
        """
        Refresh user entitlements from the service.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Invalidate cache first
            self.invalidate_user_cache(user_id)
            
            # Fetch fresh entitlements
            entitlements = self.entitlement_client.fetch_user_entitlements(user_id)
            if entitlements:
                # Cache the fresh data
                self.cache_manager._cache_entitlements(user_id, entitlements)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to refresh user entitlements: {e}")
            return False


def create_apex_security_manager(app):
    """
    Create and configure Apex security manager.
    
    Args:
        app: Flask application instance
        
    Returns:
        ApexSecurityManager instance
    """
    try:
        # Initialize components
        from .entitlement_client import init_entitlement_client
        from .cache_manager import init_cache_manager
        from .permission_evaluator import init_permission_evaluator
        from .hierarchy_registry import init_hierarchy_registry
        
        # Initialize all components
        init_entitlement_client(app)
        init_cache_manager(app)
        init_permission_evaluator(app)
        init_hierarchy_registry(app, entitlement_client)
        
        logger.info("Apex security manager components initialized")
        
        return ApexSecurityManager
        
    except Exception as e:
        logger.error(f"Failed to create Apex security manager: {e}")
        return SecurityManager  # Fallback to default 