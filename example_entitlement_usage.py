#!/usr/bin/env python3
"""
Example usage of Apex Entitlement Integration.

This script demonstrates how to use the various components
of the Apex entitlement integration system.
"""

import json
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_app():
    """Create a test Flask application with Apex entitlement integration."""
    
    app = Flask(__name__)
    
    # Basic configuration
    app.config.update({
        'SECRET_KEY': 'test-secret-key',
        'ENTITLEMENT_SERVICE_BASE_URL': 'https://entitlement.company.com',
        'ENTITLEMENT_SERVICE_API_KEY': 'test-api-key',
        'APEX_DSP_BASE_URL': 'https://apex-dsp.company.com',
        'CACHE_TYPE': 'simple',  # Use simple cache for testing
        'CACHE_DEFAULT_TIMEOUT': 300,
        'RLS_CONFIG': {
            'enabled': True,
            'dynamic_hierarchies': True,
            'hierarchy_definitions': {
                'geographic_hierarchy': {
                    'hierarchy_definition': ['country', 'state', 'city'],
                    'column_mappings': {
                        'country': 'country_code',
                        'state': 'state_code',
                        'city': 'city_name'
                    },
                    'inheritance_rules': {
                        'enabled': True,
                        'direction': 'top_down'
                    }
                },
                'product_hierarchy': {
                    'hierarchy_definition': ['category', 'sub_category', 'product'],
                    'column_mappings': {
                        'category': 'product_category',
                        'sub_category': 'product_sub_category',
                        'product': 'product_id'
                    },
                    'inheritance_rules': {
                        'enabled': True,
                        'direction': 'top_down'
                    }
                }
            }
        }
    })
    
    return app


def example_entitlement_client():
    """Example usage of EntitlementServiceClient."""
    
    print("\n=== Entitlement Service Client Example ===")
    
    from superset.apex.entitlement_client import EntitlementServiceClient
    
    # Create client
    client = EntitlementServiceClient(
        base_url='https://entitlement.company.com',
        api_key='test-api-key'
    )
    
    # Example: Fetch user entitlements
    print("Fetching user entitlements...")
    entitlements = client.fetch_user_entitlements('user123')
    
    if entitlements:
        print(f"User: {entitlements.user_id}")
        print(f"Roles: {entitlements.roles}")
        print(f"Permissions: {json.dumps(entitlements.permissions, indent=2)}")
        print(f"RLS Filters: {json.dumps(entitlements.row_level_filters, indent=2)}")
    else:
        print("No entitlements found or service unavailable")
    
    # Example: Check specific permission
    print("\nChecking specific permission...")
    has_permission = client.check_permission(
        user_id='user123',
        resource_type='dashboard',
        resource_id='dashboard_456',
        action='read'
    )
    print(f"User can read dashboard_456: {has_permission}")


def example_hierarchy_registry():
    """Example usage of HierarchyRegistry."""
    
    print("\n=== Hierarchy Registry Example ===")
    
    from superset.apex.hierarchy_registry import get_hierarchy_registry
    
    registry = get_hierarchy_registry()
    
    # Register a custom hierarchy
    print("Registering custom hierarchy...")
    registry.register_hierarchy('sales_hierarchy', {
        'hierarchy_definition': ['region', 'territory', 'account'],
        'column_mappings': {
            'region': 'sales_region',
            'territory': 'sales_territory',
            'account': 'account_id'
        },
        'inheritance_rules': {
            'enabled': True,
            'direction': 'top_down'
        }
    })
    
    # List all hierarchies
    print("\nRegistered hierarchies:")
    hierarchies = registry.list_hierarchies()
    for hierarchy_name in hierarchies:
        hierarchy_def = registry.get_hierarchy(hierarchy_name)
        print(f"- {hierarchy_name}: {hierarchy_def.hierarchy_definition}")
    
    # Get specific hierarchy
    print("\nGetting geographic hierarchy details...")
    geo_hierarchy = registry.get_hierarchy('geographic_hierarchy')
    if geo_hierarchy:
        print(f"Definition: {geo_hierarchy.hierarchy_definition}")
        print(f"Column mappings: {geo_hierarchy.column_mappings}")
        print(f"Active: {geo_hierarchy.active}")


