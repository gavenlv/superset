# 🗄️ Superset数据库调试指南

## 📊 SQL查询调试

### 1. 启用SQL日志记录

在 `superset_config.py` 中添加:

```python
# 启用SQLAlchemy查询日志
import logging

# 显示所有SQL查询
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# 显示查询结果
logging.getLogger('sqlalchemy.engine.result').setLevel(logging.INFO)

# 显示连接池信息
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)

# Superset查询日志配置
QUERY_LOGGER = True
LOG_QUERIES = True

# 自定义查询日志格式
QUERY_LOGGER_FORMAT = """
=== SQL Query Debug ===
Time: %(asctime)s
Duration: %(duration)s ms
Database: %(database)s
Query:
%(query)s
========================
"""
```

### 2. SQL Lab中的调试

```sql
-- 在SQL Lab中调试查询
-- 1. 使用EXPLAIN查看执行计划
EXPLAIN SELECT * FROM sales_data WHERE date >= '2023-01-01';

-- 2. 使用EXPLAIN ANALYZE查看实际执行统计
EXPLAIN ANALYZE SELECT category, SUM(amount) 
FROM sales_data 
GROUP BY category;

-- 3. 检查查询性能
SELECT 
    COUNT(*) as total_rows,
    MIN(created_at) as earliest_date,
    MAX(created_at) as latest_date
FROM your_table;

-- 4. 调试数据质量
SELECT 
    column_name,
    COUNT(*) as total,
    COUNT(DISTINCT column_name) as unique_values,
    COUNT(*) - COUNT(column_name) as null_count
FROM your_table
GROUP BY 1;
```

### 3. 查询上下文调试

```python
# 在Python代码中调试SQL生成过程
from superset.connectors.sqla.models import SqlaTable
from superset.models.core import Database
import logging

logger = logging.getLogger(__name__)

def debug_query_generation(datasource_id, form_data):
    """调试查询生成过程"""
    
    # 获取数据源
    datasource = SqlaTable.query.get(datasource_id)
    logger.debug(f"Datasource: {datasource.table_name}")
    
    # 调试form_data
    logger.debug(f"Form data: {form_data}")
    
    # 生成查询
    query_obj = datasource.query_obj_from_form_data(form_data)
    logger.debug(f"Query object: {query_obj}")
    
    # 获取SQL
    sql = datasource.get_query_str(query_obj)
    logger.debug(f"Generated SQL:\n{sql}")
    
    # 执行查询并计时
    import time
    start_time = time.time()
    
    df = datasource.query(query_obj)
    
    execution_time = time.time() - start_time
    logger.debug(f"Query executed in {execution_time:.2f} seconds")
    logger.debug(f"Result shape: {df.shape}")
    
    return df
```

## 🔍 数据库连接调试

### 1. 连接测试脚本

```python
#!/usr/bin/env python3
"""数据库连接调试脚本"""

from superset.models.core import Database
from superset.extensions import db
from sqlalchemy import text
import traceback

def test_database_connection(database_id):
    """测试特定数据库连接"""
    try:
        # 获取数据库配置
        database = Database.query.get(database_id)
        if not database:
            print(f"❌ Database {database_id} not found")
            return False
            
        print(f"🔍 Testing database: {database.database_name}")
        print(f"📊 URI: {database.safe_sqlalchemy_uri()}")
        
        # 测试连接
        with database.get_sqla_engine() as engine:
            print("✅ Engine created successfully")
            
            # 测试基本查询
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Test query successful: {row}")
                
                # 获取表列表 (如果支持)
                try:
                    inspector = database.get_inspector()
                    tables = inspector.get_table_names()
                    print(f"📋 Found {len(tables)} tables")
                    
                    if tables:
                        print(f"📄 Sample tables: {tables[:5]}")
                        
                except Exception as e:
                    print(f"⚠️ Could not list tables: {e}")
                    
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"🔍 Traceback:\n{traceback.format_exc()}")
        return False

def debug_all_databases():
    """调试所有数据库连接"""
    databases = Database.query.all()
    
    print(f"🔍 Found {len(databases)} databases")
    print("=" * 50)
    
    for db_obj in databases:
        print(f"\n📊 Database: {db_obj.database_name}")
        test_database_connection(db_obj.id)

if __name__ == "__main__":
    # 需要在Superset应用上下文中运行
    from superset.app import create_app
    app = create_app()
    
    with app.app_context():
        debug_all_databases()
```

### 2. 数据源调试

```python
def debug_datasource_metadata(datasource_id):
    """调试数据源元数据"""
    from superset.connectors.sqla.models import SqlaTable
    
    datasource = SqlaTable.query.get(datasource_id)
    if not datasource:
        print(f"❌ Datasource {datasource_id} not found")
        return
        
    print(f"🔍 Datasource: {datasource.table_name}")
    print(f"📊 Database: {datasource.database.database_name}")
    
    # 调试列信息
    print(f"\n📋 Columns ({len(datasource.columns)}):")
    for col in datasource.columns:
        print(f"  - {col.column_name} ({col.type}) - {col.description or 'No description'}")
        
    # 调试指标
    print(f"\n📈 Metrics ({len(datasource.metrics)}):")
    for metric in datasource.metrics:
        print(f"  - {metric.metric_name}: {metric.expression}")
        
    # 测试基本查询
    try:
        sample_query = {
            'granularity': None,
            'from_dttm': None,
            'to_dttm': None,
            'groupby': [],
            'metrics': ['count'],
            'row_limit': 10
        }
        
        df = datasource.query(sample_query)
        print(f"\n✅ Sample query successful, shape: {df.shape}")
        
    except Exception as e:
        print(f"\n❌ Sample query failed: {e}")
```

