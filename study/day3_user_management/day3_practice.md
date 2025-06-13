# Day 3 实践指南：用户管理与权限系统 🛠️

## 练习目标

通过今天的实践，你将亲手操作：
- **创建和管理用户**：从命令行到 Web 界面的完整用户管理
- **角色权限分配**：理解不同角色的权限范围和应用场景
- **权限测试验证**：验证权限系统的有效性
- **安全配置实践**：配置企业级安全策略

## 环境准备

确保你已经完成了前两天的学习，并且 Superset 环境正常运行。

---

## 练习 1：创建第一个超级用户 👤

由于我们在前两天还没有创建管理员用户，现在是时候创建一个了！

### 步骤 1：使用 CLI 创建超级用户

```bash
# 在 Superset 项目根目录下执行
superset fab create-admin

# 或者使用更详细的命令
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@superset.com \
    --password admin123
```

**预期输出**：
```
User admin created successfully
```

### 步骤 2：验证用户创建

```bash
# 查看数据库中的用户
superset fab list-users
```

**练习要点**：
- 观察密码是如何被加密存储的
- 理解 CLI 命令与数据库操作的关系
- 注意默认分配的 Admin 角色

### 步骤 3：首次登录测试

1. 启动 Superset 服务器：
   ```bash
   superset run -p 8088 --with-threads --reload --debugger
   ```

2. 打开浏览器访问 `http://localhost:8088`

3. 使用创建的管理员账户登录

**期望结果**：
- 成功登录到 Superset 主界面
- 可以看到所有菜单选项（因为是 Admin 角色）
- 右上角显示用户信息

---

## 练习 2：理解内置角色权限 🔐

### 步骤 1：探索 Admin 角色权限

1. 以 Admin 身份登录
2. 访问 **Security → List Roles** 查看所有角色
3. 点击 **Admin** 角色，查看其权限列表

**观察重点**：
- Admin 角色拥有多少权限？
- 哪些权限是 Admin 独有的？
- 权限的命名规律是什么？

### 步骤 2：创建不同角色的测试用户

在 Superset Web 界面中：

**创建 Alpha 用户**：
1. **Security → List Users → + 按钮**
2. 填写信息：
   - Username: `analyst1`
   - First Name: `Data`
   - Last Name: `Analyst`
   - Email: `analyst@company.com`
   - Active: ✅
   - Roles: 选择 `Alpha`
3. 保存

**创建 Gamma 用户**：
1. 重复上述步骤
2. 填写信息：
   - Username: `viewer1`
   - First Name: `Report`
   - Last Name: `Viewer`
   - Email: `viewer@company.com`
   - Active: ✅
   - Roles: 选择 `Gamma`

### 步骤 3：权限对比测试

**测试方法**：
1. 在不同浏览器（或隐私模式）中分别登录三个用户
2. 对比界面菜单和功能的差异

**观察对比表**：

| 功能 | Admin | Alpha | Gamma |
|------|-------|-------|-------|
| 创建仪表盘 | ✅ | ✅ | ❌ |
| 查看仪表盘 | ✅ | ✅ | ✅ |
| 用户管理 | ✅ | ❌ | ❌ |
| SQL Lab | ✅ | ✅ | ❌ |
| 数据库连接 | ✅ | ✅ | ❌ |
| 角色管理 | ✅ | ❌ | ❌ |

---

## 练习 3：深入权限机制测试 🧪

### 步骤 1：创建测试数据

1. 以 `analyst1`（Alpha 角色）登录
2. 尝试创建一个简单的图表：
   - **Charts → + 按钮**
   - 选择数据源（如果有的话）
   - 创建一个基础图表并保存

3. 创建一个测试仪表盘：
   - **Dashboards → + 按钮**
   - 命名为 "测试仪表盘"
   - 保存

### 步骤 2：权限边界测试

**测试 Alpha 用户的限制**：
1. 尝试访问 **Security** 菜单
   - **预期结果**：应该看不到或无法访问
2. 尝试管理其他用户
   - **预期结果**：无权限提示

**测试 Gamma 用户的限制**：
1. 以 `viewer1` 登录
2. 尝试创建新图表
   - **预期结果**：无权限或找不到创建按钮
3. 尝试编辑现有仪表盘
   - **预期结果**：只能查看，无法编辑

### 步骤 3：权限错误处理验证

**直接URL访问测试**：
1. 以 Gamma 用户身份登录
2. 直接访问管理 URL：`http://localhost:8088/users/list/`
3. 观察系统如何处理无权限访问

**期望行为**：
- 重定向到无权限页面
- 显示友好的错误信息
- 记录访问日志

---

## 练习 4：权限系统源码验证 🔍

