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

"""
集成示例：如何在现有Superset应用中集成Apex功能

这个文件展示了如何在不修改Superset核心代码的情况下，
通过配置和初始化代码来启用Apex的JWT header认证功能。
"""

from flask import Flask
from typing import Optional

def integrate_apex_to_existing_superset(app: Flask) -> None:
    """
    将Apex功能集成到现有的Superset应用中。
    
    这个函数可以在Superset的应用工厂函数中调用，
    或者在应用初始化完成后调用。
    
    Args:
        app: Flask应用实例
    """
    try:
        # 导入Apex配置和初始化函数
        from superset.apex.config import init_apex
        
        # 初始化Apex功能
        init_apex(app)
        
        print("✓ Apex module integrated successfully")
        
    except ImportError as e:
        print(f"✗ Failed to import Apex module: {e}")
        print("  Make sure the apex module is in the correct location")
    except Exception as e:
        print(f"✗ Failed to integrate Apex module: {e}")


def configure_superset_for_apex(app: Flask) -> None:
    """
    为Superset配置Apex相关的设置。
    
    Args:
        app: Flask应用实例
    """
    # Apex基本配置
    app.config.setdefault("APEX_JWT_HEADER_AUTH_ENABLED", True)
    app.config.setdefault("APEX_SWAGGER_ANONYMOUS_ENABLED", True)
    app.config.setdefault("APEX_API_ENABLED", True)
    
    # JWT认证设置
    app.config.setdefault("APEX_JWT_DEFAULT_EXPIRES_IN", 86400)  # 24小时
    
    # Swagger匿名访问路径
    app.config.setdefault("APEX_SWAGGER_ANONYMOUS_PATHS", [
        "/swagger",
        "/api/v1/_openapi",
        "/api/v1/_openapi.json",
        "/swaggerui/",
    ])
    
    # 确保Swagger UI启用
    app.config["FAB_API_SWAGGER_UI"] = True
    
    print("✓ Superset configured for Apex functionality")


def patch_superset_security_manager(app: Flask) -> None:
    """
    在应用启动后增强安全管理器。
    
    这个函数应该在Superset的安全管理器创建之后调用。
    
    Args:
        app: Flask应用实例
    """
    def enhance_after_startup():
        try:
            from superset.apex.middleware import enhance_security_manager
            enhance_security_manager()
            print("✓ Security manager enhanced with JWT header authentication")
        except Exception as e:
            print(f"✗ Failed to enhance security manager: {e}")
    
    # 使用before_first_request确保在第一个请求前完成增强
    @app.before_first_request
    def setup_enhanced_security():
        enhance_after_startup()


def register_apex_apis(app: Flask) -> None:
    """
    注册Apex API端点。
    
    Args:
        app: Flask应用实例
    """
    def register_apis():
        try:
            from superset.apex.api import ApexApi
            
            # 获取AppBuilder实例
            appbuilder = app.extensions.get("appbuilder")
            if appbuilder:
                appbuilder.add_api(ApexApi)
                print("✓ Apex APIs registered successfully")
            else:
                print("✗ AppBuilder not found, cannot register Apex APIs")
                
        except Exception as e:
            print(f"✗ Failed to register Apex APIs: {e}")
    
    # 使用before_first_request确保AppBuilder已经初始化
    @app.before_first_request
    def setup_apis():
        register_apis()


def example_superset_app_factory_integration():
    """
    示例：在Superset应用工厂函数中集成Apex。
    
    这个函数展示了如何在create_app函数中集成Apex功能。
    """
    
    def create_app(config_module: Optional[str] = None) -> Flask:
        """
        修改后的Superset应用工厂函数示例。
        """
        # 创建Flask应用
        app = Flask(__name__)
        
        # 加载配置
        if config_module:
            app.config.from_object(config_module)
        
        # === 这里是原有的Superset初始化代码 ===
        # from superset.initialization import SupersetAppInitializer
        # app_initializer = SupersetAppInitializer(app)
        # app_initializer.init_app()
        
        # === Apex集成点 ===
        # 1. 配置Superset以支持Apex
        configure_superset_for_apex(app)
        
        # 2. 集成Apex功能
        integrate_apex_to_existing_superset(app)
        
        # 3. 增强安全管理器（在安全管理器创建后）
        patch_superset_security_manager(app)
        
        # 4. 注册Apex API（在AppBuilder创建后）
        register_apex_apis(app)
        
        return app
    
    return create_app


def example_post_initialization_integration(app: Flask) -> None:
    """
    示例：在Superset初始化完成后集成Apex。
    
    如果你不能修改应用工厂函数，可以在应用初始化完成后调用这个函数。
    
    Args:
        app: 已初始化的Superset Flask应用
    """
    print("Integrating Apex module into existing Superset application...")
    
    # 1. 配置
    configure_superset_for_apex(app)
    
    # 2. 集成核心功能
    integrate_apex_to_existing_superset(app)
    
    # 3. 增强安全管理器
    patch_superset_security_manager(app)
    
    # 4. 注册API
    register_apex_apis(app)
    
    print("Apex integration completed!")


def example_superset_config_py():
    """
    示例：superset_config.py 文件中的配置。
    
    将以下内容添加到你的 superset_config.py 文件中：
    """
    config_content = '''
# =============================================================================
# Apex模块配置 - JWT Header认证和Swagger UI增强
# =============================================================================

# 启用Apex功能
APEX_JWT_HEADER_AUTH_ENABLED = True
APEX_SWAGGER_ANONYMOUS_ENABLED = True  
APEX_API_ENABLED = True

# JWT认证设置
APEX_JWT_DEFAULT_EXPIRES_IN = 86400  # 24小时

# Swagger UI匿名访问路径
APEX_SWAGGER_ANONYMOUS_PATHS = [
    "/swagger",
    "/api/v1/_openapi",
    "/api/v1/_openapi.json", 
    "/swaggerui/",
]

# 启用Swagger UI
FAB_API_SWAGGER_UI = True

# 应用启动后集成Apex（如果不能修改应用工厂）
def FLASK_APP_MUTATOR(app):
    """
    Flask应用变更器 - 在应用初始化完成后调用
    """
    try:
        from superset.apex.integration_example import example_post_initialization_integration
        example_post_initialization_integration(app)
    except ImportError:
        print("Apex module not found, skipping integration")
    except Exception as e:
        print(f"Failed to integrate Apex: {e}")
'''
    
    print("Add the following configuration to your superset_config.py:")
    print("=" * 80)
    print(config_content)
    print("=" * 80)


def test_integration():
    """
    测试集成是否成功。
    """
    print("Testing Apex integration...")
    
    try:
        # 测试导入
        from superset.apex import ApexApi, create_jwt_token, jwt_authenticator
        print("✓ Apex modules can be imported")
        
        # 测试基本功能
        from superset.apex.jwt_auth import JwtHeaderAuthenticator
        authenticator = JwtHeaderAuthenticator()
        print("✓ JWT authenticator can be instantiated")
        
        print("✓ All tests passed - Apex integration looks good!")
        
    except ImportError as e:
        print(f"✗ Import test failed: {e}")
    except Exception as e:
        print(f"✗ Test failed: {e}")


if __name__ == "__main__":
    print("Superset Apex Integration Guide")
    print("=" * 50)
    
    print("\n1. Configuration example:")
    example_superset_config_py()
    
    print("\n2. Testing integration:")
    test_integration()
    
    print("\n3. Integration complete!")
    print("   You can now use JWT header authentication with Superset APIs.")
    print("   Swagger UI should be accessible without login.")
    print("   Use /api/v1/apex/jwt_login to get JWT tokens.") 