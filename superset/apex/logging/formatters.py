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

try:
    from flask import has_request_context, request
except ImportError:
    has_request_context = lambda: False
    request = None


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
    - Windows compatibility for file paths and line endings
    """
    
    # Fields that should not be included in the extra fields
    EXCLUDED_FIELDS = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
        'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
        'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
        'processName', 'process', 'message', 'asctime'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: The LogRecord to format
            
        Returns:
            JSON formatted log entry
        """
        # Create the base log entry structure
        log_entry = {
            'timestamp': self.formatTime(record),
            'severity': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add process information
        if record.process:
            log_entry['process_id'] = record.process
        if record.thread:
            log_entry['thread_id'] = record.thread
        
        # Handle Windows file paths properly
        if record.pathname:
            # Normalize Windows paths for consistency
            normalized_path = record.pathname.replace('\\', '/')
            log_entry['file_path'] = normalized_path
        
        # Add exception information if present
        if record.exc_info:
            log_entry.update(self._format_exception(record))
        
        # Add request context if available
        if record.levelno >= logging.WARNING:
            request_context = self._get_request_context()
            if request_context:
                log_entry['request'] = request_context
        
        # Enhance SQL logging
        if self._is_sql_record(record):
            self._enhance_sql_logging(log_entry, record)
        
        # Add extra fields from the record
        self._add_extra_fields(log_entry, record)
        
        # Return JSON string with proper escaping
        try:
            return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            # Fallback if JSON serialization fails
            fallback_entry = {
                'timestamp': self.formatTime(record),
                'severity': 'ERROR',
                'logger': 'formatter',
                'message': f'JSON serialization failed: {str(e)}',
                'original_message': str(record.getMessage()),
                'error': str(e)
            }
            return json.dumps(fallback_entry, ensure_ascii=False, separators=(',', ':'))
    
    def _add_extra_fields(self, log_entry: Dict[str, Any], record: logging.LogRecord) -> None:
        """Add extra fields from the log record."""
        for key, value in record.__dict__.items():
            if key not in self.EXCLUDED_FIELDS:
                # Handle multi-line content (like SQL queries) properly
                if isinstance(value, str):
                    # Normalize line endings for Windows compatibility
                    normalized_value = value.replace('\r\n', '\n').replace('\r', '\n')
                    log_entry[key] = normalized_value
                else:
                    # Handle non-serializable objects
                    try:
                        json.dumps(value)  # Test if serializable
                        log_entry[key] = value
                    except (TypeError, ValueError):
                        log_entry[key] = str(value)

    def formatTime(self, record, datefmt=None):
        """Format timestamp with proper microsecond support."""
        from datetime import datetime
        dt = datetime.fromtimestamp(record.created)
        if datefmt:
            # Handle %f in datefmt which is not supported by time.strftime
            if '%f' in datefmt:
                return dt.strftime(datefmt)
            else:
                return dt.strftime(datefmt)
        return dt.isoformat() + 'Z'

    def _format_exception(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Format exception information."""
        exc_info = {
            'exception': {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown',
                'message': str(record.exc_info[1]) if record.exc_info[1] else 'Unknown error',
                'traceback': self.formatException(record).replace('\r\n', '\n').replace('\r', '\n')
            }
        }
        
        # Add exception location if available
        if record.exc_info[2]:
            tb = record.exc_info[2]
            while tb.tb_next:
                tb = tb.tb_next
            exc_info['exception']['file'] = tb.tb_frame.f_code.co_filename.replace('\\', '/')
            exc_info['exception']['line'] = tb.tb_lineno
            exc_info['exception']['function'] = tb.tb_frame.f_code.co_name
        
        return exc_info

    def _get_request_context(self) -> Optional[Dict[str, Any]]:
        """Get Flask request context information."""
        if not has_request_context() or request is None:
            return None
        
        try:
            context = {
                'method': request.method,
                'path': request.path,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }
            
            # Add query parameters if present
            if request.args:
                context['query_params'] = dict(request.args)
            
            # Add referrer if present
            if request.referrer:
                context['referrer'] = request.referrer
            
            # Add endpoint if available
            if request.endpoint:
                context['endpoint'] = request.endpoint
            
            return context
            
        except Exception:
            return None

    def _is_sql_record(self, record: logging.LogRecord) -> bool:
        """Check if this is a SQL-related log record."""
        return (
            'sql' in record.name.lower() or
            hasattr(record, 'sql_original') or
            hasattr(record, 'statement') or
            hasattr(record, 'event_type') and 'query' in getattr(record, 'event_type', '').lower()
        )

    def _enhance_sql_logging(self, log_entry: Dict[str, Any], record: logging.LogRecord) -> None:
        """Enhance SQL logging with executable queries."""
        # Check for SQL statement in various possible attributes
        sql_statement = getattr(record, 'sql_original', None) or getattr(record, 'statement', None)
        sql_params = getattr(record, 'sql_parameters', None) or getattr(record, 'parameters', None)
        
        if sql_statement:
            log_entry['sql_original'] = sql_statement
            
            if sql_params:
                log_entry['sql_parameters'] = sql_params
                # Create executable SQL
                executable_sql = self._interpolate_sql(sql_statement, sql_params)
                log_entry['sql_executable'] = executable_sql
            else:
                log_entry['sql_executable'] = sql_statement

    def _interpolate_sql(self, sql: str, params: Any) -> str:
        """
        Interpolate SQL parameters to create an executable SQL statement.
        
        Args:
            sql: The SQL statement with parameter placeholders
            params: The parameters to interpolate (can be dict or tuple)
            
        Returns:
            An executable SQL statement with parameters interpolated
        """
        if not params:
            return sql

        try:
            # Handle tuple parameters
            if isinstance(params, (list, tuple)):
                # Replace ? placeholders with %s for consistent handling
                sql = sql.replace('?', '%s')
                processed_params = []
                for value in params:
                    if hasattr(value, 'isoformat'):  # datetime-like objects
                        processed_params.append(f"'{value.isoformat()}'")
                    elif isinstance(value, str):
                        # Escape single quotes in strings
                        escaped_value = value.replace("'", "''")
                        processed_params.append(f"'{escaped_value}'")
                    elif value is None:
                        processed_params.append('NULL')
                    else:
                        processed_params.append(str(value))
                
                return sql % tuple(processed_params)

            # Handle dictionary parameters
            elif isinstance(params, dict):
                interpolated = sql
                for key, value in params.items():
                    placeholder = f"%({key})s"
                    if placeholder in interpolated:
                        if hasattr(value, 'isoformat'):  # datetime-like objects
                            replacement = f"'{value.isoformat()}'"
                        elif isinstance(value, str):
                            # Escape single quotes in strings
                            escaped_value = value.replace("'", "''")
                            replacement = f"'{escaped_value}'"
                        elif value is None:
                            replacement = 'NULL'
                        else:
                            replacement = str(value)
                        
                        interpolated = interpolated.replace(placeholder, replacement)
                
                return interpolated

        except Exception:
            pass
        
        # Fallback: return original SQL with parameters as comment
        return f"{sql}\n/* Parameters: {params} */"


class StandardFormatter(logging.Formatter):
    """
    Standard text formatter for development and debugging.
    
    Provides human-readable log output with consistent formatting
    and proper handling of multi-line messages.
    """
    
    def __init__(self, fmt=None, datefmt=None):
        if fmt is None:
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        if datefmt is None:
            datefmt = '%Y-%m-%d %H:%M:%S'
        super().__init__(fmt, datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a readable text string.
        
        Args:
            record: The LogRecord to format
            
        Returns:
            Formatted log message
        """
        # Get the basic formatted message
        formatted = super().format(record)
        
        # Normalize line endings for Windows
        formatted = formatted.replace('\r\n', '\n').replace('\r', '\n')
        
        # Add extra context for SQL queries
        if hasattr(record, 'sql_executable'):
            sql_lines = record.sql_executable.split('\n')
            if len(sql_lines) > 1:
                formatted += '\nSQL Query:\n' + '\n'.join(f"  {line}" for line in sql_lines)
            else:
                formatted += f'\nSQL: {record.sql_executable}'
        
        # Add execution time if available
        if hasattr(record, 'execution_time_ms'):
            formatted += f' ({record.execution_time_ms}ms)'
        
        return formatted 