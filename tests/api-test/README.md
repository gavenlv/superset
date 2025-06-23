# Superset API 测试套件

这个目录包含完整的 Apache Superset API 测试文件，可以导入到 Apifox、Postman 等 API 测试工具中。

## 📁 文件说明

| 文件名 | 描述 | 用途 |
|--------|------|------|
| `superset-api-collection.json` | 完整 API 测试集合 | 导入到 Apifox/Postman |
| `environment-variables.json` | 环境变量配置 | 配置测试环境 |
| `test-scenarios.http` | HTTP 文件格式测试 | VSCode REST Client |
| `validation-scripts.js` | 响应验证脚本 | 自定义验证逻辑 |
| `test-data.json` | 测试数据模板 | 测试用例数据 |

## 🚀 快速开始

### 1. Apifox 导入步骤

1. 打开 Apifox
2. 创建新项目或选择现有项目
3. 点击 "导入" → "导入数据"
4. 选择 `superset-api-collection.json` 文件
5. 导入完成后配置环境变量

### 2. 环境变量配置

在 Apifox 中设置以下环境变量：

```json
{
  "baseUrl": "http://localhost:8088",
  "username": "admin",
  "password": "admin",
  "accessToken": "",
  "refreshToken": "",
  "csrfToken": ""
}
```

### 3. Postman 导入步骤

1. 打开 Postman
2. 点击 Import → File → 选择 `superset-api-collection.json`
3. 导入后在 Collection Variables 中设置环境变量

## 📋 测试覆盖范围

### 1. 认证与授权 (Authentication)
- ✅ 用户登录 (`/api/v1/security/login`)
- ✅ 获取用户信息 (`/api/v1/me/`)
- ✅ CSRF 令牌获取 (`/api/v1/security/csrf_token/`)

### 2. 仪表板管理 (Dashboards)
- ✅ 获取仪表板列表 (`/api/v1/dashboard/`)
- ✅ 获取仪表板详情 (`/api/v1/dashboard/{id}`)
- ✅ 响应结构验证
- ✅ 数据完整性检查

### 3. 图表管理 (Charts)
- ✅ 获取图表列表 (`/api/v1/chart/`)
- ✅ 获取图表数据 (`/api/v1/chart/data`)
- ✅ 图表对象验证

### 4. 数据集管理 (Datasets)
- ✅ 获取数据集列表 (`/api/v1/dataset/`)
- ✅ 数据集结构验证

### 5. 数据库连接 (Databases)
- ✅ 获取数据库列表 (`/api/v1/database/`)
- ✅ 测试数据库连接 (`/api/v1/database/test_connection`)

### 6. SQL Lab
- ✅ 执行 SQL 查询 (`/api/v1/sqllab/execute/`)
- ✅ 获取保存的查询 (`/api/v1/saved_query/`)

### 7. 安全与权限 (Security)
- ✅ 获取角色列表 (`/api/v1/security/roles/`)
- ✅ 获取用户列表 (`/api/v1/security/users/`)

### 8. APEX JWT 认证 (Custom)
- ✅ APEX JWT 登录 (`/api/v1/apex/jwt_login`)
- ✅ 令牌验证 (`/api/v1/apex/validate_token`)

### 9. 系统健康检查 (Health)
- ✅ 健康检查 (`/health`)
- ✅ API 信息 (`/api/v1/openapi.json`)

## 🔍 验证功能

每个 API 请求都包含自动化验证：

### 状态码验证
```javascript
pm.test('API request successful', function () {
    pm.response.to.have.status(200);
});
```

### 响应结构验证
```javascript
pm.test('Response structure is valid', function () {
    const responseJson = pm.response.json();
    pm.expect(responseJson).to.have.property('result');
    pm.expect(responseJson.result).to.be.an('array');
});
```

### 数据完整性验证
```javascript
pm.test('Required fields present', function () {
    const responseJson = pm.response.json();
    if (responseJson.result.length > 0) {
        const item = responseJson.result[0];
        pm.expect(item).to.have.property('id');
        pm.expect(item).to.have.property('name');
    }
});
```

### 自动变量设置
```javascript
pm.test('Save access token', function () {
    const responseJson = pm.response.json();
    pm.collectionVariables.set('accessToken', responseJson.access_token);
});
```

## 🎯 执行顺序

建议按以下顺序执行测试：

1. **认证** → 获取访问令牌
2. **健康检查** → 验证服务状态  
3. **数据库** → 验证数据连接
4. **数据集** → 检查数据源
5. **图表** → 测试可视化功能
6. **仪表板** → 测试完整功能
7. **SQL Lab** → 测试查询功能
8. **安全** → 验证权限功能
9. **APEX** → 测试自定义认证

## 📊 预期结果

### 成功场景
- ✅ 所有 200/201 状态码
- ✅ 正确的 JSON 响应结构
- ✅ 必要字段存在且类型正确
- ✅ 令牌自动保存和使用

### 错误处理
- ⚠️ 401 - 认证失败
- ⚠️ 403 - 权限不足
- ⚠️ 404 - 资源不存在
- ⚠️ 422 - 请求参数错误

## 🛠️ 自定义配置

### 修改基础 URL
```json
{
  "baseUrl": "https://your-superset-server.com"
}
```

### 添加自定义标头
```javascript
pm.request.headers.add({
    key: 'Custom-Header',
    value: 'your-value'
});
```

### 添加新的验证逻辑
```javascript
pm.test('Custom validation', function () {
    // 你的验证逻辑
});
```

## 🔧 故障排除

### 常见问题

1. **CORS 错误**
   - 使用专业 API 客户端，不要在浏览器中直接测试
   - 确保 Superset 配置了正确的 CORS 设置

2. **认证失败**
   - 检查用户名和密码
   - 确保先执行登录请求获取令牌

3. **404 错误**
   - 检查 Superset 版本兼容性
   - 某些端点可能在不同版本中路径不同

4. **权限错误**
   - 确保用户有足够权限访问相应资源
   - 检查角色和权限配置

## 📈 扩展建议

1. **添加更多测试场景**
   - 创建/更新/删除操作
   - 错误边界测试
   - 性能测试

2. **集成 CI/CD**
   - 使用 Newman 在命令行运行测试
   - 集成到自动化流水线

3. **数据驱动测试**
   - 使用 CSV 文件提供测试数据
   - 批量测试不同场景

4. **监控集成**
   - 定期运行健康检查
   - 设置告警机制

## 📞 支持

如有问题或需要帮助，请查看：
- Superset 官方文档
- API 文档：`http://localhost:8088/swagger/v1`
- 本测试套件的验证脚本和示例 