#!/usr/bin/env python3
"""
装饰器实践练习脚本
Day 2 - CLI 学习辅助工具

运行这个脚本来理解装饰器的工作原理
"""
import time
import functools
from typing import Any, Callable
import click


# ========== 基础装饰器示例 ==========

def simple_timer(func: Callable) -> Callable:
    """简单计时装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"⏰ 开始执行 {func.__name__}()")
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        print(f"✅ {func.__name__}() 执行完毕，耗时 {end_time - start_time:.2f} 秒\n")
        return result
    return wrapper


def log_calls(func: Callable) -> Callable:
    """日志装饰器 - 记录函数调用"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"📝 调用函数: {func.__name__}")
        print(f"📝 参数: args={args}, kwargs={kwargs}")
        
        result = func(*args, **kwargs)
        
        print(f"📝 返回值: {result}")
        return result
    return wrapper


# ========== 模拟 Superset 的装饰器 ==========

class MockDatabase:
    """模拟数据库类"""
    def __init__(self):
        self.in_transaction = False
        self.operations = []
    
    def begin_transaction(self):
        print("🔄 开始数据库事务")
        self.in_transaction = True
        self.operations = []
    
    def commit(self):
        print("✅ 提交事务，执行以下操作:")
        for op in self.operations:
            print(f"   - {op}")
        self.in_transaction = False
        self.operations = []
    
    def rollback(self):
        print("❌ 回滚事务，撤销所有操作")
        self.in_transaction = False
        self.operations = []
    
    def add_operation(self, operation: str):
        self.operations.append(operation)


# 全局模拟数据库实例
mock_db = MockDatabase()


def mock_transaction(func: Callable) -> Callable:
    """模拟 @transaction() 装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        mock_db.begin_transaction()
        try:
            result = func(*args, **kwargs)
            mock_db.commit()
            return result
        except Exception as e:
            mock_db.rollback()
            print(f"💥 发生错误: {e}")
            raise
    return wrapper


def mock_with_appcontext(func: Callable) -> Callable:
    """模拟 @with_appcontext 装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("🏭 创建 Flask 应用上下文")
        try:
            result = func(*args, **kwargs)
            print("🧹 清理 Flask 应用上下文")
            return result
        except Exception as e:
            print("🧹 异常情况下清理 Flask 应用上下文")
            raise
    return wrapper


# ========== 实际示例函数 ==========

@simple_timer
def slow_function():
    """一个耗时的函数"""
    print("执行一些耗时的工作...")
    time.sleep(1)
    return "工作完成！"


@log_calls
@simple_timer
def calculate_sum(a: int, b: int) -> int:
    """展示多个装饰器叠加"""
    print(f"计算 {a} + {b}")
    return a + b


@mock_with_appcontext
@mock_transaction
def safe_database_operation():
    """模拟安全的数据库操作"""
    print("📊 执行数据库操作...")
    mock_db.add_operation("CREATE USER '张三'")
    mock_db.add_operation("ASSIGN ROLE 'admin' TO '张三'")
    print("✅ 数据库操作执行成功")


@mock_with_appcontext
@mock_transaction
def dangerous_database_operation():
    """模拟有问题的数据库操作"""
    print("📊 执行数据库操作...")
    mock_db.add_operation("CREATE USER '李四'")
    # 模拟出错
    raise ValueError("网络连接中断！")


# ========== Click 装饰器演示 ==========

class MockClickCommand:
    """模拟 Click 命令对象"""
    def __init__(self, name, callback):
        self.name = name
        self.callback = callback
        self.options = {}
        
    def add_option(self, name, **kwargs):
        self.options[name] = kwargs
        
    def invoke(self, **kwargs):
        """模拟命令调用"""
        print(f"🔧 执行 Click 命令: {self.name}")
        print(f"📝 解析到的参数: {kwargs}")
        
        # 类型转换演示
        processed_kwargs = {}
        for key, value in kwargs.items():
            if key in self.options and 'type' in self.options[key]:
                option_type = self.options[key]['type']
                if option_type == int:
                    processed_kwargs[key] = int(value)
                else:
                    processed_kwargs[key] = value
            else:
                processed_kwargs[key] = value
        
        print(f"🔄 类型转换后: {processed_kwargs}")
        return self.callback(**processed_kwargs)


