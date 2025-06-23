#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Superset Apex JWT 认证功能演示脚本

此脚本演示了如何使用Apex模块为Superset添加JWT header认证功能。
"""

import json
import time
import requests
from typing import Dict, Any

class SupersetApexDemo:
    """Superset Apex JWT认证演示类"""
    
    def __init__(self, base_url: str):
        """
        初始化演示客户端
        
        Args:
            base_url: Superset服务器URL
        """
        self.base_url = base_url.rstrip('/')
        self.token = None
        
    def login_and_get_jwt_token(self, username: str, password: str) -> Dict[str, Any]:
        """
        使用用户名密码登录并获取JWT token
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            包含access_token的响应数据
        """
        login_url = f"{self.base_url}/api/v1/apex/jwt_login"
        
        login_data = {
            "username": username,
            "password": password,
            "provider": "db",
            "expires_in": 3600  # 1小时
        }
        
        print(f"🔐 正在登录到 {login_url}")
        print(f"📤 发送数据: {json.dumps(login_data, indent=2)}")
        
        response = requests.post(
            login_url,
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            print(f"✅ 登录成功!")
            print(f"🎫 JWT Token: {self.token[:50]}...")
            print(f"⏰ 过期时间: {data['expires_in']} 秒")
            return data
        else:
            print(f"❌ 登录失败: {response.text}")
            response.raise_for_status()
    
    def validate_token(self) -> Dict[str, Any]:
        """
        验证当前JWT token
        
        Returns:
            验证结果数据
        """
        if not self.token:
            raise ValueError("请先登录获取token")
        
        validate_url = f"{self.base_url}/api/v1/apex/validate_token"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print(f"🔍 正在验证token: {validate_url}")
        
        response = requests.post(validate_url, headers=headers)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token验证成功!")
            print(f"👤 用户信息: {json.dumps(data['user'], indent=2)}")
            return data
        else:
            print(f"❌ Token验证失败: {response.text}")
            response.raise_for_status()
    
    def call_existing_api(self, endpoint: str) -> Dict[str, Any]:
        """
        使用JWT token调用现有的Superset API
        
        Args:
            endpoint: API端点路径
            
        Returns:
            API响应数据
        """
        if not self.token:
            raise ValueError("请先登录获取token")
        
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print(f"🌐 正在调用API: {url}")
        
        response = requests.get(url, headers=headers)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API调用成功!")
            return data
        else:
            print(f"❌ API调用失败: {response.text}")
            response.raise_for_status()
    
    def test_swagger_ui_access(self) -> None:
        """
        测试Swagger UI的匿名访问
        """
        swagger_urls = [
            f"{self.base_url}/api/v1/_openapi",
            f"{self.base_url}/api/v1/_openapi.json"
        ]
        
        for url in swagger_urls:
            print(f"🌐 测试Swagger UI访问: {url}")
            
            try:
                response = requests.get(url)
                print(f"📥 响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ Swagger UI可以匿名访问!")
                elif response.status_code == 404:
                    print(f"⚠️ 端点不存在 (可能Swagger UI未启用)")
                else:
                    print(f"❌ 访问失败: {response.text}")
                    
            except Exception as e:
                print(f"❌ 请求异常: {e}")


def demo_basic_usage():
    """演示基本使用流程"""
    print("=" * 60)
    print("🚀 Superset Apex JWT认证功能演示")
    print("=" * 60)
    
    # 配置 - 请根据实际情况修改
    SUPERSET_URL = "http://localhost:8088"  # 请修改为你的Superset URL
    USERNAME = "admin"  # 请修改为你的用户名
    PASSWORD = "admin"  # 请修改为你的密码
    
    try:
        # 创建演示客户端
        demo = SupersetApexDemo(SUPERSET_URL)
        
        print("\n📋 第一步: 使用用户名密码获取JWT token")
        print("-" * 40)
        token_data = demo.login_and_get_jwt_token(USERNAME, PASSWORD)
        
        print("\n📋 第二步: 验证JWT token")
        print("-" * 40)
        validation_data = demo.validate_token()
        
        print("\n📋 第三步: 使用JWT token调用现有API")
        print("-" * 40)
        try:
            csrf_data = demo.call_existing_api("/api/v1/security/csrf_token/")
            print(f"🔐 CSRF Token: {csrf_data.get('result', 'N/A')}")
        except Exception as e:
            print(f"⚠️ 调用CSRF API失败: {e}")
        
        print("\n📋 第四步: 测试Swagger UI匿名访问")
        print("-" * 40)
        demo.test_swagger_ui_access()
        
        print("\n🎉 演示完成!")
        print("💡 你现在可以使用以下方式进行API调用:")
        print(f"   Authorization: Bearer {demo.token[:50]}...")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到Superset服务器: {SUPERSET_URL}")
        print("💡 请确保:")
        print("   1. Superset服务器正在运行")
        print("   2. URL地址正确")
        print("   3. Apex模块已正确集成")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        print("💡 可能的原因:")
        print("   1. Apex模块未正确安装或配置")
        print("   2. 用户名密码错误")
        print("   3. Superset配置有误")


def demo_python_client():
    """演示Python客户端使用方式"""
    print("\n" + "=" * 60)
    print("🐍 Python客户端使用示例")
    print("=" * 60)
    
    client_code = '''
import requests
import json

class SupersetClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.token = self._get_token(username, password)
    
    def _get_token(self, username, password):
        """获取JWT token"""
        url = f"{self.base_url}/api/v1/apex/jwt_login"
        data = {"username": username, "password": password, "provider": "db"}
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()["access_token"]
    
    def get_headers(self):
        """获取包含认证信息的请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def api_call(self, endpoint, method="GET", **kwargs):
        """通用API调用方法"""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.get_headers(), **kwargs)
        response.raise_for_status()
        return response.json()
    
    def get_charts(self):
        """获取图表列表"""
        return self.api_call("/api/v1/chart/")
    
    def get_dashboards(self):
        """获取仪表板列表"""
        return self.api_call("/api/v1/dashboard/")

# 使用示例
client = SupersetClient("http://localhost:8088", "admin", "admin")
charts = client.get_charts()
dashboards = client.get_dashboards()
'''
    
    print("以下是Python客户端的完整示例代码:")
    print("-" * 40)
    print(client_code)


def demo_curl_commands():
    """演示cURL命令使用方式"""
    print("\n" + "=" * 60)
    print("🌐 cURL命令使用示例")
    print("=" * 60)
    
    curl_examples = '''
# 1. 获取JWT token
curl -X POST "http://localhost:8088/api/v1/apex/jwt_login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "admin",
    "password": "admin", 
    "provider": "db",
    "expires_in": 3600
  }'

# 2. 使用JWT token调用API (请替换<YOUR_JWT_TOKEN>)
curl -X GET "http://localhost:8088/api/v1/chart/" \\
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"

# 3. 验证token
curl -X POST "http://localhost:8088/api/v1/apex/validate_token" \\
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"

# 4. 匿名访问Swagger UI
curl -X GET "http://localhost:8088/api/v1/_openapi"
'''
    
    print("以下是cURL命令示例:")
    print("-" * 40)
    print(curl_examples)


if __name__ == "__main__":
    # 运行基本演示
    demo_basic_usage()
    
    # 显示客户端示例
    demo_python_client()
    
    # 显示cURL示例
    demo_curl_commands()
    
    print("\n" + "=" * 60)
    print("📚 更多信息请参考: superset/apex/README.md")
    print("🐛 如有问题, 请检查Superset日志和配置")
    print("=" * 60) 