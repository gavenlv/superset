# Superset JWT Authentication Implementation

## 概述

本实现为 Apache Superset 添加了 JWT (JSON Web Token) 认证支持，允许 Swagger API 调用仅使用 JWT token 而无需依赖 cookie。这个改造保持了向后兼容性，现有的 cookie 认证机制仍然可以正常工作。

## 功能特性

1. **JWT Token 认证**: 支持通过 `Authorization: Bearer <token>` 头进行认证
2. **向后兼容**: 保持对现有 cookie 认证的支持
3. **灵活配置**: 可以配置只使用 JWT、只使用 cookie 或两者并用
4. **Refresh Token 支持**: 实现了访问令牌刷新机制
5. **安全性**: 使用标准的 JWT 签名和过期机制

## 配置选项

在 `superset/config.py` 中添加了以下配置选项：

```python
# JWT Configuration for API Authentication
JWT_SECRET_KEY: Optional[str] = None          # JWT 密钥，默认使用 SECRET_KEY
JWT_ALGORITHM = "HS256"                       # JWT 签名算法
JWT_ACCESS_TOKEN_EXPIRES = 3600               # 访问令牌过期时间（秒）
JWT_REFRESH_TOKEN_EXPIRES = 30 * 24 * 3600   # 刷新令牌过期时间（秒）
ENABLE_JWT_AUTHENTICATION = True             # 启用 JWT 认证
JWT_HEADER_NAME = "Authorization"            # JWT 令牌头名称
JWT_HEADER_TYPE = "Bearer"                   # JWT 令牌类型
```

## API 端点

### 1. 登录获取 JWT Token

**端点**: `POST /api/v1/security/login/`

**请求体**:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 3600
}
```

### 2. 刷新访问令牌

**端点**: `POST /api/v1/security/refresh/`

**请求体**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 3600
}
```

## 使用方法

### 1. 获取 JWT Token

```bash
curl -X POST http://localhost:8088/api/v1/security/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin"
  }'
```

### 2. 使用 JWT Token 访问 API

```bash
curl -X GET http://localhost:8088/api/v1/dashboard/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 3. 刷新过期的 Token

```bash
curl -X POST http://localhost:8088/api/v1/security/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

## 装饰器使用

### 1. 支持 JWT 和 Cookie 认证（推荐）

```python
from superset.security.decorators import protect_with_jwt

class MyAPI(BaseSupersetApi):
    @expose("/my-endpoint/", methods=("GET",))
    @protect_with_jwt()
    @safe
    def my_endpoint(self) -> Response:
        # 此端点同时支持 JWT token 和 cookie 认证
        return self.response(200, result="success")
```

### 2. 仅支持 JWT 认证

```python
from superset.security.decorators import jwt_required

class MyAPI(BaseSupersetApi):
    @expose("/jwt-only/", methods=("GET",))
    @jwt_required
    @safe
    def jwt_only_endpoint(self) -> Response:
        # 此端点仅支持 JWT token 认证
        return self.response(200, result="success")
```

### 3. 自定义认证选项

```python
from superset.security.decorators import jwt_protect

class MyAPI(BaseSupersetApi):
    @expose("/custom-auth/", methods=("GET",))
    @jwt_protect(allow_cookie_auth=True, allow_jwt_auth=True)
    @safe
    def custom_auth_endpoint(self) -> Response:
        # 自定义认证配置
        return self.response(200, result="success")
```

## JWT Token 结构

访问令牌包含以下字段：
```json
{
  "user_id": 1,
  "username": "admin",
  "iat": 1640995200,
  "exp": 1640998800,
  "type": "access"
}
```

刷新令牌包含以下字段：
```json
{
  "user_id": 1,
  "username": "admin", 
  "iat": 1640995200,
  "exp": 1643587200,
  "type": "refresh"
}
```

## 安全考虑

1. **密钥管理**: 确保 `JWT_SECRET_KEY` 是强密钥，生产环境中不要使用默认值
2. **HTTPS**: 生产环境中必须使用 HTTPS 传输 JWT token
3. **令牌存储**: 客户端应安全存储 JWT token，避免 XSS 攻击
4. **令牌过期**: 合理设置访问令牌的过期时间，平衡安全性和用户体验
5. **刷新令牌**: 刷新令牌应有更长的过期时间，但也要定期轮换

## 兼容性

- 此实现完全向后兼容现有的 cookie 认证机制
- 现有的 API 端点无需修改即可继续使用 cookie 认证
- 可以逐步迁移到 JWT 认证，或同时支持两种认证方式

## 故障排查

### 1. JWT Token 无效

检查：
- token 是否正确包含在 Authorization 头中
- token 是否已过期
- JWT_SECRET_KEY 配置是否正确

### 2. 认证失败

检查：
- 用户账户是否激活
- 用户名和密码是否正确
- 数据库连接是否正常

### 3. 权限错误

检查：
- 用户是否有访问特定端点的权限
- 角色配置是否正确

## 测试

可以使用以下 Python 代码测试 JWT 认证：

```python
import requests
import json

# 1. 登录获取 token
login_response = requests.post(
    "http://localhost:8088/api/v1/security/login/",
    json={
        "username": "admin",
        "password": "admin"
    }
)
token_data = login_response.json()
access_token = token_data["access_token"]

# 2. 使用 token 访问 API
headers = {"Authorization": f"Bearer {access_token}"}
api_response = requests.get(
    "http://localhost:8088/api/v1/dashboard/",
    headers=headers
)

print("API Response:", api_response.json())
``` 