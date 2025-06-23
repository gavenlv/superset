# Superset Apex Module

## Overview

The Apex module provides enhanced authentication capabilities for Apache Superset, specifically supporting JWT header authentication and anonymous access to Swagger UI. This module is designed to facilitate third-party system API calls to Superset while maintaining compatibility with existing authentication systems.

## Features

### 1. JWT Header Authentication
- Supports JWT authentication via HTTP Authorization header
- Compatible with existing cookie authentication system
- Uses Bearer token format (`Authorization: Bearer <token>`)
- Supports custom token expiration times

### 2. Anonymous Swagger UI Access
- Allows anonymous access to Swagger UI documentation
- API calls still require authentication for security
- Configurable anonymous access paths

### 3. Enhanced API Endpoints
- `/api/v1/apex/jwt_login` - Obtain JWT token
- `/api/v1/apex/validate_token` - Validate JWT token

## Installation and Configuration

### 1. Integration with Superset

Add the following configuration to your Superset configuration file (`superset_config.py`):

```python
# Enable Apex module
from superset.apex.config import APEX_CONFIG

# Merge Apex configuration
for key, value in APEX_CONFIG.items():
    globals()[key] = value

# Or manually configure each setting
APEX_JWT_HEADER_AUTH_ENABLED = True
APEX_SWAGGER_ANONYMOUS_ENABLED = True
APEX_API_ENABLED = True
```

### 2. Enable Apex During App Initialization

Add the following to Superset's application initialization process (e.g., in Flask app factory):

```python
from superset.apex.config import init_apex

def create_app():
    app = Flask(__name__)
    
    # ... other initialization code ...
    
    # Initialize Apex module
    init_apex(app)
    
    return app
```

### 3. Configuration Options

```python
# JWT Header Authentication Settings
APEX_JWT_HEADER_AUTH_ENABLED = True          # Enable JWT header authentication
APEX_JWT_DEFAULT_EXPIRES_IN = 86400          # Default token expiration time (seconds)

# Swagger UI Anonymous Access Settings
APEX_SWAGGER_ANONYMOUS_ENABLED = True        # Enable Swagger UI anonymous access
APEX_SWAGGER_ANONYMOUS_PATHS = [             # Paths allowing anonymous access
    "/swagger",
    "/api/v1/_openapi",
    "/api/v1/_openapi.json",
    "/swaggerui/",
]

# API Endpoint Settings
APEX_API_ENABLED = True                      # Enable Apex API endpoints
APEX_API_PREFIX = "/api/v1/apex"            # API path prefix
```

## Usage

### 1. Obtain JWT Token

Send a POST request to `/api/v1/apex/jwt_login`:

```bash
curl -X POST "http://your-superset-domain/api/v1/apex/jwt_login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password",
    "provider": "db",
    "expires_in": 86400
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### 2. Use JWT Token for API Calls

Include the JWT token in the Authorization header of HTTP requests:

```bash
curl -X GET "http://your-superset-domain/api/v1/chart/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 3. Validate Token

Verify if the current token is valid:

```bash
curl -X POST "http://your-superset-domain/api/v1/apex/validate_token" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

Response:
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "username": "admin",
    "first_name": "Admin",
    "last_name": "User"
  }
}
```

### 4. Access Swagger UI

Access Swagger UI directly without login:

```
http://your-superset-domain/swagger/
http://your-superset-domain/api/v1/_openapi
```

## Third-party Integration Examples

### Python Example

```python
import requests
import json

class SupersetClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.token = self._get_token(username, password)
    
    def _get_token(self, username, password):
        """Get JWT token"""
        login_url = f"{self.base_url}/api/v1/apex/jwt_login"
        data = {
            "username": username,
            "password": password,
            "provider": "db"
        }
        
        response = requests.post(login_url, json=data)
        response.raise_for_status()
        
        return response.json()["access_token"]
    
    def get_headers(self):
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_charts(self):
        """Get chart list"""
        url = f"{self.base_url}/api/v1/chart/"
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()
    
    def get_dashboards(self):
        """Get dashboard list"""
        url = f"{self.base_url}/api/v1/dashboard/"
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

# Usage example
client = SupersetClient(
    base_url="http://your-superset-domain",
    username="your_username",
    password="your_password"
)

charts = client.get_charts()
dashboards = client.get_dashboards()
```