def example_permission_evaluator():
    """Example usage of ApexPermissionEvaluator."""
    
    print("\n=== Permission Evaluator Example ===")
    
    from superset.apex.permission_evaluator import get_permission_evaluator
    
    evaluator = get_permission_evaluator()
    
    # Check dashboard access
    print("Checking dashboard access...")
    can_read_dashboard = evaluator.can_access_dashboard('user123', 'dashboard_456', 'read')
    can_edit_dashboard = evaluator.can_access_dashboard('user123', 'dashboard_456', 'update')
    
    print(f"Can read dashboard: {can_read_dashboard}")
    print(f"Can edit dashboard: {can_edit_dashboard}")
    
    # Get user permissions for a resource
    print("\nGetting user permissions...")
    permissions = evaluator.get_user_permissions('user123', 'dashboard', 'dashboard_456')
    print(f"Dashboard permissions: {permissions}")
    
    # Get accessible resources
    print("\nGetting accessible dashboards...")
    accessible_dashboards = evaluator.get_accessible_resources('user123', 'dashboard', 'read')
    print(f"Accessible dashboards: {accessible_dashboards}")
    
    # Check user roles
    print("\nChecking user roles...")
    roles = evaluator.get_user_roles('user123')
    has_analyst_role = evaluator.has_role('user123', 'analyst')
    print(f"User roles: {roles}")
    print(f"Has analyst role: {has_analyst_role}")


def example_rls_builder():
    """Example usage of DynamicHierarchicalRLSBuilder."""
    
    print("\n=== RLS Builder Example ===")
    
    from superset.apex.rls_builder import DynamicHierarchicalRLSBuilder
    from superset.apex.entitlement_client import UserEntitlements
    
    # Create sample user entitlements
    sample_entitlements = UserEntitlements(
        user_id='user123',
        roles=['analyst'],
        permissions={
            'dashboards': {
                'dashboard_456': ['read', 'update']
            }
        },
        row_level_filters={
            'geographic_hierarchy': {
                'hierarchy_definition': ['country', 'state', 'city'],
                'user_access': {
                    'country': ['US'],
                    'state': ['NY', 'CA']
                }
            },
            'product_hierarchy': {
                'hierarchy_definition': ['category', 'sub_category', 'product'],
                'user_access': {
                    'category': ['Electronics'],
                    'sub_category': ['Phones', 'Laptops']
                }
            }
        }
    )
    
    # Mock dataset schema
    class MockSchema:
        def __init__(self):
            self.columns = [
                type('Column', (), {'name': 'country_code'}),
                type('Column', (), {'name': 'state_code'}),
                type('Column', (), {'name': 'product_category'}),
                type('Column', (), {'name': 'product_sub_category'})
            ]
    
    # Build RLS filters
    rls_builder = DynamicHierarchicalRLSBuilder()
    mock_schema = MockSchema()
    
    print("Building RLS filters...")
    rls_filter = rls_builder.build_filter(sample_entitlements, mock_schema)
    
    if rls_filter:
        print(f"Generated RLS filter: {rls_filter}")
    else:
        print("No RLS filters generated")


def example_cache_manager():
    """Example usage of EntitlementCacheManager."""
    
    print("\n=== Cache Manager Example ===")
    
    from superset.apex.cache_manager import cache_manager
    from superset.apex.entitlement_client import UserEntitlements
    
    # Create sample entitlements
    sample_entitlements = UserEntitlements(
        user_id='user123',
        roles=['analyst', 'viewer'],
        permissions={
            'dashboards': {
                'dashboard_1': ['read'],
                'dashboard_2': ['read', 'update']
            },
            'charts': {
                'chart_1': ['read'],
                'chart_2': ['read', 'update']
            }
        },
        row_level_filters={
            'geographic_hierarchy': {
                'user_access': {
                    'country': ['US'],
                    'state': ['NY', 'CA']
                }
            }
        },
        cache_ttl=300
    )
    
    # Cache the entitlements
    print("Caching user entitlements...")
    cache_manager._cache_entitlements('user123', sample_entitlements)
    
    # Retrieve from cache
    print("Retrieving from cache...")
    cached_entitlements = cache_manager.get_user_entitlements('user123')
    
    if cached_entitlements:
        print(f"Retrieved user: {cached_entitlements.user_id}")
        print(f"Roles: {cached_entitlements.roles}")
        print("Entitlements successfully cached and retrieved!")
    else:
        print("Failed to retrieve from cache")
    
    # Get cache stats
    print("\nCache statistics:")
    stats = cache_manager.get_cache_stats()
    for key, value in stats.items():
        print(f"- {key}: {value}")
    
    # Invalidate cache
    print("\nInvalidating user cache...")
    cache_manager.invalidate_user_cache('user123')
    
    # Try to retrieve again
    cached_after_invalidation = cache_manager.get_user_entitlements('user123')
    if not cached_after_invalidation:
        print("Cache successfully invalidated!")


