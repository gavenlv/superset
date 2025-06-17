#!/usr/bin/env python3
"""
Apache Superset 权限系统实战演示

这个演示展示了如何：
1. 理解和使用 Superset 权限系统
2. 实现自定义权限管理
3. 权限检查和验证机制
4. 权限系统性能优化

作者: Superset学习者
日期: 2024年
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache, wraps
import json

# 模拟 Flask-AppBuilder 权限模型
class PermissionType(Enum):
    """权限类型枚举"""
    CRUD = "crud"                    # CRUD操作权限
    MENU_ACCESS = "menu_access"      # 菜单访问权限
    RESOURCE_ACCESS = "resource_access"  # 资源访问权限
    ADMIN = "admin"                  # 管理员权限
    SPECIAL = "special"              # 特殊权限

class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = "Admin"
    ALPHA = "Alpha"
    GAMMA = "Gamma"
    SQL_LAB = "sql_lab"
    PUBLIC = "Public"
    GUEST = "Guest"

@dataclass
class Permission:
    """权限模型"""
    id: int
    name: str
    permission_type: PermissionType
    description: str = ""
    created_on: datetime = field(default_factory=datetime.now)

@dataclass
class ViewMenu:
    """视图菜单模型"""
    id: int
    name: str
    description: str = ""
    created_on: datetime = field(default_factory=datetime.now)

@dataclass
class PermissionView:
    """权限视图关联模型"""
    id: int
    permission: Permission
    view_menu: ViewMenu
    created_on: datetime = field(default_factory=datetime.now)

@dataclass
class Role:
    """角色模型"""
    id: int
    name: str
    permissions: List[PermissionView] = field(default_factory=list)
    description: str = ""
    created_on: datetime = field(default_factory=datetime.now)
    
    def add_permission(self, permission_view: PermissionView):
        """添加权限到角色"""
        if permission_view not in self.permissions:
            self.permissions.append(permission_view)
    
    def remove_permission(self, permission_view: PermissionView):
        """从角色移除权限"""
        if permission_view in self.permissions:
            self.permissions.remove(permission_view)
    
    def has_permission(self, permission_name: str, view_name: str) -> bool:
        """检查角色是否有特定权限"""
        for pv in self.permissions:
            if (pv.permission.name == permission_name and 
                pv.view_menu.name == view_name):
                return True
        return False

@dataclass
class User:
    """用户模型"""
    id: int
    username: str
    email: str
    active: bool = True
    roles: List[Role] = field(default_factory=list)
    login_count: int = 0
    last_login: Optional[datetime] = None
    created_on: datetime = field(default_factory=datetime.now)
    
    def add_role(self, role: Role):
        """添加角色到用户"""
        if role not in self.roles:
            self.roles.append(role)
    
    def remove_role(self, role: Role):
        """从用户移除角色"""
        if role in self.roles:
            self.roles.remove(role)
    
    def has_role(self, role_name: str) -> bool:
        """检查用户是否有特定角色"""
        return any(role.name == role_name for role in self.roles)
    
    def get_all_permissions(self) -> Set[Tuple[str, str]]:
        """获取用户的所有权限"""
        permissions = set()
        for role in self.roles:
            for pv in role.permissions:
                permissions.add((pv.permission.name, pv.view_menu.name))
        return permissions

class PermissionCache:
    """权限缓存管理"""
    
    def __init__(self, cache_timeout: int = 300):
        self.cache_timeout = cache_timeout
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """从缓存获取值"""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_timeout):
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        self._cache[key] = (value, datetime.now())
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        now = datetime.now()
        valid_entries = sum(
            1 for _, timestamp in self._cache.values()
            if now - timestamp < timedelta(seconds=self.cache_timeout)
        )
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._cache) - valid_entries
        }

def performance_monitor(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        if execution_time > 0.1:  # 超过100ms记录警告
            logging.warning(f"{func.__name__} execution time: {execution_time:.3f}s")
        else:
            logging.debug(f"{func.__name__} execution time: {execution_time:.3f}s")
        
        return result
    return wrapper

class SupersetSecurityManager:
    """Superset 安全管理器"""
    
    # 权限常量定义
    ADMIN_ONLY_PERMISSIONS = {
        "can_update_role",
        "all_query_access", 
        "can_grant_guest_token",
        "can_set_embedded",
        "can_warm_up_cache",
    }
    
    ALPHA_ONLY_PERMISSIONS = {
        "muldelete",
        "all_database_access",
        "all_datasource_access",
    }
    
    READ_ONLY_PERMISSIONS = {
        "can_show",
        "can_list", 
        "can_get",
        "can_read",
        "can_external_metadata",
    }
    
    SQLLAB_PERMISSIONS = {
        ("can_read", "SavedQuery"),
        ("can_write", "SavedQuery"),
        ("can_export", "SavedQuery"),
        ("can_execute_sql_query", "SQLLab"),
        ("can_sqllab", "Superset"),
        ("menu_access", "SQL Lab"),
    }
    
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.roles: Dict[int, Role] = {}
        self.permissions: Dict[int, Permission] = {}
        self.view_menus: Dict[int, ViewMenu] = {}
        self.permission_views: Dict[int, PermissionView] = {}
        self.cache = PermissionCache()
        self.logger = logging.getLogger(__name__)
        
        # 初始化基础数据
        self._init_permissions()
        self._init_view_menus()
        self._init_roles()
        self._init_demo_users()
    
    def _init_permissions(self):
        """初始化基础权限"""
        permissions_data = [
            (1, "can_read", PermissionType.CRUD, "读取权限"),
            (2, "can_write", PermissionType.CRUD, "写入权限"),
            (3, "can_delete", PermissionType.CRUD, "删除权限"),
            (4, "can_edit", PermissionType.CRUD, "编辑权限"),
            (5, "can_list", PermissionType.CRUD, "列表权限"),
            (6, "can_show", PermissionType.CRUD, "显示权限"),
            (7, "menu_access", PermissionType.MENU_ACCESS, "菜单访问权限"),
            (8, "database_access", PermissionType.RESOURCE_ACCESS, "数据库访问权限"),
            (9, "datasource_access", PermissionType.RESOURCE_ACCESS, "数据源访问权限"),
            (10, "schema_access", PermissionType.RESOURCE_ACCESS, "模式访问权限"),
            (11, "all_database_access", PermissionType.ADMIN, "所有数据库访问权限"),
            (12, "all_datasource_access", PermissionType.ADMIN, "所有数据源访问权限"),
            (13, "can_update_role", PermissionType.ADMIN, "角色更新权限"),
            (14, "can_execute_sql_query", PermissionType.SPECIAL, "SQL查询执行权限"),
            (15, "can_sqllab", PermissionType.SPECIAL, "SQL Lab访问权限"),
        ]
        
        for perm_id, name, perm_type, desc in permissions_data:
            self.permissions[perm_id] = Permission(perm_id, name, perm_type, desc)
    
    def _init_view_menus(self):
        """初始化视图菜单"""
        view_menus_data = [
            (1, "Database", "数据库管理"),
            (2, "Dataset", "数据集管理"),
            (3, "Chart", "图表管理"),
            (4, "Dashboard", "仪表板管理"),
            (5, "SQLLab", "SQL实验室"),
            (6, "Superset", "Superset系统"),
            (7, "SavedQuery", "保存的查询"),
            (8, "Query", "查询"),
            (9, "SQL Lab", "SQL Lab菜单"),
            (10, "Explore", "数据探索"),
            (11, "List Users", "用户列表"),
            (12, "List Roles", "角色列表"),
        ]
        
        for vm_id, name, desc in view_menus_data:
            self.view_menus[vm_id] = ViewMenu(vm_id, name, desc)
    
    def _init_roles(self):
        """初始化角色和权限关联"""
        # 创建权限视图关联
        pv_id = 1
        for perm_id, perm in self.permissions.items():
            for vm_id, vm in self.view_menus.items():
                self.permission_views[pv_id] = PermissionView(pv_id, perm, vm)
                pv_id += 1
        
        # 创建角色
        self.roles[1] = Role(1, UserRole.ADMIN.value, description="系统管理员")
        self.roles[2] = Role(2, UserRole.ALPHA.value, description="高级用户")
        self.roles[3] = Role(3, UserRole.GAMMA.value, description="普通用户")
        self.roles[4] = Role(4, UserRole.SQL_LAB.value, description="SQL实验室用户")
        self.roles[5] = Role(5, UserRole.PUBLIC.value, description="公共用户")
        
        # 分配权限给角色
        self._assign_permissions_to_roles()
    
    def _assign_permissions_to_roles(self):
        """分配权限给角色"""
        admin_role = self.roles[1]
        alpha_role = self.roles[2] 
        gamma_role = self.roles[3]
        sqllab_role = self.roles[4]
        
        # Admin 角色拥有所有权限
        for pv in self.permission_views.values():
            admin_role.add_permission(pv)
        
        # Alpha 角色权限
        for pv in self.permission_views.values():
            perm_name = pv.permission.name
            view_name = pv.view_menu.name
            
            if (perm_name not in self.ADMIN_ONLY_PERMISSIONS and
                view_name not in ["List Users", "List Roles"]):
                alpha_role.add_permission(pv)
        
        # Gamma 角色权限 (只读权限)
        for pv in self.permission_views.values():
            perm_name = pv.permission.name
            view_name = pv.view_menu.name
            
            if (perm_name in self.READ_ONLY_PERMISSIONS and
                view_name in ["Chart", "Dashboard", "Dataset", "Explore"]):
                gamma_role.add_permission(pv)
        
        # SQL Lab 角色权限
        for pv in self.permission_views.values():
            perm_name = pv.permission.name
            view_name = pv.view_menu.name
            
            if ((perm_name, view_name) in self.SQLLAB_PERMISSIONS or
                (perm_name in self.READ_ONLY_PERMISSIONS and 
                 view_name in ["SQLLab", "SavedQuery", "Query"])):
                sqllab_role.add_permission(pv)
    
    def _init_demo_users(self):
        """初始化演示用户"""
        # 创建演示用户
        self.users[1] = User(1, "admin", "admin@example.com")
        self.users[2] = User(2, "alpha_user", "alpha@example.com")
        self.users[3] = User(3, "gamma_user", "gamma@example.com")
        self.users[4] = User(4, "sql_analyst", "sql@example.com")
        self.users[5] = User(5, "guest_user", "guest@example.com")
        
        # 分配角色
        self.users[1].add_role(self.roles[1])  # Admin
        self.users[2].add_role(self.roles[2])  # Alpha
        self.users[3].add_role(self.roles[3])  # Gamma
        self.users[4].add_role(self.roles[4])  # SQL Lab
        self.users[5].add_role(self.roles[5])  # Public
    
    @performance_monitor
    def can_access(self, user_id: int, permission_name: str, view_name: str) -> bool:
        """检查用户是否有权限访问"""
        # 缓存键
        cache_key = f"user:{user_id}:perm:{permission_name}:view:{view_name}"
        
        # 尝试从缓存获取
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 权限检查逻辑
        result = self._check_permission(user_id, permission_name, view_name)
        
        # 缓存结果
        self.cache.set(cache_key, result)
        
        return result
    
    def _check_permission(self, user_id: int, permission_name: str, view_name: str) -> bool:
        """内部权限检查逻辑"""
        user = self.users.get(user_id)
        if not user or not user.active:
            return False
        
        # 检查用户的所有角色
        for role in user.roles:
            if role.has_permission(permission_name, view_name):
                return True
        
        return False
    
    @performance_monitor  
    def can_access_database(self, user_id: int, database_name: str, database_id: int) -> bool:
        """检查数据库访问权限"""
        # 检查全局数据库访问权限
        if self.can_access(user_id, "all_database_access", "all_database_access"):
            return True
        
        # 检查特定数据库权限
        database_perm = f"[{database_name}].(id:{database_id})"
        return self.can_access(user_id, "database_access", database_perm)
    
    @performance_monitor
    def can_access_datasource(self, user_id: int, database_name: str, 
                            table_name: str, table_id: int) -> bool:
        """检查数据源访问权限"""
        # 检查全局数据源访问权限
        if self.can_access(user_id, "all_datasource_access", "all_datasource_access"):
            return True
        
        # 检查特定数据源权限  
        datasource_perm = f"[{database_name}].[{table_name}](id:{table_id})"
        return self.can_access(user_id, "datasource_access", datasource_perm)
    
    def get_user_permissions(self, user_id: int) -> List[Dict[str, str]]:
        """获取用户所有权限"""
        user = self.users.get(user_id)
        if not user:
            return []
        
        permissions = []
        for role in user.roles:
            for pv in role.permissions:
                permissions.append({
                    "role": role.name,
                    "permission": pv.permission.name,
                    "view_menu": pv.view_menu.name,
                    "permission_type": pv.permission.permission_type.value
                })
        
        return permissions
    
    def get_role_permissions(self, role_name: str) -> List[Dict[str, str]]:
        """获取角色权限"""
        role = next((r for r in self.roles.values() if r.name == role_name), None)
        if not role:
            return []
        
        permissions = []
        for pv in role.permissions:
            permissions.append({
                "permission": pv.permission.name,
                "view_menu": pv.view_menu.name,
                "permission_type": pv.permission.permission_type.value,
                "description": pv.permission.description
            })
        
        return permissions
    
    def create_custom_role(self, role_name: str, permissions: List[Tuple[str, str]]) -> Role:
        """创建自定义角色"""
        role_id = max(self.roles.keys()) + 1
        role = Role(role_id, role_name, description=f"自定义角色: {role_name}")
        
        # 添加指定权限
        for perm_name, view_name in permissions:
            for pv in self.permission_views.values():
                if (pv.permission.name == perm_name and 
                    pv.view_menu.name == view_name):
                    role.add_permission(pv)
                    break
        
        self.roles[role_id] = role
        return role
    
    def audit_permissions(self) -> Dict[str, Any]:
        """权限审计"""
        audit_result = {
            "timestamp": datetime.now().isoformat(),
            "users": {},
            "roles": {},
            "permissions": {},
            "cache_stats": self.cache.get_stats()
        }
        
        # 用户审计
        for user_id, user in self.users.items():
            user_perms = self.get_user_permissions(user_id)
            audit_result["users"][user.username] = {
                "active": user.active,
                "roles": [role.name for role in user.roles],
                "permission_count": len(user_perms),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "login_count": user.login_count
            }
        
        # 角色审计
        for role_id, role in self.roles.items():
            audit_result["roles"][role.name] = {
                "permission_count": len(role.permissions),
                "user_count": sum(1 for user in self.users.values() 
                                if role in user.roles),
                "created_on": role.created_on.isoformat()
            }
        
        # 权限审计
        for perm_id, perm in self.permissions.items():
            usage_count = sum(1 for role in self.roles.values()
                            for pv in role.permissions
                            if pv.permission.id == perm_id)
            audit_result["permissions"][perm.name] = {
                "type": perm.permission_type.value,
                "usage_count": usage_count,
                "description": perm.description
            }
        
        return audit_result
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.active)
        total_roles = len(self.roles)
        total_permissions = len(self.permissions)
        total_permission_views = len(self.permission_views)
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users
            },
            "roles": {
                "total": total_roles,
                "builtin": 5,
                "custom": total_roles - 5
            },
            "permissions": {
                "total": total_permissions,
                "crud": sum(1 for p in self.permissions.values() 
                          if p.permission_type == PermissionType.CRUD),
                "admin": sum(1 for p in self.permissions.values() 
                           if p.permission_type == PermissionType.ADMIN),
                "resource": sum(1 for p in self.permissions.values() 
                              if p.permission_type == PermissionType.RESOURCE_ACCESS)
            },
            "permission_views": total_permission_views,
            "cache": self.cache.get_stats()
        }

def demo_permission_system():
    """权限系统演示"""
    print("🔒 Apache Superset 权限系统演示")
    print("=" * 50)
    
    # 初始化安全管理器
    security_manager = SupersetSecurityManager()
    
    # 1. 基础权限检查演示
    print("\n1. 基础权限检查演示")
    print("-" * 30)
    
    test_cases = [
        (1, "can_read", "Dashboard", "Admin用户访问仪表板"),
        (3, "can_read", "Dashboard", "Gamma用户访问仪表板"), 
        (3, "can_write", "Dashboard", "Gamma用户编辑仪表板"),
        (4, "can_execute_sql_query", "SQLLab", "SQL分析师执行查询"),
        (2, "all_database_access", "all_database_access", "Alpha用户全局数据库访问"),
    ]
    
    for user_id, permission, view, description in test_cases:
        result = security_manager.can_access(user_id, permission, view)
        status = "✅ 允许" if result else "❌ 拒绝"
        username = security_manager.users[user_id].username
        print(f"{status} {description} (用户: {username})")
    
    # 2. 数据访问权限演示
    print("\n2. 数据访问权限演示")
    print("-" * 30)
    
    database_tests = [
        (1, "sales_db", 1, "Admin访问销售数据库"),
        (2, "sales_db", 1, "Alpha访问销售数据库"),
        (3, "sales_db", 1, "Gamma访问销售数据库"),
    ]
    
    for user_id, db_name, db_id, description in database_tests:
        result = security_manager.can_access_database(user_id, db_name, db_id)
        status = "✅ 允许" if result else "❌ 拒绝"
        username = security_manager.users[user_id].username
        print(f"{status} {description} (用户: {username})")
    
    # 3. 角色权限分析
    print("\n3. 角色权限分析")
    print("-" * 30)
    
    for role_name in [UserRole.ADMIN.value, UserRole.ALPHA.value, UserRole.GAMMA.value]:
        permissions = security_manager.get_role_permissions(role_name)
        print(f"\n角色: {role_name}")
        print(f"权限数量: {len(permissions)}")
        
        # 按权限类型分组
        perm_by_type = {}
        for perm in permissions:
            perm_type = perm["permission_type"]
            if perm_type not in perm_by_type:
                perm_by_type[perm_type] = 0
            perm_by_type[perm_type] += 1
        
        for perm_type, count in perm_by_type.items():
            print(f"  - {perm_type}: {count}个权限")
    
    # 4. 自定义角色创建演示
    print("\n4. 自定义角色创建演示")
    print("-" * 30)
    
    # 创建数据分析师角色
    analyst_permissions = [
        ("can_read", "Chart"),
        ("can_read", "Dashboard"),
        ("can_read", "Dataset"),
        ("can_execute_sql_query", "SQLLab"),
        ("menu_access", "SQL Lab"),
    ]
    
    analyst_role = security_manager.create_custom_role("DataAnalyst", analyst_permissions)
    print(f"✅ 创建自定义角色: {analyst_role.name}")
    print(f"权限数量: {len(analyst_role.permissions)}")
    
    # 5. 性能监控演示
    print("\n5. 性能监控演示")
    print("-" * 30)
    
    # 执行大量权限检查以测试性能
    start_time = time.time()
    
    for i in range(1000):
        user_id = (i % 5) + 1  # 轮询用户
        security_manager.can_access(user_id, "can_read", "Dashboard")
    
    end_time = time.time()
    print(f"执行1000次权限检查耗时: {end_time - start_time:.3f}秒")
    
    # 6. 系统审计演示
    print("\n6. 系统审计演示")
    print("-" * 30)
    
    stats = security_manager.get_system_stats()
    print(f"总用户数: {stats['users']['total']}")
    print(f"活跃用户: {stats['users']['active']}")
    print(f"总角色数: {stats['roles']['total']}")
    print(f"总权限数: {stats['permissions']['total']}")
    print(f"缓存统计: {stats['cache']}")
    
    # 7. 权限审计报告
    print("\n7. 权限审计报告")
    print("-" * 30)
    
    audit_report = security_manager.audit_permissions()
    
    print("用户权限分布:")
    for username, user_info in audit_report["users"].items():
        print(f"  {username}: {user_info['permission_count']}个权限")
    
    print("\n角色使用情况:")
    for role_name, role_info in audit_report["roles"].items():
        print(f"  {role_name}: {role_info['user_count']}个用户")
    
    print("\n权限使用频率 (Top 5):")
    perm_usage = [(name, info["usage_count"]) 
                  for name, info in audit_report["permissions"].items()]
    perm_usage.sort(key=lambda x: x[1], reverse=True)
    
    for perm_name, usage_count in perm_usage[:5]:
        print(f"  {perm_name}: {usage_count}次使用")

def demo_row_level_security():
    """行级安全演示"""
    print("\n🛡️ 行级安全 (RLS) 演示")
    print("=" * 50)
    
    @dataclass
    class RLSFilter:
        """行级安全过滤器"""
        id: int
        name: str
        table_id: int
        clause: str
        filter_type: str = "Regular"
        group_key: Optional[str] = None
        
    @dataclass
    class RLSDemo:
        """行级安全演示类"""
        filters: List[RLSFilter] = field(default_factory=list)
        
        def add_filter(self, name: str, table_id: int, clause: str):
            """添加RLS过滤器"""
            filter_id = len(self.filters) + 1
            rls_filter = RLSFilter(filter_id, name, table_id, clause)
            self.filters.append(rls_filter)
            return rls_filter
        
        def apply_rls_filters(self, user_id: int, base_sql: str) -> str:
            """应用RLS过滤器到SQL查询"""
            # 模拟根据用户角色应用不同的过滤器
            modified_sql = base_sql
            
            for rls_filter in self.filters:
                if self._should_apply_filter(user_id, rls_filter):
                    # 在WHERE子句中添加过滤条件
                    if "WHERE" in modified_sql.upper():
                        modified_sql = modified_sql.replace(
                            "WHERE", f"WHERE ({rls_filter.clause}) AND"
                        )
                    else:
                        modified_sql += f" WHERE {rls_filter.clause}"
            
            return modified_sql
        
        def _should_apply_filter(self, user_id: int, rls_filter: RLSFilter) -> bool:
            """判断是否应该对用户应用过滤器"""
            # 简化逻辑：除了Admin用户，其他用户都应用过滤器
            return user_id != 1  # user_id=1 是Admin用户
    
    # RLS演示
    rls_demo = RLSDemo()
    
    # 添加示例过滤器
    rls_demo.add_filter(
        "部门访问限制", 
        1, 
        "department_id = {{ current_user_attr('department_id') }}"
    )
    
    rls_demo.add_filter(
        "地区访问限制",
        1,
        "region IN ({{ current_user_attr('accessible_regions') }})"
    )
    
    # 测试SQL查询
    base_sql = "SELECT * FROM sales_data"
    
    print("原始SQL查询:")
    print(f"  {base_sql}")
    
    print("\n应用RLS后的SQL查询:")
    for user_id in [1, 2, 3]:
        username = ["", "admin", "alpha_user", "gamma_user"][user_id]
        filtered_sql = rls_demo.apply_rls_filters(user_id, base_sql)
        print(f"  用户 {username}: {filtered_sql}")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 运行权限系统演示
        demo_permission_system()
        
        # 运行行级安全演示
        demo_row_level_security()
        
        print("\n🎉 权限系统演示完成!")
        print("学习要点:")
        print("1. 理解RBAC权限模型的核心概念")
        print("2. 掌握权限检查和验证机制") 
        print("3. 了解权限缓存和性能优化")
        print("4. 熟悉行级安全的实现原理")
        print("5. 掌握权限审计和监控方法")
        
    except Exception as e:
        logging.error(f"演示过程中发生错误: {e}")
        raise 