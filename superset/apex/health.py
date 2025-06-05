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

import logging
import asyncio
from contextlib import closing
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.exc import SQLAlchemyError
from flask import current_app

from superset.extensions import cache_manager, db
from superset.models.core import Database

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health checker class for Superset components"""
    
    def __init__(self, db_session=None, cache=None):
        """Initialize health checker with optional dependencies for testing"""
        self.db_session = db_session or db.session
        self.cache = cache or cache_manager.cache
        
    def check_metadata_db(self) -> Tuple[bool, str]:
        """Check if the metadata database is accessible"""
        try:
            self.db_session.execute("SELECT 1")
            return True, "Metadata database is healthy"
        except SQLAlchemyError as e:
            logger.error("Metadata database health check failed: %s", str(e))
            return False, f"Metadata database error: {str(e)}"

    def check_cache(self) -> Tuple[bool, str]:
        """Check if the cache system is working"""
        try:
            self.cache.set("health_check", "ok", timeout=10)
            result = self.cache.get("health_check")
            if result == "ok":
                return True, "Cache system is healthy"
            return False, "Cache system is not responding correctly"
        except Exception as e:
            logger.error("Cache health check failed: %s", str(e))
            return False, f"Cache system error: {str(e)}"

    def _check_single_database(self, database: Database, app) -> Dict[str, str]:
        """Check a single database connection - thread-safe method with app context"""
        try:
            with app.app_context():
                with database.get_sqla_engine() as engine:
                    with closing(engine.raw_connection()) as conn:
                        is_alive = engine.dialect.do_ping(conn)
                        if is_alive:
                            return {
                                "name": database.database_name,
                                "status": "healthy",
                                "message": "Database is accessible"
                            }
                        else:
                            return {
                                "name": database.database_name,
                                "status": "unhealthy",
                                "message": "Database is not responding"
                            }
        except Exception as e:
            logger.error("Database %s health check failed: %s", database.database_name, str(e))
            return {
                "name": database.database_name,
                "status": "unhealthy",
                "message": f"Error: {str(e)}"
            }

    async def check_database_connections_async(self, max_workers: int = 20) -> List[Dict[str, str]]:
        """Check if all configured databases are accessible using async/concurrent execution
        
        Args:
            max_workers: Maximum number of concurrent database checks (default: 20)
        """
        databases = self.db_session.query(Database).all()
        
        if not databases:
            return []
        
        # Get the current Flask app to pass to threads
        app = current_app._get_current_object()
        
        # Use ThreadPoolExecutor for concurrent database checks
        # Since SQLAlchemy operations are sync, we run them in threads
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all database check tasks
            futures = [
                loop.run_in_executor(executor, self._check_single_database, database, app)
                for database in databases
            ]
            
            # Wait for all futures to complete and gather results
            results = await asyncio.gather(*futures, return_exceptions=True)
            
            # Process results and handle any exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    database_name = databases[i].database_name if i < len(databases) else "Unknown"
                    logger.error("Async database check failed for %s: %s", database_name, str(result))
                    processed_results.append({
                        "name": database_name,
                        "status": "unhealthy",
                        "message": f"Async check error: {str(result)}"
                    })
                else:
                    processed_results.append(result)
            
            return processed_results

    def check_database_connections(self) -> List[Dict[str, str]]:
        """Check if all configured databases are accessible (sync wrapper for async method)"""
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to handle this differently
                # Create a new event loop in a thread
                import threading
                result = None
                exception = None
                
                def run_async():
                    nonlocal result, exception
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result = new_loop.run_until_complete(self.check_database_connections_async())
                        new_loop.close()
                    except Exception as e:
                        exception = e
                
                thread = threading.Thread(target=run_async)
                thread.start()
                thread.join()
                
                if exception:
                    raise exception
                return result
            else:
                # No running loop, we can use the existing one
                return loop.run_until_complete(self.check_database_connections_async())
        except RuntimeError:
            # No event loop exists, create one
            return asyncio.run(self.check_database_connections_async())

    def get_health_status(self, detailed: bool = False) -> Tuple[Dict[str, Any], int]:
        """Get comprehensive health status of all components
        
        Args:
            detailed: If True, check all components (metadata database, cache, and databases).
                     If False, check metadata database and cache only (default behavior).
        """
        # Always check metadata database (core requirement)
        metadata_db_healthy, metadata_db_message = self.check_metadata_db()
        
        # Always check cache system (now part of default checks)
        cache_healthy, cache_message = self.check_cache()
        
        response = {
            "status": "healthy" if (metadata_db_healthy and cache_healthy) else "unhealthy",
            "components": {
                "metadata_database": {
                    "status": "healthy" if metadata_db_healthy else "unhealthy",
                    "message": metadata_db_message
                },
                "cache": {
                    "status": "healthy" if cache_healthy else "unhealthy",
                    "message": cache_message
                }
            }
        }
        
        overall_healthy = metadata_db_healthy and cache_healthy
        
        if detailed:
            # Check database connections (only in detailed mode) - now async!
            database_results = self.check_database_connections()
            response["components"]["databases"] = database_results
            
            # Update overall health status to include database checks
            all_databases_healthy = all(db_result["status"] == "healthy" for db_result in database_results)
            overall_healthy = metadata_db_healthy and cache_healthy and all_databases_healthy
            response["status"] = "healthy" if overall_healthy else "unhealthy"
        else:
            # For non-detailed checks, indicate that database checks were skipped
            response["components"]["databases"] = {
                "status": "skipped",
                "message": "Database connections check skipped (use ?detail=true for full health check)"
            }
        
        status_code = 200 if overall_healthy else 503
        return response, status_code 