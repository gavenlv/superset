# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Logging Configuration Module

Provides logging configuration management for different environments.
"""

import logging.config
import os
import time
from typing import Dict, Any, Optional

from superset.apex.logging.formatters import GCPJsonFormatter, StandardFormatter


def setup_sqlalchemy_statements(logger):
    """
    Set up SQLAlchemy statement logging with parameter interpolation.
    
    Args:
        logger: Logger instance to use for SQL statement logging
    """
    try:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            try:
                if not hasattr(conn, 'info'):
                    conn.info = {}
                conn.info.setdefault('query_start_time', []).append(time.time())
                conn.info.setdefault('current_statement', statement)
                conn.info.setdefault('current_parameters', parameters)
            except Exception:
                pass  # Silently handle any errors

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            try:
                if hasattr(conn, 'info') and conn.info.get('query_start_time'):
                    total = time.time() - conn.info['query_start_time'].pop()
                    
                    # Only log data source queries (not metadata queries)
                    if hasattr(conn, 'engine') and hasattr(conn.engine, 'url'):
                        engine_url = str(conn.engine.url)
                        if not any(pattern in engine_url.lower() for pattern in [
                            'superset.db', '/superset', 'host.docker.internal'
                        ]):
                            logger.info(
                                f"Data source query executed in {total * 1000:.2f}ms",
                                extra={
                                    'event_type': 'data_source_query',
                                    'sql_original': statement,
                                    'sql_parameters': parameters,
                                    'execution_time_ms': round(total * 1000, 2),
                                    'database_url': engine_url
                                }
                            )
            except Exception:
                pass  # Silently handle any errors

    except ImportError:
        pass  # SQLAlchemy not available


class LoggingConfig:
    """
    Centralized logging configuration management.
    
    Provides different logging configurations for various environments
    and deployment scenarios.
    """
    
    @staticmethod
    def get_gcp_config(
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 5
    ) -> Dict[str, Any]:
        """
        Get GCP-compatible logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            
        Returns:
            Dictionary containing logging configuration
        """
        
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'gcp_json': {
                    '()': GCPJsonFormatter,
                    'datefmt': '%Y-%m-%dT%H:%M:%S.%fZ'
                },
                'standard': {
                    '()': StandardFormatter,
                }
            },
            'handlers': {
                'console': {
                    'level': log_level,
                    'class': 'logging.StreamHandler',
                    'formatter': 'gcp_json',
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                'superset': {
                    'level': log_level,
                    'handlers': ['console'],
                    'propagate': False
                },
                'superset.sql_lab': {
                    'level': log_level,
                    'handlers': ['console'],
                    'propagate': False
                },
                'sqlalchemy.engine': {
                    'level': log_level,
                    'handlers': ['console'],
                    'propagate': False
                },
                'flask_appbuilder': {
                    'level': 'WARNING',
                    'handlers': ['console'],
                    'propagate': False
                }
            },
            'root': {
                'level': log_level,
                'handlers': ['console']
            }
        }
        
        # Add file handler if log file is specified
        if log_file:
            # Use a safer file handler for Windows
            config['handlers']['file'] = {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_file,
                'maxBytes': max_bytes,
                'backupCount': backup_count,
                'formatter': 'gcp_json',
                'encoding': 'utf-8',
                'delay': True  # Don't open file until first log
            }
            
            # Add file handler to all loggers
            for logger_config in config['loggers'].values():
                if 'file' not in logger_config['handlers']:
                    logger_config['handlers'].append('file')
            config['root']['handlers'].append('file')
        
        return config
    
    @staticmethod
    def get_development_config(
        log_level: str = "DEBUG",
        log_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get development-friendly logging configuration.
        
        Args:
            log_level: Logging level
            log_file: Path to log file (optional)
            
        Returns:
            Dictionary containing logging configuration
        """
        
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    '()': StandardFormatter,
                },
                'gcp_json': {
                    '()': GCPJsonFormatter,
                    'datefmt': '%Y-%m-%dT%H:%M:%S.%fZ'
                }
            },
            'handlers': {
                'console': {
                    'level': log_level,
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                'superset': {
                    'level': log_level,
                    'handlers': ['console'],
                    'propagate': False
                },
                'superset.sql_lab': {
                    'level': log_level,
                    'handlers': ['console'],
                    'propagate': False
                },
                'sqlalchemy.engine': {
                    'level': 'INFO',
                    'handlers': ['console'],
                    'propagate': False
                }
            },
            'root': {
                'level': log_level,
                'handlers': ['console']
            }
        }
        
        # Add file handler if specified
        if log_file:
            config['handlers']['file'] = {
                'level': log_level,
                'class': 'logging.FileHandler',
                'filename': log_file,
                'formatter': 'gcp_json',
                'encoding': 'utf-8'
            }
            
            # Add file handler to all loggers
            for logger_config in config['loggers'].values():
                if 'file' not in logger_config['handlers']:
                    logger_config['handlers'].append('file')
            config['root']['handlers'].append('file')
        
        return config
    
    @staticmethod
    def setup_logging(
        environment: str = "production",
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Setup logging configuration based on environment.
        
        Args:
            environment: Environment name (production, development, testing)
            log_level: Logging level
            log_file: Path to log file
            **kwargs: Additional configuration options
        """
        
        try:
            if environment.lower() in ['development', 'dev', 'debug']:
                config = LoggingConfig.get_development_config(log_level, log_file)
            else:
                config = LoggingConfig.get_gcp_config(log_level, log_file, **kwargs)
            
            # Apply the configuration
            logging.config.dictConfig(config)
            
            # Setup SQLAlchemy event handlers
            logger = logging.getLogger('superset.sql_lab')
            setup_sqlalchemy_statements(logger)
            
            # Log successful configuration
            logger = logging.getLogger('superset.apex.logging')
            logger.info(
                f"Logging configured for {environment} environment",
                extra={
                    'event_type': 'logging_setup',
                    'environment': environment,
                    'log_level': log_level,
                    'log_file': log_file,
                    'has_file_handler': log_file is not None
                }
            )
            
        except Exception as e:
            # Fallback to basic console logging if configuration fails
            logging.basicConfig(
                level=getattr(logging, log_level.upper(), logging.INFO),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )
            
            logger = logging.getLogger('superset.apex.logging')
            logger.error(
                f"Failed to configure logging: {e}",
                extra={
                    'event_type': 'logging_setup_error',
                    'error': str(e),
                    'environment': environment
                }
            )


def setup_query_logging() -> None:
    """
    Setup query logging configuration.
    
    This function should be called during Superset initialization to ensure
    query logging is properly configured.
    """
    try:
        logger = logging.getLogger('superset.sql_lab')
        setup_sqlalchemy_statements(logger)
        
        logger.info(
            "Query logging setup completed",
            extra={'event_type': 'query_logging_setup'}
        )
    except Exception as e:
        logger = logging.getLogger('superset.apex.logging')
        logger.error(
            f"Failed to setup query logging: {e}",
            extra={
                'event_type': 'query_logging_setup_error',
                'error': str(e)
            }
        )


# Convenience functions for common configurations
def setup_production_logging(log_file: str = "/tmp/superset.log") -> None:
    """Setup production logging with GCP JSON format."""
    LoggingConfig.setup_logging("production", "INFO", log_file)


def setup_development_logging(log_file: Optional[str] = None) -> None:
    """Setup development logging with readable format."""
    LoggingConfig.setup_logging("development", "DEBUG", log_file)


def get_environment() -> str:
    """
    Detect the current environment based on environment variables.
    
    Returns:
        Environment string ('production', 'development', 'test')
    """
    env = os.environ.get('SUPERSET_ENV', '').lower()
    flask_env = os.environ.get('FLASK_ENV', '').lower()
    
    if env in ['test', 'testing'] or flask_env in ['test', 'testing']:
        return 'test'
    elif env in ['dev', 'development'] or flask_env in ['dev', 'development']:
        return 'development'
    else:
        return 'production' 