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
from datetime import datetime, timedelta
from typing import Any

import jwt
from flask import current_app, request, Response
from flask_appbuilder import expose
from flask_appbuilder.api import safe
from flask_appbuilder.security.decorators import permission_name, protect
from flask_wtf.csrf import generate_csrf
from marshmallow import EXCLUDE, fields, post_load, Schema, ValidationError

from superset.commands.dashboard.embedded.exceptions import (
    EmbeddedDashboardNotFoundError,
)
from superset.exceptions import SupersetGenericErrorException
from superset.extensions import event_logger, security_manager
from superset.security.guest_token import GuestTokenResourceType
from superset.views.base_api import BaseSupersetApi, statsd_metrics

logger = logging.getLogger(__name__)


class PermissiveSchema(Schema):
    """
    A marshmallow schema that ignores unexpected fields, instead of throwing an error.
    """

    class Meta:  # pylint: disable=too-few-public-methods
        unknown = EXCLUDE


class UserSchema(PermissiveSchema):
    username = fields.String()
    first_name = fields.String()
    last_name = fields.String()


class ResourceSchema(PermissiveSchema):
    type = fields.Enum(GuestTokenResourceType, by_value=True, required=True)
    id = fields.String(required=True)

    @post_load
    def convert_enum_to_value(  # pylint: disable=unused-argument
        self,
        data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        # we don't care about the enum, we want the value inside
        data["type"] = data["type"].value
        return data


class RlsRuleSchema(PermissiveSchema):
    dataset = fields.Integer()
    clause = fields.String(required=True)  # todo other options?


class GuestTokenCreateSchema(PermissiveSchema):
    user = fields.Nested(UserSchema)
    resources = fields.List(fields.Nested(ResourceSchema), required=True)
    rls = fields.List(fields.Nested(RlsRuleSchema), required=True)


class LoginSchema(PermissiveSchema):
    username = fields.String(required=True)
    password = fields.String(required=True)


class RefreshTokenSchema(PermissiveSchema):
    refresh_token = fields.String(required=True)


guest_token_create_schema = GuestTokenCreateSchema()
login_schema = LoginSchema()
refresh_token_schema = RefreshTokenSchema()


class SecurityRestApi(BaseSupersetApi):
    resource_name = "security"
    allow_browser_login = True
    openapi_spec_tag = "Security"

    @expose("/csrf_token/", methods=("GET",))
    @event_logger.log_this
    @protect()
    @safe
    @statsd_metrics
    @permission_name("read")
    def csrf_token(self) -> Response:
        """Get the CSRF token.
        ---
        get:
          summary: Get the CSRF token
          responses:
            200:
              description: Result contains the CSRF token
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                        result:
                          type: string
            401:
              $ref: '#/components/responses/401'
            500:
              $ref: '#/components/responses/500'
        """
        return self.response(200, result=generate_csrf())

    @expose("/login/", methods=("POST",))
    @event_logger.log_this
    @safe
    @statsd_metrics
    def login(self) -> Response:
        """Authenticate and get a JWT access and refresh token.
        ---
        post:
          summary: Authenticate and get a JWT access and refresh token
          requestBody:
            description: Login credentials
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    username:
                      type: string
                    password:
                      type: string
                  required:
                    - username
                    - password
          responses:
            200:
              description: Authentication successful
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      access_token:
                        type: string
                      refresh_token:
                        type: string
                      expires_in:
                        type: integer
            400:
              $ref: '#/components/responses/400'
            401:
              description: Invalid credentials
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      message:
                        type: string
            500:
              $ref: '#/components/responses/500'
        """
        try:
            credentials = login_schema.load(request.json)
            username = credentials["username"]
            password = credentials["password"]
            
            # Authenticate user
            user = security_manager.auth_user_db(username, password)
            if not user:
                return self.response_401(message="Invalid credentials")
                
            if not user.is_active:
                return self.response_401(message="User account is inactive")
            
            # Generate JWT tokens
            access_token, refresh_token, expires_in = self._generate_jwt_tokens(user)
            
            return self.response(200, 
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in
            )
            
        except ValidationError as error:
            return self.response_400(message=error.messages)
        except Exception as error:
            logger.exception("Error during JWT login")
            return self.response_500(message="Internal server error during login")

    @expose("/refresh/", methods=("POST",))
    @event_logger.log_this
    @safe
    @statsd_metrics
    def refresh(self) -> Response:
        """Use the refresh token to get a new JWT access token.
        ---
        post:
          summary: Use the refresh token to get a new JWT access token
          requestBody:
            description: Refresh token
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    refresh_token:
                      type: string
                  required:
                    - refresh_token
          responses:
            200:
              description: Token refresh successful
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      access_token:
                        type: string
                      expires_in:
                        type: integer
            400:
              $ref: '#/components/responses/400'
            401:
              description: Invalid or expired refresh token
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      message:
                        type: string
            500:
              $ref: '#/components/responses/500'
        """
        try:
            data = refresh_token_schema.load(request.json)
            refresh_token = data["refresh_token"]
            
            # Validate refresh token
            user = self._validate_refresh_token(refresh_token)
            if not user:
                return self.response_401(message="Invalid or expired refresh token")
                
            if not user.is_active:
                return self.response_401(message="User account is inactive")
            
            # Generate new access token
            access_token = self._generate_access_token(user)
            expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
            
            return self.response(200,
                access_token=access_token,
                expires_in=expires_in
            )
            
        except ValidationError as error:
            return self.response_400(message=error.messages)
        except Exception as error:
            logger.exception("Error during token refresh")
            return self.response_500(message="Internal server error during token refresh")

    @expose("/guest_token/", methods=("POST",))
    @event_logger.log_this
    @protect()
    @safe
    @statsd_metrics
    @permission_name("grant_guest_token")
    def guest_token(self) -> Response:
        """Get a guest token that can be used for auth in embedded Superset.
        ---
        post:
          summary: Get a guest token
          requestBody:
            description: Parameters for the guest token
            required: true
            content:
              application/json:
                schema: GuestTokenCreateSchema
          responses:
            200:
              description: Result contains the guest token
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                        token:
                          type: string
            401:
              $ref: '#/components/responses/401'
            400:
              $ref: '#/components/responses/400'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            body = guest_token_create_schema.load(request.json)
            self.appbuilder.sm.validate_guest_token_resources(body["resources"])
            guest_token_validator_hook = current_app.config.get(
                "GUEST_TOKEN_VALIDATOR_HOOK"
            )
            # Run validator to ensure the token parameters are OK.
            if guest_token_validator_hook is not None:
                if callable(guest_token_validator_hook):
                    if not guest_token_validator_hook(body):
                        raise ValidationError(message="Guest token validation failed")
                else:
                    raise SupersetGenericErrorException(
                        message="Guest token validator hook not callable"
                    )
            # TODO: Add generic validation:
            # make sure username doesn't reference an existing user
            # check rls rules for validity?
            token = self.appbuilder.sm.create_guest_access_token(
                body["user"], body["resources"], body["rls"]
            )
            return self.response(200, token=token)
        except EmbeddedDashboardNotFoundError as error:
            return self.response_400(message=error.message)
        except ValidationError as error:
            return self.response_400(message=error.messages)

    def _generate_jwt_tokens(self, user) -> tuple[str, str, int]:
        """Generate JWT access and refresh tokens for a user."""
        access_token = self._generate_access_token(user)
        refresh_token = self._generate_refresh_token(user)
        expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
        return access_token, refresh_token, expires_in

    def _generate_access_token(self, user) -> str:
        """Generate JWT access token for a user."""
        secret_key = current_app.config.get('JWT_SECRET_KEY') or current_app.config['SECRET_KEY']
        algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
        expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
        
        now = datetime.utcnow()
        payload = {
            'user_id': user.id,
            'username': user.username,
            'iat': now,
            'exp': now + timedelta(seconds=expires_in),
            'type': 'access'
        }
        
        return jwt.encode(payload, secret_key, algorithm=algorithm)

    def _generate_refresh_token(self, user) -> str:
        """Generate JWT refresh token for a user."""
        secret_key = current_app.config.get('JWT_SECRET_KEY') or current_app.config['SECRET_KEY']
        algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
        expires_in = current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES', 30 * 24 * 3600)  # 30 days
        
        now = datetime.utcnow()
        payload = {
            'user_id': user.id,
            'username': user.username,
            'iat': now,
            'exp': now + timedelta(seconds=expires_in),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, secret_key, algorithm=algorithm)

    def _validate_refresh_token(self, token: str):
        """Validate refresh token and return user if valid."""
        try:
            secret_key = current_app.config.get('JWT_SECRET_KEY') or current_app.config['SECRET_KEY']
            algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
            
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[algorithm],
                options={"verify_exp": True}
            )
            
            # Check if it's a refresh token
            if payload.get('type') != 'refresh':
                return None
                
            user_id = payload.get('user_id')
            if not user_id:
                return None
                
            user = security_manager.get_user_by_id(user_id)
            return user
            
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