### JavaScript Example

```javascript
class SupersetClient {
    constructor(baseUrl, username, password) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.token = null;
        this.init(username, password);
    }
    
    async init(username, password) {
        this.token = await this._getToken(username, password);
    }
    
    async _getToken(username, password) {
        const loginUrl = `${this.baseUrl}/api/v1/apex/jwt_login`;
        const data = {
            username: username,
            password: password,
            provider: 'db'
        };
        
        const response = await fetch(loginUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Login failed');
        }
        
        const result = await response.json();
        return result.access_token;
    }
    
    getHeaders() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }
    
    async getCharts() {
        const url = `${this.baseUrl}/api/v1/chart/`;
        const response = await fetch(url, {
            headers: this.getHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch charts');
        }
        
        return await response.json();
    }
    
    async getDashboards() {
        const url = `${this.baseUrl}/api/v1/dashboard/`;
        const response = await fetch(url, {
            headers: this.getHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch dashboards');
        }
        
        return await response.json();
    }
}

// Usage
const client = new SupersetClient(
    'http://your-superset-domain',
    'your_username',
    'your_password'
);

client.getCharts().then(charts => console.log(charts));
client.getDashboards().then(dashboards => console.log(dashboards));
```

## Security Considerations

### JWT Token Security
- Tokens are signed using Superset's SECRET_KEY
- Use HTTPS in production environments
- Set appropriate token expiration times
- Store tokens securely in client applications

### API Security
- JWT authentication does not bypass Superset's permission system
- Users can only access resources they have permission for
- API rate limiting should be implemented for production use

### Swagger UI Security
- Only documentation paths are accessible anonymously
- All API calls still require authentication
- Consider restricting Swagger UI access in production

## Troubleshooting

### Common Issues

1. **Token validation fails**
   - Check if SECRET_KEY is consistent
   - Verify token hasn't expired
   - Ensure proper Bearer token format

2. **Swagger UI not accessible**
   - Verify APEX_SWAGGER_ANONYMOUS_ENABLED is True
   - Check FAB_API_SWAGGER_UI configuration
   - Ensure anonymous paths are correctly configured

3. **API calls fail with JWT token**
   - Verify token is included in Authorization header
   - Check user permissions for the requested resource
   - Ensure Apex middleware is properly initialized

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
# In superset_config.py
import logging
logging.getLogger('superset.apex').setLevel(logging.DEBUG)
```

## Advanced Configuration

### Custom JWT Claims

You can extend JWT tokens with custom claims:

```python
# In superset_config.py
APEX_JWT_CUSTOM_CLAIMS = {
    'organization': 'your_org',
    'role': 'api_user'
}
```

### Custom Authentication Provider

For custom authentication logic:

```python
# In superset_config.py
from superset.apex.jwt_auth import JwtHeaderAuthenticator

class CustomJwtAuthenticator(JwtHeaderAuthenticator):
    def authenticate_user(self, user_id, username):
        # Custom authentication logic
        return super().authenticate_user(user_id, username)

APEX_JWT_AUTHENTICATOR_CLASS = CustomJwtAuthenticator
```

## API Reference

### POST /api/v1/apex/jwt_login

Login and obtain JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "provider": "string",
  "expires_in": "integer (optional)"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": "integer"
}
```

### POST /api/v1/apex/validate_token

Validate current JWT token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "valid": "boolean",
  "user": {
    "id": "integer",
    "username": "string",
    "first_name": "string",
    "last_name": "string"
  }
}
```

## Contributing

When contributing to the Apex module:

1. Maintain backward compatibility
2. Add comprehensive tests for new features
3. Update documentation
4. Follow Superset's coding standards
5. Test integration with various Superset versions

## License

This module follows the same license as Apache Superset. 