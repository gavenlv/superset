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

"""
Apex module for enhanced Superset functionality.

This module provides comprehensive integration with Apex platform including:
- JWT header authentication and SSO integration
- Dynamic entitlement service integration
- Hierarchical row-level security (RLS)
- Multi-level caching for performance
- CRUD permission management
"""

from .api import ApexApi
from .jwt_auth import (
    JwtHeaderAuthenticator,
    create_jwt_token,
    jwt_authenticator,
    jwt_header_auth_middleware,
)
from .middleware import (
    JwtHeaderSecurityExtension,
    configure_swagger_anonymous_access,
    enhance_security_manager,
    jwt_security_extension,
)

# Entitlement integration components
from .entitlement_client import (
    EntitlementServiceClient,
    UserEntitlements,
    entitlement_client,
    init_entitlement_client,
)
from .cache_manager import (
    EntitlementCacheManager,
    CacheInvalidationManager,
    cache_manager,
    cache_invalidation_manager,
    get_user_entitlements,
    invalidate_user_cache,
    invalidate_role_cache,
    init_cache_manager,
)
from .permission_evaluator import (
    ApexPermissionEvaluator,
    permission_evaluator,
    get_permission_evaluator,
    check_user_permission,
    get_user_accessible_resources,
    require_permission,
    require_role,
    init_permission_evaluator,
)
from .hierarchy_registry import (
    HierarchyRegistry,
    HierarchyDefinition,
    hierarchy_registry,
    get_hierarchy_registry,
    init_hierarchy_registry,
    register_default_hierarchies,
)
from .rls_builder import (
    DynamicHierarchicalRLSBuilder,
    RLSQueryBuilder,
    get_rls_filter_for_user,
    apply_rls_to_query,
    validate_rls_configuration,
)
from .security_manager import (
    ApexSecurityManager,
    create_apex_security_manager,
)
from .entitlement_api import (
    EntitlementApi,
    InternalEntitlementApi,
)
from .entitlement_config import (
    ENTITLEMENT_CONFIG,
    DEVELOPMENT_CONFIG,
    PRODUCTION_CONFIG,
    TESTING_CONFIG,
    init_entitlement_config,
    init_entitlement_integration,
    get_entitlement_config,
    update_entitlement_config,
    get_config_for_environment,
)

__all__ = [
    # Original components
    "ApexApi",
    "JwtHeaderAuthenticator", 
    "JwtHeaderSecurityExtension",
    "configure_swagger_anonymous_access",
    "create_jwt_token",
    "enhance_security_manager",
    "jwt_authenticator",
    "jwt_header_auth_middleware",
    "jwt_security_extension",
    
    # Entitlement service components
    "EntitlementServiceClient",
    "UserEntitlements",
    "entitlement_client",
    "init_entitlement_client",
    
    # Cache management
    "EntitlementCacheManager",
    "CacheInvalidationManager",
    "cache_manager",
    "cache_invalidation_manager",
    "get_user_entitlements",
    "invalidate_user_cache",
    "invalidate_role_cache",
    "init_cache_manager",
    
    # Permission evaluation
    "ApexPermissionEvaluator",
    "permission_evaluator",
    "get_permission_evaluator",
    "check_user_permission",
    "get_user_accessible_resources",
    "require_permission",
    "require_role",
    "init_permission_evaluator",
    
    # Hierarchy management
    "HierarchyRegistry",
    "HierarchyDefinition",
    "hierarchy_registry",
    "get_hierarchy_registry",
    "init_hierarchy_registry",
    "register_default_hierarchies",
    
    # RLS components
    "DynamicHierarchicalRLSBuilder",
    "RLSQueryBuilder",
    "get_rls_filter_for_user",
    "apply_rls_to_query",
    "validate_rls_configuration",
    
    # Security manager
    "ApexSecurityManager",
    "create_apex_security_manager",
    
    # API endpoints
    "EntitlementApi",
    "InternalEntitlementApi",
    
    # Configuration
    "ENTITLEMENT_CONFIG",
    "DEVELOPMENT_CONFIG",
    "PRODUCTION_CONFIG", 
    "TESTING_CONFIG",
    "init_entitlement_config",
    "init_entitlement_integration",
    "get_entitlement_config",
    "update_entitlement_config",
    "get_config_for_environment",
] 