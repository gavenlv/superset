#!/usr/bin/env python3
"""
测试环境变量加载的脚本
"""

import os
from dotenv import load_dotenv

def test_env_loading():
    print("=== 环境变量加载测试 ===")
    
    # 检查 .env 文件是否存在
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✓ 找到 {env_file} 文件")
    else:
        print(f"✗ 未找到 {env_file} 文件")
        print("请创建 .env 文件并添加你的配置")
        return False
    
    # 加载环境变量
    print("\n正在加载环境变量...")
    load_dotenv()
    
    # 检查关键环境变量
    env_vars = [
        "SQLALCHEMY_DATABASE_URI",
        "SUPERSET_DATABASE_URI", 
        "SECRET_KEY",
        "REDIS_HOST",
        "REDIS_PORT"
    ]
    
    print("\n环境变量状态:")
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # 对于敏感信息，只显示是否设置
            if "SECRET" in var or "KEY" in var:
                print(f"  {var}: ✓ 已设置")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: ✗ 未设置")
    
    return True

if __name__ == "__main__":
    test_env_loading() 