def example_api_usage():
    """Example of using the API endpoints (simulated)."""
    
    print("\n=== API Usage Examples ===")
    
    # These would be actual HTTP calls in a real scenario
    print("API endpoints available:")
    
    api_examples = [
        {
            "method": "POST",
            "endpoint": "/api/v1/entitlement/permissions/check",
            "description": "Check user permission",
            "payload": {
                "user_id": "user123",
                "resource_type": "dashboard",
                "resource_id": "dashboard_456",
                "action": "read"
            }
        },
        {
            "method": "POST",
            "endpoint": "/api/v1/entitlement/permissions/bulk-check",
            "description": "Bulk permission check",
            "payload": {
                "user_id": "user123",
                "resources": [
                    {
                        "resource_type": "dashboard",
                        "resource_id": "dashboard_1",
                        "actions": ["read", "update"]
                    }
                ]
            }
        },
        {
            "method": "DELETE",
            "endpoint": "/api/v1/entitlement/cache/user/user123",
            "description": "Invalidate user cache",
            "payload": None
        },
        {
            "method": "GET",
            "endpoint": "/api/v1/entitlement/hierarchies",
            "description": "List all hierarchies",
            "payload": None
        },
        {
            "method": "GET",
            "endpoint": "/api/v1/entitlement/cache/stats",
            "description": "Get cache statistics",
            "payload": None
        }
    ]
    
    for api in api_examples:
        print(f"\n{api['method']} {api['endpoint']}")
        print(f"Description: {api['description']}")
        if api['payload']:
            print(f"Payload: {json.dumps(api['payload'], indent=2)}")


def example_decorators():
    """Example usage of permission decorators."""
    
    print("\n=== Permission Decorators Example ===")
    
    from superset.apex.permission_evaluator import require_permission, require_role
    from flask import Flask, g
    
    app = Flask(__name__)
    
    # Mock user context
    with app.app_context():
        g.user_id = 'user123'
        
        # Example view with permission requirement
        @require_permission('dashboard', 'dashboard_id', 'read')
        def view_dashboard(dashboard_id):
            return f"Viewing dashboard {dashboard_id}"
        
        # Example view with role requirement
        @require_role('admin')
        def admin_view():
            return "Admin view accessed"
        
        print("Decorator examples created (would be used in actual Flask views)")
        print("@require_permission('dashboard', 'dashboard_id', 'read')")
        print("@require_role('admin')")


def main():
    """Main function to run all examples."""
    
    print("Apex Entitlement Integration - Usage Examples")
    print("=" * 50)
    
    # Create test app
    app = create_test_app()
    
    with app.app_context():
        try:
            # Initialize the integration (this would normally be done at app startup)
            from superset.apex.entitlement_config import init_entitlement_integration
            
            # For this example, we'll skip actual initialization to avoid external dependencies
            print("Note: Using mock data for demonstration. In real usage, configure external services.")
            
            # Run examples
            # example_entitlement_client()  # Requires actual service
            example_hierarchy_registry()
            # example_permission_evaluator()  # Requires cached entitlements
            example_rls_builder()
            example_cache_manager()
            example_api_usage()
            example_decorators()
            
            print("\n" + "=" * 50)
            print("Examples completed successfully!")
            print("\nTo use in production:")
            print("1. Configure your entitlement service URLs and API keys")
            print("2. Set up Redis for caching")
            print("3. Initialize the integration in your superset_config.py")
            print("4. Use the components in your Superset application")
            
        except Exception as e:
            logger.error(f"Example execution failed: {e}")
            print(f"\nError running examples: {e}")
            print("This is expected if external services are not configured.")


if __name__ == '__main__':
    main() 