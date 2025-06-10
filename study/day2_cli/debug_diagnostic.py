#!/usr/bin/env python3
"""
Superset调试环境诊断脚本

用于快速诊断调试启动失败的原因
"""

import os
import sys
import subprocess
import traceback
from pathlib import Path

def check_python_environment():
    """检查Python环境"""
    print("🐍 检查Python环境")
    print("-" * 30)
    
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"工作目录: {os.getcwd()}")
    
    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 虚拟环境已激活")
    else:
        print("⚠️ 未检测到虚拟环境")
    
    print()

def check_superset_installation():
    """检查Superset安装"""
    print("📦 检查Superset安装")
    print("-" * 30)
    
    try:
        import superset
        print(f"✅ Superset已安装，版本: {superset.__version__ if hasattr(superset, '__version__') else 'unknown'}")
        print(f"✅ Superset路径: {superset.__file__}")
    except ImportError as e:
        print(f"❌ Superset未安装: {e}")
        print("💡 解决方案: pip install -e .")
        return False
    
    # 检查关键模块
    modules_to_check = [
        'superset.config',
        'superset.cli.main',
        'superset.models.core',
        'superset.extensions'
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
    
    print()
    return True

def check_configuration():
    """检查配置文件"""
    print("⚙️ 检查配置文件")
    print("-" * 30)
    
    config_files = [
        'superset_config.py',
        'debug_config.py'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file} 存在")
            
            # 尝试加载配置
            try:
                if config_file == 'superset_config.py':
                    import superset_config
                    print(f"✅ {config_file} 语法正确")
                elif config_file == 'debug_config.py':
                    import debug_config
                    print(f"✅ {config_file} 语法正确")
            except Exception as e:
                print(f"❌ {config_file} 语法错误: {e}")
                print(f"🔍 详细错误:\n{traceback.format_exc()}")
        else:
            print(f"⚠️ {config_file} 不存在")
    
    # 检查环境变量
    superset_config = os.environ.get('SUPERSET_CONFIG_PATH')
    if superset_config:
        print(f"🔧 SUPERSET_CONFIG_PATH: {superset_config}")
    else:
        print("⚠️ SUPERSET_CONFIG_PATH 未设置")
    
    print()

def check_database():
    """检查数据库配置"""
    print("🗄️ 检查数据库")
    print("-" * 30)
    
    try:
        # 设置配置环境变量
        os.environ['SUPERSET_CONFIG_PATH'] = 'debug_config'
        
        from superset.app import create_app
        from superset.extensions import db
        
        app = create_app()
        with app.app_context():
            # 测试数据库连接
            db.engine.execute("SELECT 1")
            print("✅ 数据库连接成功")
            
            # 检查数据库表
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ 数据库表数量: {len(tables)}")
            
            if len(tables) == 0:
                print("⚠️ 数据库表为空，需要运行初始化")
                print("💡 解决方案: superset db upgrade")
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        print("💡 可能的解决方案:")
        print("   1. 运行: superset db upgrade")
        print("   2. 检查数据库配置文件")
        print("   3. 确保数据库服务正在运行")
    
    print()

def check_dependencies():
    """检查关键依赖"""
    print("📚 检查关键依赖")
    print("-" * 30)
    
    critical_packages = [
        'flask',
        'sqlalchemy',
        'flask-appbuilder',
        'celery',
        'redis',
        'pandas',
        'numpy'
    ]
    
    for package in critical_packages:
        try:
            pkg = __import__(package)
            version = getattr(pkg, '__version__', 'unknown')
            print(f"✅ {package}: {version}")
        except ImportError:
            print(f"❌ {package}: 未安装")
    
    print()

def test_cli_command():
    """测试CLI命令"""
    print("🔧 测试CLI命令")
    print("-" * 30)
    
    try:
        # 测试superset命令是否可用
        result = subprocess.run([
            sys.executable, '-m', 'superset.cli.main', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ superset CLI命令可用")
        else:
            print(f"❌ superset CLI命令失败:")
            print(f"stderr: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠️ CLI命令超时")
    except Exception as e:
        print(f"❌ CLI测试失败: {e}")
    
    print()

def suggest_solutions():
    """提供解决方案"""
    print("💡 常见解决方案")
    print("-" * 30)
    
    solutions = [
        "1. 重新安装Superset: pip uninstall apache-superset && pip install -e .",
        "2. 初始化数据库: superset db upgrade",
        "3. 创建管理员用户: superset fab create-admin",
        "4. 初始化应用: superset init",
        "5. 检查配置文件语法错误",
        "6. 确保虚拟环境已激活",
        "7. 清理Python缓存: find . -name '*.pyc' -delete",
        "8. 重启VS Code和终端"
    ]
    
    for solution in solutions:
        print(solution)
    
    print()

def main():
    """主诊断函数"""
    print("🔍 Superset调试环境诊断")
    print("=" * 50)
    print()
    
    # 执行各项检查
    check_python_environment()
    superset_ok = check_superset_installation()
    
    if superset_ok:
        check_configuration()
        check_database()
        check_dependencies()
        test_cli_command()
    
    suggest_solutions()
    
    print("🎯 诊断完成！")
    print("请根据上述检查结果解决相应问题")

if __name__ == "__main__":
    main() 