def mock_click_command(name=None):
    """模拟 @click.command() 装饰器"""
    def decorator(func):
        cmd_name = name or func.__name__
        command_obj = MockClickCommand(cmd_name, func)
        
        # 复制 click 选项
        if hasattr(func, '_mock_click_options'):
            for opt_name, opt_config in func._mock_click_options.items():
                command_obj.add_option(opt_name, **opt_config)
        
        return command_obj
    return decorator


def mock_click_option(option_name, **kwargs):
    """模拟 @click.option() 装饰器"""
    def decorator(func):
        if not hasattr(func, '_mock_click_options'):
            func._mock_click_options = {}
        
        # 去掉 option_name 的 '--' 前缀
        clean_name = option_name.lstrip('-')
        func._mock_click_options[clean_name] = kwargs
        
        return func
    return decorator


# Click 装饰器使用示例
@mock_click_command('hello')
@mock_click_option('--name', default='World', help='要问候的人')
@mock_click_option('--count', type=int, default=1, help='重复次数')
def hello_command(name, count):
    """Click 命令示例"""
    print(f"✨ 生成问候语:")
    for i in range(count):
        print(f"   Hello, {name}! (第 {i+1} 次)")


# 演示 Click 参数顺序问题
@mock_click_command('demo-order')
@mock_click_option('--first', default='A')    # 最后添加
@mock_click_option('--second', default='B')   # 中间添加  
@mock_click_option('--third', default='C')    # 最先添加
def order_demo(third, second, first):  # 注意：参数顺序与装饰器相反！
    """演示 Click 参数顺序"""
    print(f"📋 参数接收顺序: third={third}, second={second}, first={first}")


# ========== 装饰器执行顺序演示 ==========

def decorator_a(func):
    print("装饰器 A - 初始化")
    def wrapper(*args, **kwargs):
        print("装饰器 A - 执行前")
        result = func(*args, **kwargs)
        print("装饰器 A - 执行后")
        return result
    return wrapper


def decorator_b(func):
    print("装饰器 B - 初始化")
    def wrapper(*args, **kwargs):
        print("装饰器 B - 执行前")
        result = func(*args, **kwargs)
        print("装饰器 B - 执行后")
        return result
    return wrapper


def decorator_c(func):
    print("装饰器 C - 初始化")
    def wrapper(*args, **kwargs):
        print("装饰器 C - 执行前")
        result = func(*args, **kwargs)
        print("装饰器 C - 执行后")
        return result
    return wrapper


@decorator_a  # 最后执行
@decorator_b  # 中间执行
@decorator_c  # 最先执行
def test_order():
    """测试装饰器执行顺序"""
    print("🎯 原始函数执行")


# ========== 主程序 ==========

def main():
    """主函数 - 运行所有示例"""
    print("=" * 60)
    print("🎓 装饰器实践练习 - Day 2 CLI 学习")
    print("=" * 60)
    
    print("\n1️⃣ 简单计时装饰器示例:")
    print("-" * 30)
    result = slow_function()
    print(f"函数返回值: {result}")
    
    print("\n2️⃣ 多装饰器叠加示例:")
    print("-" * 30)
    result = calculate_sum(10, 20)
    print(f"最终结果: {result}")
    
    print("\n3️⃣ 模拟 Superset 安全数据库操作:")
    print("-" * 40)
    try:
        safe_database_operation()
    except Exception as e:
        print(f"捕获异常: {e}")
    
    print("\n4️⃣ 模拟数据库操作失败场景:")
    print("-" * 35)
    try:
        dangerous_database_operation()
    except Exception as e:
        print(f"捕获异常: {e}")
    
    print("\n5️⃣ Click 装饰器原理演示:")
    print("-" * 30)
    print("🔧 模拟 Click 命令执行:")
    hello_command.invoke(name="张三", count="3")  # 注意 count 是字符串，会被自动转换
    
    print("\n🔧 演示参数顺序问题:")
    order_demo.invoke(first="X", second="Y", third="Z")
    
    print("\n6️⃣ 装饰器执行顺序演示:")
    print("-" * 30)
    print("注意观察装饰器的初始化顺序:")
    test_order()
    
    print("\n" + "=" * 60)
    print("🎉 练习完成！现在你应该理解装饰器的工作原理了！")
    print("特别是 Click 装饰器如何将普通函数转换为强大的命令行工具！")
    print("=" * 60)


if __name__ == "__main__":
    main() 