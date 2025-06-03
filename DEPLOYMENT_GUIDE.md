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

### 1. 检查端点可用性

```bash
# 检查登录端点
curl -X POST http://your-superset-domain/api/v1/security/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# 应该返回 401 或 200 状态码（取决于凭据是否有效）
```

### 2. 运行测试脚本

```bash
python test_jwt_auth.py --url http://your-superset-domain --username admin --password your-admin-password
```

### 3. 检查日志

查看 Superset 日志确保没有错误：

```bash
# 检查应用日志
tail -f /var/log/superset/superset.log

# 或者查看 systemctl 日志
journalctl -u superset -f
```

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