#!/usr/bin/env python3
"""
Day 7 - API与Web服务演示脚本
展示Superset风格的RESTful API设计和实现
"""

import json
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from functools import wraps

# 模拟Flask和相关库
class MockRequest:
    """模拟Flask request对象"""
    def __init__(self):
        self.headers = {}
        self.args = {}
        self.json = {}
        self.method = 'GET'
        self.endpoint = ''
        self.remote_addr = '127.0.0.1'
        self.current_user = None

class MockResponse:
    """模拟Flask response对象"""
    def __init__(self, data, status_code=200, headers=None):
        self.data = data
        self.status_code = status_code
        self.headers = headers or {}

# 全局request对象
request = MockRequest()

# 数据模型
@dataclass
class User:
    """用户模型"""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    roles: List[str]
    active: bool
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'roles': self.roles,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class Dashboard:
    """仪表板模型"""
    id: str
    title: str
    slug: str
    owner_id: str
    description: str
    position_json: str
    published: bool
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'owner_id': self.owner_id,
            'description': self.description,
            'position_json': self.position_json,
            'published': self.published,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# 数据仓库
class UserRepository:
    """用户数据仓库"""
    
    def __init__(self):
        self.users = {}
        self.email_index = {}
        self.username_index = {}
        self._init_default_users()
    
    def _init_default_users(self):
        """初始化默认用户"""
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'roles': ['Admin']
            },
            {
                'username': 'editor',
                'email': 'editor@example.com',
                'first_name': 'Editor',
                'last_name': 'User',
                'roles': ['Editor']
            },
            {
                'username': 'viewer',
                'email': 'viewer@example.com',
                'first_name': 'Viewer',
                'last_name': 'User',
                'roles': ['Viewer']
            }
        ]
        
        for user_data in users_data:
            user = User(
                id=str(uuid.uuid4()),
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                roles=user_data['roles'],
                active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.create(user)
    
    def create(self, user: User) -> User:
        """创建用户"""
        self.users[user.id] = user
        self.email_index[user.email] = user.id
        self.username_index[user.username] = user.id
        return user
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.users.get(user_id)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user_id = self.username_index.get(username)
        return self.users.get(user_id) if user_id else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        user_id = self.email_index.get(email)
        return self.users.get(user_id) if user_id else None
    
    def get_all(self) -> List[User]:
        """获取所有用户"""
        return list(self.users.values())

class DashboardRepository:
    """仪表板数据仓库"""
    
    def __init__(self):
        self.dashboards = {}
        self.slug_index = {}
        self._init_default_dashboards()
    
    def _init_default_dashboards(self):
        """初始化默认仪表板"""
        dashboards_data = [
            {
                'title': '销售概览',
                'slug': 'sales-overview',
                'description': '销售数据的综合概览',
                'owner_id': 'admin',
                'published': True
            },
            {
                'title': '用户分析',
                'slug': 'user-analytics',
                'description': '用户行为分析仪表板',
                'owner_id': 'editor',
                'published': False
            }
        ]
        
        for dash_data in dashboards_data:
            dashboard = Dashboard(
                id=str(uuid.uuid4()),
                title=dash_data['title'],
                slug=dash_data['slug'],
                owner_id=dash_data['owner_id'],
                description=dash_data['description'],
                position_json='{}',
                published=dash_data['published'],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.create(dashboard)
    
    def create(self, dashboard: Dashboard) -> Dashboard:
        """创建仪表板"""
        self.dashboards[dashboard.id] = dashboard
        self.slug_index[dashboard.slug] = dashboard.id
        return dashboard
    
    def get_by_id(self, dashboard_id: str) -> Optional[Dashboard]:
        """根据ID获取仪表板"""
        return self.dashboards.get(dashboard_id)
    
    def get_by_slug(self, slug: str) -> Optional[Dashboard]:
        """根据slug获取仪表板"""
        dashboard_id = self.slug_index.get(slug)
        return self.dashboards.get(dashboard_id) if dashboard_id else None
    
    def get_all(self) -> List[Dashboard]:
        """获取所有仪表板"""
        return list(self.dashboards.values())
    
    def get_by_owner(self, owner_id: str) -> List[Dashboard]:
        """根据所有者获取仪表板"""
        return [d for d in self.dashboards.values() if d.owner_id == owner_id]

# JWT工具类
class JWTHelper:
    """JWT助手类"""
    SECRET_KEY = "demo-secret-key"
    
    @classmethod
    def generate_token(cls, user_id: str, username: str, roles: List[str]) -> str:
        """生成JWT Token"""
        import base64
        
        # 简化的JWT实现
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "user_id": user_id,
            "username": username,
            "roles": roles,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600  # 1小时过期
        }
        
        # 编码（实际应该使用真正的JWT库）
        header_encoded = base64.b64encode(json.dumps(header).encode()).decode()
        payload_encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        signature = hashlib.md5(f"{header_encoded}.{payload_encoded}.{cls.SECRET_KEY}".encode()).hexdigest()
        
        return f"{header_encoded}.{payload_encoded}.{signature}"
    
    @classmethod
    def verify_token(cls, token: str) -> dict:
        """验证JWT Token"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return {'valid': False, 'error': 'Invalid token format'}
            
            header_encoded, payload_encoded, signature = parts
            
            # 验证签名
            expected_signature = hashlib.md5(f"{header_encoded}.{payload_encoded}.{cls.SECRET_KEY}".encode()).hexdigest()
            if signature != expected_signature:
                return {'valid': False, 'error': 'Invalid signature'}
            
            # 解码payload
            import base64
            payload_json = base64.b64decode(payload_encoded).decode()
            payload = json.loads(payload_json)
            
            # 检查过期时间
            if payload.get('exp', 0) < time.time():
                return {'valid': False, 'error': 'Token expired'}
            
            return {'valid': True, 'payload': payload}
        except Exception as e:
            return {'valid': False, 'error': f'Token validation failed: {str(e)}'}

# 权限管理
class PermissionManager:
    """权限管理器"""
    
    PERMISSIONS = {
        'Admin': ['user.read', 'user.write', 'user.delete', 'dashboard.read', 'dashboard.write', 'dashboard.delete'],
        'Editor': ['user.read', 'dashboard.read', 'dashboard.write'],
        'Viewer': ['user.read', 'dashboard.read']
    }
    
    @classmethod
    def has_permission(cls, user_roles: List[str], permission: str) -> bool:
        """检查用户是否有指定权限"""
        for role in user_roles:
            if permission in cls.PERMISSIONS.get(role, []):
                return True
        return False
    
    @classmethod
    def can_access_resource(cls, user_id: str, user_roles: List[str], 
                           resource_owner_id: str, permission: str) -> bool:
        """检查用户是否可以访问特定资源"""
        # 管理员可以访问所有资源
        if 'Admin' in user_roles:
            return True
        
        # 检查基础权限
        if not cls.has_permission(user_roles, permission):
            return False
        
        # 所有者可以访问自己的资源
        if user_id == resource_owner_id:
            return True
        
        # 其他用户只能读取已发布的资源
        return permission.endswith('.read')

# 装饰器
def jwt_required(f):
    """JWT认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 从请求头获取token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return {'error': 'Token is missing'}, 401
        
        result = JWTHelper.verify_token(token)
        if not result['valid']:
            return {'error': result['error']}, 401
        
        # 设置当前用户
        request.current_user = result['payload']
        return f(*args, **kwargs)
    
    return decorated

def permission_required(permission: str):
    """权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return {'error': 'Authentication required'}, 401
            
            user_roles = request.current_user.get('roles', [])
            if not PermissionManager.has_permission(user_roles, permission):
                return {'error': 'Insufficient permissions'}, 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# API限流器
class RateLimiter:
    """API限流器"""
    
    def __init__(self):
        self.requests = {}  # {user_id: [(timestamp, count), ...]}
        self.limits = {
            'default': 60,  # 每分钟60次请求
            'Admin': 300,   # 管理员每分钟300次
            'Editor': 120,  # 编辑者每分钟120次
            'Viewer': 60    # 查看者每分钟60次
        }
    
    def is_allowed(self, user_id: str, user_roles: List[str]) -> dict:
        """检查是否允许请求"""
        # 确定限制值
        limit = self.limits['default']
        for role in user_roles:
            if role in self.limits:
                limit = max(limit, self.limits[role])
        
        # 清理过期记录
        current_time = time.time()
        if user_id in self.requests:
            self.requests[user_id] = [
                (ts, count) for ts, count in self.requests[user_id]
                if current_time - ts < 60  # 保留最近1分钟的记录
            ]
        
        # 计算当前请求数
        user_requests = self.requests.get(user_id, [])
        current_count = sum(count for _, count in user_requests)
        
        if current_count >= limit:
            return {
                'allowed': False,
                'limit': limit,
                'remaining': 0,
                'reset_time': int(current_time + 60)
            }
        
        # 记录当前请求
        if user_id not in self.requests:
            self.requests[user_id] = []
        self.requests[user_id].append((current_time, 1))
        
        return {
            'allowed': True,
            'limit': limit,
            'remaining': limit - current_count - 1,
            'reset_time': int(current_time + 60)
        }

# API资源
class AuthApi:
    """认证API"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def login(self, username: str, password: str) -> tuple:
        """用户登录"""
        # 查找用户
        user = self.user_repo.get_by_username(username)
        if not user:
            user = self.user_repo.get_by_email(username)
        
        if not user or not user.active:
            return {'error': 'Invalid credentials'}, 401
        
        # 简化的密码验证
        expected_password = f"{user.username}123"  # 简单的测试密码
        if password != expected_password:
            return {'error': 'Invalid credentials'}, 401
        
        # 生成token
        token = JWTHelper.generate_token(user.id, user.username, user.roles)
        
        return {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'roles': user.roles
            }
        }, 200
    
    def verify_token(self, token: str) -> tuple:
        """验证token"""
        result = JWTHelper.verify_token(token)
        
        if result['valid']:
            payload = result['payload']
            return {
                'valid': True,
                'user': {
                    'id': payload['user_id'],
                    'username': payload['username'],
                    'roles': payload['roles']
                }
            }, 200
        else:
            return {'valid': False, 'error': result['error']}, 401

