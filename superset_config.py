import os
from datetime import timedelta
from dotenv import load_dotenv
import os

# 自动加载.env文件
load_dotenv(override=True)  # 强制覆盖已有变量

SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
SECRET_KEY = 'fiVM2JDST7oP0SkXtge8RhCE+mtWk2GmoI7xHwMc5BsspcWfbMmWoqf8'

# 数据库配置
SQLALCHEMY_DATABASE_URI = os.environ.get("SUPERSET_DATABASE_URI", "postgresql+psycopg2://postgres:root@localhost:25011/superset_db")

# Redis配置
REDIS_HOST = "localhost"
REDIS_PORT = "6379"
REDIS_CACHE_DB = "1"
REDIS_CELERY_DB = "0"

# 缓存配置 - 使用Redis
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_cache_',
    'CACHE_REDIS_URL': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CACHE_DB}'
}

# 数据缓存配置 - 使用同样的Redis配置
DATA_CACHE_CONFIG = CACHE_CONFIG

# 功能标志
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
     "DASHBOARD_NATIVE_FILTERS": True,
    # "DASHBOARD_NATIVE_FILTERS_SET": True,
    "DASHBOARD_CROSS_FILTERS": True, 
    "HORIZONTAL_FILTER_BAR": True,
    # "THUMBNAILS": True,
    # "ENABLE_DASHBOARD_DOWNLOAD_WEBDRIVER_SCREENSHOT": True,
    # "SHARE_QUERIES_VIA_KV_STORE": True,
    "TAGGING_SYSTEM": True,
    # "SQLLAB_BACKEND_PERSISTENCE": True,
    # "LISTVIEWS_DEFAULT_CARD_VIEW": True,
}


SUPERSET_WEBSERVER_TIMEOUT=10000
FAB_API_SWAGGER_UI = True

AUTH_ROLE_PUBLIC = 'Public'

# ============================================================================
# Apex Logging Configuration
# ============================================================================

# Import the apex logging modules
from superset.apex.logging.config import LoggingConfig
from superset.apex.logging.query_logger import create_query_logger

# Determine environment
environment = os.environ.get('SUPERSET_ENV', 'production').lower()

# Setup logging with Windows-compatible configuration
log_file = os.environ.get('SUPERSET_LOG_FILE', 'D:/tmp/superset.log')
log_level = os.environ.get('SUPERSET_LOG_LEVEL', 'INFO')

# Use our improved logging configuration
LoggingConfig.setup_logging(
    environment=environment,
    log_level=log_level,
    log_file=log_file
)

# Setup SQL query logger with proper multi-line handling
QUERY_LOGGER = create_query_logger('superset.sql_lab')
