#!/usr/bin/env python3
"""
第1天实践练习：理解Superset的Flask应用架构

本练习帮助你深入理解：
1. Flask应用工厂模式
2. 配置加载机制
3. 扩展初始化流程
4. 全局对象管理

运行方式：
python day1_practice.py
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加superset到Python路径
sys.path.insert(0, '.')

def practice_1_config_loading():
    """练习1: 理解配置加载机制"""
    print("🔧 练习1: 配置加载机制")
    print("=" * 50)
    
    # 查看默认配置路径
    from superset import config
    print(f"📁 默认DATA_DIR: {config.DATA_DIR}")
    print(f"🔑 SECRET_KEY前8位: {config.SECRET_KEY[:8]}...")
    print(f"🗄️ 默认数据库URI: {config.SQLALCHEMY_DATABASE_URI}")
    print(f"📊 默认行限制: {config.ROW_LIMIT}")
    
    # 演示环境变量覆盖
    original_key = os.environ.get('SUPERSET_SECRET_KEY', '')
    os.environ['SUPERSET_SECRET_KEY'] = 'test_secret_key_123'
    
    # 重新导入配置模块来查看变化
    import importlib
    importlib.reload(config)
    print(f"🔄 环境变量覆盖后: {config.SECRET_KEY}")
    
    # 恢复原始值
    if original_key:
        os.environ['SUPERSET_SECRET_KEY'] = original_key
    else:
        os.environ.pop('SUPERSET_SECRET_KEY', None)
    
    print()

def practice_2_app_factory():
    """练习2: 理解Flask应用工厂模式"""
    print("🏭 练习2: Flask应用工厂模式")
    print("=" * 50)
    
    try:
        from superset.app import create_app, SupersetApp
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
# 测试配置
SECRET_KEY = 'test_secret_key_for_learning'
TESTING = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
WTF_CSRF_ENABLED = False
""")
            test_config_path = f.name
        
        # 注意：实际创建应用需要完整的环境，这里只是演示工厂模式
        print("📋 应用工厂模式的特点：")
        print("  1. create_app() 函数接受配置参数")
        print("  2. 支持不同环境的不同配置")
        print("  3. 返回完全初始化的Flask应用实例")
        print("  4. SupersetApp继承自Flask，可以自定义行为")
        
        # 清理临时文件
        os.unlink(test_config_path)
        
    except Exception as e:
        print(f"⚠️ 注意：完整应用创建需要数据库等依赖: {e}")
    
    print()

def practice_3_extensions_analysis():
    """练习3: 分析全局扩展对象"""
    print("🧩 练习3: 全局扩展对象分析")
    print("=" * 50)
    
    try:
        from superset.extensions import (
            appbuilder, db, cache_manager, celery_app,
            security_manager, async_query_manager
        )
        
        print("📦 核心扩展对象类型：")
        print(f"  - appbuilder: {type(appbuilder)}")
        print(f"  - db: {type(db)}")
        print(f"  - cache_manager: {type(cache_manager)}")
        print(f"  - celery_app: {type(celery_app)}")
        
        print("\n🔗 LocalProxy对象（延迟加载）：")
        print(f"  - security_manager: {type(security_manager)}")
        print(f"  - async_query_manager: {type(async_query_manager)}")
        
        print("\n💡 LocalProxy的优势：")
        print("  1. 延迟初始化 - 只在使用时创建")
        print("  2. 应用上下文绑定 - 确保正确的上下文")
        print("  3. 线程安全 - 每个线程独立实例")
        
    except Exception as e:
        print(f"⚠️ 需要应用上下文才能访问某些对象: {e}")
    
    print()

def practice_4_initialization_flow():
    """练习4: 理解初始化流程"""
    print("🚀 练习4: 初始化流程分析")
    print("=" * 50)
    
    try:
        from superset.initialization import SupersetAppInitializer
        
        print("🔄 SupersetAppInitializer的关键方法：")
        
        # 获取所有方法名
        methods = [method for method in dir(SupersetAppInitializer) 
                  if not method.startswith('_') and callable(getattr(SupersetAppInitializer, method))]
        
        # 按类别分组显示
        config_methods = [m for m in methods if m.startswith('configure_')]
        setup_methods = [m for m in methods if m.startswith('setup_') or m.startswith('init_')]
        other_methods = [m for m in methods if m not in config_methods and m not in setup_methods]
        
        print(f"\n⚙️ 配置类方法 ({len(config_methods)}个):")
        for method in sorted(config_methods):
            print(f"  - {method}")
            
        print(f"\n🏗️ 初始化类方法 ({len(setup_methods)}个):")
        for method in sorted(setup_methods):
            print(f"  - {method}")
            
        print(f"\n🔧 其他方法 ({len(other_methods)}个):")
        for method in sorted(other_methods):
            print(f"  - {method}")
            
    except Exception as e:
        print(f"❌ 导入错误: {e}")
    
    print()

def practice_5_feature_flags():
    """练习5: 理解功能开关机制"""
    print("🎛️ 练习5: 功能开关机制")
    print("=" * 50)
    
    try:
        from superset import config
        
        # 查看默认功能开关
        if hasattr(config, 'FEATURE_FLAGS'):
            print("🚩 默认功能开关状态：")
            for flag, status in config.FEATURE_FLAGS.items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {flag}: {status}")
        else:
            print("📋 在config.py中查看FEATURE_FLAGS配置")
            
        print("\n💡 功能开关的作用：")
        print("  1. 逐步发布新功能 (渐进式部署)")
        print("  2. A/B测试和实验")
        print("  3. 快速关闭有问题的功能")
        print("  4. 为不同用户群体提供不同功能")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print()

def main():
    """主函数 - 运行所有练习"""
    print("🎓 Superset 第1天学习实践")
    print("=" * 60)
    print("今日重点：Flask应用架构深入理解\n")
    
    try:
        practice_1_config_loading()
        practice_2_app_factory()
        practice_3_extensions_analysis()
        practice_4_initialization_flow()
        practice_5_feature_flags()
        
        print("🎉 第1天练习完成！")
        print("\n📝 总结要点：")
        print("1. ✅ 理解了Flask应用工厂模式的实现")
        print("2. ✅ 掌握了配置加载的优先级机制")
        print("3. ✅ 了解了全局对象的依赖注入模式")
        print("4. ✅ 熟悉了应用初始化的完整流程")
        print("5. ✅ 学习了功能开关的设计思想")
        
        print("\n🚀 明日预告：")
        print("- 深入学习数据模型层(models)")
        print("- 理解SQLAlchemy ORM的使用")
        print("- 掌握Database、Dashboard、Slice等核心模型")
        
    except Exception as e:
        print(f"❌ 练习过程中遇到错误: {e}")
        print("💡 提示：确保在Superset项目根目录下运行此脚本")

if __name__ == "__main__":
    main() 