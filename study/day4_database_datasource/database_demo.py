#!/usr/bin/env python3
"""
数据库连接与数据源管理演示脚本
Day 4 - 数据层架构学习辅助工具

运行这个脚本来理解 Superset 数据库连接和查询优化的核心概念
"""
import time
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional


class DatabaseConnection:
    """模拟数据库连接"""
    
    def __init__(self, name: str, uri: str):
        self.name = name
        self.uri = uri
        self.engine_type = uri.split(':')[0]
        self.cache_timeout = 300
        
        # 模拟示例数据
        self.sample_data = [
            {'product': 'Laptop', 'category': 'Electronics', 'sales': 1200, 'region': 'North'},
            {'product': 'Mouse', 'category': 'Electronics', 'sales': 25, 'region': 'South'},
            {'product': 'Desk', 'category': 'Furniture', 'sales': 250, 'region': 'East'},
            {'product': 'Chair', 'category': 'Furniture', 'sales': 150, 'region': 'West'},
        ]
    
    def test_connection(self) -> bool:
        """测试连接"""
        time.sleep(0.1)  # 模拟连接延迟
        return True
    
    def execute_query(self, sql: str) -> List[Dict]:
        """执行查询"""
        time.sleep(0.2)  # 模拟查询延迟
        if 'GROUP BY' in sql.upper():
            # 模拟聚合查询
            return [
                {'category': 'Electronics', 'total_sales': 1225, 'count': 2},
                {'category': 'Furniture', 'total_sales': 400, 'count': 2}
            ]
        return self.sample_data


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.cache = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            self.hits += 1
            print(f"✅ 缓存命中: {key[:20]}...")
            return self.cache[key]
        else:
            self.misses += 1
            print(f"❌ 缓存未命中: {key[:20]}...")
            return None
    
    def set(self, key: str, value: Any, timeout: int = 300):
        """设置缓存"""
        self.cache[key] = value
        print(f"💾 缓存已保存: {key[:20]}... (超时: {timeout}秒)")
    
    def generate_key(self, query: Dict) -> str:
        """生成缓存键"""
        query_str = json.dumps(query, sort_keys=True)
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 1)
        }


def demo_database_connections():
    """演示数据库连接"""
    print("=" * 50)
    print("🔌 数据库连接演示")
    print("=" * 50)
    
    # 创建不同类型的数据库连接
    databases = [
        DatabaseConnection("SQLite DB", "sqlite:///example.db"),
        DatabaseConnection("PostgreSQL", "postgresql://user:pass@localhost/db"),
        DatabaseConnection("MySQL", "mysql://user:pass@localhost/db"),
    ]
    
    for db in databases:
        print(f"\n数据库: {db.name}")
        print(f"  引擎: {db.engine_type}")
        print(f"  URI: {db.uri}")
        print(f"  连接测试: {'✅ 成功' if db.test_connection() else '❌ 失败'}")
    
    return databases


def demo_query_execution():
    """演示查询执行"""
    print("\n" + "=" * 50)
    print("🚀 查询执行演示")
    print("=" * 50)
    
    db = DatabaseConnection("Demo DB", "sqlite:///demo.db")
    cache = CacheManager()
    
    # 测试查询
    queries = [
        {
            'name': '基础查询',
            'sql': 'SELECT * FROM sales_data',
            'params': {'table': 'sales_data', 'columns': ['*']}
        },
        {
            'name': '聚合查询',
            'sql': 'SELECT category, SUM(sales) FROM sales_data GROUP BY category',
            'params': {'table': 'sales_data', 'columns': ['category'], 'metrics': ['sum_sales']}
        }
    ]
    
    for query in queries:
        print(f"\n📊 {query['name']}")
        print(f"SQL: {query['sql']}")
        
        # 生成缓存键
        cache_key = cache.generate_key(query['params'])
        
        # 第一次执行
        print("第一次执行:")
        start_time = time.time()
        cached_result = cache.get(cache_key)
        
        if not cached_result:
            result = db.execute_query(query['sql'])
            cache.set(cache_key, result)
            print(f"查询时间: {time.time() - start_time:.3f}秒")
            print(f"结果: {len(result)} 行数据")
        
        # 第二次执行（应该从缓存获取）
        print("第二次执行:")
        start_time = time.time()
        cached_result = cache.get(cache_key)
        print(f"查询时间: {time.time() - start_time:.3f}秒")
    
    # 显示缓存统计
    print(f"\n📈 缓存统计: {cache.get_stats()}")


def demo_security_permissions():
    """演示安全权限"""
    print("\n" + "=" * 50)
    print("🔒 安全权限演示")
    print("=" * 50)
    
    # 模拟用户权限
    users = [
        {'name': 'admin', 'role': 'Admin', 'databases': ['all'], 'filters': []},
        {'name': 'analyst', 'role': 'Alpha', 'databases': ['sqlite', 'postgres'], 'filters': []},
        {'name': 'sales_user', 'role': 'Gamma', 'databases': ['sqlite'], 'filters': ['region = North']},
    ]
    
    print("用户权限配置:")
    print("-" * 60)
    print(f"{'用户':<12} {'角色':<8} {'数据库访问':<15} {'行级过滤'}")
    print("-" * 60)
    
    for user in users:
        db_access = ', '.join(user['databases'])
        filters = ', '.join(user['filters']) if user['filters'] else '无'
        print(f"{user['name']:<12} {user['role']:<8} {db_access:<15} {filters}")


def demo_performance_tips():
    """演示性能优化技巧"""
    print("\n" + "=" * 50)
    print("⚡ 性能优化技巧")
    print("=" * 50)
    
    tips = [
        {
            'title': '使用 LIMIT 限制结果',
            'bad': 'SELECT * FROM large_table',
            'good': 'SELECT * FROM large_table LIMIT 1000'
        },
        {
            'title': '在数据库层面聚合',
            'bad': '获取所有数据后在应用层聚合',
            'good': 'SELECT category, SUM(amount) GROUP BY category'
        },
        {
            'title': '使用合适的缓存时间',
            'bad': '所有查询都用相同缓存时间',
            'good': '实时数据60秒，历史数据1小时'
        }
    ]
    
    for i, tip in enumerate(tips, 1):
        print(f"\n{i}. {tip['title']}")
        print(f"   ❌ 不好: {tip['bad']}")
        print(f"   ✅ 推荐: {tip['good']}")


def main():
    """主函数"""
    print("🎓 Superset 数据库连接与数据源管理演示")
    print("Day 4 学习辅助工具\n")
    
    # 运行演示
    demo_database_connections()
    demo_query_execution()
    demo_security_permissions()
    demo_performance_tips()
    
    print("\n" + "=" * 50)
    print("🎉 演示完成！")
    print("建议结合实际 Superset 环境进行练习")
    print("=" * 50)


if __name__ == "__main__":
    main() 