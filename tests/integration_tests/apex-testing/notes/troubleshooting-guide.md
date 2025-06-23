# Superset 初始化故障排除指南

## 常见问题及解决方案

### 1. 数据库连接问题

#### 问题现象
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

#### 可能原因和解决方案

**原因1: 数据库服务未启动**
```bash
# 检查 PostgreSQL 服务状态
sudo systemctl status postgresql

# 启动 PostgreSQL 服务
sudo systemctl start postgresql

# 检查 MySQL 服务状态
sudo systemctl status mysql

# 启动 MySQL 服务
sudo systemctl start mysql
```

**原因2: 连接字符串配置错误**
```python
# 检查 superset_config.py 中的数据库连接配置
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost:5432/superset'

# 常见错误：
# - 用户名/密码错误
# - 主机地址错误
# - 端口号错误
# - 数据库名不存在
```

**原因3: 数据库用户权限不足**
```sql
-- PostgreSQL 创建用户和数据库
CREATE USER superset WITH PASSWORD 'superset';
CREATE DATABASE superset OWNER superset;
GRANT ALL PRIVILEGES ON DATABASE superset TO superset;

-- MySQL 创建用户和数据库
CREATE DATABASE superset;
CREATE USER 'superset'@'localhost' IDENTIFIED BY 'superset';
GRANT ALL PRIVILEGES ON superset.* TO 'superset'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 数据库迁移失败

#### 问题现象1: 迁移版本冲突
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xxx'
```

**解决方案**：
```bash
# 1. 检查当前数据库版本
superset db current

# 2. 查看迁移历史
superset db history

# 3. 手动设置版本（谨慎使用）
superset db stamp head

# 4. 重新运行迁移
superset db upgrade
```

#### 问题现象2: 表已存在错误
```
sqlalchemy.exc.ProgrammingError: relation "ab_user" already exists
```

**解决方案**：
```bash
# 方法1: 检查并修复迁移状态
superset db current
superset db stamp head

# 方法2: 开发环境 - 重置数据库（会丢失数据！）
rm -rf superset.db  # SQLite
# 或删除 PostgreSQL/MySQL 数据库后重新创建

# 方法3: 生产环境 - 手动检查表结构
# 确认哪些表存在，手动修正迁移状态
```

### 3. 管理员用户创建失败

#### 问题现象1: 用户已存在
```
User already exists
```

**解决方案**：
```bash
# 方法1: 检查现有用户
superset fab list-users

# 方法2: 使用不同的用户名
superset fab create-admin --username admin2 --password admin

# 方法3: 删除现有用户（谨慎！）
# 通过 Flask-AppBuilder admin 界面删除
# 或直接操作数据库
```

#### 问题现象2: 密码策略限制
```
Password does not meet security requirements
```

**解决方案**：
```python
# 在 superset_config.py 中调整密码策略
AUTH_PASSWORD_COMPLEXITY_ENABLED = False

# 或使用符合策略的强密码
superset fab create-admin --password 'StrongPassword123!'
```

### 4. 权限初始化失败

#### 问题现象: 权限创建失败
```
Permission/Role creation failed
sqlalchemy.exc.IntegrityError: duplicate key value violates unique constraint
```

**解决方案**：
```bash
# 1. 清理权限表中的重复数据
# 连接到数据库，检查相关表
SELECT * FROM ab_permission;
SELECT * FROM ab_view_menu;
SELECT * FROM ab_permission_view;

# 2. 重新运行 init 命令
superset init

# 3. 如果问题持续，考虑重置权限系统
# （这可能需要手动清理相关表）
```

### 5. Flask-AppBuilder 相关问题

#### 问题现象: FAB 配置错误
```
ImportError: No module named 'flask_appbuilder'
```

**解决方案**：
```bash
# 确保所有依赖已正确安装
pip install -r requirements.txt
pip install apache-superset

# 检查虚拟环境
which python
which pip
```

### 6. 配置文件问题

#### 问题现象: 配置文件未找到
```
Config file not found: superset_config.py
```

