# 🚨 Superset常见问题快速排查指南

## 🏁 启动问题

### 1. 应用无法启动

**症状**: `superset run` 命令失败

**排查步骤**:
```bash
# 1. 检查Python版本
python --version  # 需要Python 3.8+

# 2. 检查依赖安装
pip show apache-superset

# 3. 检查数据库连接
superset db upgrade

# 4. 检查配置文件
export SUPERSET_CONFIG_PATH=/path/to/superset_config.py
python -c "import superset.config; print('Config loaded successfully')"

# 5. 检查端口占用
netstat -tulpn | grep :8088
```

**常见解决方案**:
```bash
# 重置数据库
superset db upgrade
superset fab create-admin  # 创建管理员用户
superset init

# 清理缓存
rm -rf ~/.superset
pip cache purge
```

### 2. 前端编译失败

**症状**: `npm run dev` 报错

**排查步骤**:
```bash
# 1. 检查Node.js版本
node --version  # 需要Node 16+

# 2. 清理依赖
rm -rf node_modules package-lock.json
npm install

# 3. 检查内存
node --max-old-space-size=4096 node_modules/.bin/webpack --mode development

# 4. 查看详细错误
npm run dev --verbose
```

## 🗄️ 数据库问题

### 1. 连接失败

**排查清单**:
```python
# 检查连接字符串
from superset.models.core import Database
db = Database.query.filter_by(database_name='your_db').first()
print(db.sqlalchemy_uri)

# 测试连接
with db.get_sqla_engine() as engine:
    result = engine.execute("SELECT 1")
    print(result.fetchone())
```

**常见错误和解决方案**:

| 错误类型 | 解决方案 |
|---------|---------|
| `Connection timeout` | 检查网络连接、防火墙设置 |
| `Authentication failed` | 验证用户名密码、权限设置 |
| `Database does not exist` | 创建数据库或检查名称 |
| `Driver not found` | 安装对应数据库驱动 |

### 2. 查询超时

**诊断脚本**:
```python
def diagnose_query_timeout(datasource_id, form_data):
    """诊断查询超时问题"""
    from superset.connectors.sqla.models import SqlaTable
    import time
    
    datasource = SqlaTable.query.get(datasource_id)
    
    # 1. 检查查询复杂度
    query_obj = datasource.query_obj_from_form_data(form_data)
    sql = datasource.get_query_str(query_obj)
    
    print(f"📝 SQL查询:")
    print(sql)
    print(f"📊 查询长度: {len(sql)} 字符")
    
    # 2. 检查数据量
    row_limit = form_data.get('row_limit', 10000)
    print(f"📈 行限制: {row_limit}")
    
    # 3. 检查时间范围
    time_range = form_data.get('time_range')
    print(f"⏰ 时间范围: {time_range}")
    
    # 4. 建议优化
    suggestions = []
    if row_limit > 50000:
        suggestions.append("减少行限制")
    if len(sql) > 10000:
        suggestions.append("简化查询条件")
    if "JOIN" in sql.upper():
        suggestions.append("检查JOIN条件和索引")
        
    if suggestions:
        print("💡 优化建议:")
        for suggestion in suggestions:
            print(f"   - {suggestion}")
```

## 🎨 前端问题

### 1. 图表不显示

**排查步骤**:
```javascript
// 1. 检查浏览器控制台错误
console.log('Chart data:', chartData);

// 2. 检查网络请求
// 打开 DevTools > Network 查看API请求状态

// 3. 检查React组件状态
// 使用React DevTools查看组件props和state

// 4. 检查数据格式
const validateChartData = (data) => {
  if (!data || !Array.isArray(data)) {
    console.error('Invalid chart data format:', data);
    return false;
  }
  return true;
};
```

### 2. 仪表板加载慢

**性能诊断**:
```javascript
// 添加性能监控
const performanceObserver = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.duration > 1000) {  // 超过1秒
      console.warn('Slow operation:', entry.name, entry.duration);
    }
  }
});

performanceObserver.observe({ entryTypes: ['measure', 'navigation'] });

// 测量组件渲染时间
console.time('Dashboard Render');
// ... 组件渲染代码 ...
console.timeEnd('Dashboard Render');
```

## 🔐 权限问题

### 1. 访问被拒绝

