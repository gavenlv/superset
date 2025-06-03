# Apex Logging System

A modular, enterprise-grade logging system for Apache Superset optimized for cloud platforms like GCP.

## Features

- **GCP Cloud Logging Compatible**: Structured JSON logs that GCP can parse automatically
- **Multi-line SQL Handling**: Properly handles long SQL queries without breaking log format
- **Environment-aware**: Different logging configurations for development, testing, and production
- **Modular Design**: Separated concerns with dedicated modules for formatters, configuration, and query logging
- **Performance Tracking**: Built-in query performance logging capabilities

## Architecture

```
superset/apex/logging/
├── __init__.py          # Main module exports
├── formatters.py        # Custom log formatters (GCP JSON, Standard)
├── config.py           # Logging configuration builder and management
├── query_logger.py     # Specialized SQL query logging
└── README.md           # This documentation
```

## Quick Start

### 1. Basic Setup in superset_config.py

```python
from superset.apex.logging import setup_logging, create_query_logger, get_environment

# Auto-detect environment and setup logging
environment = get_environment()
setup_logging(environment=environment)

# Setup query logger
QUERY_LOGGER = create_query_logger('superset.sql_lab')
```

### 2. Environment-specific Configuration

The system automatically detects the environment based on `SUPERSET_ENV` or `FLASK_ENV` environment variables:

- **Development**: Uses readable text format for console output
- **Production**: Uses structured JSON format for better parsing
- **Test**: Uses JSON format with minimal output

### 3. Custom Configuration

```python
from superset.apex.logging import setup_logging

# Custom file path and settings
setup_logging(
    environment='production',
    log_file_path='/var/log/superset/app.log',
    enable_file_logging=True
)
```

## Environment Variables

- `SUPERSET_ENV`: Environment type (development, production, test)
- `FLASK_ENV`: Flask environment (development, production)
- `SUPERSET_LOG_FILE`: Custom log file path (default: /tmp/superset.log)
- `SUPERSET_ENABLE_FILE_LOGGING`: Enable/disable file logging (default: true)

## Log Format Examples

### Development Environment
```
2024-01-15 10:30:45 - superset.sql_lab - INFO - SQL query executed by admin on database postgres_db
```

### Production Environment (GCP JSON)
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "severity": "INFO",
  "logger": "superset.sql_lab",
  "message": "SQL query executed by admin on database postgres_db",
  "module": "views",
  "function": "run_query",
  "line": 123,
  "event_type": "sql_query_execution",
  "user": "admin",
  "database": "postgres_db",
  "schema": "public",
  "query_length": 245,
  "sql_query": "SELECT \n  users.id,\n  users.name,\n  COUNT(orders.id) as order_count\nFROM users\nLEFT JOIN orders ON users.id = orders.user_id\nWHERE users.created_at >= '2024-01-01'\nGROUP BY users.id, users.name\nORDER BY order_count DESC\nLIMIT 100",
  "execution_time": "2024-01-15T10:30:45.123456Z"
}
```

## Advanced Usage

### Custom Query Logger

```python
from superset.apex.logging.query_logger import QueryLogger

# Create a custom query logger
query_logger = QueryLogger('custom.sql_logger')

# Log with additional context
query_logger.log_query_execution(
    query="SELECT * FROM users",
    database=database_obj,
    schema="public",
    execution_time_ms=150.5,
    row_count=1000,
    error=None  # or error message if query failed
)
```

### Performance Logging

```python
from superset.apex.logging.query_logger import QueryPerformanceLogger

perf_logger = QueryPerformanceLogger()
perf_logger.log_performance_metrics(
    query_id="query_123",
    execution_time_ms=1250.0,
    row_count=5000,
    bytes_processed=1024000,
    cache_hit=False,
    database_name="postgres_db",
    user="admin"
)
```

### Custom Formatter

```python
from superset.apex.logging.config import LoggingConfigBuilder

config = (LoggingConfigBuilder()
    .with_gcp_json_formatter()
    .with_console_handler(formatter='gcp_json')
    .with_logger('myapp', handlers=['console'])
    .build())
```

## GCP Integration

The JSON formatter is specifically designed for GCP Cloud Logging:

1. **Automatic Field Extraction**: GCP automatically extracts and indexes JSON fields
2. **Query and Filter**: Use GCP Console to query logs by any field
3. **Alerting**: Set up alerts based on specific log conditions
4. **Multi-line Support**: SQL queries maintain formatting without breaking JSON structure

### Example GCP Log Query
```
resource.type="k8s_container"
jsonPayload.event_type="sql_query_execution"
jsonPayload.user="admin"
jsonPayload.execution_time_ms>1000
```

## Best Practices

1. **Environment Detection**: Let the system auto-detect environment when possible
2. **Structured Logging**: Use the extra parameter to add context to log messages
3. **Error Handling**: Always include error information in query logs when available
4. **Performance Monitoring**: Use performance logging for query optimization
5. **Security**: Avoid logging sensitive data in query parameters

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the apex module is in Python path
2. **File Permissions**: Check log file write permissions
3. **JSON Parsing**: Verify JSON logs are properly escaped

### Debug Mode

Set environment to 'development' for readable console output:
```bash
export SUPERSET_ENV=development
```

## Testing

```python
import logging
from superset.apex.logging import setup_logging

# Setup test logging
setup_logging(environment='test')

# Test logging
logger = logging.getLogger('test')
logger.info("Test message", extra={'test_field': 'test_value'})
``` 