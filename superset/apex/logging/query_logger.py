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
Query Logger Module

Provides specialized logging for SQL queries with structured output.
"""

import logging
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable

from sqlalchemy import event
from sqlalchemy.engine import Engine


class QueryLogger:
    """
    Specialized logger for SQL queries with structured output.
    
    Handles multi-line SQL queries properly and provides rich context
    for query execution logging.
    """
    
    def __init__(self, logger_name: str = 'superset.sql_lab'):
        self.logger = logging.getLogger(logger_name)
        self._setup_complete = False
        self._setup_query_capture()
    
    def _setup_query_capture(self):
        """Set up query capture for data source queries."""
        if self._setup_complete:
            return
            
        try:
            from sqlalchemy import event
            from sqlalchemy.engine import Engine
            
            @event.listens_for(Engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                # Store query start time and info for data source connections
                if self._is_data_source_connection(conn):
                    if not hasattr(conn, 'info'):
                        conn.info = {}
                    conn.info['query_start_time'] = time.time()
                    conn.info['query_statement'] = statement
                    conn.info['query_parameters'] = parameters

            @event.listens_for(Engine, "after_cursor_execute")
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                # Log completed data source queries
                if self._is_data_source_connection(conn) and hasattr(conn, 'info'):
                    start_time = conn.info.get('query_start_time')
                    if start_time:
                        execution_time = (time.time() - start_time) * 1000  # Convert to ms
                        self._log_data_source_query(
                            statement=statement,
                            parameters=parameters,
                            execution_time_ms=execution_time,
                            connection=conn
                        )
            
            self._setup_complete = True
            
        except ImportError:
            self.logger.warning("SQLAlchemy not available for query capture")
        except Exception as e:
            self.logger.error(f"Failed to setup query capture: {e}")

    def _is_data_source_connection(self, conn) -> bool:
        """Check if this is a data source connection (not metadata)."""
        try:
            if not hasattr(conn, 'engine') or not hasattr(conn.engine, 'url'):
                return False
                
            url_str = str(conn.engine.url).lower()
            
            # Skip Superset metadata database patterns
            metadata_patterns = [
                'superset.db',      # SQLite default
                '/superset',        # Common database name
                'superset_meta',    # Alternative naming
                'host.docker.internal',  # Docker setups often use this for metadata
            ]
            
            return not any(pattern in url_str for pattern in metadata_patterns)
            
        except Exception:
            return False

    def _get_database_info(self, conn) -> Dict[str, str]:
        """Extract database information from connection."""
        try:
            if hasattr(conn, 'engine') and hasattr(conn.engine, 'url'):
                url = conn.engine.url
                return {
                    'database_name': url.database or 'unknown',
                    'database_type': url.drivername or 'unknown',
                    'host': url.host or 'unknown'
                }
        except Exception:
            pass
        
        return {
            'database_name': 'unknown',
            'database_type': 'unknown', 
            'host': 'unknown'
        }

    def _interpolate_parameters(self, sql: str, params: Any) -> str:
        """Create executable SQL by interpolating parameters."""
        if not params:
            return sql

        try:
            # Handle dictionary parameters
            if isinstance(params, dict):
                interpolated = sql
                for key, value in params.items():
                    placeholder = f"%({key})s"
                    if placeholder in interpolated:
                        if isinstance(value, str):
                            interpolated = interpolated.replace(placeholder, f"'{value}'")
                        elif value is None:
                            interpolated = interpolated.replace(placeholder, "NULL")
                        else:
                            interpolated = interpolated.replace(placeholder, str(value))
                return interpolated
            
            # Handle tuple/list parameters
            elif isinstance(params, (tuple, list)):
                interpolated = sql
                # Replace ? with %s for consistent handling
                interpolated = interpolated.replace('?', '%s')
                
                # Replace %s placeholders
                for value in params:
                    if '%s' in interpolated:
                        if isinstance(value, str):
                            interpolated = interpolated.replace('%s', f"'{value}'", 1)
                        elif value is None:
                            interpolated = interpolated.replace('%s', "NULL", 1)
                        else:
                            interpolated = interpolated.replace('%s', str(value), 1)
                return interpolated
            
        except Exception:
            pass
        
        # Fallback: return original SQL with parameters as comment
        return f"{sql} /* Parameters: {params} */"

    def _log_data_source_query(self, statement: str, parameters: Any, execution_time_ms: float, connection):
        """Log a data source query with full context."""
        db_info = self._get_database_info(connection)
        executable_sql = self._interpolate_parameters(statement, parameters)
        
        query_context = {
            'event_type': 'data_source_query',
            'database_name': db_info['database_name'],
            'database_type': db_info['database_type'],
            'database_host': db_info['host'],
            'execution_time_ms': round(execution_time_ms, 2),
            'sql_original': statement,
            'sql_parameters': parameters,
            'sql_executable': executable_sql,
            'query_length': len(statement) if statement else 0,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        self.logger.info(
            f"Data source query: {db_info['database_name']} ({execution_time_ms:.2f}ms)",
            extra=query_context
        )
    
    def log_query_execution(
        self,
        query: str,
        database: Optional[Any] = None,
        schema: Optional[str] = None,
        client: Optional[str] = None,
        security_manager: Optional[Any] = None,
        log_params: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
        row_count: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log SQL query execution with structured data.
        
        This is the main entry point for QUERY_LOGGER functionality.
        """
        # Get user context
        user_info = self._extract_user_info(security_manager)
        
        # Create base query context
        query_context = {
            'event_type': 'sql_lab_query',
            'user': user_info,
            'database': self._extract_database_name(database),
            'schema': schema or 'default',
            'client': client or 'sql_lab',
            'query_length': len(query) if query else 0,
            'sql_query': query,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Add performance metrics
        if execution_time_ms is not None:
            query_context['execution_time_ms'] = execution_time_ms
        
        if row_count is not None:
            query_context['row_count'] = row_count
        
        # Add status and error info
        if error:
            query_context['status'] = 'failed'
            query_context['error'] = error
        else:
            query_context['status'] = 'success'
        
        # Add additional parameters
        if log_params:
            query_context.update(log_params)
        
        # Log with appropriate level
        if error:
            self.logger.error(
                f"SQL Lab query failed: {user_info} on {query_context['database']}",
                extra=query_context
            )
        else:
            self.logger.info(
                f"SQL Lab query: {user_info} on {query_context['database']}",
                extra=query_context
            )
    
    def _extract_user_info(self, security_manager: Optional[Any]) -> str:
        """Extract user information."""
        try:
            # Try security manager first
            if security_manager and hasattr(security_manager, 'current_user'):
                user = security_manager.current_user
                if user and hasattr(user, 'username'):
                    return user.username
            
            # Try Flask-Login
            from flask_login import current_user
            if hasattr(current_user, 'username'):
                return current_user.username
                
        except Exception:
            pass
        
        return "anonymous"
    
    def _extract_database_name(self, database: Optional[Any]) -> str:
        """Extract database name from various input types."""
        try:
            if database:
                if hasattr(database, 'database_name'):
                    return database.database_name
                elif isinstance(database, str):
                    # Extract from URL string
                    if '/' in database:
                        return database.split('/')[-1] or 'unknown'
                    return database
        except Exception:
            pass
        
        return 'unknown'


def create_query_logger(logger_name: str = 'superset.sql_lab') -> Callable:
    """
    Create a query logger function compatible with Superset's QUERY_LOGGER interface.
    
    Returns:
        Function that can be used as QUERY_LOGGER in Superset configuration
    """
    query_logger = QueryLogger(logger_name)
    
    def query_logger_func(
        database,
        query,
        schema=None,
        client=None,
        security_manager=None,
        log_params=None
    ):
        """
        Query logger function compatible with Superset's QUERY_LOGGER interface.
        """
        query_logger.log_query_execution(
            query=query,
            database=database,
            schema=schema,
            client=client,
            security_manager=security_manager,
            log_params=log_params
        )
    
    return query_logger_func


class QueryPerformanceLogger:
    """
    Specialized logger for query performance metrics.
    
    Provides detailed performance logging with timing and resource usage data.
    """
    
    def __init__(self, logger_name: str = 'superset.performance'):
        self.logger = logging.getLogger(logger_name)
    
    def log_performance_metrics(
        self,
        query_id: str,
        execution_time_ms: float,
        row_count: int,
        bytes_processed: Optional[int] = None,
        cache_hit: bool = False,
        database_name: str = 'unknown',
        user: str = 'anonymous'
    ) -> None:
        """
        Log query performance metrics.
        
        Args:
            query_id: Unique identifier for the query
            execution_time_ms: Execution time in milliseconds
            row_count: Number of rows returned
            bytes_processed: Number of bytes processed
            cache_hit: Whether the query hit cache
            database_name: Name of the database
            user: Username
        """
        perf_data = {
            'event_type': 'query_performance',
            'query_id': query_id,
            'execution_time_ms': execution_time_ms,
            'row_count': row_count,
            'cache_hit': cache_hit,
            'database': database_name,
            'user': user,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        if bytes_processed is not None:
            perf_data['bytes_processed'] = bytes_processed
        
        self.logger.info(
            f"Query performance: {execution_time_ms}ms, {row_count} rows",
            extra=perf_data
        ) 