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

"""Apex API module for enhanced authentication and API access."""

import logging
from typing import Any

from flask import request, Response
from flask_appbuilder.api import expose, safe
from flask_appbuilder.security.decorators import permission_name, protect
from marshmallow import fields, Schema, ValidationError

from superset.extensions import event_logger, security_manager
from superset.views.base_api import BaseSupersetApi, statsd_metrics
from .jwt_auth import create_jwt_token

logger = logging.getLogger(__name__)


class JwtLoginSchema(Schema):
    """Schema for JWT login request."""
    username = fields.String(required=True)
    password = fields.String(required=True)
    provider = fields.String(missing="db")
    expires_in = fields.Integer(missing=86400)  # 24 hours default


class JwtTokenResponseSchema(Schema):
    """Schema for JWT token response."""
    access_token = fields.String()
    token_type = fields.String()
    expires_in = fields.Integer()


class ApexApi(BaseSupersetApi):
    """
    Apex API for enhanced authentication and third-party integration.
    
    This API provides additional authentication methods and utilities
    for better third-party integration with Superset.
    """
    
    resource_name = "apex"
    allow_browser_login = True
    openapi_spec_tag = "Apex"

    @expose("/jwt_login", methods=("POST",))
    @event_logger.log_this
    @safe
    @statsd_metrics
    def jwt_login(self) -> Response:
        """
        Authenticate and get a JWT token for API access.
        ---
        post:
          summary: Authenticate and get JWT token
          description: >-
            Generate a JWT token for API access. This token can be used in 
            the Authorization header as "Bearer <token>" for subsequent API calls.
          requestBody:
            description: Login credentials
            required: true
            content:
              application/json:
                schema: JwtLoginSchema
          responses:
            200:
              description: Authentication successful
              content:
                application/json:
                  schema: JwtTokenResponseSchema
            400:
              $ref: '#/components/responses/400'
            401:
              $ref: '#/components/responses/401'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            # Validate request data
            schema = JwtLoginSchema()
            data = schema.load(request.json or {})
            
            # Authenticate user
            user = security_manager.auth_user_db(
                data["username"], 
                data["password"]
            )
            
            if not user:
                return self.response_401()
            
            # Create JWT token
            token = create_jwt_token(user, data["expires_in"])
            
            response_data = {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": data["expires_in"]
            }
            
            logger.info(f"JWT token generated for user {user.username}")
            return self.response(200, **response_data)
            
        except ValidationError as e:
            return self.response_400(message=str(e.messages))
        except Exception as e:
            logger.error(f"Error in JWT login: {e}")
            return self.response_500(message="Internal server error")

    @expose("/validate_token", methods=("POST",))
    @event_logger.log_this
    @protect()
    @safe
    @statsd_metrics
    @permission_name("read")
    def validate_token(self) -> Response:
        """
        Validate the current JWT token.
        ---
        post:
          summary: Validate JWT token
          description: >-
            Validate the current JWT token and return user information.
          security:
            - jwt: []
          responses:
            200:
              description: Token is valid
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      valid:
                        type: boolean
                      user:
                        type: object
                        properties:
                          id:
                            type: integer
                          username:
                            type: string
                          first_name:
                            type: string
                          last_name:
                            type: string
            401:
              $ref: '#/components/responses/401'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            from flask import g
            
            user = g.user
            if not user:
                return self.response_401()
            
            user_data = {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            
            return self.response(200, valid=True, user=user_data)
            
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return self.response_500(message="Internal server error")


# Schema definitions for OpenAPI
jwt_login_schema = JwtLoginSchema()
jwt_token_response_schema = JwtTokenResponseSchema() 