# Superset Apex Module

## 概述

Apex模块为Apache Superset提供了增强的认证功能，特别是支持JWT header认证和Swagger UI的免登录访问。这个模块是为了方便第三方系统调用Superset API而设计的，同时保持与现有认证系统的兼容性。

## 功能特性

### 1. JWT Header 认证
- 支持通过HTTP Authorization header进行JWT认证
- 与现有的cookie认证系统兼容
- 使用Bearer token格式 (`Authorization: Bearer <token>`)
- 支持自定义token过期时间

### 2. Swagger UI 免登录访问
- 允许匿名访问Swagger UI文档
- API调用仍然需要认证，确保安全性
- 配置化的匿名访问路径

### 3. 增强的API端点
- `/api/v1/apex/jwt_login` - 获取JWT token
- `/api/v1/apex/validate_token` - 验证JWT token

## 安装和配置

### 1. 集成到Superset

在你的Superset配置文件 (`superset_config.py`) 中添加以下配置：

```python
# 启用Apex模块
from superset.apex.config import APEX_CONFIG

# 合并Apex配置
for key, value in APEX_CONFIG.items():
    globals()[key] = value

# 或者手动配置各项设置
APEX_JWT_HEADER_AUTH_ENABLED = True
APEX_SWAGGER_ANONYMOUS_ENABLED = True
APEX_API_ENABLED = True
```

### 2. 在应用初始化时启用Apex

在Superset的应用初始化过程中（例如在Flask app factory中）添加：

```python
from superset.apex.config import init_apex

def create_app():
    app = Flask(__name__)
    
    # ... 其他初始化代码 ...
    
    # 初始化Apex模块
    init_apex(app)
    
    return app
```

### 3. 配置选项

```python
# JWT Header认证设置
APEX_JWT_HEADER_AUTH_ENABLED = True          # 启用JWT header认证
APEX_JWT_DEFAULT_EXPIRES_IN = 86400          # 默认token过期时间（秒）

# Swagger UI匿名访问设置
APEX_SWAGGER_ANONYMOUS_ENABLED = True        # 启用Swagger UI匿名访问
APEX_SWAGGER_ANONYMOUS_PATHS = [             # 允许匿名访问的路径
    "/swagger",
    "/api/v1/_openapi",
    "/api/v1/_openapi.json",
    "/swaggerui/",
]

# API端点设置
APEX_API_ENABLED = True                      # 启用Apex API端点
APEX_API_PREFIX = "/api/v1/apex"            # API路径前缀
```

## 使用方法

### 1. 获取JWT Token

发送POST请求到 `/api/v1/apex/jwt_login`：

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

响应：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### 2. 使用JWT Token调用API

在HTTP请求的Authorization header中包含JWT token：

```bash
curl -X GET "http://your-superset-domain/api/v1/chart/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 3. 验证Token

验证当前token是否有效：

```bash
curl -X POST "http://your-superset-domain/api/v1/apex/validate_token" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

响应：
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

### 4. 访问Swagger UI

直接访问Swagger UI，无需登录：

```
http://your-superset-domain/swagger/
http://your-superset-domain/api/v1/_openapi
```

## 第三方集成示例

### Python 示例

```python
import requests
import json

class SupersetClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.token = self._get_token(username, password)
    
    def _get_token(self, username, password):
        """获取JWT token"""
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
        """获取包含认证信息的请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_charts(self):
        """获取图表列表"""
        url = f"{self.base_url}/api/v1/chart/"
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()
    
    def get_dashboards(self):
        """获取仪表板列表"""
        url = f"{self.base_url}/api/v1/dashboard/"
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

# 使用示例
client = SupersetClient(
    base_url="http://your-superset-domain",
    username="your_username", 
    password="your_password"
)

charts = client.get_charts()
dashboards = client.get_dashboards()
```

### JavaScript 示例

```javascript
class SupersetClient {
    constructor(baseUrl, username, password) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.initializeToken(username, password);
    }
    
    async initializeToken(username, password) {
        const loginUrl = `${this.baseUrl}/api/v1/apex/jwt_login`;
        const response = await fetch(loginUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                provider: 'db'
            })
        });
        
        if (!response.ok) {
            throw new Error('Login failed');
        }
        
        const data = await response.json();
        this.token = data.access_token;
    }
    
    getHeaders() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }
    
    async apiCall(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.statusText}`);
        }
        
        return response.json();
    }
    
    async getCharts() {
        return this.apiCall('/api/v1/chart/');
    }
    
    async getDashboards() {
        return this.apiCall('/api/v1/dashboard/');
    }
}

// 使用示例
const client = new SupersetClient(
    'http://your-superset-domain',
    'your_username',
    'your_password'
);

client.getCharts().then(charts => console.log(charts));
client.getDashboards().then(dashboards => console.log(dashboards));
```

## 安全注意事项

1. **JWT Token安全**：
   - JWT token包含敏感信息，请安全存储
   - 在生产环境中使用HTTPS传输
   - 定期更新token，避免长期使用同一token

2. **配置安全**：
   - 确保`SECRET_KEY`足够复杂且保密
   - 根据需要调整token过期时间
   - 定期审查匿名访问路径的配置

3. **Swagger UI**：
   - Swagger UI本身不提供数据访问，只是文档展示
   - 实际的API调用仍需要认证
   - 可以根据需要禁用匿名访问

## 故障排除

### 常见问题

1. **Token认证失败**：
   - 检查token是否过期
   - 验证SECRET_KEY配置是否正确
   - 确认token格式是否正确（Bearer prefix）

2. **Swagger UI无法访问**：
   - 检查`APEX_SWAGGER_ANONYMOUS_ENABLED`配置
   - 验证路径配置是否正确
   - 确认Flask-AppBuilder的Swagger UI已启用

3. **API调用失败**：
   - 检查JWT header格式
   - 验证用户权限
   - 查看Superset日志获取详细错误信息

### 调试

启用调试日志：

```python
import logging
logging.getLogger('superset.apex').setLevel(logging.DEBUG)
```

## 版本兼容性

- 支持Apache Superset 2.0+
- 需要PyJWT库支持
- 兼容Flask-AppBuilder认证系统

## 许可证

本模块遵循Apache Superset的Apache License 2.0许可证。 