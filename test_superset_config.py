#!/usr/bin/env python3
"""
测试 Superset 配置加载的脚本
"""

import os
import sys
from dotenv import load_dotenv

def test_superset_config():
    print("=== Superset 配置测试 ===")
    
    # 加载环境变量
    load_dotenv()
    
    # 模拟导入 superset_config
    try:
        # 添加当前目录到 Python 路径
        sys.path.insert(0, os.getcwd())
        
        # 导入配置
        import superset_config
        
        print("✓ Superset 配置加载成功")
        
        # 检查关键配置
        print(f"\n配置检查:")
        print(f"  SQLALCHEMY_DATABASE_URI: {getattr(superset_config, 'SQLALCHEMY_DATABASE_URI', 'Not set')}")
        print(f"  SECRET_KEY: {'Set' if getattr(superset_config, 'SECRET_KEY', None) else 'Not set'}")
        print(f"  REDIS_HOST: {getattr(superset_config, 'REDIS_HOST', 'Not set')}")
        print(f"  REDIS_PORT: {getattr(superset_config, 'REDIS_PORT', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Superset 配置加载失败: {e}")
        return False

if __name__ == "__main__":
    test_superset_config() 