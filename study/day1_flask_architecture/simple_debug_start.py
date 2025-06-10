#!/usr/bin/env python3
"""
简化的Superset调试启动脚本
专门用于VS Code调试，避免CLI模块的复杂性
"""

import os
import sys

# 设置环境变量
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'
os.environ['SUPERSET_CONFIG'] = 'superset_config'

def main():
    """启动Superset调试服务器"""
    print("🚀 启动Superset调试服务器...")
    print(f"Python路径: {sys.executable}")
    print(f"工作目录: {os.getcwd()}")
    print(f"配置文件: {os.environ.get('SUPERSET_CONFIG')}")
    
    try:
        # 导入并创建应用
        from superset.app import create_app
        
        print("📦 创建Superset应用...")
        app = create_app()
        
        print("✅ 应用创建成功!")
        print("🌐 服务器将在 http://localhost:8088 启动")
        print("🔍 调试模式已启用")
        print("=" * 50)
        
        # 启动Flask开发服务器
        app.run(
            host='0.0.0.0',
            port=8088,
            debug=True,
            threaded=True,
            use_reloader=False,  # 在调试模式下禁用reloader避免冲突
            use_debugger=False   # 使用VS Code调试器而不是Flask调试器
        )
        
    except KeyboardInterrupt:
        print("\n⚡ 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 