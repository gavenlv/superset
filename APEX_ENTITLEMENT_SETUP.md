# Apex Entitlement Integration Setup Guide

This guide provides step-by-step instructions for setting up the Apex entitlement integration in Superset.

## Overview

The Apex entitlement integration provides:
- **SSO Integration**: Seamless authentication via Apex DSP
- **Dynamic Permissions**: CRUD permissions for dashboards, charts, and datasets
- **Hierarchical RLS**: Dynamic row-level security with configurable hierarchies
- **Multi-level Caching**: Performance optimization with memory + Redis caching
- **RESTful APIs**: Management endpoints for permissions and cache operations

## Prerequisites

- **Superset**: Apache Superset installation
- **Python**: 3.8 or higher
- **Redis**: For caching (optional but recommended)
- **Apex DSP**: Running and accessible
- **Apex Entitlement Service**: Running and accessible

## Installation

### Step 1: Install Dependencies

Add to your `requirements.txt`:

```txt
requests>=2.25.0
redis>=4.0.0
dataclasses>=0.6  # for Python < 3.7
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Step 2: Update Superset Configuration

Create or update `superset_config.py`:

```python
import os
from superset.apex.entitlement_config import (
    init_entitlement_integration,
    get_config_for_environment
)

# Get environment-specific configuration
ENV = os.getenv('SUPERSET_ENV', 'development')
entitlement_config = get_config_for_environment(ENV)

# Apply entitlement configuration
locals().update(entitlement_config)

# Override with environment-specific values
ENTITLEMENT_SERVICE_BASE_URL = os.getenv('ENTITLEMENT_SERVICE_BASE_URL', 
                                       'https://entitlement.company.com')
ENTITLEMENT_SERVICE_API_KEY = os.getenv('ENTITLEMENT_SERVICE_API_KEY')
APEX_DSP_BASE_URL = os.getenv('APEX_DSP_BASE_URL', 
                             'https://apex-dsp.company.com')

# Redis configuration
CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Enable Apex security manager
from superset.apex.security_manager import ApexSecurityManager
CUSTOM_SECURITY_MANAGER = ApexSecurityManager

# Initialize entitlement integration
def init_app_in_ctx():
    from flask import current_app
    init_entitlement_integration(current_app)

# This will be called after app creation
FLASK_APP_MUTATOR = init_app_in_ctx
```

### Step 3: Environment Configuration

Set environment variables:

```bash
# Required
export ENTITLEMENT_SERVICE_BASE_URL="https://entitlement.company.com"
export ENTITLEMENT_SERVICE_API_KEY="your-api-key-here"
export APEX_DSP_BASE_URL="https://apex-dsp.company.com"

# Optional
export REDIS_URL="redis://localhost:6379/0"
export SUPERSET_ENV="production"  # or development, testing
```

### Step 4: Database Migration (if needed)

If you need to store hierarchy configurations in the database:

```bash
# Create migration
superset db upgrade

# Initialize default hierarchies (optional)
python -c "
from superset.apex.hierarchy_registry import register_default_hierarchies
register_default_hierarchies()
"
```

## Configuration

### Basic Configuration

The integration uses a hierarchical configuration system:

```python
# superset_config.py

# Entitlement Service Settings
ENTITLEMENT_SERVICE_BASE_URL = 'https://entitlement.company.com'
ENTITLEMENT_SERVICE_API_KEY = 'your-api-key'
ENTITLEMENT_SERVICE_TIMEOUT = 30

# Apex DSP Settings  
APEX_DSP_BASE_URL = 'https://apex-dsp.company.com'
APEX_DSP_TOKEN_VALIDATION_ENDPOINT = '/api/v1/validate-token'

# Cache Settings
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = 'redis://localhost:6379/0'
CACHE_DEFAULT_TIMEOUT = 300

# RLS Configuration
RLS_CONFIG = {
    'enabled': True,
    'dynamic_hierarchies': True,
    'default_inheritance': 'top_down',
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
        }
    }
}
```

### Advanced Configuration

For production environments:

```python
# Production optimizations
APEX_CACHE_CLEANUP_INTERVAL = 1800  # 30 minutes
APEX_MAX_CACHE_SIZE = 50000
CACHE_DEFAULT_TIMEOUT = 1800  # 30 minutes

# Security settings
APEX_FAIL_SECURE = True  # Deny access if service unavailable
APEX_AUDIT_ENABLED = True

# Performance settings
APEX_ENTITLEMENT_BATCH_SIZE = 100
```

## Usage

### Authentication Flow

1. **User Access**: User accesses Superset through Apex platform
2. **JWT Token**: Apex DSP provides JWT token
3. **Token Validation**: Superset validates token with DSP
4. **Entitlement Fetch**: User permissions fetched from entitlement service
5. **Session Creation**: Superset session created with cached entitlements

### Permission Checking

```python
from superset.apex import check_user_permission

# Check specific permission
can_edit = check_user_permission(
    user_id="user123",
    resource_type="dashboard", 
    resource_id="dashboard_456",
    action="update"
)

# Get accessible resources
from superset.apex import get_user_accessible_resources

dashboards = get_user_accessible_resources(
    user_id="user123",
    resource_type="dashboard",
    action="read"
)
```

### Hierarchy Management

```python
from superset.apex import get_hierarchy_registry

registry = get_hierarchy_registry()

# Register new hierarchy
registry.register_hierarchy('custom_hierarchy', {
    'hierarchy_definition': ['region', 'district', 'store'],
    'column_mappings': {
        'region': 'region_code',
        'district': 'district_id',
        'store': 'store_id'
    },
    'inheritance_rules': {
        'enabled': True,
        'direction': 'top_down'
    }
})

