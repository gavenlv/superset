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

from flask import jsonify, request

from superset import app, talisman
from superset.apex.health import HealthChecker
from superset.stats_logger import BaseStatsLogger
from superset.superset_typing import FlaskResponse


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
