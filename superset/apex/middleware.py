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

"""Middleware integration module for JWT header authentication."""

import logging
from typing import Optional

from flask import Flask, request
from flask_appbuilder.security.sqla.models import User

from .jwt_auth import jwt_header_auth_middleware

logger = logging.getLogger(__name__)


class JwtHeaderSecurityExtension:
    """
    Security extension for JWT header authentication.
    
    This class extends Superset's security manager to support JWT header
    authentication alongside existing cookie-based authentication.
    """
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """
        Initialize the JWT header security extension.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Enable JWT header authentication by default
        app.config.setdefault("APEX_JWT_HEADER_AUTH_ENABLED", True)
        
        # Configure paths that should allow anonymous access for Swagger UI
        app.config.setdefault("APEX_SWAGGER_ANONYMOUS_PATHS", [
            "/swagger",
            "/api/v1/_openapi",
            "/api/v1/_openapi.json",
            "/swaggerui/"
        ])
        
        # Register request middleware
        if app.config.get("APEX_JWT_HEADER_AUTH_ENABLED", True):
            self._register_middleware(app)
    
    def _register_middleware(self, app: Flask) -> None:
        """
        Register JWT header authentication middleware.
        
        Args:
            app: Flask application instance
        """
        @app.before_request
        def before_request_jwt_auth():
            """Before request hook for JWT header authentication."""
            if app.config.get("APEX_JWT_HEADER_AUTH_ENABLED", True):
                jwt_header_auth_middleware()
    
    def is_swagger_path(self, path: str) -> bool:
        """
        Check if the given path is a Swagger-related path.
        
        Args:
            path: Request path
            
        Returns:
            True if path is Swagger-related, False otherwise
        """
        if not self.app:
            return False
            
        swagger_paths = self.app.config.get("APEX_SWAGGER_ANONYMOUS_PATHS", [])
        return any(path.startswith(swagger_path) for swagger_path in swagger_paths)


def enhance_security_manager():
    """
    Enhance Superset's security manager with JWT header authentication.
    
    This function patches the security manager's request_loader to support
    JWT header authentication alongside existing authentication methods.
    """
    from superset.extensions import security_manager
    from .jwt_auth import jwt_authenticator
    
    # Store original request_loader
    original_request_loader = security_manager.request_loader
    
    def enhanced_request_loader(request) -> Optional[User]:
        """
        Enhanced request loader with JWT header authentication support.
        
        Args:
            request: Flask request object
            
        Returns:
            Authenticated user if found, None otherwise
        """
        # First try original request loader (guest tokens, etc.)
        user = original_request_loader(request) if original_request_loader else None
        if user:
            return user
        
        # Then try JWT header authentication
        return jwt_authenticator.authenticate_request()
    
    # Replace request_loader with enhanced version
    security_manager.lm.request_loader(enhanced_request_loader)
    logger.info("Security manager enhanced with JWT header authentication")


def configure_swagger_anonymous_access():
    """
    Configure Swagger UI for anonymous access.
    
    This function modifies the security settings to allow anonymous access
    to Swagger UI endpoints while keeping API calls protected.
    """
    from flask import current_app
    
    # Enable anonymous access to Swagger UI
    current_app.config["FAB_API_SWAGGER_UI"] = True
    
    # Configure additional anonymous paths if needed
    anonymous_paths = current_app.config.get("APEX_SWAGGER_ANONYMOUS_PATHS", [])
    logger.info(f"Configured anonymous access for paths: {anonymous_paths}")


# Global extension instance
jwt_security_extension = JwtHeaderSecurityExtension() 