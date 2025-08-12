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

"""Configuration for Apex entitlement integration."""

import logging
from typing import Any, Dict
from flask import Flask

logger = logging.getLogger(__name__)


# Default entitlement configuration
ENTITLEMENT_CONFIG = {
    # Entitlement Service Configuration
    'ENTITLEMENT_SERVICE_BASE_URL': 'https://entitlement.company.com',
    'ENTITLEMENT_SERVICE_API_KEY': 'your-api-key-here',
    'ENTITLEMENT_SERVICE_TIMEOUT': 30,
    
    # Apex DSP Configuration
    'APEX_DSP_BASE_URL': 'https://apex-dsp.company.com',
    'APEX_DSP_TOKEN_VALIDATION_ENDPOINT': '/api/v1/validate-token',
    'APEX_DSP_USER_INFO_ENDPOINT': '/api/v1/user-info',
    
    # Cache Configuration
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300,
    
    # Row-Level Security Configuration
    'RLS_CONFIG': {
        'enabled': True,
        'hierarchy_service_url': 'https://hierarchy.company.com/api/v1',
        'dynamic_hierarchies': True,
        'default_inheritance': 'top_down',
        'hierarchy_cache_ttl': 3600,  # 1 hour
        'hierarchy_definitions': {
            'geographic_hierarchy': {
                'hierarchy_definition': ['country', 'state', 'city', 'district'],
                'column_mappings': {
                    'country': 'country_code',
                    'state': 'state_code',
                    'city': 'city_name',
                    'district': 'district_id'
                },
                'inheritance_rules': {
                    'enabled': True,
                    'direction': 'top_down'
                }
            },
            'product_hierarchy': {
                'hierarchy_definition': ['category', 'sub_category', 'product_type', 'sku'],
                'column_mappings': {
                    'category': 'product_category',
                    'sub_category': 'product_sub_category',
                    'product_type': 'product_type_code',
                    'sku': 'product_sku'
                },
                'inheritance_rules': {
                    'enabled': True,
                    'direction': 'top_down'
                }
            },
            'organization_hierarchy': {
                'hierarchy_definition': ['division', 'department', 'team', 'project'],
                'column_mappings': {
                    'division': 'div_code',
                    'department': 'dept_code',
                    'team': 'team_id',
                    'project': 'project_id'
                },
                'inheritance_rules': {
                    'enabled': True,
                    'direction': 'top_down'
                }
            },
            'time_hierarchy': {
                'hierarchy_definition': ['year', 'quarter', 'month', 'week'],
                'column_mappings': {
                    'year': 'fiscal_year',
                    'quarter': 'fiscal_quarter',
                    'month': 'fiscal_month',
                    'week': 'fiscal_week'
                },
                'inheritance_rules': {
                    'enabled': True,
                    'direction': 'top_down'
                }
            }
        }
    },
    
    # Apex Integration Settings
    'APEX_ENTITLEMENT_ENABLED': True,
    'APEX_JWT_HEADER_AUTH_ENABLED': True,
    'APEX_CACHE_ENABLED': True,
    'APEX_RLS_ENABLED': True,
    
    # Security Settings
    'APEX_SECURITY_MANAGER': 'superset.apex.security_manager.ApexSecurityManager',
    'APEX_FAIL_SECURE': True,  # Deny access if entitlement service is unavailable
    'APEX_AUDIT_ENABLED': True,
    
    # Performance Settings
    'APEX_CACHE_CLEANUP_INTERVAL': 3600,  # 1 hour
    'APEX_ENTITLEMENT_BATCH_SIZE': 100,
    'APEX_MAX_CACHE_SIZE': 10000,
}


def init_entitlement_config(app: Flask) -> None:
    """
    Initialize entitlement configuration.
    
    Args:
        app: Flask application instance
    """
    try:
        # Apply default configuration
        for key, value in ENTITLEMENT_CONFIG.items():
            app.config.setdefault(key, value)
        
        # Validate required configuration
        _validate_entitlement_config(app)
        
        logger.info("Entitlement configuration initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize entitlement configuration: {e}")
        raise


