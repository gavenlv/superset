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
from typing import Dict, Any, Optional

from superset.apex.logging.formatters import GCPJsonFormatter, StandardFormatter


class LoggingConfigBuilder:
    """
    Builder class for creating logging configurations.
    
    Supports different environments and output formats with sensible defaults.
    """
    
    def __init__(self):
        self.config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {},
            'handlers': {},
            'loggers': {},
            'root': {}
        }
    
    def with_gcp_json_formatter(self, name: str = 'gcp_json') -> 'LoggingConfigBuilder':
        """Add GCP JSON formatter to the configuration."""
        self.config['formatters'][name] = {
            '()': GCPJsonFormatter,
            'datefmt': '%Y-%m-%dT%H:%M:%S.%fZ'
        }
        return self
    
    def with_standard_formatter(self, name: str = 'standard') -> 'LoggingConfigBuilder':
        """Add standard text formatter to the configuration."""
        self.config['formatters'][name] = {
            '()': StandardFormatter
        }
        return self
    
    def with_console_handler(
        self, 
        name: str = 'console', 
        level: str = 'INFO', 
        formatter: str = 'gcp_json'
    ) -> 'LoggingConfigBuilder':
        """Add console handler to the configuration."""
        self.config['handlers'][name] = {
            'class': 'logging.StreamHandler',
            'level': level,
            'formatter': formatter,
            'stream': 'ext://sys.stdout'
        }
        return self
    
    def with_file_handler(
        self,
        name: str = 'file',
        level: str = 'INFO',
        formatter: str = 'gcp_json',
        filename: str = '/tmp/superset.log',
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ) -> 'LoggingConfigBuilder':
        """Add rotating file handler to the configuration."""
        self.config['handlers'][name] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': level,
            'formatter': formatter,
            'filename': filename,
            'maxBytes': max_bytes,
            'backupCount': backup_count
        }
        return self
    
    def with_logger(
        self,
        name: str,
        level: str = 'INFO',
        handlers: list = None,
        propagate: bool = False
    ) -> 'LoggingConfigBuilder':
        """Add logger configuration."""
        if handlers is None:
            handlers = ['console']
        
        self.config['loggers'][name] = {
            'level': level,
            'handlers': handlers,
            'propagate': propagate
        }
        return self
    
    def with_root_logger(
        self,
        level: str = 'INFO',
        handlers: list = None
    ) -> 'LoggingConfigBuilder':
        """Configure root logger."""
        if handlers is None:
            handlers = ['console']
        
        self.config['root'] = {
            'level': level,
            'handlers': handlers
        }
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the logging configuration."""
        return self.config


def _ensure_log_directory(log_file_path: str) -> bool:
    """
    Ensure the log directory exists and is writable.
    
    Args:
        log_file_path: Path to the log file
        
    Returns:
        True if directory exists and is writable, False otherwise
    """
    try:
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Test if we can write to the directory
        test_file = os.path.join(log_dir or '.', '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except (OSError, IOError, PermissionError):
        return False


def get_logging_config(
    environment: str = 'production',
    log_file_path: Optional[str] = None,
    enable_file_logging: bool = True
) -> Dict[str, Any]:
    """
    Get logging configuration for different environments.
    
    Args:
        environment: Environment type ('production', 'development', 'test')
        log_file_path: Path for log file. Defaults to /tmp/superset.log
        enable_file_logging: Whether to enable file logging
        
    Returns:
        Logging configuration dictionary
    """
    builder = LoggingConfigBuilder()
    
    if environment == 'development':
        # Development: Use standard formatter for console readability
        builder = (builder
                  .with_standard_formatter()
                  .with_gcp_json_formatter()
                  .with_console_handler(formatter='standard')
                  )
    else:
        # Production/Test: Use JSON formatter for structured logging
        builder = (builder
                  .with_gcp_json_formatter()
                  .with_standard_formatter()
                  .with_console_handler(formatter='gcp_json')
                  )
    
    # Add file handler if enabled and possible
    handlers = ['console']
    if enable_file_logging:
        file_path = log_file_path or '/tmp/superset.log'
        
        # Check if we can write to the log file location
        if _ensure_log_directory(file_path):
            try:
                builder = builder.with_file_handler(filename=file_path, formatter='gcp_json')
                handlers.append('file')
            except Exception:
                # If file handler fails, just use console
                pass
    
    # Configure loggers
    builder = (builder
              .with_logger('superset', handlers=handlers)
              .with_logger('sqlalchemy.engine', handlers=handlers)
              .with_logger('werkzeug', level='WARNING', handlers=['console'])
              .with_root_logger(handlers=['console'])
              )
    
    return builder.build()


def setup_logging(
    environment: str = 'production',
    log_file_path: Optional[str] = None,
    enable_file_logging: bool = True
) -> None:
    """
    Set up logging configuration.
    
    Args:
        environment: Environment type ('production', 'development', 'test')
        log_file_path: Path for log file
        enable_file_logging: Whether to enable file logging
    """
    try:
        config = get_logging_config(
            environment=environment,
            log_file_path=log_file_path,
            enable_file_logging=enable_file_logging
        )
        
        logging.config.dictConfig(config)
        
        # Log success message
        logger = logging.getLogger('superset.apex.logging')
        logger.info(f"Apex logging initialized for environment: {environment}")
        
    except Exception as e:
        # Fallback to basic console logging if configuration fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        
        logger = logging.getLogger('superset.apex.logging')
        logger.warning(f"Failed to setup advanced logging, using basic config: {e}")


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