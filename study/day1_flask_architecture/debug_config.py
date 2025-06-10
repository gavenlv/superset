"""
调试专用的Superset配置文件

这个配置文件专门用于开发和调试，包含了详细的日志配置和调试选项
"""

import os
import logging
from superset.config import *  # 导入默认配置

# ===== 基础调试配置 =====
DEBUG = True
FLASK_DEBUG = True

# 密钥（仅用于开发）
SECRET_KEY = 'debug_secret_key_for_development_only'

# ===== 数据库配置 =====
# 使用SQLite进行本地调试（更简单）
SQLALCHEMY_DATABASE_URI = 'sqlite:///superset_debug.db'

# 或者使用PostgreSQL（如果你有的话）
# SQLALCHEMY_DATABASE_URI = 'postgresql://superset:superset@localhost:5432/superset_debug'

# 数据库调试设置
SQLALCHEMY_ECHO = True  # 显示所有SQL查询
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ===== 日志配置 =====
LOG_LEVEL = 'DEBUG'

# 详细日志配置
LOGGING_CONFIGURATOR = None  # 使用默认配置

# 设置各个模块的日志级别
import logging
logging.getLogger('superset').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('flask_appbuilder').setLevel(logging.DEBUG)

# ===== 缓存配置 =====
# 禁用缓存以便调试
CACHE_CONFIG = {
    'CACHE_TYPE': 'NullCache'
}

DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'NullCache'
}

# ===== 安全配置 =====
# 调试时禁用CSRF（仅开发环境）
WTF_CSRF_ENABLED = False
WTF_CSRF_EXEMPT_LIST = []

# CORS配置（用于前端调试）
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['http://localhost:9000', 'http://127.0.0.1:9000']
}

# ===== 功能开关 =====
# 启用所有功能进行测试
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'GLOBAL_ASYNC_QUERIES': True,
    'VERSIONED_EXPORT': True,
    'EMBEDDED_SUPERSET': True,
    'ESCAPE_MARKDOWN_HTML': True,
    'DASHBOARD_VIRTUALIZATION': True,
}

# ===== 性能配置 =====
# 调试时减少超时时间
SUPERSET_WEBSERVER_TIMEOUT = 300  # 5分钟

# 减少行数限制便于调试
ROW_LIMIT = 1000
SAMPLES_ROW_LIMIT = 100

# ===== 邮件配置 =====
# 调试时使用控制台输出邮件
SMTP_HOST = 'localhost'
SMTP_STARTTLS = False
SMTP_SSL = False
SMTP_USER = 'superset'
SMTP_PORT = 25
SMTP_PASSWORD = 'superset'
SMTP_MAIL_FROM = 'superset@debug.local'

# ===== Celery配置 =====
class CeleryConfig:
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/0'
    imports = (
        'superset.sql_lab',
        'superset.tasks.scheduler',
        'superset.tasks.thumbnails',
        'superset.tasks.cache',
    )
    
    # 调试配置
    task_always_eager = True  # 同步执行任务便于调试
    task_eager_propagates = True

CELERY_CONFIG = CeleryConfig

# ===== 自定义配置 =====
# 启用Flask调试工具栏（如果安装了）
try:
    from flask_debugtoolbar import DebugToolbarExtension
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
except ImportError:
    pass

# ===== 开发环境特定设置 =====
# 禁用某些生产环境特性
ENABLE_PROXY_FIX = False
TALISMAN_ENABLED = False

# 允许从任何主机访问（仅开发环境）
SUPERSET_WEBSERVER_ADDRESS = '0.0.0.0'

print("🔧 调试配置已加载")
print(f"📊 数据库: {SQLALCHEMY_DATABASE_URI}")
print(f"🔍 调试模式: {DEBUG}")
print(f"📝 SQL日志: {SQLALCHEMY_ECHO}") 