## 🐛 常见问题排查

### 1. 连接超时问题

```python
# 在superset_config.py中配置
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_timeout': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'connect_args': {
        'connect_timeout': 60,
        'read_timeout': 60,
        'write_timeout': 60,
    }
}

# 调试连接池状态
def debug_connection_pool(database_id):
    database = Database.query.get(database_id)
    
    with database.get_sqla_engine() as engine:
        pool = engine.pool
        print(f"Pool status:")
        print(f"  - Size: {pool.size()}")
        print(f"  - Checked in: {pool.checkedin()}")
        print(f"  - Checked out: {pool.checkedout()}")
        print(f"  - Overflow: {pool.overflow()}")
```

### 2. 查询性能问题

```python
def debug_slow_query(datasource_id, form_data):
    """调试慢查询"""
    import time
    from superset.connectors.sqla.models import SqlaTable
    
    datasource = SqlaTable.query.get(datasource_id)
    
    # 生成查询
    start_time = time.time()
    query_obj = datasource.query_obj_from_form_data(form_data)
    sql_generation_time = time.time() - start_time
    
    print(f"⏱️ SQL generation time: {sql_generation_time:.2f}s")
    
    # 获取SQL语句
    sql = datasource.get_query_str(query_obj)
    print(f"📝 Generated SQL:\n{sql}")
    
    # 执行查询
    start_time = time.time()
    df = datasource.query(query_obj)
    execution_time = time.time() - start_time
    
    print(f"⏱️ Query execution time: {execution_time:.2f}s")
    print(f"📊 Result shape: {df.shape}")
    
    # 分析结果
    if execution_time > 5:  # 慢查询阈值
        print("⚠️ Slow query detected!")
        print("💡 Optimization suggestions:")
        print("   - Add database indexes")
        print("   - Reduce date range")
        print("   - Limit result rows")
        print("   - Optimize groupby columns")
```

### 3. 权限问题调试

```python
def debug_database_permissions(user_id, database_id):
    """调试数据库权限"""
    from superset.security.manager import SupersetSecurityManager
    from flask_appbuilder.models.sqla import Model
    
    security_manager = SupersetSecurityManager(appbuilder)
    
    # 获取用户和数据库
    user = security_manager.get_user_by_id(user_id)
    database = Database.query.get(database_id)
    
    print(f"👤 User: {user.username}")
    print(f"📊 Database: {database.database_name}")
    
    # 检查数据库访问权限
    has_access = security_manager.can_access_database(database, user)
    print(f"🔐 Database access: {'✅' if has_access else '❌'}")
    
    # 检查用户角色
    print(f"🎭 User roles:")
    for role in user.roles:
        print(f"   - {role.name}")
        
    # 检查数据库权限
    perms = security_manager.get_database_permissions(database, user)
    print(f"🔑 Database permissions: {perms}")
```

## 📈 性能监控

### 1. 查询监控配置

```python
# 在superset_config.py中配置
import time
from superset.utils.log import DBEventLogger

class CustomEventLogger(DBEventLogger):
    def log(self, user_id, action, dashboard_id=None, duration_ms=None, slice_id=None, **kwargs):
        # 记录慢查询
        if action == 'query' and duration_ms and duration_ms > 5000:  # 5秒
            print(f"🐌 Slow query detected: {duration_ms}ms")
            print(f"   User: {user_id}")
            print(f"   Dashboard: {dashboard_id}")
            print(f"   Chart: {slice_id}")
            
        super().log(user_id, action, dashboard_id, duration_ms, slice_id, **kwargs)

EVENT_LOGGER = CustomEventLogger()
```

### 2. 实时监控脚本

```python
#!/usr/bin/env python3
"""实时监控Superset查询性能"""

import time
import psutil
from superset.models.logs import Log
from superset.extensions import db

def monitor_queries():
    """监控实时查询"""
    last_check = time.time() - 60  # 最近1分钟
    
    while True:
        current_time = time.time()
        
        # 查询最近的日志
        recent_logs = db.session.query(Log).filter(
            Log.dttm >= last_check,
            Log.action == 'query'
        ).all()
        
        for log in recent_logs:
            if log.duration_ms and log.duration_ms > 5000:  # 5秒以上
                print(f"⚠️ Slow query: {log.duration_ms}ms")
                print(f"   Dashboard: {log.dashboard_id}")
                print(f"   Chart: {log.slice_id}")
                
        # 检查系统资源
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 80:
            print(f"🔥 High CPU usage: {cpu_percent}%")
            
        if memory_percent > 80:
            print(f"🔥 High memory usage: {memory_percent}%")
            
        last_check = current_time
        time.sleep(30)  # 每30秒检查一次

if __name__ == "__main__":
    monitor_queries()
``` 