### 步骤 1：查看权限数据库表

如果你有数据库访问权限，可以查看权限相关的表：

```sql
-- 查看所有角色
SELECT * FROM ab_role;

-- 查看所有权限
SELECT * FROM ab_permission;

-- 查看用户-角色关系
SELECT u.username, r.name as role_name
FROM ab_user u
JOIN ab_user_role ur ON u.id = ur.user_id
JOIN ab_role r ON ur.role_id = r.id;

-- 查看角色-权限关系（复杂查询）
SELECT r.name as role_name, p.name as permission, vm.name as view_menu
FROM ab_role r
JOIN ab_permission_view_role pvr ON r.id = pvr.role_id
JOIN ab_permission_view pv ON pvr.permission_view_id = pv.id
JOIN ab_permission p ON pv.permission_id = p.id
JOIN ab_view_menu vm ON pv.view_menu_id = vm.id
ORDER BY r.name, vm.name, p.name;
```

### 步骤 2：验证权限同步机制

```bash
# 重新同步权限（这会更新角色权限）
superset init

# 观察输出日志，查看权限同步过程
```

**观察要点**：
- 哪些权限被创建或更新？
- 角色权限如何被重新分配？
- 同步过程的时间和复杂度

---

## 练习 5：自定义权限配置 ⚙️

### 步骤 1：创建自定义角色

1. 以 Admin 身份登录
2. **Security → List Roles → + 按钮**
3. 创建新角色：
   - Name: `DataViewer`
   - 选择特定权限：
     - `can_list on DashboardModelView`
     - `can_show on DashboardModelView`
     - `can_list on SliceModelView`
     - `can_show on SliceModelView`
     - `menu_access on Dashboards`
     - `menu_access on Charts`

### 步骤 2：测试自定义角色

1. 创建一个新用户分配 `DataViewer` 角色
2. 测试该用户的权限范围
3. 验证权限是否符合预期

### 步骤 3：权限调试

如果遇到权限问题，可以通过以下方式调试：

```bash
# 查看 Superset 日志
tail -f superset.log

# 或者启动时启用详细日志
superset run --debug
```

---

## 思考题 🤔

### 基础理解题

1. **角色设计题**：如果你要为一个销售团队配置 Superset，需要以下角色：
   - 销售总监：可以查看所有销售数据和报表
   - 区域经理：只能查看自己区域的数据
   - 销售代表：只能查看自己的业绩数据
   
   你会如何设计角色和权限？

2. **权限边界题**：为什么 Gamma 用户不能访问 SQL Lab？这样设计的安全考虑是什么？

3. **扩展性题**：当 Superset 部署到生产环境，用户数量达到几百人时，如何有效管理角色和权限？

### 高级应用题

4. **行级安全题**：如何实现"销售代表只能看到自己客户的数据"这种行级权限控制？

5. **集成认证题**：如果公司使用 LDAP 或 Active Directory，如何与 Superset 的权限系统集成？

6. **权限审计题**：如何追踪和审计用户的权限使用情况？

---

## 深入练习（可选）🚀

### 1. 权限系统源码阅读

```bash
# 阅读关键源码文件
grep -r "has_access" superset/
grep -r "sync_role_definitions" superset/

# 查看安全管理器实现
cat superset/security/manager.py | head -100
```

### 2. 自定义安全管理器

尝试创建一个自定义的 SecurityManager 类，添加额外的权限逻辑。

### 3. 权限性能测试

测试在大量用户和权限情况下的性能表现：
- 创建 100+ 用户
- 分配不同角色
- 测试登录和权限检查的响应时间

### 4. 安全策略配置

实践配置企业级安全策略：
- 密码复杂度要求
- 会话超时设置
- 失败登录锁定
- HTTPS 强制使用

---

## 成果验证 ✅

完成今天的练习后，你应该能够：

### 技能掌握
- [x] 熟练创建和管理 Superset 用户
- [x] 理解不同角色的权限边界
- [x] 配置自定义角色和权限
- [x] 诊断和解决权限相关问题

### 理论理解
- [x] 深度理解 RBAC 权限模型
- [x] 掌握 Flask-AppBuilder 安全机制
- [x] 理解权限检查和同步流程
- [x] 知晓企业级安全最佳实践

### 实际应用
- [x] 能够为真实业务场景设计权限方案
- [x] 具备 Superset 生产环境部署的安全考虑
- [x] 掌握权限系统的维护和故障排除

**恭喜你完成第三天的学习！** 🎉

现在你不仅理解了 Superset 的技术架构，还掌握了其用户管理和权限系统的精髓。这为你在企业环境中部署和管理 Superset 奠定了坚实的基础！ 