#!/usr/bin/env python3
"""
增强的数据库测试脚本
检查数据库初始化前后的状态
"""

import os
import sys
from pathlib import Path

# 设置配置路径
config_path = Path("D:/workspace/superset-github/superset/superset_config.py")
os.environ['SUPERSET_CONFIG_PATH'] = str(config_path)

def test_database_connection():
    """测试数据库连接"""
    try:
        import psycopg2
        
        # 从配置文件读取数据库信息
        connection_params = {
            'host': 'localhost',
            'port': 25011,
            'database': 'superset_db',
            'user': 'superset_user',
            'password': 'superset_password'
        }
        
        print("🔍 测试 PostgreSQL 连接...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # 检查连接
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ 数据库连接成功")
        print(f"PostgreSQL 版本: {version}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False

def get_table_info():
    """获取数据库表信息"""
    try:
        from superset.app import create_app
        from superset.extensions import db
        
        print("\n🔍 检查数据库表结构...")
        
        app = create_app()
        with app.app_context():
            engine = db.get_engine()
            with engine.connect() as conn:
                # 获取所有表
                result = conn.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = [row[0] for row in result]
                
                print(f"📊 总表数量: {len(tables)}")
                
                # 关键表检查
                key_tables = {
                    'ab_user': '用户表',
                    'ab_role': '角色表', 
                    'dashboards': '仪表板',
                    'slices': '图表',
                    'tables': '数据表元数据',
                    'datasources': '数据源',
                    'clusters': '集群配置',
                    'dbs': '数据库连接',
                    'query': '查询记录',
                    'logs': '日志记录'
                }
                
                print("\n📋 关键表状态:")
                missing_tables = []
                existing_tables = []
                
                for table, desc in key_tables.items():
                    if table in tables:
                        existing_tables.append(table)
                        print(f"  ✅ {table:<15} - {desc}")
                    else:
                        missing_tables.append(table)
                        print(f"  ❌ {table:<15} - {desc}")
                
                # 显示所有表
                print(f"\n📝 所有表列表 ({len(tables)} 个):")
                for i, table in enumerate(tables, 1):
                    print(f"  {i:2d}. {table}")
                
                # 数据库状态判断
                print(f"\n📈 数据库状态分析:")
                if len(tables) < 10:
                    print("  ⚠️  数据库架构不完整 - 需要运行 'superset db upgrade'")
                    print("  📝 建议执行初始化脚本")
                    return False
                elif missing_tables:
                    print(f"  ⚠️  部分关键表缺失: {', '.join(missing_tables)}")
                    print("  📝 可能需要重新初始化")
                    return False
                else:
                    print("  ✅ 数据库架构完整")
                    return True
                    
    except Exception as e:
        print(f"❌ 检查数据库表失败: {str(e)}")
        print("💡 这通常意味着需要先运行数据库初始化")
        return False

def check_superset_config():
    """检查 Superset 配置"""
    print("\n🔧 检查 Superset 配置...")
    
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return False
        
    print(f"✅ 配置文件存在: {config_path}")
    
    # 检查环境变量
    env_config = os.environ.get('SUPERSET_CONFIG_PATH')
    if env_config:
        print(f"✅ 环境变量 SUPERSET_CONFIG_PATH: {env_config}")
    else:
        print("⚠️  环境变量 SUPERSET_CONFIG_PATH 未设置")
        
    return True

def main():
    """主函数"""
    print("🚀 Superset 数据库状态检查")
    print("=" * 50)
    
    # 1. 检查配置
    if not check_superset_config():
        return
    
    # 2. 测试连接
    if not test_database_connection():
        print("\n❌ 数据库连接失败，请检查:")
        print("  1. PostgreSQL 服务是否运行")
        print("  2. 端口 25011 是否可访问")
        print("  3. 用户名密码是否正确")
        return
    
    # 3. 检查表结构
    is_initialized = get_table_info()
    
    print(f"\n{'='*50}")
    
    if is_initialized:
        print("🎉 数据库已完全初始化!")
        print("✨ 现在可以启动 Superset 调试:")
        print("   1. 在 VS Code 中按 F5")
        print("   2. 或运行: superset run -p 8088")
        print("   3. 访问: http://localhost:8088")
    else:
        print("⚠️  数据库需要初始化!")
        print("🔧 执行以下步骤:")
        print("   1. 运行: quick_db_init.bat")
        print("   2. 或手动执行:")
        print("      - superset db upgrade")
        print("      - superset fab create-admin")
        print("      - superset init")

if __name__ == "__main__":
    main() 