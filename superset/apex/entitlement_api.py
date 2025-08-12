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

"""API endpoints for Apex entitlement management."""

import logging
from typing import Any, Dict, List
from flask import request, g
from flask_appbuilder import expose
from flask_appbuilder.api import BaseApi, safe
from flask_appbuilder.security.decorators import has_access_api

from .permission_evaluator import permission_evaluator, require_role
from .cache_manager import cache_manager, cache_invalidation_manager
from .hierarchy_registry import get_hierarchy_registry

logger = logging.getLogger(__name__)


class EntitlementApi(BaseApi):
    """
    API for entitlement management operations.
    
    Provides endpoints for permission checking, cache management,
    and hierarchy operations.
    """
    
    resource_name = "entitlement"
    allow_browser_login = True
    
    @expose("/permissions/check", methods=["POST"])
    @safe
    @has_access_api
    def check_permission(self):
        """
        Check user permission for a specific resource and action.
        
        Request body:
        {
            "user_id": "string",
            "resource_type": "dashboard|chart|dataset",
            "resource_id": "string", 
            "action": "create|read|update|delete"
        }
        
        Returns:
        {
            "allowed": boolean,
            "reason": "string",
            "permissions": ["action1", "action2"],
            "rls_filters": {...}
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return self.response_400("Request body required")
            
            user_id = data.get('user_id')
            resource_type = data.get('resource_type')
            resource_id = data.get('resource_id')
            action = data.get('action')
            
            if not all([user_id, resource_type, resource_id, action]):
                return self.response_400("Missing required fields")
            
            # Check permission
            allowed = permission_evaluator.check_crud_permission(
                user_id, resource_type, resource_id, action
            )
            
            # Get all permissions for this resource
            permissions = permission_evaluator.get_user_permissions(
                user_id, resource_type, resource_id
            )
            
            # Get RLS filters if dataset access
            rls_filters = {}
            if resource_type.lower() == 'dataset':
                rls_filters = permission_evaluator.get_row_level_filters(user_id, resource_id)
            
            response_data = {
                'allowed': allowed,
                'permissions': permissions,
                'rls_filters': rls_filters,
                'reason': 'Permission granted' if allowed else 'Permission denied'
            }
            
            return self.response(200, **response_data)
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return self.response_500()
    
    @expose("/permissions/bulk-check", methods=["POST"])
    @safe
    @has_access_api
    def bulk_check_permissions(self):
        """
        Check permissions for multiple resources at once.
        
        Request body:
        {
            "user_id": "string",
            "resources": [
                {
                    "resource_type": "dashboard",
                    "resource_id": "dashboard_1",
                    "actions": ["read", "update"]
                }
            ]
        }
        
        Returns:
        {
            "results": [
                {
                    "resource_type": "dashboard",
                    "resource_id": "dashboard_1",
                    "permissions": {
                        "read": true,
                        "update": false
                    }
                }
            ]
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return self.response_400("Request body required")
            
            user_id = data.get('user_id')
            resources = data.get('resources', [])
            
            if not user_id or not resources:
                return self.response_400("Missing required fields")
            
            # Perform bulk permission check
            results = permission_evaluator.bulk_check_permissions(user_id, resources)
            
            # Format response
            formatted_results = []
            for resource in resources:
                resource_id = resource.get('resource_id')
                if resource_id in results:
                    formatted_results.append({
                        'resource_type': resource.get('resource_type'),
                        'resource_id': resource_id,
                        'permissions': results[resource_id]
                    })
            
            return self.response(200, results=formatted_results)
            
        except Exception as e:
            logger.error(f"Bulk permission check error: {e}")
            return self.response_500()
    
    @expose("/cache/user/<user_id>", methods=["DELETE"])
    @safe
    @has_access_api
    @require_role("Admin")
    def invalidate_user_cache(self, user_id: str):
        """
        Invalidate cache for a specific user.
        
        Returns:
        {
            "success": boolean,
            "message": "string"
        }
        """
        try:
            success = cache_invalidation_manager.invalidate_user_cache(user_id)
            
            if success:
                return self.response(200, 
                    success=True, 
                    message=f"Cache invalidated for user {user_id}"
                )
            else:
                return self.response_400("Failed to invalidate cache")
                
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return self.response_500()
    
    @expose("/cache/role/<role_name>", methods=["DELETE"])
    @safe
    @has_access_api
    @require_role("Admin")
    def invalidate_role_cache(self, role_name: str):
        """
        Invalidate cache for all users with a specific role.
        
        Returns:
        {
            "success": boolean,
            "message": "string"
        }
        """
        try:
            success = cache_invalidation_manager.invalidate_role_cache(role_name)
            
            if success:
                return self.response(200,
                    success=True,
                    message=f"Cache invalidated for role {role_name}"
                )
            else:
                return self.response_400("Failed to invalidate role cache")
                
        except Exception as e:
            logger.error(f"Role cache invalidation error: {e}")
            return self.response_500()
    
    @expose("/cache/refresh", methods=["POST"])
    @safe
    @has_access_api
    @require_role("Admin")
    def refresh_cache(self):
        """
        Refresh cache for specified users.
        
        Request body:
        {
            "user_ids": ["user1", "user2"] // optional, if not provided refreshes all
        }
        
        Returns:
        {
            "results": {
                "user1": true,
                "user2": false
            }
        }
        """
        try:
            data = request.get_json() or {}
            user_ids = data.get('user_ids')
            
            results = cache_invalidation_manager.refresh_cache(user_ids)
            
            return self.response(200, results=results)
            
        except Exception as e:
            logger.error(f"Cache refresh error: {e}")
            return self.response_500()
    
    @expose("/cache/stats", methods=["GET"])
    @safe
    @has_access_api
    @require_role("Admin")
    def get_cache_stats(self):
        """
        Get cache statistics.
        
        Returns:
        {
            "memory_cache_size": integer,
            "redis_available": boolean,
            "redis_cache_size": integer
        }
        """
        try:
            stats = cache_manager.get_cache_stats()
            return self.response(200, **stats)
            
        except Exception as e:
            logger.error(f"Get cache stats error: {e}")
            return self.response_500()
    
    @expose("/hierarchies", methods=["GET"])
    @safe
    @has_access_api
    def list_hierarchies(self):
        """
        List all registered hierarchies.
        
        Returns:
        {
            "hierarchies": [
                {
                    "hierarchy_name": "string",
                    "hierarchy_definition": ["level1", "level2"],
                    "active": boolean
                }
            ]
        }
        """
        try:
            registry = get_hierarchy_registry()
            hierarchies = []
            
            for name, hierarchy_def in registry.hierarchies.items():
                hierarchies.append({
                    'hierarchy_name': name,
                    'hierarchy_definition': hierarchy_def.hierarchy_definition,
                    'active': hierarchy_def.active,
                    'column_mappings': hierarchy_def.column_mappings
                })
            
            return self.response(200, hierarchies=hierarchies)
            
        except Exception as e:
            logger.error(f"List hierarchies error: {e}")
            return self.response_500()
    
    @expose("/hierarchies/<hierarchy_name>", methods=["GET"])
    @safe
    @has_access_api
    def get_hierarchy(self, hierarchy_name: str):
        """
        Get specific hierarchy configuration.
        
        Returns:
        {
            "hierarchy_name": "string",
            "hierarchy_definition": ["level1", "level2"],
            "column_mappings": {...},
            "inheritance_rules": {...},
            "active": boolean
        }
        """
        try:
            registry = get_hierarchy_registry()
            hierarchy_def = registry.get_hierarchy(hierarchy_name)
            
            if not hierarchy_def:
                return self.response_404()
            
            return self.response(200, **hierarchy_def.to_dict())
            
        except Exception as e:
            logger.error(f"Get hierarchy error: {e}")
            return self.response_500()
    
    @expose("/hierarchies", methods=["POST"])
    @safe
    @has_access_api
    @require_role("Admin")
    def create_hierarchy(self):
        """
        Create a new hierarchy.
        
        Request body:
        {
            "hierarchy_name": "string",
            "hierarchy_definition": ["level1", "level2"],
            "column_mappings": {...},
            "inheritance_rules": {...}
        }
        
        Returns:
        {
            "success": boolean,
            "message": "string"
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return self.response_400("Request body required")
            
            hierarchy_name = data.get('hierarchy_name')
            if not hierarchy_name:
                return self.response_400("hierarchy_name required")
            
            # Remove hierarchy_name from config to avoid duplication
            config = {k: v for k, v in data.items() if k != 'hierarchy_name'}
            
            registry = get_hierarchy_registry()
            registry.register_hierarchy(hierarchy_name, config)
            
            return self.response(201,
                success=True,
                message=f"Hierarchy {hierarchy_name} created successfully"
            )
            
        except ValueError as e:
            return self.response_400(str(e))
        except Exception as e:
            logger.error(f"Create hierarchy error: {e}")
            return self.response_500()
    
    @expose("/hierarchies/<hierarchy_name>", methods=["PUT"])
    @safe
    @has_access_api
    @require_role("Admin")
    def update_hierarchy(self, hierarchy_name: str):
        """
        Update an existing hierarchy.
        
        Request body:
        {
            "hierarchy_definition": ["level1", "level2"],
            "column_mappings": {...},
            "inheritance_rules": {...}
        }
        
        Returns:
        {
            "success": boolean,
            "message": "string"
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return self.response_400("Request body required")
            
            registry = get_hierarchy_registry()
            registry.update_hierarchy(hierarchy_name, data)
            
            return self.response(200,
                success=True,
                message=f"Hierarchy {hierarchy_name} updated successfully"
            )
            
        except ValueError as e:
            return self.response_400(str(e))
        except Exception as e:
            logger.error(f"Update hierarchy error: {e}")
            return self.response_500()
    
    @expose("/hierarchies/<hierarchy_name>", methods=["DELETE"])
    @safe
    @has_access_api
    @require_role("Admin")
    def delete_hierarchy(self, hierarchy_name: str):
        """
        Delete a hierarchy.
        
        Returns:
        {
            "success": boolean,
            "message": "string"
        }
        """
        try:
            registry = get_hierarchy_registry()
            registry.remove_hierarchy(hierarchy_name)
            
            return self.response(200,
                success=True,
                message=f"Hierarchy {hierarchy_name} deleted successfully"
            )
            
        except Exception as e:
            logger.error(f"Delete hierarchy error: {e}")
            return self.response_500()
    
    @expose("/user/<user_id>/entitlements", methods=["GET"])
    @safe
    @has_access_api
    def get_user_entitlements(self, user_id: str):
        """
        Get user entitlements.
        
        Returns:
        {
            "user_id": "string",
            "roles": ["role1", "role2"],
            "permissions": {...},
            "row_level_filters": {...}
        }
        """
        try:
            entitlements = cache_manager.get_user_entitlements(user_id)
            
            if not entitlements:
                return self.response_404()
            
            return self.response(200, **entitlements.__dict__)
            
        except Exception as e:
            logger.error(f"Get user entitlements error: {e}")
            return self.response_500()
    
    @expose("/user/<user_id>/accessible-resources", methods=["GET"])
    @safe
    @has_access_api
    def get_user_accessible_resources(self, user_id: str):
        """
        Get accessible resources for a user.
        
        Query parameters:
        - resource_type: dashboard|chart|dataset
        - action: create|read|update|delete (default: read)
        
        Returns:
        {
            "resource_type": "string",
            "action": "string",
            "accessible_resources": ["id1", "id2"]
        }
        """
        try:
            resource_type = request.args.get('resource_type')
            action = request.args.get('action', 'read')
            
            if not resource_type:
                return self.response_400("resource_type parameter required")
            
            accessible_resources = permission_evaluator.get_accessible_resources(
                user_id, resource_type, action
            )
            
            return self.response(200,
                resource_type=resource_type,
                action=action,
                accessible_resources=accessible_resources
            )
            
        except Exception as e:
            logger.error(f"Get accessible resources error: {e}")
            return self.response_500()


# Additional helper API class for internal use
class InternalEntitlementApi(BaseApi):
    """Internal API for system operations (no authentication required)."""
    
    resource_name = "internal_entitlement"
    allow_browser_login = False
    
    @expose("/health", methods=["GET"])
    @safe
    def health_check(self):
        """
        Health check endpoint.
        
        Returns:
        {
            "status": "healthy|unhealthy",
            "components": {
                "entitlement_service": boolean,
                "cache": boolean,
                "hierarchy_registry": boolean
            }
        }
        """
        try:
            components = {
                'entitlement_service': True,
                'cache': cache_manager.redis_client is not None,
                'hierarchy_registry': len(get_hierarchy_registry().hierarchies) > 0
            }
            
            # Test entitlement service connection
            try:
                # This is a simple test - in practice you might want a dedicated health endpoint
                cache_manager.entitlement_client.get_hierarchies()
            except Exception:
                components['entitlement_service'] = False
            
            status = "healthy" if all(components.values()) else "unhealthy"
            
            return self.response(200, status=status, components=components)
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return self.response(500, status="unhealthy", error=str(e)) 