**解决方案**：
```bash
# 1. 检查配置文件路径
export SUPERSET_CONFIG_PATH=/path/to/superset_config.py

# 2. 创建基本配置文件
cat > superset_config.py << EOF
SECRET_KEY = 'your-secret-key-here'
SQLALCHEMY_DATABASE_URI = 'sqlite:///superset.db'
EOF

# 3. 设置环境变量
export FLASK_APP=superset
```

### 7. 权限和角色问题

#### 问题现象: 角色权限不正确
```
User doesn't have the required permissions
```

**诊断步骤**：
```bash
# 1. 检查用户角色
superset fab list-users

# 2. 检查角色权限
superset fab list-roles

# 3. 重新同步权限
superset init

# 4. 手动分配权限（通过 web 界面）
# 访问 /users/userinfo/ 进行用户管理
```

### 8. 环境相关问题

#### 问题现象1: Python 版本不兼容
```
SyntaxError: invalid syntax
```

**解决方案**：
```bash
# 检查 Python 版本（需要 3.8+）
python --version

# 使用正确的 Python 版本
python3.9 -m pip install apache-superset
```

#### 问题现象2: 依赖冲突
```
DistributionNotFound: The 'package-name' distribution was not found
```

**解决方案**：
```bash
# 1. 重新安装依赖
pip uninstall apache-superset
pip install apache-superset

# 2. 使用虚拟环境
python -m venv superset_env
source superset_env/bin/activate
pip install apache-superset

# 3. 锁定依赖版本
pip freeze > requirements.txt
```

## 诊断工具和命令

### 基本诊断命令
```bash
# 检查 Superset 版本和配置
superset version --verbose

# 检查数据库连接
superset db current

# 验证配置文件
python -c "import superset.config; print('Config loaded successfully')"

# 检查环境变量
env | grep SUPERSET
```

### 数据库诊断
```bash
# 检查数据库表
superset db tables

# 显示迁移状态
superset db show

# 检查权限表
superset fab permissions
```

### 日志诊断
```bash
# 启用详细日志
export SUPERSET_LOG_LEVEL=DEBUG

# 查看应用程序日志
tail -f superset.log

# 临时启用 SQL 日志
export SUPERSET_LOG_SQL=true
```

## 完全重置指南（开发环境）

### SQLite 环境
```bash
# 删除数据库文件
rm -f superset.db

# 重新初始化
superset db upgrade
superset fab create-admin --username admin --password admin
superset init
```

### PostgreSQL 环境
```bash
# 删除并重新创建数据库
psql -c "DROP DATABASE IF EXISTS superset;"
psql -c "CREATE DATABASE superset OWNER superset;"

# 重新初始化
superset db upgrade
superset fab create-admin --username admin --password admin
superset init
```

### MySQL 环境
```bash
# 删除并重新创建数据库
mysql -e "DROP DATABASE IF EXISTS superset;"
mysql -e "CREATE DATABASE superset;"

# 重新初始化
superset db upgrade
superset fab create-admin --username admin --password admin
superset init
```

## 生产环境恢复

### 备份策略
```bash
# PostgreSQL 备份
pg_dump superset > backup_$(date +%Y%m%d_%H%M%S).sql

# MySQL 备份
mysqldump superset > backup_$(date +%Y%m%d_%H%M%S).sql

# 配置文件备份
cp superset_config.py superset_config.py.backup
```

### 恢复步骤
```bash
# 1. 停止 Superset 服务
systemctl stop superset

# 2. 备份当前状态
pg_dump superset > pre_recovery_backup.sql

# 3. 尝试修复问题
superset db upgrade
superset init

# 4. 如果修复失败，恢复备份
psql superset < backup_YYYYMMDD_HHMMSS.sql

# 5. 重启服务
systemctl start superset
```

## 预防措施

### 监控检查点
```bash
# 创建健康检查脚本
#!/bin/bash
superset db current >/dev/null 2>&1 || echo "DB connection failed"
superset fab list-users >/dev/null 2>&1 || echo "User system failed"
```

### 自动化维护
```bash
# 定期权限同步
0 2 * * * /path/to/superset init

# 定期备份
0 3 * * * pg_dump superset > /backups/superset_$(date +\%Y\%m\%d).sql
```

### 最佳实践
1. **始终在测试环境验证更改**
2. **定期备份数据库**
3. **监控日志文件**
4. **文档化自定义配置**
5. **保持依赖项版本稳定** 