#!/usr/bin/env python3
"""
测试PostgreSQL数据库连接和Superset表状态
"""

import os
import psycopg2
from urllib.parse import urlparse

# 从环境变量或配置获取数据库URI
SQLALCHEMY_DATABASE_URI = os.environ.get("SUPERSET_DATABASE_URI", "postgresql+psycopg2://postgres:root@localhost:25011/superset_db")

def parse_database_url(url):
    """解析数据库URL"""
    # 移除 postgresql+psycopg2:// 前缀，只保留 postgresql://
    if url.startswith('postgresql+psycopg2://'):
        url = url.replace('postgresql+psycopg2://', 'postgresql://')
    
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
        'username': parsed.username,
        'password': parsed.password
    }

def test_database_connection():
    """测试数据库连接"""
    print("🔗 测试PostgreSQL数据库连接...")
    print(f"数据库URI: {SQLALCHEMY_DATABASE_URI}")
    
    try:
        # 解析数据库URL
        db_config = parse_database_url(SQLALCHEMY_DATABASE_URI)
        print(f"数据库主机: {db_config['host']}:{db_config['port']}")
        print(f"数据库名称: {db_config['database']}")
        print(f"用户名: {db_config['username']}")
        
        # 尝试连接
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['username'],
            password=db_config['password']
        )
        
        print("✅ 数据库连接成功!")
        
        # 检查Superset表是否存在
        cursor = conn.cursor()
        
        # 查询所有表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%superset%' OR table_name IN ('ab_user', 'ab_role', 'dbs')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ 找到 {len(tables)} 个Superset相关表:")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("❌ 没有找到Superset表，需要初始化数据库")
            print("💡 请运行: python -m superset.cli.main db upgrade")
        
        # 检查用户表
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'ab_user'")
        user_table_exists = cursor.fetchone()[0] > 0
        
        if user_table_exists:
            cursor.execute("SELECT COUNT(*) FROM ab_user")
            user_count = cursor.fetchone()[0]
            print(f"📊 用户表中有 {user_count} 个用户")
            
            if user_count == 0:
                print("⚠️ 没有管理员用户，需要创建")
                print("💡 请运行: python -m superset.cli.main fab create-admin")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ 数据库连接失败: {e}")
        print("💡 请检查:")
        print("   1. PostgreSQL服务是否运行")
        print("   2. 数据库配置是否正确")
        print("   3. 网络连接是否正常")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    print("🔍 Superset PostgreSQL数据库检查")
    print("=" * 40)
    
    success = test_database_connection()
    
    if success:
        print("\n🎯 数据库连接正常！")
        print("如果调试仍然无法启动，可能的原因:")
        print("1. 数据库表未初始化")
        print("2. 没有管理员用户")
        print("3. 其他配置问题")
    else:
        print("\n❌ 请先解决数据库连接问题")

if __name__ == "__main__":
    main() 