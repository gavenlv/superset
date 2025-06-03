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

import functools
import logging
from typing import Any, Callable, Optional
import json

import jwt
from flask import current_app, g, request, Response
from flask_appbuilder.security.decorators import protect as fab_protect
from flask_login import current_user

from superset.extensions import security_manager

logger = logging.getLogger(__name__)


def jwt_protect(
    allow_cookie_auth: bool = True,
    allow_jwt_auth: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Enhanced protection decorator that supports both JWT token and cookie authentication.
    
    This decorator extends Flask-AppBuilder's protect decorator to support JWT tokens
    in addition to the default cookie-based authentication.
    
    :param allow_cookie_auth: Whether to allow cookie-based authentication (default: True)
    :param allow_jwt_auth: Whether to allow JWT token authentication (default: True)
    :return: Decorated function
    """
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Try JWT authentication first if enabled
            if allow_jwt_auth:
                user = _authenticate_with_jwt()
                if user:
                    g.user = user
                    return f(*args, **kwargs)
            
            # Fall back to cookie authentication if enabled
            if allow_cookie_auth:
                # Use Flask-AppBuilder's original protect decorator
                protected_func = fab_protect()(f)
                return protected_func(*args, **kwargs)
            
            # If no authentication method is allowed or successful, return 401
            return Response(
                json.dumps({"message": "Authentication required"}),
                status=401,
                content_type="application/json"
            )
            
        return wrapper
    return decorator


def _authenticate_with_jwt() -> Optional[Any]:
    """
    Extract and validate JWT token from Authorization header.
    
    :return: User object if authentication successful, None otherwise
    """
    try:
        # Check for Authorization header with Bearer token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
            
        if not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ', 1)[1]
        if not token:
            return None
            
        # Decode and validate JWT token
        secret_key = current_app.config.get('JWT_SECRET_KEY') or current_app.config['SECRET_KEY']
        algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
        
        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[algorithm],
                options={"verify_exp": True}
            )
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
            
        # Extract user information from payload
        user_id = payload.get('user_id')
        username = payload.get('username')
        
        if not user_id and not username:
            logger.warning("JWT token missing user identification")
            return None
            
        # Get user from database
        if user_id:
            user = security_manager.get_user_by_id(user_id)
        else:
            user = security_manager.find_user(username=username)
            
        if not user:
            logger.warning(f"User not found for JWT token: user_id={user_id}, username={username}")
            return None
            
        if not user.is_active:
            logger.warning(f"User is not active: {user.username}")
            return None
            
        return user
        
    except Exception as e:
        logger.exception(f"Error during JWT authentication: {e}")
        return None


def jwt_required() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that requires JWT authentication only (no cookie fallback).
    
    :return: Decorated function
    """
    return jwt_protect(allow_cookie_auth=False, allow_jwt_auth=True)


def protect_with_jwt() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that allows both JWT and cookie authentication.
    This is the recommended decorator for most API endpoints.
    
    :return: Decorated function
    """
    return jwt_protect(allow_cookie_auth=True, allow_jwt_auth=True) 