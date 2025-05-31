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
from superset import app, talisman
from superset.stats_logger import BaseStatsLogger
from superset.superset_typing import FlaskResponse
from superset.extensions import db, cache_manager
from superset.models.core import Database
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, request
import logging
from contextlib import closing
from typing import Dict, List, Tuple, Any

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

    def check_database_connections(self) -> List[Dict[str, str]]:
        """Check if all configured databases are accessible"""
        results = []
        databases = self.db_session.query(Database).all()
        
        for database in databases:
            try:
                with database.get_sqla_engine() as engine:
                    with closing(engine.raw_connection()) as conn:
                        is_alive = engine.dialect.do_ping(conn)
                        if is_alive:
                            results.append({
                                "name": database.database_name,
                                "status": "healthy",
                                "message": "Database is accessible"
                            })
                        else:
                            results.append({
                                "name": database.database_name,
                                "status": "unhealthy",
                                "message": "Database is not responding"
                            })
            except Exception as e:
                logger.error("Database %s health check failed: %s", database.database_name, str(e))
                results.append({
                    "name": database.database_name,
                    "status": "unhealthy",
                    "message": f"Error: {str(e)}"
                })
        
        return results

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
            # Check database connections (only in detailed mode)
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


@talisman(force_https=False)
@app.route("/health")
@app.route("/healthcheck")
@app.route("/ping")
def health() -> FlaskResponse:
    """Enhanced health check endpoint that verifies the status of critical components
    
    Query Parameters:
        detail (bool): If 'true', performs detailed health checks on all components
                      (metadata database, cache, and database connections). If 'false' or omitted,
                      checks metadata database and cache only (default behavior).
    
    Examples:
        GET /health - Standard check (metadata database and cache)
        GET /health?detail=true - Full health check (all components including database connections)
    """
    stats_logger: BaseStatsLogger = app.config["STATS_LOGGER"]
    stats_logger.incr("health")
    
    # Parse detail parameter
    detail_param = request.args.get('detail', 'false').lower()
    detailed = detail_param in ('true', '1', 'yes', 'on')
    
    health_checker = HealthChecker()
    response, status_code = health_checker.get_health_status(detailed=detailed)
    
    return jsonify(response), status_code
