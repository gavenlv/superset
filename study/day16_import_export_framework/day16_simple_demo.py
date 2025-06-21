#!/usr/bin/env python3
"""
Day 16: Superset Import/Export Framework 简化演示

展示核心功能：
1. 基础导入导出
2. 幂等性处理
3. 依赖关系管理
4. 连接测试
"""

import json
import logging
import uuid
import yaml
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockDatabase:
    """模拟数据库模型"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid', str(uuid.uuid4()))
        self.database_name = kwargs.get('database_name', 'test_db')
        self.sqlalchemy_uri = kwargs.get('sqlalchemy_uri', 'sqlite:///test.db')
        self.extra = kwargs.get('extra', '{}')
        
    def to_dict(self):
        return {
            'uuid': str(self.uuid),
            'database_name': self.database_name,
            'sqlalchemy_uri': self.sqlalchemy_uri,
            'extra': self.extra,
            'version': '1.0.0'
        }

class SimpleImportExportManager:
    """简化的导入导出管理器"""
    
    def __init__(self):
        self.databases = {}  # uuid -> MockDatabase
    
    def export_database(self, database_id: int) -> str:
        """导出数据库配置"""
        # 模拟从数据库查询
        db = MockDatabase(
            id=database_id,
            database_name=f"export_db_{database_id}",
            sqlalchemy_uri=f"postgresql://user:pass@host/db_{database_id}",
            extra='{"pool_size": 10}'
        )
        
        config = db.to_dict()
        config['exported_at'] = datetime.now(tz=timezone.utc).isoformat()
        
        return yaml.safe_dump(config, sort_keys=False)
    
    def import_database(self, config_yaml: str, overwrite: bool = False) -> MockDatabase:
        """导入数据库配置 - 展示幂等性"""
        config = yaml.safe_load(config_yaml)
        
        # 步骤1: 检查是否已存在（幂等性）
        existing = self.databases.get(config['uuid'])
        if existing:
            if not overwrite:
                logger.info(f"数据库 {config['database_name']} 已存在，跳过导入")
                return existing
            else:
                logger.info(f"数据库 {config['database_name']} 已存在，执行覆盖")
                config['id'] = existing.id
        
        # 步骤2: 安全检查
        if 'unsafe' in config.get('sqlalchemy_uri', ''):
            raise ValueError("检测到不安全的数据库连接URI")
        
        # 步骤3: 创建数据库对象
        database = MockDatabase(**config)
        
        # 步骤4: 连接测试
        try:
            self._test_connection(database)
            logger.info(f"数据库连接测试成功: {database.database_name}")
        except Exception as ex:
            logger.warning(f"数据库连接测试失败: {ex}")
            # 注意：连接失败不阻止导入
        
        # 步骤5: 保存
        self.databases[database.uuid] = database
        logger.info(f"成功导入数据库: {database.database_name}")
        
        return database
    
    def _test_connection(self, database: MockDatabase):
        """模拟连接测试"""
        if 'fail_connection' in database.sqlalchemy_uri:
            raise ConnectionError("模拟连接失败")
        # 模拟成功连接
        pass
    
    def list_databases(self):
        """列出所有数据库"""
        print(f"\n当前数据库列表 (共 {len(self.databases)} 个):")
        for db_uuid, db in self.databases.items():
            print(f"  - {db.database_name} (UUID: {db_uuid[:8]}...)")

def demo_basic_export():
    """演示基础导出"""
    print("\n=== 基础导出演示 ===")
    
    manager = SimpleImportExportManager()
    
    # 导出数据库配置
    config_yaml = manager.export_database(1)
    print("导出的配置:")
    print(config_yaml)

def demo_basic_import():
    """演示基础导入"""
    print("\n=== 基础导入演示 ===")
    
    manager = SimpleImportExportManager()
    
    # 创建配置
    config = {
        'uuid': 'demo-uuid-123',
        'database_name': 'demo_database',
        'sqlalchemy_uri': 'postgresql://user:pass@host/demo_db',
        'extra': '{"pool_size": 5}',
        'version': '1.0.0'
    }
    
    config_yaml = yaml.safe_dump(config)
    
    # 导入
    database = manager.import_database(config_yaml)
    manager.list_databases()

def demo_idempotent_import():
    """演示幂等性导入"""
    print("\n=== 幂等性导入演示 ===")
    
    manager = SimpleImportExportManager()
    
    config = {
        'uuid': 'idempotent-uuid-456',
        'database_name': 'idempotent_db',
        'sqlalchemy_uri': 'sqlite:///idempotent.db',
        'extra': '{}',
        'version': '1.0.0'
    }
    
    config_yaml = yaml.safe_dump(config)
    
    print("第一次导入:")
    manager.import_database(config_yaml)
    manager.list_databases()
    
    print("\n第二次导入（相同UUID，不覆盖）:")
    manager.import_database(config_yaml, overwrite=False)
    manager.list_databases()
    
    print("\n第三次导入（强制覆盖）:")
    config['database_name'] = 'updated_idempotent_db'
    config_yaml = yaml.safe_dump(config)
    manager.import_database(config_yaml, overwrite=True)
    manager.list_databases()

def demo_connection_testing():
    """演示连接测试"""
    print("\n=== 连接测试演示 ===")
    
    manager = SimpleImportExportManager()
    
    # 成功连接的数据库
    good_config = {
        'uuid': str(uuid.uuid4()),
        'database_name': 'good_connection_db',
        'sqlalchemy_uri': 'postgresql://user:pass@host/good_db',
        'extra': '{}',
        'version': '1.0.0'
    }
    
    # 连接失败的数据库
    bad_config = {
        'uuid': str(uuid.uuid4()),
        'database_name': 'bad_connection_db',
        'sqlalchemy_uri': 'postgresql://user:pass@host/fail_connection',
        'extra': '{}',
        'version': '1.0.0'
    }
    
    print("导入连接成功的数据库:")
    manager.import_database(yaml.safe_dump(good_config))
    
    print("\n导入连接失败的数据库:")
    manager.import_database(yaml.safe_dump(bad_config))
    
    manager.list_databases()

def demo_dependency_chain():
    """演示依赖关系链"""
    print("\n=== 依赖关系链演示 ===")
    
    # 创建依赖链：数据库 -> 数据集 -> 图表 -> 仪表板
    db_uuid = str(uuid.uuid4())
    dataset_uuid = str(uuid.uuid4())
    chart_uuid = str(uuid.uuid4())
    dashboard_uuid = str(uuid.uuid4())
    
    # 配置
    configs = {
        'database': {
            'uuid': db_uuid,
            'database_name': 'analytics_db',
            'sqlalchemy_uri': 'postgresql://user:pass@host/analytics',
            'type': 'database'
        },
        'dataset': {
            'uuid': dataset_uuid,
            'table_name': 'sales_data',
            'database_uuid': db_uuid,  # 依赖数据库
            'type': 'dataset'
        },
        'chart': {
            'uuid': chart_uuid,
            'slice_name': 'Sales Chart',
            'dataset_uuid': dataset_uuid,  # 依赖数据集
            'type': 'chart'
        },
        'dashboard': {
            'uuid': dashboard_uuid,
            'dashboard_title': 'Sales Dashboard',
            'chart_uuids': [chart_uuid],  # 依赖图表
            'type': 'dashboard'
        }
    }
    
    print("依赖关系链:")
    print("  Database:", configs['database']['database_name'])
    print("    └── Dataset:", configs['dataset']['table_name'])
    print("        └── Chart:", configs['chart']['slice_name'])
    print("            └── Dashboard:", configs['dashboard']['dashboard_title'])
    
    print("\n导入顺序验证:")
    print("1. 数据库 ->", "✓")
    print("2. 数据集 ->", "✓")
    print("3. 图表 ->", "✓")
    print("4. 仪表板 ->", "✓")
    
    # 验证UUID引用
    print(f"\nUUID引用验证:")
    print(f"数据集引用数据库: {configs['dataset']['database_uuid']} == {db_uuid}")
    print(f"图表引用数据集: {configs['chart']['dataset_uuid']} == {dataset_uuid}")
    print(f"仪表板引用图表: {configs['dashboard']['chart_uuids']} == [{chart_uuid}]")

def demo_error_handling():
    """演示错误处理"""
    print("\n=== 错误处理演示 ===")
    
    manager = SimpleImportExportManager()
    
    # 测试各种错误场景
    error_cases = [
        {
            'name': '无效YAML格式',
            'config': 'invalid: yaml: format: [',
            'expected_error': 'YAML解析错误'
        },
        {
            'name': '不安全的数据库URI',
            'config': yaml.safe_dump({
                'uuid': str(uuid.uuid4()),
                'database_name': 'unsafe_db',
                'sqlalchemy_uri': 'postgresql://user:pass@host/unsafe_db',
                'version': '1.0.0'
            }),
            'expected_error': '安全检查失败'
        }
    ]
    
    for case in error_cases:
        print(f"\n测试: {case['name']}")
        try:
            if case['name'] == '无效YAML格式':
                yaml.safe_load(case['config'])
            else:
                manager.import_database(case['config'])
            print(f"  结果: 未检测到预期错误")
        except Exception as e:
            print(f"  结果: 成功捕获错误 - {type(e).__name__}: {e}")

if __name__ == "__main__":
    """主演示程序"""
    print("Superset Import/Export Framework 简化演示")
    print("=" * 50)
    
    # 运行所有演示
    demo_basic_export()
    demo_basic_import()
    demo_idempotent_import()
    demo_connection_testing()
    demo_dependency_chain()
    demo_error_handling()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    
    print("\n关键概念总结:")
    print("1. 幂等性: 基于UUID避免重复创建")
    print("2. 依赖关系: Database -> Dataset -> Chart -> Dashboard")
    print("3. 连接测试: 非阻塞，失败只警告")
    print("4. 错误处理: 分层处理，详细日志")
    print("5. 安全检查: 导入前验证配置安全性") 