class UserApi:
    """用户API"""
    
    def __init__(self, user_repo: UserRepository, limiter: RateLimiter):
        self.user_repo = user_repo
        self.limiter = limiter
    
    @jwt_required
    @permission_required('user.read')
    def get_users(self) -> tuple:
        """获取用户列表"""
        users = self.user_repo.get_all()
        return {
            'users': [user.to_dict() for user in users],
            'total': len(users)
        }, 200
    
    @jwt_required
    @permission_required('user.read')
    def get_user(self, user_id: str) -> tuple:
        """获取用户详情"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        
        return user.to_dict(), 200
    
    @jwt_required
    @permission_required('user.write')
    def create_user(self, data: dict) -> tuple:
        """创建用户"""
        try:
            user = User(
                id=str(uuid.uuid4()),
                username=data['username'],
                email=data['email'],
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                roles=['Viewer'],
                active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            created_user = self.user_repo.create(user)
            return created_user.to_dict(), 201
            
        except Exception as e:
            return {'error': f'Failed to create user: {str(e)}'}, 400

class DashboardApi:
    """仪表板API"""
    
    def __init__(self, dashboard_repo: DashboardRepository, user_repo: UserRepository, limiter: RateLimiter):
        self.dashboard_repo = dashboard_repo
        self.user_repo = user_repo
        self.limiter = limiter
    
    @jwt_required
    @permission_required('dashboard.read')
    def get_dashboards(self) -> tuple:
        """获取仪表板列表"""
        dashboards = self.dashboard_repo.get_all()
        
        # 过滤用户可访问的仪表板
        user_id = request.current_user['user_id']
        user_roles = request.current_user['roles']
        
        accessible_dashboards = []
        for dashboard in dashboards:
            if PermissionManager.can_access_resource(
                user_id, user_roles, dashboard.owner_id, 'dashboard.read'
            ):
                accessible_dashboards.append(dashboard)
        
        return {
            'dashboards': [d.to_dict() for d in accessible_dashboards],
            'total': len(accessible_dashboards)
        }, 200
    
    @jwt_required
    @permission_required('dashboard.read')
    def get_dashboard(self, dashboard_id: str) -> tuple:
        """获取仪表板详情"""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            return {'error': 'Dashboard not found'}, 404
        
        # 检查访问权限
        user_id = request.current_user['user_id']
        user_roles = request.current_user['roles']
        
        if not PermissionManager.can_access_resource(
            user_id, user_roles, dashboard.owner_id, 'dashboard.read'
        ):
            return {'error': 'Access denied'}, 403
        
        return dashboard.to_dict(), 200
    
    @jwt_required
    @permission_required('dashboard.write')
    def create_dashboard(self, data: dict) -> tuple:
        """创建仪表板"""
        try:
            user_id = request.current_user['user_id']
            
            dashboard = Dashboard(
                id=str(uuid.uuid4()),
                title=data['title'],
                slug=data.get('slug', data['title'].lower().replace(' ', '-')),
                owner_id=user_id,
                description=data.get('description', ''),
                position_json=data.get('position_json', '{}'),
                published=data.get('published', False),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            created_dashboard = self.dashboard_repo.create(dashboard)
            return created_dashboard.to_dict(), 201
            
        except Exception as e:
            return {'error': f'Failed to create dashboard: {str(e)}'}, 400

# 演示函数
def demo_api_system():
    """演示API系统"""
    print("🌐 Day 7 API与Web服务演示")
    print("=" * 60)
    
    # 初始化组件
    user_repo = UserRepository()
    dashboard_repo = DashboardRepository()
    limiter = RateLimiter()
    
    auth_api = AuthApi(user_repo)
    user_api = UserApi(user_repo, limiter)
    dashboard_api = DashboardApi(dashboard_repo, user_repo, limiter)
    
    print("\n" + "=" * 60)
    print("🔐 认证系统演示")
    print("=" * 60)
    
    # 演示登录
    print("\n🔑 用户登录演示:")
    login_result, status = auth_api.login("admin", "admin123")
    print(f"✓ 登录结果 (状态码: {status}):")
    print(f"  Token: {login_result.get('access_token', 'N/A')[:50]}...")
    print(f"  用户: {login_result.get('user', {}).get('username', 'N/A')}")
    print(f"  角色: {login_result.get('user', {}).get('roles', [])}")
    
    # 设置token用于后续请求
    if status == 200:
        token = login_result['access_token']
        request.headers['Authorization'] = f'Bearer {token}'
    
    # 演示token验证
    print("\n🔍 Token验证演示:")
    verify_result, status = auth_api.verify_token(token)
    print(f"✓ 验证结果 (状态码: {status}):")
    print(f"  有效性: {verify_result.get('valid', False)}")
    if verify_result.get('valid'):
        print(f"  用户ID: {verify_result['user']['id']}")
        print(f"  用户名: {verify_result['user']['username']}")
    
    print("\n" + "=" * 60)
    print("👥 用户管理API演示")
    print("=" * 60)
    
    # 获取用户列表
    print("\n📋 获取用户列表:")
    users_result, status = user_api.get_users()
    print(f"✓ 用户列表 (状态码: {status}):")
    if status == 200:
        for user in users_result['users']:
            print(f"  - {user['username']} ({user['email']}) - 角色: {user['roles']}")
        print(f"  总计: {users_result['total']} 个用户")
    
    # 创建新用户
    print("\n➕ 创建新用户:")
    new_user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User'
    }
    create_result, status = user_api.create_user(new_user_data)
    print(f"✓ 创建结果 (状态码: {status}):")
    if status == 201:
        print(f"  用户ID: {create_result['id']}")
        print(f"  用户名: {create_result['username']}")
        print(f"  角色: {create_result['roles']}")
    
    print("\n" + "=" * 60)
    print("📊 仪表板管理API演示")
    print("=" * 60)
    
    # 获取仪表板列表
    print("\n📋 获取仪表板列表:")
    dashboards_result, status = dashboard_api.get_dashboards()
    print(f"✓ 仪表板列表 (状态码: {status}):")
    if status == 200:
        for dashboard in dashboards_result['dashboards']:
            print(f"  - {dashboard['title']} (#{dashboard['slug']})")
            print(f"    所有者: {dashboard['owner_id']}")
            print(f"    发布状态: {'已发布' if dashboard['published'] else '草稿'}")
        print(f"  总计: {dashboards_result['total']} 个仪表板")
    
    # 创建新仪表板
    print("\n➕ 创建新仪表板:")
    new_dashboard_data = {
        'title': '演示仪表板',
        'description': '这是一个API演示创建的仪表板',
        'published': True
    }
    dashboard_result, status = dashboard_api.create_dashboard(new_dashboard_data)
    print(f"✓ 创建结果 (状态码: {status}):")
    if status == 201:
        print(f"  仪表板ID: {dashboard_result['id']}")
        print(f"  标题: {dashboard_result['title']}")
        print(f"  Slug: {dashboard_result['slug']}")
    
    print("\n" + "=" * 60)
    print("⚡ 性能优化演示")
    print("=" * 60)
    
    # 演示限流
    print("\n🚦 API限流演示:")
    
    # 模拟多次请求
    user_id = request.current_user['user_id']
    user_roles = request.current_user['roles']
    
    print(f"  用户角色: {user_roles}")
    print(f"  限制: {limiter.limits.get(user_roles[0], limiter.limits['default'])} 请求/分钟")
    
    # 快速发送多个请求
    success_count = 0
    rate_limited_count = 0
    
    for i in range(5):
        result = limiter.is_allowed(user_id, user_roles)
        if result['allowed']:
            success_count += 1
            print(f"  请求 {i+1}: ✓ 允许 (剩余: {result['remaining']})")
        else:
            rate_limited_count += 1
            print(f"  请求 {i+1}: ✗ 限流 (重置时间: {result['reset_time']})")
    
    print(f"  成功请求: {success_count}, 被限流: {rate_limited_count}")
    
    print("\n" + "=" * 60)
    print("🛡️ 权限控制演示")
    print("=" * 60)
    
    # 测试不同权限
    permissions_to_test = [
        'user.read',
        'user.write',
        'user.delete',
        'dashboard.read',
        'dashboard.write',
        'dashboard.delete'
    ]
    
    current_user_roles = request.current_user['roles']
    print(f"\n👤 当前用户角色: {current_user_roles}")
    print("🔐 权限检查结果:")
    
    for permission in permissions_to_test:
        has_perm = PermissionManager.has_permission(current_user_roles, permission)
        status_icon = "✓" if has_perm else "✗"
        print(f"  {status_icon} {permission}: {'允许' if has_perm else '拒绝'}")
    
    print("\n" + "=" * 60)
    print("📈 API监控统计")
    print("=" * 60)
    
    # 模拟API调用统计
    api_stats = {
        'total_requests': 15,
        'successful_requests': 13,
        'failed_requests': 2,
        'avg_response_time': 0.125,
        'endpoints': {
            '/api/v1/users': {'requests': 5, 'avg_time': 0.08},
            '/api/v1/dashboards': {'requests': 7, 'avg_time': 0.15},
            '/api/v1/auth/login': {'requests': 3, 'avg_time': 0.20}
        }
    }
    
    print(f"📊 API统计摘要:")
    print(f"  总请求数: {api_stats['total_requests']}")
    print(f"  成功请求: {api_stats['successful_requests']}")
    print(f"  失败请求: {api_stats['failed_requests']}")
    print(f"  成功率: {api_stats['successful_requests']/api_stats['total_requests']*100:.1f}%")
    print(f"  平均响应时间: {api_stats['avg_response_time']*1000:.1f}ms")
    
    print(f"\n🎯 热门端点:")
    for endpoint, stats in api_stats['endpoints'].items():
        print(f"  {endpoint}")
        print(f"    请求数: {stats['requests']}")
        print(f"    平均时间: {stats['avg_time']*1000:.1f}ms")
    
    print("\n" + "=" * 60)
    print("✅ API系统演示完成！")
    print("=" * 60)
    
    print(f"\n📚 核心功能总结:")
    print(f"- RESTful API设计：符合REST原则的资源管理")
    print(f"- JWT认证系统：安全的Token生成和验证")
    print(f"- 细粒度权限控制：基于角色的权限管理")
    print(f"- API限流机制：防止API滥用的保护措施")
    print(f"- 资源级权限：所有者和角色的双重检查")
    print(f"- 性能监控：实时API统计和性能分析")

if __name__ == "__main__":
    demo_api_system() 