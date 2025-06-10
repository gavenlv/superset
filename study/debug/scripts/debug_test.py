#!/usr/bin/env python3
"""
调试环境测试脚本

这个脚本用于验证VS Code调试环境是否正确配置
运行方式：选择"🔍 Superset: Debug Current File"配置，然后按F5
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_basic_debugging():
    """测试基础调试功能"""
    print("🔍 开始调试环境测试")
    
    # 测试变量查看
    test_data = {
        "dashboard_id": 123,
        "user_name": "admin",
        "charts": ["chart1", "chart2", "chart3"]
    }
    
    logger.info(f"测试数据: {test_data}")
    
    # 设置断点在这里 🔴
    # 在VS Code中点击这行左侧设置断点，然后按F5启动调试
    for i, chart in enumerate(test_data["charts"]):
        print(f"处理图表 {i+1}: {chart}")
        
        # 条件断点测试 - 只在i==1时暂停
        if i == 1:
            logger.debug(f"这是第{i+1}个图表，应该在这里暂停")
    
    return test_data

def test_superset_imports():
    """测试Superset模块导入"""
    print("\n📦 测试Superset模块导入")
    
    try:
        # 测试基础导入
        from superset import config
        print("✅ superset.config 导入成功")
        
        from superset.models.core import Database
        print("✅ Database模型导入成功") 
        
        from superset.extensions import db
        print("✅ 数据库扩展导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_environment_setup():
    """测试环境配置"""
    print("\n⚙️ 检查环境配置")
    
    # 检查Python路径
    print(f"🐍 Python版本: {sys.version}")
    print(f"📁 当前工作目录: {os.getcwd()}")
    print(f"🛤️ Python路径: {sys.path[:3]}...")  # 显示前3个路径
    
    # 检查环境变量
    superset_config = os.environ.get('SUPERSET_CONFIG')
    print(f"🔧 SUPERSET_CONFIG: {superset_config}")
    
    # 检查VS Code调试环境
    if 'VSCODE_PID' in os.environ:
        print("✅ VS Code调试环境检测到")
    else:
        print("⚠️ 非VS Code环境运行")

def simulate_error_debugging():
    """模拟错误调试"""
    print("\n🐛 模拟错误调试场景")
    
    try:
        # 故意制造一个错误用于调试
        data = {"users": [{"name": "Alice", "age": 25}, {"name": "Bob"}]}
        
        total_age = 0
        for user in data["users"]:
            # 这里会出错，因为Bob没有age字段
            total_age += user["age"]  # KeyError!
            
    except Exception as e:
        print(f"❌ 捕获到错误: {e}")
        logger.error(f"调试错误示例: {e}", exc_info=True)
        
        # 在异常处理中设置断点，可以查看异常详情
        print("💡 在这里设置断点可以查看异常堆栈和变量状态")

def main():
    """主函数"""
    print("🎯 VS Code + Superset 调试环境验证")
    print("=" * 50)
    
    # 基础调试测试
    result = test_basic_debugging()
    
    # 模块导入测试
    imports_ok = test_superset_imports()
    
    # 环境配置测试
    test_environment_setup()
    
    # 错误调试测试
    simulate_error_debugging()
    
    print("\n🎉 调试测试完成!")
    print("\n💡 调试技巧提示:")
    print("1. 在代码行左侧点击设置断点 🔴")
    print("2. 按F5启动调试")
    print("3. 使用F10单步执行，F11进入函数")
    print("4. 在调试面板查看变量值")
    print("5. 在调试控制台执行Python表达式")
    
    return {
        "basic_test": result,
        "imports_success": imports_ok,
        "status": "completed"
    }

if __name__ == "__main__":
    # 这是脚本入口点
    # 选择"🔍 Superset: Debug Current File"配置并按F5来调试这个脚本
    
    # 在这里设置断点开始调试 🔴
    final_result = main()
    print(f"\n✅ 最终结果: {final_result}") 