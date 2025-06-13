#!/usr/bin/env python3
"""
用户管理演示脚本
Day 3 - 用户管理与权限系统学习辅助工具

运行这个脚本来理解 Superset 用户管理的核心概念
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional


# ========== 模拟用户和角色数据结构 ==========

class MockUser:
    """模拟用户类"""
    def __init__(self, username: str, email: str, first_name: str, last_name: str, 
                 password: str, roles: List[str] = None, active: bool = True):
        self.id = hash(username) % 10000  # 简单的ID生成
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.password_hash = self._hash_password(password)
        self.roles = roles or []
        self.active = active
        self.created_on = datetime.now()
        self.last_login = None
        self.login_count = 0
        self.fail_login_count = 0

    def _hash_password(self, password: str) -> str:
        """模拟密码哈希"""
        salt = secrets.token_hex(16)
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

    def check_password(self, password: str) -> bool:
        """模拟密码验证"""
        # 实际场景中会验证哈希，这里简化处理
        return len(password) >= 6  # 简单的密码验证

    def has_role(self, role_name: str) -> bool:
        """检查用户是否拥有指定角色"""
        return role_name in self.roles

    def __str__(self):
        return f"User({self.username}, roles={self.roles}, active={self.active})"


class MockRole:
    """模拟角色类"""
    def __init__(self, name: str, permissions: List[str] = None):
        self.name = name
        self.permissions = permissions or []

    def has_permission(self, permission: str) -> bool:
        """检查角色是否拥有指定权限"""
        return permission in self.permissions

    def __str__(self):
        return f"Role({self.name}, permissions={len(self.permissions)})"


class MockSecurityManager:
    """模拟安全管理器"""
    
    def __init__(self):
        self.users: Dict[str, MockUser] = {}
        self.roles: Dict[str, MockRole] = {}
        self.sessions: Dict[str, MockUser] = {}
        self._init_default_roles()

    def _init_default_roles(self):
        """初始化默认角色"""
        # Admin 角色 - 完全权限
        admin_permissions = [
            'can_read', 'can_write', 'can_delete', 'can_add',
            'can_list_users', 'can_edit_users', 'can_delete_users',
            'can_manage_roles', 'can_access_sql_lab', 'can_run_queries',
            'can_access_all_databases', 'can_override_permissions'
        ]
        self.roles['Admin'] = MockRole('Admin', admin_permissions)

        # Alpha 角色 - 内容创建和编辑
        alpha_permissions = [
            'can_read', 'can_write', 'can_add',
            'can_access_sql_lab', 'can_run_queries',
            'can_create_dashboard', 'can_edit_dashboard',
            'can_create_chart', 'can_edit_chart'
        ]
        self.roles['Alpha'] = MockRole('Alpha', alpha_permissions)

        # Gamma 角色 - 只读权限
        gamma_permissions = [
            'can_read', 'can_view_dashboard', 'can_view_chart'
        ]
        self.roles['Gamma'] = MockRole('Gamma', gamma_permissions)

        # SQL Lab 专用角色
        sql_lab_permissions = [
            'can_access_sql_lab', 'can_run_queries', 'can_save_queries',
            'can_view_query_history', 'can_export_csv'
        ]
        self.roles['sql_lab'] = MockRole('sql_lab', sql_lab_permissions)

    def create_user(self, username: str, email: str, first_name: str, 
                   last_name: str, password: str, roles: List[str]) -> MockUser:
        """创建新用户"""
        if username in self.users:
            raise ValueError(f"用户 {username} 已存在")

        # 验证角色是否存在
        for role_name in roles:
            if role_name not in self.roles:
                raise ValueError(f"角色 {role_name} 不存在")

        user = MockUser(username, email, first_name, last_name, password, roles)
        self.users[username] = user
        
        print(f"✅ 用户 {username} 创建成功")
        print(f"   角色: {', '.join(roles)}")
        print(f"   邮箱: {email}")
        
        return user

    def authenticate(self, username: str, password: str) -> Optional[MockUser]:
        """用户认证"""
        user = self.users.get(username)
        if not user:
            print(f"❌ 用户 {username} 不存在")
            return None

        if not user.active:
            print(f"❌ 用户 {username} 已被禁用")
            return None

        if user.check_password(password):
            # 更新登录信息
            user.last_login = datetime.now()
            user.login_count += 1
            user.fail_login_count = 0
            
            # 创建会话
            session_id = secrets.token_hex(16)
            self.sessions[session_id] = user
            
            print(f"✅ 用户 {username} 登录成功")
            print(f"   会话ID: {session_id}")
            return user
        else:
            user.fail_login_count += 1
            print(f"❌ 用户 {username} 密码错误")
            return None

    def has_access(self, user: MockUser, permission: str, resource: str = None) -> bool:
        """权限检查"""
        if not user or not user.active:
            return False

        # Admin 用户拥有所有权限
        if user.has_role('Admin'):
            return True

        # 检查用户角色的权限
        for role_name in user.roles:
            role = self.roles.get(role_name)
            if role and role.has_permission(permission):
                return True

        return False

    def list_users(self) -> List[MockUser]:
        """列出所有用户"""
        return list(self.users.values())

    def list_roles(self) -> List[MockRole]:
        """列出所有角色"""
        return list(self.roles.values())


# ========== 演示函数 ==========

def demo_user_creation():
    """演示用户创建过程"""
    print("=" * 60)
    print("🎓 用户创建演示")
    print("=" * 60)
    
    sm = MockSecurityManager()
    
    # 创建不同角色的用户
    users_to_create = [
        ("admin", "admin@company.com", "System", "Admin", "admin123", ["Admin"]),
        ("analyst1", "analyst@company.com", "Data", "Analyst", "analyst123", ["Alpha"]),
        ("viewer1", "viewer@company.com", "Report", "Viewer", "viewer123", ["Gamma"]),
        ("sqluser", "sql@company.com", "SQL", "Developer", "sql123", ["sql_lab"]),
        ("poweruser", "power@company.com", "Power", "User", "power123", ["Alpha", "sql_lab"])
    ]
    
    for username, email, firstname, lastname, password, roles in users_to_create:
        try:
            sm.create_user(username, email, firstname, lastname, password, roles)
        except ValueError as e:
            print(f"❌ 创建用户失败: {e}")
        print()
    
    return sm


def demo_authentication():
    """演示认证过程"""
    print("=" * 60)
    print("🔐 用户认证演示")
    print("=" * 60)
    
    sm = demo_user_creation()
    
    # 测试不同的认证场景
    auth_tests = [
        ("admin", "admin123"),      # 正确密码
        ("admin", "wrongpass"),     # 错误密码
        ("nonexist", "anypass"),    # 不存在的用户
        ("analyst1", "analyst123"), # 正确密码
        ("viewer1", "short"),       # 密码太短
    ]
    
    print("认证测试:")
    for username, password in auth_tests:
        print(f"\n🔍 尝试登录: {username} / {password}")
        user = sm.authenticate(username, password)
        if user:
            print(f"   登录次数: {user.login_count}")
            print(f"   最后登录: {user.last_login}")
    
    return sm


def demo_permission_checking():
    """演示权限检查过程"""
    print("\n" + "=" * 60)
    print("🛡️ 权限检查演示")
    print("=" * 60)
    
    sm = demo_user_creation()
    
    # 获取测试用户
    admin = sm.users["admin"]
    analyst = sm.users["analyst1"] 
    viewer = sm.users["viewer1"]
    sql_user = sm.users["sqluser"]
    
    # 权限测试矩阵
    permission_tests = [
        ("can_read", "所有用户都应该有读权限"),
        ("can_write", "只有 Admin 和 Alpha 应该有写权限"),
        ("can_delete", "只有 Admin 应该有删除权限"),
        ("can_edit_users", "只有 Admin 应该能管理用户"),
        ("can_access_sql_lab", "Admin、Alpha、sql_lab 角色可以访问"),
        ("can_run_queries", "Admin、Alpha、sql_lab 角色可以执行查询"),
    ]
    
    users_to_test = [
        ("Admin用户", admin),
        ("Alpha用户", analyst),
        ("Gamma用户", viewer),
        ("SQL Lab用户", sql_user)
    ]
    
    print("权限检查矩阵:")
    print("-" * 80)
    print(f"{'权限':<20} {'Admin':<8} {'Alpha':<8} {'Gamma':<8} {'SQL Lab':<10}")
    print("-" * 80)
    
    for permission, description in permission_tests:
        results = []
        for user_name, user in users_to_test:
            has_permission = sm.has_access(user, permission)
            results.append("✅" if has_permission else "❌")
        
        print(f"{permission:<20} {results[0]:<8} {results[1]:<8} {results[2]:<8} {results[3]:<10}")
    
    print("-" * 80)
    print("\n权限解释:")
    for permission, description in permission_tests:
        print(f"• {permission}: {description}")


def demo_role_management():
    """演示角色管理"""
    print("\n" + "=" * 60)
    print("👥 角色管理演示")
    print("=" * 60)
    
    sm = demo_user_creation()
    
    print("内置角色概览:")
    for role_name, role in sm.roles.items():
        print(f"\n🎭 {role_name} 角色:")
        print(f"   权限数量: {len(role.permissions)}")
        print(f"   主要权限: {', '.join(role.permissions[:5])}")
        if len(role.permissions) > 5:
            print(f"   还有 {len(role.permissions) - 5} 个权限...")
    
    # 统计用户角色分布
    print(f"\n📊 用户角色分布:")
    role_count = {}
    for user in sm.users.values():
        for role in user.roles:
            role_count[role] = role_count.get(role, 0) + 1
    
    for role, count in role_count.items():
        print(f"   {role}: {count} 个用户")


def demo_security_scenarios():
    """演示安全场景"""
    print("\n" + "=" * 60)
    print("🔒 安全场景演示")
    print("=" * 60)
    
    sm = demo_user_creation()
    
    scenarios = [
        {
            "name": "场景1: 数据分析师日常工作",
            "user": "analyst1",
            "actions": [
                ("访问SQL Lab", "can_access_sql_lab"),
                ("执行查询", "can_run_queries"),
                ("创建图表", "can_create_chart"),
                ("创建仪表盘", "can_create_dashboard"),
                ("管理用户", "can_edit_users"),  # 应该被拒绝
            ]
        },
        {
            "name": "场景2: 业务用户查看报表",
            "user": "viewer1", 
            "actions": [
                ("查看仪表盘", "can_view_dashboard"),
                ("查看图表", "can_view_chart"),
                ("编辑图表", "can_write"),  # 应该被拒绝
                ("访问SQL Lab", "can_access_sql_lab"),  # 应该被拒绝
            ]
        },
        {
            "name": "场景3: 系统管理员操作",
            "user": "admin",
            "actions": [
                ("管理用户", "can_edit_users"),
                ("删除数据", "can_delete"),
                ("访问所有数据库", "can_access_all_databases"),
                ("覆盖权限", "can_override_permissions"),
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🎬 {scenario['name']}")
        user = sm.users[scenario['user']]
        print(f"   用户: {user.username} (角色: {', '.join(user.roles)})")
        
        for action_name, permission in scenario['actions']:
            has_access = sm.has_access(user, permission)
            status = "✅ 允许" if has_access else "❌ 拒绝"
            print(f"   {action_name}: {status}")


def demo_password_security():
    """演示密码安全机制"""
    print("\n" + "=" * 60)
    print("🔑 密码安全演示")
    print("=" * 60)
    
    # 模拟密码复杂度检查
    def check_password_strength(password: str) -> Dict[str, bool]:
        """检查密码强度"""
        checks = {
            "长度>=8": len(password) >= 8,
            "包含大写字母": any(c.isupper() for c in password),
            "包含小写字母": any(c.islower() for c in password),
            "包含数字": any(c.isdigit() for c in password),
            "包含特殊字符": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password),
        }
        return checks
    
    test_passwords = [
        "123456",           # 弱密码
        "password",         # 常见密码
        "Password123",      # 中等强度
        "MyStr0ng!Pass",    # 强密码
        "admin",            # 太短
    ]
    
    print("密码强度检查:")
    print("-" * 70)
    print(f"{'密码':<15} {'长度>=8':<8} {'大写':<6} {'小写':<6} {'数字':<6} {'特殊':<6} {'评级'}")
    print("-" * 70)
    
    for password in test_passwords:
        checks = check_password_strength(password)
        score = sum(checks.values())
        
        # 评级
        if score >= 5:
            rating = "🟢 强"
        elif score >= 3:
            rating = "🟡 中"
        else:
            rating = "🔴 弱"
        
        print(f"{password:<15} "
              f"{'✅' if checks['长度>=8'] else '❌':<8} "
              f"{'✅' if checks['包含大写字母'] else '❌':<6} "
              f"{'✅' if checks['包含小写字母'] else '❌':<6} "
              f"{'✅' if checks['包含数字'] else '❌':<6} "
              f"{'✅' if checks['包含特殊字符'] else '❌':<6} "
              f"{rating}")


def main():
    """主函数"""
    print("🎓 Superset 用户管理与权限系统演示")
    print("Day 3 学习辅助工具")
    print()
    
    # 运行所有演示
    demo_user_creation()
    demo_authentication()
    demo_permission_checking()
    demo_role_management()
    demo_security_scenarios()
    demo_password_security()
    
    print("\n" + "=" * 60)
    print("🎉 演示完成！")
    print("现在你应该对 Superset 的用户管理和权限系统有了深入的理解。")
    print("建议结合实际的 Superset 环境进行练习，验证这些概念。")
    print("=" * 60)


if __name__ == "__main__":
    main() 