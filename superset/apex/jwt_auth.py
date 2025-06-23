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

"""JWT header authentication module for Superset API access."""

import logging
from typing import Any, Optional

import jwt
from flask import current_app, g, request
from flask_appbuilder.security.sqla.models import User
from flask_login import login_user

logger = logging.getLogger(__name__)


class JwtHeaderAuthenticator:
    """
    JWT Header Authenticator for Superset APIs.
    
    This class provides functionality to authenticate users via JWT tokens
    passed in HTTP headers, enabling third-party API access without cookies.
    """
    
    def __init__(self):
        self.jwt_header_name = "Authorization"
        self.jwt_token_prefix = "Bearer "
        
    def get_jwt_token_from_header(self) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Returns:
            JWT token string if found, None otherwise
        """
        auth_header = request.headers.get(self.jwt_header_name)
        if not auth_header:
            return None
            
        if not auth_header.startswith(self.jwt_token_prefix):
            return None
            
        return auth_header[len(self.jwt_token_prefix):].strip()
    
    def decode_jwt_token(self, token: str) -> Optional[dict[str, Any]]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            # Use same secret and algorithm as Superset's login system
            secret_key = current_app.config.get("SECRET_KEY")
            if not secret_key:
                logger.error("SECRET_KEY not configured")
                return None
                
            # Decode the JWT token
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=["HS256"],
                options={"verify_exp": True}
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error decoding JWT token: {e}")
            return None
    
    def get_user_from_payload(self, payload: dict[str, Any]) -> Optional[User]:
        """
        Get user from JWT payload.
        
        Args:
            payload: Decoded JWT payload
            
        Returns:
            User object if found, None otherwise
        """
        try:
            from superset.extensions import security_manager
            
            # Extract user identifier from payload
            user_id = payload.get("sub") or payload.get("user_id")
            username = payload.get("username")
            
            if user_id:
                # Try to find user by ID first
                try:
                    user_id = int(user_id)
                    user = security_manager.get_user_by_id(user_id)
                    if user:
                        return user
                except (ValueError, TypeError):
                    pass
            
            if username:
                # Fallback to username
                user = security_manager.find_user(username=username)
                if user:
                    return user
                    
            logger.warning(f"User not found for payload: {payload}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user from payload: {e}")
            return None
    
    def authenticate_request(self) -> Optional[User]:
        """
        Authenticate current request using JWT token from header.
        
        Returns:
            Authenticated user if successful, None otherwise
        """
        # Extract JWT token from header
        token = self.get_jwt_token_from_header()
        if not token:
            return None
            
        # Decode and validate token
        payload = self.decode_jwt_token(token)
        if not payload:
            return None
            
        # Get user from payload
        user = self.get_user_from_payload(payload)
        if not user:
            return None
            
        # Set user in Flask-Login context
        login_user(user)
        g.user = user
        
        logger.info(f"Successfully authenticated user {user.username} via JWT header")
        return user


# Global instance
jwt_authenticator = JwtHeaderAuthenticator()


def jwt_header_auth_middleware():
    """
    Middleware function to authenticate requests via JWT header.
    
    This function should be called early in the request processing pipeline
    to enable JWT header authentication for APIs.
    """
    # Skip authentication for certain paths
    skip_paths = [
        "/login",
        "/logout", 
        "/api/v1/security/login",
        "/static/",
        "/swagger",
        "/api/v1/_openapi"
    ]
    
    # Check if current path should skip JWT authentication
    if any(request.path.startswith(path) for path in skip_paths):
        return
    
    # Skip if user is already authenticated
    if hasattr(g, 'user') and g.user and g.user.is_authenticated:
        return
        
    # Try to authenticate via JWT header
    jwt_authenticator.authenticate_request()


def create_jwt_token(user: User, expires_delta: Optional[int] = None) -> str:
    """
    Create a JWT token for a user.
    
    Args:
        user: User object
        expires_delta: Token expiration time in seconds (default: 24 hours)
        
    Returns:
        JWT token string
    """
    import time
    
    if expires_delta is None:
        expires_delta = 24 * 60 * 60  # 24 hours
    
    payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "username": user.username,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_delta
    }
    
    secret_key = current_app.config.get("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY not configured")
    
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token 