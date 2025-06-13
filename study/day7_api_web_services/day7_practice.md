# Day 7 实践指南 - API与Web服务开发

## 目录
1. [环境准备](#环境准备)
2. [基础API开发](#基础api开发)
3. [认证系统实现](#认证系统实现)
4. [权限控制实践](#权限控制实践)
5. [性能优化实践](#性能优化实践)
6. [API监控与调试](#api监控与调试)

## 环境准备

### 1. 安装依赖包

```bash
# API开发相关
pip install flask-restx marshmallow

# 认证相关
pip install PyJWT authlib

# 性能监控
pip install flask-limiter redis

# API文档
pip install flasgger
```

### 2. 项目结构设置

```
api_project/
├── app.py                  # 主应用文件
├── config.py              # 配置文件
├── models/                 # 数据模型
│   ├── __init__.py
│   ├── user.py
│   └── dashboard.py
├── api/                    # API资源
│   ├── __init__.py
│   ├── auth.py
│   ├── dashboard.py
│   └── user.py
├── schemas/                # 序列化Schema
│   ├── __init__.py
│   ├── user.py
│   └── dashboard.py
├── middleware/             # 中间件
│   ├── __init__.py
│   ├── auth.py
│   └── rate_limit.py
└── utils/                  # 工具函数
    ├── __init__.py
    ├── jwt_helper.py
    └── response.py
```

## 基础API开发

### 练习1：创建用户管理API

```python
# models/user.py
from dataclasses import dataclass
from typing import List, Optional
import uuid
from datetime import datetime

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
    
    def __init__(self, username: str, email: str, first_name: str = "", last_name: str = ""):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.roles = ["Viewer"]  # 默认角色
        self.active = True
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_role(self, role: str):
        """添加角色"""
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.now()
    
    def remove_role(self, role: str):
        """移除角色"""
        if role in self.roles:
            self.roles.remove(role)
            self.updated_at = datetime.now()
    
    def has_role(self, role: str) -> bool:
        """检查是否有指定角色"""
        return role in self.roles
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "roles": self.roles,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

# 模拟数据库
class UserRepository:
    """用户数据仓库"""
    
    def __init__(self):
        self.users = {}
        self.email_index = {}
        self.username_index = {}
        
        # 创建默认用户
        admin_user = User("admin", "admin@example.com", "Admin", "User")
        admin_user.add_role("Admin")
        self.create(admin_user)
    
    def create(self, user: User) -> User:
        """创建用户"""
        if user.email in self.email_index:
            raise ValueError("Email already exists")
        if user.username in self.username_index:
            raise ValueError("Username already exists")
        
        self.users[user.id] = user
        self.email_index[user.email] = user.id
        self.username_index[user.username] = user.id
        return user
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.users.get(user_id)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        user_id = self.email_index.get(email)
        return self.users.get(user_id) if user_id else None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user_id = self.username_index.get(username)
        return self.users.get(user_id) if user_id else None
    
    def get_all(self) -> List[User]:
        """获取所有用户"""
        return list(self.users.values())
    
    def update(self, user: User) -> User:
        """更新用户"""
        if user.id in self.users:
            self.users[user.id] = user
            user.updated_at = datetime.now()
            return user
        raise ValueError("User not found")
    
    def delete(self, user_id: str) -> bool:
        """删除用户"""
        if user_id in self.users:
            user = self.users[user_id]
            del self.users[user_id]
            del self.email_index[user.email]
            del self.username_index[user.username]
            return True
        return False

# 全局用户仓库实例
user_repository = UserRepository()
```

### 练习2：实现用户API端点

```python
# schemas/user.py
from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class UserSchema(Schema):
    """用户序列化Schema"""
    
    id = fields.String(dump_only=True)
    username = fields.String(
        required=True,
        validate=validate.Length(min=3, max=50),
        metadata={"description": "用户名，3-50字符"}
    )
    email = fields.Email(
        required=True,
        metadata={"description": "邮箱地址"}
    )
    first_name = fields.String(
        validate=validate.Length(max=50),
        metadata={"description": "名字"}
    )
    last_name = fields.String(
        validate=validate.Length(max=50),
        metadata={"description": "姓氏"}
    )
    roles = fields.List(
        fields.String(),
        dump_only=True,
        metadata={"description": "用户角色列表"}
    )
    active = fields.Boolean(
        dump_only=True,
        metadata={"description": "是否激活"}
    )
    created_at = fields.DateTime(
        dump_only=True,
        metadata={"description": "创建时间"}
    )
    updated_at = fields.DateTime(
        dump_only=True,
        metadata={"description": "更新时间"}
    )

class UserCreateSchema(Schema):
    """用户创建Schema"""
    
    username = fields.String(
        required=True,
        validate=validate.Length(min=3, max=50)
    )
    email = fields.Email(required=True)
    first_name = fields.String(validate=validate.Length(max=50))
    last_name = fields.String(validate=validate.Length(max=50))

class UserUpdateSchema(Schema):
    """用户更新Schema"""
    
    first_name = fields.String(validate=validate.Length(max=50))
    last_name = fields.String(validate=validate.Length(max=50))
    active = fields.Boolean()

# api/user.py
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError
from models.user import user_repository, User
from schemas.user import UserSchema, UserCreateSchema, UserUpdateSchema
from utils.response import ApiResponse

# 创建命名空间
user_ns = Namespace('users', description='用户管理API')

# 定义API模型
user_model = user_ns.model('User', {
    'id': fields.String(description='用户ID'),
    'username': fields.String(required=True, description='用户名'),
    'email': fields.String(required=True, description='邮箱'),
    'first_name': fields.String(description='名字'),
    'last_name': fields.String(description='姓氏'),
    'roles': fields.List(fields.String, description='角色列表'),
    'active': fields.Boolean(description='是否激活'),
    'created_at': fields.DateTime(description='创建时间'),
    'updated_at': fields.DateTime(description='更新时间')
})

user_create_model = user_ns.model('UserCreate', {
    'username': fields.String(required=True, description='用户名'),
    'email': fields.String(required=True, description='邮箱'),
    'first_name': fields.String(description='名字'),
    'last_name': fields.String(description='姓氏')
})

user_update_model = user_ns.model('UserUpdate', {
    'first_name': fields.String(description='名字'),
    'last_name': fields.String(description='姓氏'),
    'active': fields.Boolean(description='是否激活')
})

# Schema实例
user_schema = UserSchema()
user_list_schema = UserSchema(many=True)
user_create_schema = UserCreateSchema()
user_update_schema = UserUpdateSchema()

@user_ns.route('/')
class UserListApi(Resource):
    """用户列表API"""
    
    @user_ns.marshal_with(user_model, as_list=True)
    @user_ns.doc('list_users')
    def get(self):
        """获取用户列表"""
        try:
            users = user_repository.get_all()
            return [user.to_dict() for user in users]
        except Exception as e:
            user_ns.abort(500, f"Internal server error: {str(e)}")
    
    @user_ns.expect(user_create_model)
    @user_ns.marshal_with(user_model)
    @user_ns.doc('create_user')
    def post(self):
        """创建新用户"""
        try:
            # 验证请求数据
            json_data = user_ns.payload
            data = user_create_schema.load(json_data)
            
            # 创建用户
            user = User(**data)
            created_user = user_repository.create(user)
            
            return created_user.to_dict(), 201
            
        except ValidationError as e:
            user_ns.abort(400, f"Validation error: {e.messages}")
        except ValueError as e:
            user_ns.abort(409, f"Conflict: {str(e)}")
        except Exception as e:
            user_ns.abort(500, f"Internal server error: {str(e)}")

@user_ns.route('/<string:user_id>')
class UserApi(Resource):
    """单个用户API"""
    
    @user_ns.marshal_with(user_model)
    @user_ns.doc('get_user')
    def get(self, user_id):
        """获取用户详情"""
        user = user_repository.get_by_id(user_id)
        if not user:
            user_ns.abort(404, "User not found")
        return user.to_dict()
    
    @user_ns.expect(user_update_model)
    @user_ns.marshal_with(user_model)
    @user_ns.doc('update_user')
    def put(self, user_id):
        """更新用户"""
        try:
            user = user_repository.get_by_id(user_id)
            if not user:
                user_ns.abort(404, "User not found")
            
            # 验证请求数据
            json_data = user_ns.payload
            data = user_update_schema.load(json_data)
            
            # 更新用户
            for key, value in data.items():
                setattr(user, key, value)
            
            updated_user = user_repository.update(user)
            return updated_user.to_dict()
            
        except ValidationError as e:
            user_ns.abort(400, f"Validation error: {e.messages}")
        except Exception as e:
            user_ns.abort(500, f"Internal server error: {str(e)}")
    
    @user_ns.doc('delete_user')
    def delete(self, user_id):
        """删除用户"""
        if user_repository.delete(user_id):
            return '', 204
        else:
            user_ns.abort(404, "User not found")

@user_ns.route('/<string:user_id>/roles')
class UserRolesApi(Resource):
    """用户角色管理API"""
    
    @user_ns.doc('get_user_roles')
    def get(self, user_id):
        """获取用户角色"""
        user = user_repository.get_by_id(user_id)
        if not user:
            user_ns.abort(404, "User not found")
        return {'roles': user.roles}
    
    @user_ns.expect(user_ns.model('RoleUpdate', {
        'role': fields.String(required=True, description='角色名称'),
        'action': fields.String(required=True, enum=['add', 'remove'], description='操作类型')
    }))
    @user_ns.doc('update_user_roles')
    def post(self, user_id):
        """更新用户角色"""
        user = user_repository.get_by_id(user_id)
        if not user:
            user_ns.abort(404, "User not found")
        
        json_data = user_ns.payload
        role = json_data.get('role')
        action = json_data.get('action')
        
        if not role or not action:
            user_ns.abort(400, "Role and action are required")
        
        try:
            if action == 'add':
                user.add_role(role)
            elif action == 'remove':
                user.remove_role(role)
            else:
                user_ns.abort(400, "Invalid action")
            
            user_repository.update(user)
            return {'roles': user.roles}
            
        except Exception as e:
            user_ns.abort(500, f"Internal server error: {str(e)}")
```

## 认证系统实现

### 练习3：实现JWT认证

```python
# utils/jwt_helper.py
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, request, jsonify

class JWTHelper:
    """JWT工具类"""
    
    @staticmethod
    def generate_token(user_id: str, username: str, roles: list = None) -> str:
        """生成JWT Token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'roles': roles or [],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iss': 'superset-api',
            'aud': 'superset-client'
        }
        
        secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key')
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """验证JWT Token"""
        try:
            secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key')
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=['HS256'],
                audience='superset-client',
                issuer='superset-api'
            )
            return {'valid': True, 'payload': payload}
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token has expired'}
        except jwt.InvalidTokenError as e:
            return {'valid': False, 'error': f'Invalid token: {str(e)}'}
    
    @staticmethod
    def get_token_from_request() -> str:
        """从请求中获取Token"""
        token = None
        
        # 从Authorization header获取
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                pass
        
        # 从查询参数获取
        if not token:
            token = request.args.get('token')
        
        return token

def jwt_required(f):
    """JWT认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = JWTHelper.get_token_from_request()
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        result = JWTHelper.verify_token(token)
        if not result['valid']:
            return jsonify({'message': result['error']}), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = result['payload']
        return f(*args, **kwargs)
    
    return decorated

def role_required(required_roles):
    """角色验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'message': 'Authentication required'}), 401
            
            user_roles = request.current_user.get('roles', [])
            
            # 检查是否有所需角色
            if isinstance(required_roles, str):
                required_roles_list = [required_roles]
            else:
                required_roles_list = required_roles
            
            if not any(role in user_roles for role in required_roles_list):
                return jsonify({'message': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# api/auth.py
from flask_restx import Namespace, Resource, fields
from models.user import user_repository
from utils.jwt_helper import JWTHelper
import hashlib

auth_ns = Namespace('auth', description='认证API')

login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='用户名或邮箱'),
    'password': fields.String(required=True, description='密码')
})

token_model = auth_ns.model('Token', {
    'access_token': fields.String(description='访问令牌'),
    'token_type': fields.String(description='令牌类型'),
    'expires_in': fields.Integer(description='过期时间（秒）'),
    'user': fields.Nested(auth_ns.model('UserInfo', {
        'id': fields.String(description='用户ID'),
        'username': fields.String(description='用户名'),
        'email': fields.String(description='邮箱'),
        'roles': fields.List(fields.String, description='角色列表')
    }))
})

@auth_ns.route('/login')
class LoginApi(Resource):
    """登录API"""
    
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_model)
    @auth_ns.doc('login')
    def post(self):
        """用户登录"""
        json_data = auth_ns.payload
        username = json_data.get('username')
        password = json_data.get('password')
        
        if not username or not password:
            auth_ns.abort(400, "Username and password are required")
        
        # 查找用户（支持用户名或邮箱登录）
        user = user_repository.get_by_username(username)
        if not user:
            user = user_repository.get_by_email(username)
        
        if not user or not user.active:
            auth_ns.abort(401, "Invalid credentials")
        
        # 简化的密码验证（实际应用中应使用安全的密码哈希）
        expected_password = hashlib.md5(f"{user.username}password".encode()).hexdigest()
        provided_password = hashlib.md5(password.encode()).hexdigest()
        
        if expected_password != provided_password:
            auth_ns.abort(401, "Invalid credentials")
        
        # 生成JWT Token
        token = JWTHelper.generate_token(user.id, user.username, user.roles)
        
        return {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 86400,  # 24小时
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'roles': user.roles
            }
        }

@auth_ns.route('/verify')
class VerifyTokenApi(Resource):
    """Token验证API"""
    
    @auth_ns.doc('verify_token')
    def get(self):
        """验证Token有效性"""
        token = JWTHelper.get_token_from_request()
        
        if not token:
            return {'valid': False, 'message': 'Token is missing'}, 401
        
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
            }
        else:
            return {'valid': False, 'message': result['error']}, 401

@auth_ns.route('/refresh')
class RefreshTokenApi(Resource):
    """Token刷新API"""
    
    @auth_ns.marshal_with(token_model)
    @auth_ns.doc('refresh_token')
    def post(self):
        """刷新Token"""
        token = JWTHelper.get_token_from_request()
        
        if not token:
            auth_ns.abort(401, "Token is missing")
        
        result = JWTHelper.verify_token(token)
        if not result['valid']:
            auth_ns.abort(401, result['error'])
        
        payload = result['payload']
        
        # 生成新Token
        new_token = JWTHelper.generate_token(
            payload['user_id'],
            payload['username'],
            payload['roles']
        )
        
        # 获取用户信息
        user = user_repository.get_by_id(payload['user_id'])
        if not user:
            auth_ns.abort(404, "User not found")
        
        return {
            'access_token': new_token,
            'token_type': 'Bearer',
            'expires_in': 86400,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'roles': user.roles
            }
        }
```

## 权限控制实践

### 练习4：实现细粒度权限控制

```python
# utils/permission.py
from functools import wraps
from flask import request, jsonify
from typing import List, Callable

class Permission:
    """权限类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

class Role:
    """角色类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.permissions: List[Permission] = []
    
    def add_permission(self, permission: Permission):
        """添加权限"""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def has_permission(self, permission_name: str) -> bool:
        """检查是否有指定权限"""
        return any(p.name == permission_name for p in self.permissions)

class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.permissions = {}
        self.roles = {}
        self.resource_checkers = {}
        self._init_default_permissions()
    
    def _init_default_permissions(self):
        """初始化默认权限"""
        # 定义权限
        permissions = [
            Permission('user.read', '读取用户信息'),
            Permission('user.write', '修改用户信息'),
            Permission('user.delete', '删除用户'),
            Permission('dashboard.read', '读取仪表板'),
            Permission('dashboard.write', '修改仪表板'),
            Permission('dashboard.delete', '删除仪表板'),
            Permission('admin.all', '管理员权限'),
        ]
        
        for perm in permissions:
            self.permissions[perm.name] = perm
        
        # 定义角色
        admin_role = Role('Admin', '管理员')
        admin_role.add_permission(self.permissions['admin.all'])
        
        editor_role = Role('Editor', '编辑者')
        editor_role.add_permission(self.permissions['user.read'])
        editor_role.add_permission(self.permissions['user.write'])
        editor_role.add_permission(self.permissions['dashboard.read'])
        editor_role.add_permission(self.permissions['dashboard.write'])
        
        viewer_role = Role('Viewer', '查看者')
        viewer_role.add_permission(self.permissions['user.read'])
        viewer_role.add_permission(self.permissions['dashboard.read'])
        
        self.roles['Admin'] = admin_role
        self.roles['Editor'] = editor_role
        self.roles['Viewer'] = viewer_role
    
    def register_resource_checker(self, resource_type: str, checker: Callable):
        """注册资源检查器"""
        self.resource_checkers[resource_type] = checker
    
    def check_permission(self, user_roles: List[str], permission: str, resource_id: str = None) -> bool:
        """检查权限"""
        # 管理员拥有所有权限
        if 'Admin' in user_roles:
            return True
        
        # 检查角色权限
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and (role.has_permission(permission) or role.has_permission('admin.all')):
                # 如果有资源ID，还需要检查资源级权限
                if resource_id:
                    resource_type = permission.split('.')[0]
                    if resource_type in self.resource_checkers:
                        return self.resource_checkers[resource_type](user_roles, resource_id)
                return True
        
        return False

# 全局权限管理器
permission_manager = PermissionManager()

def permission_required(permission: str, resource_id_param: str = None):
    """权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 检查认证
            if not hasattr(request, 'current_user'):
                return jsonify({'message': 'Authentication required'}), 401
            
            user_roles = request.current_user.get('roles', [])
            
            # 获取资源ID
            resource_id = None
            if resource_id_param:
                resource_id = kwargs.get(resource_id_param)
            
            # 检查权限
            if not permission_manager.check_permission(user_roles, permission, resource_id):
                return jsonify({'message': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def ownership_required(resource_getter: Callable):
    """所有权验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'message': 'Authentication required'}), 401
            
            user_id = request.current_user.get('user_id')
            user_roles = request.current_user.get('roles', [])
            
            # 管理员跳过所有权检查
            if 'Admin' in user_roles:
                return f(*args, **kwargs)
            
            # 获取资源并检查所有权
            resource = resource_getter(*args, **kwargs)
            if not resource:
                return jsonify({'message': 'Resource not found'}), 404
            
            if hasattr(resource, 'owner_id') and resource.owner_id != user_id:
                return jsonify({'message': 'Access denied'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# 资源级权限检查器示例
def check_user_resource_permission(user_roles: List[str], user_id: str) -> bool:
    """检查用户资源权限"""
    # 用户只能访问自己的资源，除非是管理员
    current_user_id = request.current_user.get('user_id')
    return current_user_id == user_id or 'Admin' in user_roles

# 注册资源检查器
permission_manager.register_resource_checker('user', check_user_resource_permission)
```

## 性能优化实践

### 练习5：实现API缓存和限流

```python
# middleware/rate_limit.py
import redis
import time
from functools import wraps
from flask import request, jsonify, current_app

class RateLimiter:
    """API限流器"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
    
    def is_allowed(self, key: str, limit: int, window: int) -> dict:
        """检查是否允许请求"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            result = pipe.execute()
            
            current_count = result[0]
            
            return {
                'allowed': current_count <= limit,
                'count': current_count,
                'limit': limit,
                'remaining': max(0, limit - current_count),
                'reset_time': int(time.time()) + window
            }
        except redis.RedisError:
            # Redis连接失败时允许请求
            return {
                'allowed': True,
                'count': 0,
                'limit': limit,
                'remaining': limit,
                'reset_time': int(time.time()) + window
            }
    
    def get_key(self, identifier: str, endpoint: str) -> str:
        """生成限流键"""
        return f"rate_limit:{identifier}:{endpoint}"

# 全局限流器
rate_limiter = RateLimiter()

def rate_limit(requests_per_minute: int = 60, per_user: bool = True):
    """限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 确定限流标识符
            if per_user and hasattr(request, 'current_user'):
                identifier = request.current_user.get('user_id', 'anonymous')
            else:
                identifier = request.remote_addr
            
            # 生成限流键
            endpoint = request.endpoint or f.__name__
            key = rate_limiter.get_key(identifier, endpoint)
            
            # 检查限流
            result = rate_limiter.is_allowed(key, requests_per_minute, 60)
            
            if not result['allowed']:
                response = jsonify({
                    'message': 'Rate limit exceeded',
                    'limit': result['limit'],
                    'remaining': result['remaining'],
                    'reset_time': result['reset_time']
                })
                response.headers['X-RateLimit-Limit'] = str(result['limit'])
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                response.headers['X-RateLimit-Reset'] = str(result['reset_time'])
                return response, 429
            
            # 在响应中添加限流头
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(result['limit'])
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                response.headers['X-RateLimit-Reset'] = str(result['reset_time'])
            
            return response
        return decorated
    return decorator

# middleware/cache.py
import json
import hashlib
from functools import wraps
from flask import request, current_app

class ApiCache:
    """API缓存"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(
            host='localhost',
            port=6379,
            db=1,
            decode_responses=True
        )
    
    def get_cache_key(self, endpoint: str, args: tuple, kwargs: dict, user_id: str = None) -> str:
        """生成缓存键"""
        # 创建唯一标识符
        key_data = {
            'endpoint': endpoint,
            'args': args,
            'kwargs': kwargs,
            'user_id': user_id,
            'query_params': dict(request.args)
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"api_cache:{endpoint}:{key_hash}"
    
    def get(self, key: str):
        """获取缓存"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except (redis.RedisError, json.JSONDecodeError):
            pass
        return None
    
    def set(self, key: str, data, ttl: int = 300):
        """设置缓存"""
        try:
            self.redis_client.setex(key, ttl, json.dumps(data, default=str))
        except redis.RedisError:
            pass
    
    def delete(self, pattern: str):
        """删除缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except redis.RedisError:
            pass

# 全局缓存实例
api_cache = ApiCache()

def cache_response(ttl: int = 300, user_specific: bool = True):
    """响应缓存装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 只缓存GET请求
            if request.method != 'GET':
                return f(*args, **kwargs)
            
            # 生成缓存键
            user_id = None
            if user_specific and hasattr(request, 'current_user'):
                user_id = request.current_user.get('user_id')
            
            cache_key = api_cache.get_cache_key(
                request.endpoint, args, kwargs, user_id
            )
            
            # 尝试从缓存获取
            cached_response = api_cache.get(cache_key)
            if cached_response:
                return cached_response, 200, {'X-Cache': 'HIT'}
            
            # 执行函数并缓存结果
            response = f(*args, **kwargs)
            
            # 只缓存成功响应
            if isinstance(response, tuple):
                data, status_code = response[0], response[1]
                if status_code == 200:
                    api_cache.set(cache_key, data, ttl)
                    return data, status_code, {'X-Cache': 'MISS'}
            elif hasattr(response, 'status_code') and response.status_code == 200:
                api_cache.set(cache_key, response.get_json(), ttl)
                response.headers['X-Cache'] = 'MISS'
            
            return response
        return decorated
    return decorator

def invalidate_cache(pattern: str):
    """缓存失效装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            result = f(*args, **kwargs)
            
            # 成功操作后清除相关缓存
            if (isinstance(result, tuple) and result[1] in [200, 201, 204]) or \
               (hasattr(result, 'status_code') and result.status_code in [200, 201, 204]):
                api_cache.delete(pattern)
            
            return result
        return decorated
    return decorator
```

## API监控与调试

### 练习6：实现API监控和日志

```python
# utils/monitoring.py
import time
import logging
from functools import wraps
from flask import request, g
from datetime import datetime
import json

class ApiMonitor:
    """API监控器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.metrics = {
            'requests': 0,
            'errors': 0,
            'response_times': []
        }
    
    def _setup_logger(self):
        """设置日志器"""
        logger = logging.getLogger('api_monitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def log_request(self, endpoint: str, method: str, user_id: str = None, 
                   status_code: int = None, response_time: float = None, 
                   error: str = None):
        """记录请求日志"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'user_id': user_id,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'status_code': status_code,
            'response_time': response_time,
            'error': error
        }
        
        # 更新指标
        self.metrics['requests'] += 1
        if error or (status_code and status_code >= 400):
            self.metrics['errors'] += 1
        if response_time:
            self.metrics['response_times'].append(response_time)
        
        # 记录日志
        if error or (status_code and status_code >= 400):
            self.logger.error(f"API Error: {json.dumps(log_data)}")
        else:
            self.logger.info(f"API Request: {json.dumps(log_data)}")
    
    def get_metrics(self) -> dict:
        """获取监控指标"""
        response_times = self.metrics['response_times']
        
        return {
            'total_requests': self.metrics['requests'],
            'total_errors': self.metrics['errors'],
            'error_rate': self.metrics['errors'] / max(1, self.metrics['requests']),
            'avg_response_time': sum(response_times) / max(1, len(response_times)),
            'max_response_time': max(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0
        }

# 全局监控器
api_monitor = ApiMonitor()

def monitor_api(f):
    """API监控装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        error = None
        status_code = None
        
        try:
            # 执行函数
            result = f(*args, **kwargs)
            
            # 提取状态码
            if isinstance(result, tuple):
                status_code = result[1] if len(result) > 1 else 200
            elif hasattr(result, 'status_code'):
                status_code = result.status_code
            else:
                status_code = 200
            
            return result
            
        except Exception as e:
            error = str(e)
            status_code = 500
            raise
        
        finally:
            # 记录监控数据
            end_time = time.time()
            response_time = end_time - start_time
            
            user_id = None
            if hasattr(request, 'current_user'):
                user_id = request.current_user.get('user_id')
            
            api_monitor.log_request(
                endpoint=request.endpoint,
                method=request.method,
                user_id=user_id,
                status_code=status_code,
                response_time=response_time,
                error=error
            )
    
    return decorated

# utils/debug.py
from flask import request, current_app
import traceback
import sys

class ApiDebugger:
    """API调试器"""
    
    @staticmethod
    def debug_request():
        """调试请求信息"""
        if current_app.debug:
            print(f"\n=== API Debug Info ===")
            print(f"Endpoint: {request.endpoint}")
            print(f"Method: {request.method}")
            print(f"URL: {request.url}")
            print(f"Headers: {dict(request.headers)}")
            if request.is_json:
                print(f"JSON Data: {request.get_json()}")
            else:
                print(f"Form Data: {request.form.to_dict()}")
            print(f"Query Params: {request.args.to_dict()}")
            print("=" * 50)
    
    @staticmethod
    def debug_response(response_data, status_code):
        """调试响应信息"""
        if current_app.debug:
            print(f"\n=== API Response Debug ===")
            print(f"Status Code: {status_code}")
            print(f"Response Data: {response_data}")
            print("=" * 50)
    
    @staticmethod
    def debug_exception(e):
        """调试异常信息"""
        if current_app.debug:
            print(f"\n=== API Exception Debug ===")
            print(f"Exception: {type(e).__name__}: {str(e)}")
            print(f"Traceback:")
            traceback.print_exc()
            print("=" * 50)

def debug_api(f):
    """API调试装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_app.debug:
            ApiDebugger.debug_request()
        
        try:
            result = f(*args, **kwargs)
            
            if current_app.debug:
                if isinstance(result, tuple):
                    ApiDebugger.debug_response(result[0], result[1])
                else:
                    ApiDebugger.debug_response(result, 200)
            
            return result
            
        except Exception as e:
            if current_app.debug:
                ApiDebugger.debug_exception(e)
            raise
    
    return decorated
```

这个实践指南提供了：

1. **基础API开发** - 用户管理API的完整实现
2. **认证系统** - JWT Token生成、验证和刷新
3. **权限控制** - 细粒度权限管理和资源级权限检查
4. **性能优化** - API限流和响应缓存机制
5. **监控调试** - 完整的API监控和调试工具

每个练习都包含完整的代码示例和详细的注释，可以直接运行和测试。接下来我会创建演示脚本来展示这些功能。 