#!/usr/bin/env python3
"""
手动启动Superset调试服务器
当VS Code调试失败时使用
"""

import os
import sys

def start_superset_debug():
    """手动启动Superset调试服务器"""
    print("🚀 手动启动Superset调试服务器")
    print("=" * 40)
    
    # 设置环境变量
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    os.environ['SUPERSET_CONFIG'] = 'superset_config'
    
    print("🔧 环境变量设置:")
    print(f"   FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    print(f"   FLASK_DEBUG: {os.environ.get('FLASK_DEBUG')}")
    print(f"   SUPERSET_CONFIG: {os.environ.get('SUPERSET_CONFIG')}")
    
    try:
        # 导入Superset
        from superset.app import create_app
        
        print("\n📦 创建Superset应用...")
        app = create_app()
        
        print("✅ 应用创建成功!")
        print("\n▶️ 启动开发服务器...")
        print("🌐 访问地址: http://localhost:8088")
        print("⚡ 按Ctrl+C停止服务器")
        print("-" * 40)
        
        # 启动开发服务器
        app.run(
            host='0.0.0.0',
            port=8088,
            debug=True,
            threaded=True,
            use_reloader=True,
            use_debugger=True
        )
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n🔍 可能的解决方案:")
        print("1. 检查数据库连接")
        print("2. 检查配置文件语法")
        print("3. 检查端口8088是否被占用")
        print("4. 重新安装依赖: pip install -e .")

if __name__ == "__main__":
    start_superset_debug() 