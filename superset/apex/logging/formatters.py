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
Logging Formatters Module

Provides custom logging formatters optimized for cloud platforms.
"""

import json
import logging
import re
import traceback
from typing import Any, Dict, Optional

from flask import has_request_context, request


class GCPJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for GCP Cloud Logging compatibility.
    
    This formatter creates structured JSON logs that GCP can parse automatically,
    properly handling multi-line messages like SQL queries without breaking
    the JSON structure.
    
    Features:
    - GCP Cloud Logging compatible structure
    - Proper handling of multi-line content (SQL queries, stack traces)
    - ISO 8601 timestamp format
    - Structured fields for easy querying and filtering
    - Exception handling with proper formatting
    - Enhanced HTTP request context for debugging
    """
    
    # Fields that should not be included in the extra fields
    EXCLUDED_FIELDS = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
        'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
        'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
        'thread', 'threadName', 'processName', 'process', 'getMessage'
    }

    def _get_request_info(self) -> Dict[str, Any]:
        """
        Get relevant information from the current request context.
        
        Returns:
            Dictionary containing request information if available
        """
        if not has_request_context():
            return {}
            
        return {
            'request_path': request.path,
            'request_method': request.method,
            'request_url': request.url,
            'request_remote_addr': request.remote_addr,
            'request_user_agent': str(request.user_agent),
            'request_args': dict(request.args),
            'request_endpoint': request.endpoint,
            'request_referrer': request.referrer,
        }

    def _format_exception(self, exc_info) -> Dict[str, Any]:
        """
        Format exception information in a structured way.
        
        Args:
            exc_info: Exception information tuple
            
        Returns:
            Dictionary containing formatted exception details
        """
        if not exc_info:
            return {}
            
        exc_type, exc_value, exc_tb = exc_info
        
        return {
            'error_type': exc_type.__name__ if exc_type else None,
            'error_message': str(exc_value),
            'error_traceback': traceback.format_exception(*exc_info),
            'error_location': {
                'file': exc_tb.tb_frame.f_code.co_filename if exc_tb else None,
                'line': exc_tb.tb_lineno if exc_tb else None,
                'function': exc_tb.tb_frame.f_code.co_name if exc_tb else None
            }
        }

    def _interpolate_sql(self, sql: str, params: Dict[str, Any]) -> str:
        """
        Interpolate SQL parameters to create an executable SQL statement.
        
        Args:
            sql: The SQL statement with parameter placeholders
            params: The parameters to interpolate
            
        Returns:
            An executable SQL statement with parameters interpolated
        """
        if not params:
            return sql

        # Convert Python datetime objects to strings
        processed_params = {}
        for key, value in params.items():
            if hasattr(value, 'isoformat'):  # datetime-like objects
                processed_params[key] = f"'{value.isoformat()}'"
            elif isinstance(value, str):
                processed_params[key] = f"'{value}'"
            elif value is None:
                processed_params[key] = 'NULL'
            else:
                processed_params[key] = str(value)

        # Replace %(name)s style parameters with their values
        pattern = r'%\(([^)]+)\)s'
        def replace(match):
            param_name = match.group(1)
            return processed_params.get(param_name, match.group(0))
            
        return re.sub(pattern, replace, sql)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a JSON string suitable for GCP Cloud Logging.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON-formatted string with structured log data
        """
        # Create base log entry with standard fields
        log_entry = self._create_base_entry(record)
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self._format_exception(record.exc_info)
            # Add request context for errors
            if record.levelno >= logging.ERROR:
                log_entry["request"] = self._get_request_info()

        # Handle SQL logging specially
        if hasattr(record, 'statement') and hasattr(record, 'parameters'):
            # For SQL queries, include both original and interpolated versions
            log_entry['sql_original'] = record.statement
            log_entry['sql_parameters'] = record.parameters
            log_entry['sql_executable'] = self._interpolate_sql(record.statement, record.parameters)
            
        # Add extra fields from the record
        self._add_extra_fields(log_entry, record)
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)
    
    def _create_base_entry(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Create the base log entry with standard fields."""
        entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        
        # Add request context for warnings and errors
        if record.levelno >= logging.WARNING:
            request_info = self._get_request_info()
            if request_info:
                entry["request"] = request_info
                
        return entry
    
    def _add_extra_fields(self, log_entry: Dict[str, Any], record: logging.LogRecord) -> None:
        """Add extra fields from the log record, handling multi-line content properly."""
        for key, value in record.__dict__.items():
            if key not in self.EXCLUDED_FIELDS:
                # Handle multi-line content (like SQL queries) properly
                if isinstance(value, str) and '\n' in value:
                    log_entry[key] = value
                else:
                    log_entry[key] = value

    def formatTime(self, record, datefmt=None):
        from datetime import datetime
        dt = datetime.fromtimestamp(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


class StandardFormatter(logging.Formatter):
    """
    Standard text formatter for local development and legacy systems.
    
    Provides a readable format for console output during development.
    """
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ) 