def _validate_entitlement_config(app: Flask) -> None:
    """
    Validate entitlement configuration.
    
    Args:
        app: Flask application instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    required_settings = [
        'ENTITLEMENT_SERVICE_BASE_URL',
        'ENTITLEMENT_SERVICE_API_KEY',
        'APEX_DSP_BASE_URL'
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not app.config.get(setting):
            missing_settings.append(setting)
    
    if missing_settings:
        raise ValueError(f"Missing required configuration: {', '.join(missing_settings)}")
    
    # Validate RLS configuration
    rls_config = app.config.get('RLS_CONFIG', {})
    if rls_config.get('enabled') and not rls_config.get('hierarchy_definitions'):
        logger.warning("RLS is enabled but no hierarchy definitions found")


def init_entitlement_integration(app: Flask) -> None:
    """
    Initialize complete entitlement integration.
    
    This is the main initialization function that should be called
    during Superset application setup.
    
    Args:
        app: Flask application instance
    """
    logger.info("Initializing Apex entitlement integration...")
    
    try:
        # Initialize configuration
        init_entitlement_config(app)
        
        # Initialize components
        from .entitlement_client import init_entitlement_client
        from .cache_manager import init_cache_manager
        from .permission_evaluator import init_permission_evaluator
        from .hierarchy_registry import init_hierarchy_registry
        from .security_manager import create_apex_security_manager
        
        # Initialize all components
        init_entitlement_client(app)
        init_cache_manager(app)
        init_permission_evaluator(app)
        
        # Initialize hierarchy registry with entitlement client
        from .entitlement_client import entitlement_client
        init_hierarchy_registry(app, entitlement_client)
        
        # Set up security manager
        apex_security_manager = create_apex_security_manager(app)
        app.config['CUSTOM_SECURITY_MANAGER'] = apex_security_manager
        
        # Register APIs
        _register_entitlement_apis(app)
        
        # Set up background tasks if enabled
        _setup_background_tasks(app)
        
        logger.info("Apex entitlement integration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize entitlement integration: {e}")
        raise


def _register_entitlement_apis(app: Flask) -> None:
    """Register entitlement APIs with the application."""
    try:
        @app.before_first_request
        def register_apis():
            from flask_appbuilder import AppBuilder
            from .entitlement_api import EntitlementApi, InternalEntitlementApi
            
            appbuilder = app.extensions.get('appbuilder')
            if appbuilder:
                appbuilder.add_api(EntitlementApi)
                appbuilder.add_api(InternalEntitlementApi)
                logger.info("Entitlement APIs registered successfully")
            else:
                logger.warning("AppBuilder not found, cannot register entitlement APIs")
        
    except Exception as e:
        logger.error(f"Failed to register entitlement APIs: {e}")


def _setup_background_tasks(app: Flask) -> None:
    """Set up background tasks for cache cleanup and maintenance."""
    try:
        if not app.config.get('APEX_CACHE_ENABLED', True):
            return
        
        # Set up cache cleanup task (would typically use Celery)
        cleanup_interval = app.config.get('APEX_CACHE_CLEANUP_INTERVAL', 3600)
        
        # In a real implementation, you would set up a Celery beat task here
        logger.info(f"Cache cleanup scheduled every {cleanup_interval} seconds")
        
    except Exception as e:
        logger.error(f"Failed to setup background tasks: {e}")


def get_entitlement_config() -> Dict[str, Any]:
    """
    Get current entitlement configuration.
    
    Returns:
        Dictionary of entitlement configuration
    """
    from flask import current_app
    
    config = {}
    for key in ENTITLEMENT_CONFIG.keys():
        config[key] = current_app.config.get(key)
    
    return config


def update_entitlement_config(updates: Dict[str, Any]) -> None:
    """
    Update entitlement configuration at runtime.
    
    Args:
        updates: Dictionary of configuration updates
    """
    from flask import current_app
    
    try:
        for key, value in updates.items():
            if key in ENTITLEMENT_CONFIG:
                current_app.config[key] = value
                logger.info(f"Updated configuration: {key}")
            else:
                logger.warning(f"Unknown configuration key: {key}")
        
        # Re-validate configuration
        _validate_entitlement_config(current_app)
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise


# Configuration templates for different environments

DEVELOPMENT_CONFIG = {
    **ENTITLEMENT_CONFIG,
    'ENTITLEMENT_SERVICE_BASE_URL': 'http://localhost:8080',
    'APEX_DSP_BASE_URL': 'http://localhost:8081',
    'CACHE_REDIS_URL': 'redis://localhost:6379/1',
    'RLS_CONFIG': {
        **ENTITLEMENT_CONFIG['RLS_CONFIG'],
        'enabled': True,
        'hierarchy_cache_ttl': 300,  # 5 minutes for development
    }
}

PRODUCTION_CONFIG = {
    **ENTITLEMENT_CONFIG,
    'ENTITLEMENT_SERVICE_TIMEOUT': 60,
    'CACHE_DEFAULT_TIMEOUT': 1800,  # 30 minutes
    'RLS_CONFIG': {
        **ENTITLEMENT_CONFIG['RLS_CONFIG'],
        'hierarchy_cache_ttl': 7200,  # 2 hours
    },
    'APEX_CACHE_CLEANUP_INTERVAL': 1800,  # 30 minutes
    'APEX_MAX_CACHE_SIZE': 50000,
}

TESTING_CONFIG = {
    **ENTITLEMENT_CONFIG,
    'ENTITLEMENT_SERVICE_BASE_URL': 'http://test-entitlement:8080',
    'APEX_DSP_BASE_URL': 'http://test-dsp:8081',
    'CACHE_TYPE': 'simple',  # Use simple cache for testing
    'RLS_CONFIG': {
        **ENTITLEMENT_CONFIG['RLS_CONFIG'],
        'enabled': True,
        'hierarchy_cache_ttl': 60,  # 1 minute for testing
    },
    'APEX_FAIL_SECURE': False,  # Allow tests to run without external services
}


def get_config_for_environment(env: str) -> Dict[str, Any]:
    """
    Get configuration for a specific environment.
    
    Args:
        env: Environment name (development, production, testing)
        
    Returns:
        Configuration dictionary
    """
    configs = {
        'development': DEVELOPMENT_CONFIG,
        'production': PRODUCTION_CONFIG,
        'testing': TESTING_CONFIG
    }
    
    return configs.get(env.lower(), ENTITLEMENT_CONFIG) 