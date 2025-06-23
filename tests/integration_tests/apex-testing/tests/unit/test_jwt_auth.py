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

"""Unit tests for JWT header authentication functionality."""

import time
from unittest.mock import Mock, patch
import jwt
import pytest
from flask import Flask, request
from flask_appbuilder.security.sqla.models import User

from superset.apex.jwt_auth import (
    JwtHeaderAuthenticator,
    create_jwt_token,
    jwt_header_auth_middleware,
)


class TestJwtHeaderAuthenticator:
    """Test cases for JwtHeaderAuthenticator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.authenticator = JwtHeaderAuthenticator()
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "test-secret-key"
        
        # Mock user
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 1
        self.mock_user.username = "testuser"
        self.mock_user.first_name = "Test"
        self.mock_user.last_name = "User"
        self.mock_user.is_authenticated = True
    
    def test_get_jwt_token_from_header_with_valid_token(self):
        """Test extracting JWT token from valid Authorization header."""
        with self.app.test_request_context(headers={"Authorization": "Bearer test-token"}):
            token = self.authenticator.get_jwt_token_from_header()
            assert token == "test-token"
    
    def test_get_jwt_token_from_header_without_bearer_prefix(self):
        """Test handling Authorization header without Bearer prefix."""
        with self.app.test_request_context(headers={"Authorization": "test-token"}):
            token = self.authenticator.get_jwt_token_from_header()
            assert token is None
    
    def test_get_jwt_token_from_header_no_header(self):
        """Test handling missing Authorization header."""
        with self.app.test_request_context():
            token = self.authenticator.get_jwt_token_from_header()
            assert token is None
    
    def test_decode_jwt_token_valid(self):
        """Test decoding valid JWT token."""
        with self.app.app_context():
            payload = {"sub": "1", "username": "testuser", "exp": int(time.time()) + 3600}
            token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
            
            decoded = self.authenticator.decode_jwt_token(token)
            assert decoded is not None
            assert decoded["sub"] == "1"
            assert decoded["username"] == "testuser"
    
    def test_decode_jwt_token_expired(self):
        """Test handling expired JWT token."""
        with self.app.app_context():
            payload = {"sub": "1", "username": "testuser", "exp": int(time.time()) - 3600}
            token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
            
            decoded = self.authenticator.decode_jwt_token(token)
            assert decoded is None
    
    def test_decode_jwt_token_invalid_signature(self):
        """Test handling JWT token with invalid signature."""
        with self.app.app_context():
            payload = {"sub": "1", "username": "testuser", "exp": int(time.time()) + 3600}
            token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
            
            decoded = self.authenticator.decode_jwt_token(token)
            assert decoded is None
    
    @patch("superset.apex.jwt_auth.security_manager")
    def test_get_user_from_payload_by_id(self, mock_security_manager):
        """Test getting user from payload using user ID."""
        mock_security_manager.get_user_by_id.return_value = self.mock_user
        
        payload = {"sub": "1", "user_id": 1}
        user = self.authenticator.get_user_from_payload(payload)
        
        assert user == self.mock_user
        mock_security_manager.get_user_by_id.assert_called_once_with(1)
    
    @patch("superset.apex.jwt_auth.security_manager")
    def test_get_user_from_payload_by_username(self, mock_security_manager):
        """Test getting user from payload using username."""
        mock_security_manager.get_user_by_id.return_value = None
        mock_security_manager.find_user.return_value = self.mock_user
        
        payload = {"username": "testuser"}
        user = self.authenticator.get_user_from_payload(payload)
        
        assert user == self.mock_user
        mock_security_manager.find_user.assert_called_once_with(username="testuser")
    
    @patch("superset.apex.jwt_auth.security_manager")
    def test_get_user_from_payload_not_found(self, mock_security_manager):
        """Test handling when user is not found."""
        mock_security_manager.get_user_by_id.return_value = None
        mock_security_manager.find_user.return_value = None
        
        payload = {"sub": "999", "username": "nonexistent"}
        user = self.authenticator.get_user_from_payload(payload)
        
        assert user is None
    
    @patch("superset.apex.jwt_auth.login_user")
    @patch("superset.apex.jwt_auth.g")
    def test_authenticate_request_success(self, mock_g, mock_login_user):
        """Test successful request authentication."""
        with self.app.app_context():
            # Create valid token
            payload = {"sub": "1", "username": "testuser", "exp": int(time.time()) + 3600}
            token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
            
            with patch.object(self.authenticator, "get_jwt_token_from_header", return_value=token):
                with patch.object(self.authenticator, "get_user_from_payload", return_value=self.mock_user):
                    user = self.authenticator.authenticate_request()
                    
                    assert user == self.mock_user
                    mock_login_user.assert_called_once_with(self.mock_user)
                    assert mock_g.user == self.mock_user
    
    def test_authenticate_request_no_token(self):
        """Test authentication when no token is provided."""
        with self.app.test_request_context():
            user = self.authenticator.authenticate_request()
            assert user is None


class TestCreateJwtToken:
    """Test cases for create_jwt_token function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "test-secret-key"
        
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 1
        self.mock_user.username = "testuser"
    
    def test_create_jwt_token_default_expiration(self):
        """Test creating JWT token with default expiration."""
        with self.app.app_context():
            token = create_jwt_token(self.mock_user)
            
            decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
            assert decoded["sub"] == "1"
            assert decoded["user_id"] == 1
            assert decoded["username"] == "testuser"
            assert "iat" in decoded
            assert "exp" in decoded
    
    def test_create_jwt_token_custom_expiration(self):
        """Test creating JWT token with custom expiration."""
        with self.app.app_context():
            expires_delta = 3600  # 1 hour
            token = create_jwt_token(self.mock_user, expires_delta)
            
            decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
            expected_exp = decoded["iat"] + expires_delta
            assert decoded["exp"] == expected_exp
    
    def test_create_jwt_token_no_secret_key(self):
        """Test error handling when SECRET_KEY is not configured."""
        app = Flask(__name__)
        with app.app_context():
            with pytest.raises(ValueError, match="SECRET_KEY not configured"):
                create_jwt_token(self.mock_user)


class TestJwtHeaderAuthMiddleware:
    """Test cases for JWT header authentication middleware."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "test-secret-key"
    
    @patch("superset.apex.jwt_auth.jwt_authenticator")
    def test_middleware_skip_paths(self, mock_authenticator):
        """Test that middleware skips authentication for certain paths."""
        skip_paths = ["/login", "/api/v1/security/login", "/swagger"]
        
        for path in skip_paths:
            with self.app.test_request_context(path=path):
                jwt_header_auth_middleware()
                mock_authenticator.authenticate_request.assert_not_called()
    
    @patch("superset.apex.jwt_auth.jwt_authenticator")
    @patch("superset.apex.jwt_auth.g")
    def test_middleware_skip_authenticated_user(self, mock_g, mock_authenticator):
        """Test that middleware skips when user is already authenticated."""
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_g.user = mock_user
        
        with self.app.test_request_context("/api/v1/chart/"):
            jwt_header_auth_middleware()
            mock_authenticator.authenticate_request.assert_not_called()
    
    @patch("superset.apex.jwt_auth.jwt_authenticator")
    @patch("superset.apex.jwt_auth.g")
    def test_middleware_authenticate_unauthenticated_request(self, mock_g, mock_authenticator):
        """Test that middleware attempts authentication for unauthenticated requests."""
        mock_g.user = None
        
        with self.app.test_request_context("/api/v1/chart/"):
            jwt_header_auth_middleware()
            mock_authenticator.authenticate_request.assert_called_once() 