# List hierarchies
hierarchies = registry.list_hierarchies()
```

### Cache Management

```python
from superset.apex import invalidate_user_cache, invalidate_role_cache

# Invalidate specific user
invalidate_user_cache("user123")

# Invalidate all users with role
invalidate_role_cache("analyst")
```

## API Endpoints

### Permission Check API

```bash
# Check single permission
curl -X POST "http://localhost:8088/api/v1/entitlement/permissions/check" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "resource_type": "dashboard",
    "resource_id": "dashboard_456", 
    "action": "read"
  }'

# Bulk permission check
curl -X POST "http://localhost:8088/api/v1/entitlement/permissions/bulk-check" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "resources": [
      {
        "resource_type": "dashboard",
        "resource_id": "dashboard_1",
        "actions": ["read", "update"]
      }
    ]
  }'
```

### Cache Management API

```bash
# Invalidate user cache
curl -X DELETE "http://localhost:8088/api/v1/entitlement/cache/user/user123" \
  -H "Authorization: Bearer {admin_token}"

# Invalidate role cache  
curl -X DELETE "http://localhost:8088/api/v1/entitlement/cache/role/analyst" \
  -H "Authorization: Bearer {admin_token}"

# Get cache stats
curl -X GET "http://localhost:8088/api/v1/entitlement/cache/stats" \
  -H "Authorization: Bearer {admin_token}"
```

### Hierarchy Management API

```bash
# List hierarchies
curl -X GET "http://localhost:8088/api/v1/entitlement/hierarchies" \
  -H "Authorization: Bearer {token}"

# Create hierarchy
curl -X POST "http://localhost:8088/api/v1/entitlement/hierarchies" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "hierarchy_name": "custom_hierarchy",
    "hierarchy_definition": ["level1", "level2"],
    "column_mappings": {
      "level1": "col1",
      "level2": "col2"
    }
  }'
```

## Testing

### Unit Tests

```python
# test_entitlement_integration.py
import pytest
from superset.apex import (
    check_user_permission,
    get_user_entitlements,
    get_hierarchy_registry
)

def test_permission_check():
    # Mock entitlement data
    assert check_user_permission("user123", "dashboard", "dash1", "read")

def test_hierarchy_registry():
    registry = get_hierarchy_registry()
    assert registry is not None
```

### Integration Tests

```bash
# Test with test configuration
SUPERSET_ENV=testing python -m pytest tests/apex/
```

## Troubleshooting

### Common Issues

1. **"Entitlement service unavailable"**
   - Check `ENTITLEMENT_SERVICE_BASE_URL` and `ENTITLEMENT_SERVICE_API_KEY`
   - Verify network connectivity
   - Check service health: `curl {base_url}/health`

2. **"Redis connection failed"**
   - Verify Redis is running: `redis-cli ping`
   - Check `CACHE_REDIS_URL` configuration
   - Fallback to simple cache: `CACHE_TYPE = 'simple'`

3. **"No entitlements found for user"**
   - Verify user exists in entitlement service
   - Check API key permissions
   - Enable debug logging: `logging.getLogger('superset.apex').setLevel(logging.DEBUG)`

4. **"Hierarchy not found"**
   - Check hierarchy is registered: `registry.list_hierarchies()`
   - Verify hierarchy configuration in `RLS_CONFIG`
   - Use API to create hierarchy if needed

### Debug Mode

Enable debug logging:

```python
# superset_config.py
import logging

logging.getLogger('superset.apex').setLevel(logging.DEBUG)
```

### Health Check

Check integration health:

```bash
curl -X GET "http://localhost:8088/api/v1/internal_entitlement/health"
```

## Production Deployment

### Performance Optimization

1. **Redis Configuration**:
   ```bash
   # redis.conf
   maxmemory 2gb
   maxmemory-policy allkeys-lru
   ```

2. **Cache Tuning**:
   ```python
   CACHE_DEFAULT_TIMEOUT = 1800  # 30 minutes
   APEX_MAX_CACHE_SIZE = 50000
   ```

3. **Connection Pooling**:
   ```python
   ENTITLEMENT_SERVICE_TIMEOUT = 60
   APEX_ENTITLEMENT_BATCH_SIZE = 100
   ```

### Monitoring

1. **Cache Metrics**: Monitor cache hit rates via `/api/v1/entitlement/cache/stats`
2. **API Latency**: Monitor entitlement service response times
3. **Error Rates**: Track authentication and authorization failures
4. **Memory Usage**: Monitor Redis memory usage

### High Availability

1. **Redis Cluster**: Use Redis cluster for cache redundancy
2. **Service Discovery**: Use service discovery for entitlement service endpoints
3. **Circuit Breaker**: Implement circuit breaker pattern for external service calls
4. **Graceful Degradation**: Configure `APEX_FAIL_SECURE = False` if needed

## Support

For issues and questions:

1. Check logs: `tail -f superset.log | grep apex`
2. Verify configuration: Use health check endpoint
3. Test connectivity: Direct API calls to entitlement service
4. Review documentation: This guide and design document

## Migration from Built-in Security

If migrating from Superset's built-in security:

1. **Backup**: Export existing roles and permissions
2. **Map Users**: Ensure users exist in Apex system
3. **Test**: Use testing environment first
4. **Gradual Rollout**: Enable for specific user groups initially
5. **Monitor**: Watch for authentication failures during transition 