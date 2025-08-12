#!/usr/bin/env python3
"""
诊断 Superset 环境变量和配置问题
"""

import os
import sys
from dotenv import load_dotenv

def diagnose_superset():
    print("=== Superset 环境诊断 ===")
    
    # 1. 检查 .env 文件
    print("\n1. 检查 .env 文件:")
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"  ✓ 找到 {env_file} 文件")
        with open(env_file, 'r') as f:
            content = f.read()
            print(f"  文件大小: {len(content)} 字符")
            lines = content.split('\n')
            print(f"  行数: {len(lines)}")
            for i, line in enumerate(lines, 1):
                if line.strip() and not line.strip().startswith('#'):
                    print(f"  第{i}行: {line.strip()}")
    else:
        print(f"  ✗ 未找到 {env_file} 文件")
    
    # 2. 加载环境变量
    print("\n2. 加载环境变量:")
    load_dotenv()
    print("  ✓ 已调用 load_dotenv()")
    
    # 3. 检查关键环境变量
    print("\n3. 环境变量状态:")
    env_vars = {
        "SUPERSET_DATABASE_URI": "数据库连接字符串",
        "SQLALCHEMY_DATABASE_URI": "SQLAlchemy 数据库连接",
        "SECRET_KEY": "密钥",
        "SUPERSET_SECRET_KEY": "Superset 密钥",
        "REDIS_HOST": "Redis 主机",
        "REDIS_PORT": "Redis 端口",
        "FLASK_APP": "Flask 应用",
        "FLASK_DEBUG": "Flask 调试模式"
    }
    
    for var, desc in env_vars.items():
        value = os.environ.get(var)
        if value:
            if "SECRET" in var or "KEY" in var:
                print(f"  {var} ({desc}): ✓ 已设置")
            else:
                print(f"  {var} ({desc}): {value}")
        else:
            print(f"  {var} ({desc}): ✗ 未设置")
    
    # 4. 检查 Python 路径
    print("\n4. Python 路径:")
    for path in sys.path:
        print(f"  {path}")
    
    # 5. 检查 Superset 配置
    print("\n5. 尝试导入 Superset 配置:")
    try:
        import superset_config
        print("  ✓ Superset 配置导入成功")
        
        # 检查关键配置
        configs = [
            'SQLALCHEMY_DATABASE_URI',
            'SECRET_KEY',
            'REDIS_HOST',
            'REDIS_PORT',
            'CACHE_CONFIG'
        ]
        
        for config in configs:
            if hasattr(superset_config, config):
                value = getattr(superset_config, config)
                if isinstance(value, str) and ("SECRET" in config or "KEY" in config):
                    print(f"  {config}: ✓ 已设置")
                else:
                    print(f"  {config}: {value}")
            else:
                print(f"  {config}: ✗ 未定义")
                
    except Exception as e:
        print(f"  ✗ Superset 配置导入失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 诊断完成 ===")

if __name__ == "__main__":
    diagnose_superset() 