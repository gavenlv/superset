# Superset JWT 认证部署指南

## 部署步骤

### 1. 文件更改清单

确保以下文件已正确修改：

- `superset/security/decorators.py` - 新的 JWT 认证装饰器
- `superset/security/api.py` - JWT 登录和刷新端点
- `superset/security/manager.py` - SecurityManager 更新以支持 JWT
- `superset/config.py` - JWT 配置选项
- `superset/dashboards/api.py` - 示例端点修改

### 2. 配置文件设置

在 `superset_config.py` 中添加以下配置：

```python
# JWT Authentication Configuration
# 强烈建议在生产环境中设置独立的 JWT 密钥
JWT_SECRET_KEY = "your-very-secure-jwt-secret-key-here"  # 修改为强密钥

# JWT token 过期时间（可根据需要调整）
JWT_ACCESS_TOKEN_EXPIRES = 3600      # 1小时
JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30天

# 启用 JWT 认证
ENABLE_JWT_AUTHENTICATION = True

# JWT 算法（推荐使用 HS256）
JWT_ALGORITHM = "HS256"
```

### 3. 数据库无需更改

JWT 认证不需要任何数据库模式更改。它与现有的用户表兼容。

### 4. 重启服务

部署完成后，重启 Superset 服务：

```bash
# 如果使用 gunicorn
sudo systemctl restart superset

# 或者如果使用开发服务器
superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger
```

## 验证部署

### 1. 测试 JWT 登录

```bash
# 使用 curl 测试登录
curl -X POST http://localhost:8088/api/v1/security/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# 应该返回类似以下的响应：
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
#   "expires_in": 3600
# }
```

### 2. 测试 API 调用

```bash
# 使用获得的 token 调用 API
curl -X GET http://localhost:8088/api/v1/dashboard/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

### 3. 使用 Python 测试脚本

运行提供的测试脚本：

```bash
python test_jwt_simple.py
```

## 故障排除

### 1. WebSocket 404 错误

如果你在日志中看到类似以下的错误：

```
GET /ws HTTP/1.1" 404 -
werkzeug.exceptions.NotFound: 404 Not Found
```

这些错误与 JWT 认证无关，是 WebSocket 连接尝试引起的。可以通过以下方式解决：

**方法1: 在配置中禁用 WebSocket**
```python
# 在 superset_config.py 中添加
GLOBAL_ASYNC_QUERIES_TRANSPORT = "polling"
# 注释掉或删除 WebSocket URL
# GLOBAL_ASYNC_QUERIES_WEBSOCKET_URL = "ws://127.0.0.1:8080/"
```

**方法2: 禁用全局异步查询功能**
```python
# 在 superset_config.py 中添加
FEATURE_FLAGS = {
    "GLOBAL_ASYNC_QUERIES": False,
}
```

### 2. CSRF Token 错误

如果收到 CSRF token 错误，确保已将 JWT 端点添加到 CSRF 豁免列表：

```python
WTF_CSRF_EXEMPT_LIST = [
    "superset.views.core.log",
    "superset.views.core.explore_json", 
    "superset.charts.data.api.data",
    "superset.dashboards.api.cache_dashboard_screenshot",
    "superset.security.api.login",      # JWT 登录端点
    "superset.security.api.refresh",    # JWT 刷新端点
]
```

### 3. Token 过期问题

如果 token 过期太快，可以调整过期时间：

```python
# 增加 token 有效期
JWT_ACCESS_TOKEN_EXPIRES = 86400      # 24小时
JWT_REFRESH_TOKEN_EXPIRES = 604800    # 7天
```

### 4. 导入错误

如果遇到导入错误，确保安装了 PyJWT 库：

```bash
pip install PyJWT
# 或者
pip install 'PyJWT>=2.0.0'
```

### 5. 检查日志

如果遇到其他问题，检查 Superset 日志：

```bash
# 查看最近的日志
tail -f superset.log

# 或者如果使用 systemd
journalctl -u superset -f
```

## 安全建议

1. **JWT 密钥安全**: 在生产环境中使用强随机密钥
2. **Token 过期时间**: 根据安全需求设置合适的过期时间
3. **HTTPS**: 在生产环境中始终使用 HTTPS
4. **Token 存储**: 在客户端安全存储 JWT token
5. **定期轮换**: 定期更换 JWT 密钥

## 性能优化

1. **Token 缓存**: 考虑缓存已验证的 token 以提高性能
2. **并发**: JWT 认证支持高并发访问
3. **监控**: 监控 JWT 认证端点的性能和错误率

## 生产环境配置

### 1. 安全设置

```python
# 生产环境推荐配置
JWT_SECRET_KEY = os.environ.get('SUPERSET_JWT_SECRET_KEY')  # 从环境变量读取
JWT_ACCESS_TOKEN_EXPIRES = 1800   # 30分钟，更短的过期时间
JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7天，较短的刷新令牌过期时间

# 确保使用 HTTPS
TALISMAN_ENABLED = True
TALISMAN_CONFIG = {
    "force_https": True,
    # 其他安全头配置...
}
```

### 2. 负载均衡配置

如果使用负载均衡器，确保：

- JWT token 是无状态的，不依赖会话亲和性
- 所有服务器实例使用相同的 JWT_SECRET_KEY

### 3. 监控和日志

添加监控来跟踪：
- JWT 认证失败率
- Token 刷新频率
- API 访问模式

## 迁移策略

### 渐进式迁移

1. **阶段 1**: 部署 JWT 功能，但保持所有端点使用 `@protect_with_jwt()` 装饰器（支持两种认证方式）

2. **阶段 2**: 更新客户端应用程序以使用 JWT token

3. **阶段 3**: 监控 cookie 认证的使用情况

4. **阶段 4**: 根据需要，将特定端点改为 `@jwt_required` 装饰器

### 回滚计划

如果需要回滚：

1. 将所有 `@protect_with_jwt()` 和 `@jwt_required` 装饰器改回 `@protect()`
2. 在配置中设置 `ENABLE_JWT_AUTHENTICATION = False`
3. 重启服务

## 故障排查

### 常见问题

1. **JWT token 无效**
   - 检查 JWT_SECRET_KEY 是否在所有服务器实例中一致
   - 验证 token 格式和内容

2. **认证失败**
   - 检查用户凭据
   - 验证用户账户状态
   - 查看认证相关日志

3. **权限错误**
   - 确认用户角色和权限配置
   - 检查 Flask-AppBuilder 权限设置

### 调试模式

启用调试日志：

```python
import logging
logging.getLogger('superset.security').setLevel(logging.DEBUG)
```

### 性能监控

监控以下指标：
- JWT 验证时间
- 数据库查询次数（用户验证）
- API 响应时间

## 安全最佳实践

1. **密钥管理**
   - 使用强随机密钥
   - 定期轮换密钥
   - 在环境变量中存储敏感配置

2. **网络安全**
   - 强制使用 HTTPS
   - 配置适当的 CORS 策略
   - 使用安全头

3. **令牌管理**
   - 设置合理的过期时间
   - 实现令牌撤销机制（如需要）
   - 监控异常令牌使用

4. **访问控制**
   - 保持现有的角色和权限系统
   - 定期审核用户权限
   - 记录和监控 API 访问

## 兼容性说明

- 此实现与 Superset 1.x+ 版本兼容
- 与现有的 Flask-AppBuilder 认证系统完全兼容
- 不影响现有的用户管理和权限系统
- 支持所有现有的认证方法（LDAP、OAuth 等） 