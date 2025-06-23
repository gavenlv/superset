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

"""Configuration module for Apex functionality."""

import logging
from typing import Any

from flask import Flask

logger = logging.getLogger(__name__)


def init_apex_config(app: Flask) -> None:
    """
    Initialize Apex configuration settings.
    
    Args:
        app: Flask application instance
    """
    # JWT Header Authentication settings
    app.config.setdefault("APEX_JWT_HEADER_AUTH_ENABLED", True)
    app.config.setdefault("APEX_JWT_DEFAULT_EXPIRES_IN", 86400)  # 24 hours
    
    # Swagger UI anonymous access settings
    app.config.setdefault("APEX_SWAGGER_ANONYMOUS_ENABLED", True)
    app.config.setdefault("APEX_SWAGGER_ANONYMOUS_PATHS", [
        "/swagger",
        "/api/v1/_openapi",
        "/api/v1/_openapi.json",
        "/swaggerui/",
    ])
    
    # API endpoint settings
    app.config.setdefault("APEX_API_ENABLED", True)
    app.config.setdefault("APEX_API_PREFIX", "/api/v1/apex")
    
    logger.info("Apex configuration initialized")


def register_apex_apis(app: Flask) -> None:
    """
    Register Apex APIs with the Flask application.
    
    Args:
        app: Flask application instance
    """
    if not app.config.get("APEX_API_ENABLED", True):
        return
    
    try:
        from flask_appbuilder import AppBuilder
        from .api import ApexApi
        
        # Get AppBuilder instance
        appbuilder = app.extensions.get("appbuilder")
        if appbuilder:
            # Register Apex API
            appbuilder.add_api(ApexApi)
            logger.info("Apex API registered successfully")
        else:
            logger.warning("AppBuilder not found, cannot register Apex API")
            
    except Exception as e:
        logger.error(f"Failed to register Apex APIs: {e}")


def init_apex_security(app: Flask) -> None:
    """
    Initialize Apex security enhancements.
    
    Args:
        app: Flask application instance
    """
    if not app.config.get("APEX_JWT_HEADER_AUTH_ENABLED", True):
        return
    
    try:
        from .middleware import jwt_security_extension, enhance_security_manager
        
        # Initialize JWT security extension
        jwt_security_extension.init_app(app)
        
        # Enhance security manager (this should be done after security manager is created)
        @app.before_first_request
        def enhance_security():
            enhance_security_manager()
            
        logger.info("Apex security enhancements initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize Apex security: {e}")


def configure_swagger_access(app: Flask) -> None:
    """
    Configure Swagger UI for anonymous access.
    
    Args:
        app: Flask application instance
    """
    if not app.config.get("APEX_SWAGGER_ANONYMOUS_ENABLED", True):
        return
    
    try:
        # Enable Swagger UI
        app.config["FAB_API_SWAGGER_UI"] = True
        
        # Override Flask-AppBuilder's security check for Swagger UI
        @app.before_request
        def allow_swagger_anonymous():
            from flask import request
            
            swagger_paths = app.config.get("APEX_SWAGGER_ANONYMOUS_PATHS", [])
            if any(request.path.startswith(path) for path in swagger_paths):
                # Skip authentication for Swagger UI paths
                pass
        
        logger.info("Swagger UI anonymous access configured")
        
    except Exception as e:
        logger.error(f"Failed to configure Swagger access: {e}")


def init_apex(app: Flask) -> None:
    """
    Initialize all Apex functionality.
    
    This is the main initialization function that should be called
    during Superset application setup.
    
    Args:
        app: Flask application instance
    """
    logger.info("Initializing Apex module...")
    
    # Initialize configuration
    init_apex_config(app)
    
    # Configure Swagger access
    configure_swagger_access(app)
    
    # Initialize security enhancements
    init_apex_security(app)
    
    # Register APIs (should be done after AppBuilder is created)
    @app.before_first_request
    def register_apis():
        register_apex_apis(app)
    
    logger.info("Apex module initialization completed")


# Configuration settings that can be imported and used in superset_config.py
APEX_CONFIG = {
    # Enable/disable JWT header authentication
    "APEX_JWT_HEADER_AUTH_ENABLED": True,
    
    # Default JWT token expiration time (in seconds)
    "APEX_JWT_DEFAULT_EXPIRES_IN": 86400,  # 24 hours
    
    # Enable/disable Swagger UI anonymous access
    "APEX_SWAGGER_ANONYMOUS_ENABLED": True,
    
    # Paths that should allow anonymous access for Swagger UI
    "APEX_SWAGGER_ANONYMOUS_PATHS": [
        "/swagger",
        "/api/v1/_openapi", 
        "/api/v1/_openapi.json",
        "/swaggerui/",
    ],
    
    # Enable/disable Apex API endpoints
    "APEX_API_ENABLED": True,
    
    # API prefix for Apex endpoints
    "APEX_API_PREFIX": "/api/v1/apex",
} 