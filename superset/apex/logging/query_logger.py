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
from datetime import datetime
from typing import Optional, Dict, Any, Callable


class QueryLogger:
    """
    Specialized logger for SQL queries with structured output.
    
    Handles multi-line SQL queries properly and provides rich context
    for query execution logging.
    """
    
    def __init__(self, logger_name: str = 'superset.sql_lab'):
        self.logger = logging.getLogger(logger_name)
    
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
        
        Args:
            query: The SQL query being executed
            database: Database object
            schema: Schema name
            client: Client identifier
            security_manager: Security manager for user context
            log_params: Additional logging parameters
            execution_time_ms: Query execution time in milliseconds
            row_count: Number of rows returned
            error: Error message if query failed
        """
        # Get current user info
        user_info = self._get_user_info(security_manager)
        
        # Create structured log entry for SQL query
        query_info = {
            'event_type': 'sql_query_execution',
            'user': user_info,
            'database': self._get_database_name(database),
            'schema': schema or 'default',
            'client': client or 'unknown',
            'query_length': len(query) if query else 0,
            'sql_query': query,  # This will be properly escaped in JSON
            'execution_time': datetime.utcnow().isoformat(),
        }
        
        # Add performance metrics if available
        if execution_time_ms is not None:
            query_info['execution_time_ms'] = execution_time_ms
        
        if row_count is not None:
            query_info['row_count'] = row_count
        
        # Add error information if present
        if error:
            query_info['error'] = error
            query_info['status'] = 'failed'
        else:
            query_info['status'] = 'success'
        
        # Add any additional log parameters
        if log_params:
            query_info.update(log_params)
        
        # Log with appropriate level based on status
        if error:
            self.logger.error(
                f"SQL query failed for user {user_info} on database {query_info['database']}",
                extra=query_info
            )
        else:
            self.logger.info(
                f"SQL query executed by {user_info} on database {query_info['database']}",
                extra=query_info
            )
    
    def _get_user_info(self, security_manager: Optional[Any]) -> str:
        """Extract user information from security manager."""
        try:
            if security_manager and hasattr(security_manager, 'current_user'):
                current_user = security_manager.current_user
                if current_user and hasattr(current_user, 'username'):
                    return current_user.username
        except Exception:
            # Silently handle any errors in user extraction
            pass
        
        return "anonymous"
    
    def _get_database_name(self, database: Optional[Any]) -> str:
        """Extract database name from database object."""
        try:
            if database and hasattr(database, 'database_name'):
                return database.database_name
        except Exception:
            pass
        
        return 'unknown'


def create_query_logger(logger_name: str = 'superset.sql_lab') -> Callable:
    """
    Create a query logger function compatible with Superset's QUERY_LOGGER interface.
    
    Args:
        logger_name: Name of the logger to use
        
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
        
        This function properly handles multi-line SQL queries without breaking
        the JSON log structure.
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