**权限检查脚本**:
```python
def debug_user_permissions(username, resource_type, resource_id):
    """调试用户权限"""
    from superset.security.manager import SupersetSecurityManager
    from superset import appbuilder
    
    security_manager = appbuilder.sm
    user = security_manager.find_user(username=username)
    
    if not user:
        print(f"❌ User '{username}' not found")
        return
        
    print(f"👤 User: {user.username}")
    print(f"🎭 Roles: {[role.name for role in user.roles]}")
    
    # 检查资源权限
    if resource_type == 'dashboard':
        from superset.models.dashboard import Dashboard
        dashboard = Dashboard.query.get(resource_id)
        can_access = security_manager.can_access('can_read', 'Dashboard', dashboard)
        print(f"🔐 Dashboard access: {'✅' if can_access else '❌'}")
        
    elif resource_type == 'datasource':
        from superset.connectors.sqla.models import SqlaTable
        datasource = SqlaTable.query.get(resource_id)
        can_access = security_manager.can_access('can_read', 'Datasource', datasource)
        print(f"🔐 Datasource access: {'✅' if can_access else '❌'}")
```

### 2. 角色配置问题

**角色检查**:
```python
def check_role_permissions(role_name):
    """检查角色权限配置"""
    from superset import appbuilder
    
    role = appbuilder.sm.find_role(role_name)
    if not role:
        print(f"❌ Role '{role_name}' not found")
        return
        
    print(f"🎭 Role: {role.name}")
    print(f"📋 Permissions ({len(role.permissions)}):")
    
    for perm in role.permissions:
        print(f"   - {perm.permission.name} on {perm.view_menu.name}")
```

## 📊 API调试

### 1. API请求失败

**API测试脚本**:
```python
def test_api_endpoint(endpoint, method='GET', data=None):
    """测试API端点"""
    import requests
    from superset import app
    
    base_url = 'http://localhost:8088'
    url = f"{base_url}{endpoint}"
    
    # 获取认证token (需要先登录)
    session = requests.Session()
    
    # 模拟登录
    login_data = {
        'username': 'admin',
        'password': 'admin'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data)
    
    if login_response.status_code == 200:
        print("✅ Login successful")
        
        # 测试API
        if method == 'GET':
            response = session.get(url)
        elif method == 'POST':
            response = session.post(url, json=data)
            
        print(f"📡 {method} {url}")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API request successful")
            return response.json()
        else:
            print(f"❌ API request failed: {response.text}")
            
    else:
        print("❌ Login failed")
```

### 2. CSRF保护问题

**CSRF调试**:
```python
# 在superset_config.py中
WTF_CSRF_ENABLED = False  # 仅用于调试，生产环境请启用

# 或者正确获取CSRF token
def get_csrf_token():
    """获取CSRF token"""
    import requests
    session = requests.Session()
    
    # 获取登录页面以获取CSRF token
    response = session.get('http://localhost:8088/login')
    # 解析HTML获取csrf_token
    # ... 实现token提取逻辑 ...
    
    return csrf_token
```

## 🔧 调试工具箱

### 快速诊断命令

```bash
#!/bin/bash
# superset_health_check.sh - 健康检查脚本

echo "🔍 Superset健康检查"
echo "=================="

# 1. 检查进程
echo "📋 检查Superset进程:"
ps aux | grep superset || echo "❌ Superset进程未运行"

# 2. 检查端口
echo "🌐 检查端口8088:"
netstat -tulpn | grep :8088 || echo "❌ 端口8088未监听"

# 3. 检查数据库连接
echo "🗄️ 检查数据库:"
python -c "
from superset import create_app
app = create_app()
with app.app_context():
    from superset.extensions import db
    db.engine.execute('SELECT 1')
    print('✅ 数据库连接正常')
" || echo "❌ 数据库连接失败"

# 4. 检查前端构建
echo "🎨 检查前端资源:"
ls superset/static/assets/manifest.json > /dev/null 2>&1 && echo "✅ 前端资源存在" || echo "❌ 前端资源缺失"

# 5. 检查日志
echo "📝 最近的错误日志:"
tail -n 20 /var/log/superset/superset.log | grep -i error || echo "ℹ️ 无最近错误"
```

### 性能分析工具

```python
# performance_profiler.py
import cProfile
import pstats
from superset.app import create_app

def profile_superset_startup():
    """分析Superset启动性能"""
    profiler = cProfile.Profile()
    
    profiler.enable()
    app = create_app()
    profiler.disable()
    
    # 保存和分析结果
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 显示前20个最耗时的函数
    
    return app

if __name__ == "__main__":
    profile_superset_startup()
``` 