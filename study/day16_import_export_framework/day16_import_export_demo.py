#!/usr/bin/env python3
"""
Day 16: Superset Import/Export Framework 实战演示

本演示展示如何：
1. 使用导入导出API
2. 实现自定义导入导出命令
3. 处理依赖关系和幂等性
4. 二次开发导入导出功能
"""

import json
import logging
import uuid
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator, Tuple, Callable
from zipfile import ZipFile
from io import BytesIO
import tempfile
import os

# 模拟Superset的导入导出框架
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockModel:
    """模拟Superset模型基类"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid', str(uuid.uuid4()))
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def export_to_dict(self, recursive=False, include_parent_ref=False, 
                      include_defaults=True, export_uuids=True):
        """模拟导出到字典"""
        result = self.to_dict()
        if export_uuids and hasattr(self, 'uuid'):
            result['uuid'] = str(self.uuid)
        return result

class MockDatabase(MockModel):
    """模拟数据库模型"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.database_name = kwargs.get('database_name', 'test_db')
        self.sqlalchemy_uri = kwargs.get('sqlalchemy_uri', 'sqlite:///test.db')
        self.extra = kwargs.get('extra', '{}')
        self.allow_file_upload = kwargs.get('allow_file_upload', False)

class MockDataset(MockModel):
    """模拟数据集模型"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.table_name = kwargs.get('table_name', 'test_table')
        self.database_uuid = kwargs.get('database_uuid')
        self.database_id = kwargs.get('database_id')
        self.schema = kwargs.get('schema', 'public')
        self.sql = kwargs.get('sql', '')

class MockChart(MockModel):
    """模拟图表模型"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.slice_name = kwargs.get('slice_name', 'test_chart')
        self.dataset_uuid = kwargs.get('dataset_uuid')
        self.viz_type = kwargs.get('viz_type', 'table')
        self.params = kwargs.get('params', '{}')

class MockDashboard(MockModel):
    """模拟仪表板模型"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dashboard_title = kwargs.get('dashboard_title', 'test_dashboard')
        self.position_json = kwargs.get('position_json', '{}')
        self.json_metadata = kwargs.get('json_metadata', '{}')
        self.slices = kwargs.get('slices', [])

# ==================== 基础导入导出框架 ====================

class BaseExportCommand:
    """基础导出命令"""
    
    EXPORT_VERSION = "1.0.0"
    
    def __init__(self, model_ids: List[int], export_related: bool = True):
        self.model_ids = model_ids
        self.export_related = export_related
        self._models: List[MockModel] = []
    
    def validate(self):
        """验证模型存在性"""
        # 模拟从数据库查找模型
        self._models = [self._get_mock_model(id_) for id_ in self.model_ids]
        if len(self._models) != len(self.model_ids):
            raise ValueError("Some models not found")
    
    def _get_mock_model(self, model_id: int) -> MockModel:
        """获取模拟模型 - 子类需要实现"""
        raise NotImplementedError
    
    def _file_name(self, model: MockModel) -> str:
        """生成文件名 - 子类需要实现"""
        raise NotImplementedError
    
    def _file_content(self, model: MockModel) -> str:
        """生成文件内容 - 子类需要实现"""
        raise NotImplementedError
    
    def _export_related(self, model: MockModel) -> Iterator[Tuple[str, Callable[[], str]]]:
        """导出相关资源 - 子类可以覆盖"""
        return iter([])
    
    def run(self) -> Iterator[Tuple[str, Callable[[], str]]]:
        """执行导出"""
        self.validate()
        
        # 生成元数据文件
        metadata = {
            "version": self.EXPORT_VERSION,
            "type": self.__class__.__name__.replace("Export", "").replace("Command", ""),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        yield "metadata.yaml", lambda: yaml.safe_dump(metadata, sort_keys=False)
        
        # 导出每个模型
        seen = {"metadata.yaml"}
        for model in self._models:
            # 导出主模型
            file_name = self._file_name(model)
            if file_name not in seen:
                yield file_name, lambda m=model: self._file_content(m)
                seen.add(file_name)
            
            # 导出相关资源
            if self.export_related:
                for related_file, related_content in self._export_related(model):
                    if related_file not in seen:
                        yield related_file, related_content
                        seen.add(related_file)

class DatabaseExportCommand(BaseExportCommand):
    """数据库导出命令"""
    
    def _get_mock_model(self, model_id: int) -> MockDatabase:
        # 模拟数据库查询
        return MockDatabase(
            id=model_id,
            database_name=f"database_{model_id}",
            sqlalchemy_uri=f"postgresql://user:pass@host/db_{model_id}",
            extra='{"engine_params": {"pool_size": 10}}',
            allow_file_upload=True
        )
    
    def _file_name(self, model: MockDatabase) -> str:
        safe_name = model.database_name.replace(" ", "_").replace("/", "_")
        return f"databases/{safe_name}.yaml"
    
    def _file_content(self, model: MockDatabase) -> str:
        data = model.export_to_dict()
        # 处理特殊字段
        if data.get('extra'):
            try:
                data['extra'] = json.loads(data['extra'])
            except json.JSONDecodeError:
                data['extra'] = {}
        
        data['version'] = self.EXPORT_VERSION
        return yaml.safe_dump(data, sort_keys=False)

class DatasetExportCommand(BaseExportCommand):
    """数据集导出命令"""
    
    def _get_mock_model(self, model_id: int) -> MockDataset:
        return MockDataset(
            id=model_id,
            table_name=f"table_{model_id}",
            database_uuid=str(uuid.uuid4()),
            schema="public",
            sql=f"SELECT * FROM table_{model_id}"
        )
    
    def _file_name(self, model: MockDataset) -> str:
        safe_name = model.table_name.replace(" ", "_").replace("/", "_")
        return f"datasets/{safe_name}.yaml"
    
    def _file_content(self, model: MockDataset) -> str:
        data = model.export_to_dict()
        data['version'] = self.EXPORT_VERSION
        return yaml.safe_dump(data, sort_keys=False)
    
    def _export_related(self, model: MockDataset) -> Iterator[Tuple[str, Callable[[], str]]]:
        """导出相关数据库"""
        if model.database_uuid and self.export_related:
            # 模拟导出关联的数据库
            db_export = DatabaseExportCommand([1])  # 假设数据库ID为1
            yield from db_export.run()

class ChartExportCommand(BaseExportCommand):
    """图表导出命令"""
    
    def _get_mock_model(self, model_id: int) -> MockChart:
        return MockChart(
            id=model_id,
            slice_name=f"chart_{model_id}",
            dataset_uuid=str(uuid.uuid4()),
            viz_type="bar",
            params='{"metric": "count", "groupby": ["category"]}'
        )
    
    def _file_name(self, model: MockChart) -> str:
        safe_name = model.slice_name.replace(" ", "_").replace("/", "_")
        return f"charts/{safe_name}.yaml"
    
    def _file_content(self, model: MockChart) -> str:
        data = model.export_to_dict()
        # 处理参数
        if data.get('params'):
            try:
                data['params'] = json.loads(data['params'])
            except json.JSONDecodeError:
                data['params'] = {}
        
        data['version'] = self.EXPORT_VERSION
        return yaml.safe_dump(data, sort_keys=False)
    
    def _export_related(self, model: MockChart) -> Iterator[Tuple[str, Callable[[], str]]]:
        """导出相关数据集"""
        if model.dataset_uuid and self.export_related:
            dataset_export = DatasetExportCommand([1])  # 假设数据集ID为1
            yield from dataset_export.run()

class DashboardExportCommand(BaseExportCommand):
    """仪表板导出命令"""
    
    def _get_mock_model(self, model_id: int) -> MockDashboard:
        # 创建模拟的仪表板位置配置
        position = {
            "DASHBOARD_VERSION_KEY": "v2",
            "GRID_ID": {
                "type": "GRID",
                "id": "GRID_ID",
                "children": ["CHART-1", "CHART-2"]
            },
            "CHART-1": {
                "type": "CHART",
                "id": "CHART-1",
                "meta": {
                    "width": 6,
                    "height": 4,
                    "chartId": 101,
                    "uuid": str(uuid.uuid4())
                }
            },
            "CHART-2": {
                "type": "CHART", 
                "id": "CHART-2",
                "meta": {
                    "width": 6,
                    "height": 4,
                    "chartId": 102,
                    "uuid": str(uuid.uuid4())
                }
            }
        }
        
        return MockDashboard(
            id=model_id,
            dashboard_title=f"dashboard_{model_id}",
            position_json=json.dumps(position),
            json_metadata='{"filter_scopes": {}, "native_filter_configuration": []}',
            slices=[101, 102]  # 关联的图表ID
        )
    
    def _file_name(self, model: MockDashboard) -> str:
        safe_name = model.dashboard_title.replace(" ", "_").replace("/", "_")
        return f"dashboards/{safe_name}.yaml"
    
    def _file_content(self, model: MockDashboard) -> str:
        data = model.export_to_dict()
        
        # 处理JSON字段
        json_keys = {"position_json": "position", "json_metadata": "metadata"}
        for key, new_name in json_keys.items():
            value = data.pop(key, None)
            if value:
                try:
                    data[new_name] = json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(f"Unable to decode {key} field: {value}")
                    data[new_name] = {}
        
        data['version'] = self.EXPORT_VERSION
        return yaml.safe_dump(data, sort_keys=False)
    
    def _export_related(self, model: MockDashboard) -> Iterator[Tuple[str, Callable[[], str]]]:
        """导出相关图表"""
        if model.slices and self.export_related:
            chart_export = ChartExportCommand(model.slices)
            yield from chart_export.run()

# ==================== 基础导入框架 ====================

class BaseImportCommand:
    """基础导入命令"""
    
    def __init__(self, contents: Dict[str, str], overwrite: bool = False):
        self.contents = contents
        self.overwrite = overwrite
        self._configs: Dict[str, Any] = {}
        
    def validate(self):
        """验证导入内容"""
        # 解析所有配置文件
        for file_name, content in self.contents.items():
            if file_name.endswith('.yaml') or file_name.endswith('.yml'):
                try:
                    self._configs[file_name] = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML in {file_name}: {e}")
    
    def run(self):
        """执行导入"""
        self.validate()
        self._import(self._configs, self.overwrite)
    
    def _import(self, configs: Dict[str, Any], overwrite: bool = False):
        """执行实际导入逻辑 - 子类需要实现"""
        raise NotImplementedError

class DatabaseImportCommand(BaseImportCommand):
    """数据库导入命令"""
    
    def __init__(self, contents: Dict[str, str], **kwargs):
        super().__init__(contents, **kwargs)
        self.existing_databases: Dict[str, MockDatabase] = {}
    
    def _import_database(self, config: Dict[str, Any], overwrite: bool = False) -> MockDatabase:
        """导入单个数据库 - 展示幂等性处理"""
        
        # 步骤1: 检查是否已存在
        existing = self.existing_databases.get(config['uuid'])
        if existing:
            if not overwrite:
                logger.info(f"Database {config['database_name']} already exists, skipping")
                return existing
            else:
                logger.info(f"Database {config['database_name']} exists, updating")
                config['id'] = existing.id
        
        # 步骤2: 安全检查
        if 'sqlalchemy_uri' in config:
            # 模拟安全检查
            if 'unsafe_uri' in config['sqlalchemy_uri']:
                raise ValueError("Unsafe database URI detected")
        
        # 步骤3: 兼容性处理
        if 'allow_csv_upload' in config:
            config['allow_file_upload'] = config.pop('allow_csv_upload')
        
        # 步骤4: 创建数据库对象
        database = MockDatabase(**config)
        
        # 步骤5: 连接测试
        try:
            self._test_connection(database)
            logger.info(f"Database connection test successful for {database.database_name}")
        except Exception as ex:
            logger.warning(f"Database connection test failed: {ex}")
            # 注意：连接失败不阻止导入，只记录警告
        
        # 步骤6: 保存到"数据库"
        self.existing_databases[database.uuid] = database
        logger.info(f"Successfully imported database: {database.database_name}")
        
        return database
    
    def _test_connection(self, database: MockDatabase):
        """模拟数据库连接测试"""
        # 模拟连接测试逻辑
        if 'fail_connection' in database.sqlalchemy_uri:
            raise ConnectionError("Connection test failed")
        
        # 模拟成功连接
        logger.debug(f"Testing connection to {database.database_name}")
    
    def _import(self, configs: Dict[str, Any], overwrite: bool = False):
        """导入所有数据库"""
        for file_name, config in configs.items():
            if file_name.startswith('databases/'):
                self._import_database(config, overwrite)

class DatasetImportCommand(BaseImportCommand):
    """数据集导入命令"""
    
    def __init__(self, contents: Dict[str, str], **kwargs):
        super().__init__(contents, **kwargs)
        self.existing_datasets: Dict[str, MockDataset] = {}
        self.database_import = DatabaseImportCommand(contents, **kwargs)
    
    def _import(self, configs: Dict[str, Any], overwrite: bool = False):
        """导入数据集 - 展示依赖关系处理"""
        
        # 步骤1: 发现数据集依赖的数据库
        database_uuids = set()
        for file_name, config in configs.items():
            if file_name.startswith('datasets/'):
                if 'database_uuid' in config:
                    database_uuids.add(config['database_uuid'])
        
        # 步骤2: 先导入依赖的数据库
        self.database_import.run()
        database_mapping = {}
        for db_uuid, database in self.database_import.existing_databases.items():
            database_mapping[db_uuid] = database.id
        
        # 步骤3: 导入数据集
        for file_name, config in configs.items():
            if file_name.startswith('datasets/'):
                self._import_dataset(config, database_mapping, overwrite)
    
    def _import_dataset(self, config: Dict[str, Any], database_mapping: Dict[str, int], 
                       overwrite: bool = False) -> MockDataset:
        """导入单个数据集"""
        
        # 幂等性检查
        existing = self.existing_datasets.get(config['uuid'])
        if existing:
            if not overwrite:
                return existing
            config['id'] = existing.id
        
        # 设置数据库引用
        if 'database_uuid' in config and config['database_uuid'] in database_mapping:
            config['database_id'] = database_mapping[config['database_uuid']]
        
        # 创建数据集
        dataset = MockDataset(**config)
        self.existing_datasets[dataset.uuid] = dataset
        
        logger.info(f"Successfully imported dataset: {dataset.table_name}")
        return dataset

class FullImportCommand(BaseImportCommand):
    """完整导入命令 - 处理所有资源类型"""
    
    def __init__(self, contents: Dict[str, str], **kwargs):
        super().__init__(contents, **kwargs)
        self.existing_objects = {
            'databases': {},
            'datasets': {},
            'charts': {},
            'dashboards': {}
        }
    
    def _import(self, configs: Dict[str, Any], overwrite: bool = False):
        """按依赖顺序导入所有资源"""
        
        # 步骤1: 发现所有依赖关系
        dependencies = self._discover_dependencies(configs)
        
        # 步骤2: 按顺序导入
        self._import_databases(configs, dependencies, overwrite)
        self._import_datasets(configs, dependencies, overwrite)
        self._import_charts(configs, dependencies, overwrite)
        self._import_dashboards(configs, dependencies, overwrite)
        
        logger.info("Import completed successfully!")
    
    def _discover_dependencies(self, configs: Dict[str, Any]) -> Dict[str, set]:
        """发现依赖关系"""
        dependencies = {
            'chart_uuids': set(),
            'dataset_uuids': set(),
            'database_uuids': set()
        }
        
        # 从仪表板中发现图表依赖
        for file_name, config in configs.items():
            if file_name.startswith('dashboards/'):
                position = config.get('position', {})
                for component in position.values():
                    if isinstance(component, dict) and component.get('type') == 'CHART':
                        if 'uuid' in component.get('meta', {}):
                            dependencies['chart_uuids'].add(component['meta']['uuid'])
        
        # 从图表中发现数据集依赖
        for file_name, config in configs.items():
            if file_name.startswith('charts/') and 'uuid' in config:
                if config['uuid'] in dependencies['chart_uuids']:
                    dependencies['dataset_uuids'].add(config['dataset_uuid'])
        
        # 从数据集中发现数据库依赖
        for file_name, config in configs.items():
            if file_name.startswith('datasets/'):
                if config['uuid'] in dependencies['dataset_uuids']:
                    dependencies['database_uuids'].add(config['database_uuid'])
        
        return dependencies
    
    def _import_databases(self, configs: Dict[str, Any], dependencies: Dict[str, set], 
                         overwrite: bool = False):
        """导入数据库"""
        for file_name, config in configs.items():
            if (file_name.startswith('databases/') and 
                config['uuid'] in dependencies['database_uuids']):
                
                # 模拟导入逻辑
                database = MockDatabase(**config)
                self.existing_objects['databases'][database.uuid] = database
                logger.info(f"Imported database: {database.database_name}")
    
    def _import_datasets(self, configs: Dict[str, Any], dependencies: Dict[str, set], 
                        overwrite: bool = False):
        """导入数据集"""
        for file_name, config in configs.items():
            if (file_name.startswith('datasets/') and 
                config['uuid'] in dependencies['dataset_uuids']):
                
                # 设置数据库引用
                db_uuid = config['database_uuid']
                if db_uuid in self.existing_objects['databases']:
                    config['database_id'] = self.existing_objects['databases'][db_uuid].id
                
                dataset = MockDataset(**config)
                self.existing_objects['datasets'][dataset.uuid] = dataset
                logger.info(f"Imported dataset: {dataset.table_name}")
    
    def _import_charts(self, configs: Dict[str, Any], dependencies: Dict[str, set], 
                      overwrite: bool = False):
        """导入图表"""
        for file_name, config in configs.items():
            if (file_name.startswith('charts/') and 
                config['uuid'] in dependencies['chart_uuids']):
                
                chart = MockChart(**config)
                self.existing_objects['charts'][chart.uuid] = chart
                logger.info(f"Imported chart: {chart.slice_name}")
    
    def _import_dashboards(self, configs: Dict[str, Any], dependencies: Dict[str, set], 
                          overwrite: bool = False):
        """导入仪表板"""
        for file_name, config in configs.items():
            if file_name.startswith('dashboards/'):
                
                # 更新图表引用
                position = config.get('position', {})
                chart_mapping = {}
                for chart_uuid, chart in self.existing_objects['charts'].items():
                    chart_mapping[chart_uuid] = chart.id
                
                # 更新position中的chartId
                for component in position.values():
                    if isinstance(component, dict) and component.get('type') == 'CHART':
                        meta = component.get('meta', {})
                        if 'uuid' in meta and meta['uuid'] in chart_mapping:
                            meta['chartId'] = chart_mapping[meta['uuid']]
                
                config['position'] = position
                dashboard = MockDashboard(**config)
                self.existing_objects['dashboards'][dashboard.uuid] = dashboard
                logger.info(f"Imported dashboard: {dashboard.dashboard_title}")

# ==================== 高级功能演示 ====================

class ZipExportManager:
    """ZIP文件导出管理器"""
    
    def __init__(self):
        self.export_commands = {
            'databases': DatabaseExportCommand,
            'datasets': DatasetExportCommand, 
            'charts': ChartExportCommand,
            'dashboards': DashboardExportCommand
        }
    
    def export_to_zip(self, export_requests: Dict[str, List[int]], 
                     output_path: str = None) -> bytes:
        """导出多种资源到ZIP文件"""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
            output_path = f"superset_export_{timestamp}.zip"
        
        zip_buffer = BytesIO()
        
        with ZipFile(zip_buffer, 'w') as zip_file:
            # 生成根元数据
            root_metadata = {
                "version": "1.0.0",
                "type": "assets",
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "exported_resources": export_requests
            }
            zip_file.writestr("metadata.yaml", 
                            yaml.safe_dump(root_metadata, sort_keys=False))
            
            # 导出每种资源类型
            for resource_type, model_ids in export_requests.items():
                if resource_type in self.export_commands and model_ids:
                    command_class = self.export_commands[resource_type]
                    command = command_class(model_ids, export_related=True)
                    
                    for file_name, file_content_func in command.run():
                        full_path = f"{resource_type}/{file_name}"
                        zip_file.writestr(full_path, file_content_func())
                        logger.info(f"Added to ZIP: {full_path}")
        
        zip_buffer.seek(0)
        
        # 保存到文件
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
            logger.info(f"Export saved to: {output_path}")
        
        return zip_buffer.getvalue()

class ZipImportManager:
    """ZIP文件导入管理器"""
    
    def import_from_zip(self, zip_data: bytes, overwrite: bool = False):
        """从ZIP文件导入"""
        
        contents = {}
        
        with ZipFile(BytesIO(zip_data), 'r') as zip_file:
            # 读取所有文件内容
            for file_info in zip_file.filelist:
                if not file_info.is_dir():
                    file_path = file_info.filename
                    file_content = zip_file.read(file_path).decode('utf-8')
                    contents[file_path] = file_content
                    logger.debug(f"Loaded from ZIP: {file_path}")
        
        # 执行导入
        import_command = FullImportCommand(contents, overwrite=overwrite)
        import_command.run()
        
        return import_command.existing_objects

class CustomExportCommand(BaseExportCommand):
    """自定义导出命令示例 - 展示二次开发"""
    
    def __init__(self, model_ids: List[int], export_format: str = 'yaml', 
                 include_metadata: bool = True, custom_fields: List[str] = None):
        super().__init__(model_ids, True)
        self.export_format = export_format
        self.include_metadata = include_metadata
        self.custom_fields = custom_fields or []
    
    def _get_mock_model(self, model_id: int) -> MockDashboard:
        # 自定义模型获取逻辑
        return MockDashboard(
            id=model_id,
            dashboard_title=f"custom_dashboard_{model_id}",
            custom_field_1="custom_value_1",
            custom_field_2="custom_value_2"
        )
    
    def _file_name(self, model: MockDashboard) -> str:
        extension = 'json' if self.export_format == 'json' else 'yaml'
        safe_name = model.dashboard_title.replace(" ", "_")
        return f"custom_exports/{safe_name}.{extension}"
    
    def _file_content(self, model: MockDashboard) -> str:
        """自定义导出格式"""
        data = model.export_to_dict()
        
        # 添加自定义字段
        for field in self.custom_fields:
            if hasattr(model, field):
                data[field] = getattr(model, field)
        
        # 添加导出元数据
        if self.include_metadata:
            data['_export_metadata'] = {
                'exported_at': datetime.now(tz=timezone.utc).isoformat(),
                'exported_by': 'CustomExportCommand',
                'format_version': '2.0.0'
            }
        
        # 根据格式序列化
        if self.export_format == 'json':
            return json.dumps(data, indent=2, default=str)
        else:
            return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)

# ==================== 实战演示函数 ====================

def demo_basic_export():
    """演示基础导出功能"""
    print("\n=== 基础导出演示 ===")
    
    # 导出数据库
    db_export = DatabaseExportCommand([1, 2])
    print("导出数据库:")
    for file_name, content_func in db_export.run():
        print(f"  文件: {file_name}")
        print(f"  内容预览: {content_func()[:200]}...")
    
    # 导出图表
    chart_export = ChartExportCommand([101, 102], export_related=True)
    print("\n导出图表（包含相关资源）:")
    for file_name, content_func in chart_export.run():
        print(f"  文件: {file_name}")
        print(f"  大小: {len(content_func())} 字符")

def demo_basic_import():
    """演示基础导入功能"""
    print("\n=== 基础导入演示 ===")
    
    # 准备导入内容
    database_config = {
        'uuid': str(uuid.uuid4()),
        'database_name': 'imported_db',
        'sqlalchemy_uri': 'postgresql://user:pass@host/imported_db',
        'extra': '{"pool_size": 5}',
        'allow_file_upload': True,
        'version': '1.0.0'
    }
    
    contents = {
        'databases/imported_db.yaml': yaml.safe_dump(database_config)
    }
    
    # 执行导入
    import_command = DatabaseImportCommand(contents, overwrite=False)
    import_command.run()
    
    print(f"导入成功！共导入 {len(import_command.existing_databases)} 个数据库")
    for db_uuid, db in import_command.existing_databases.items():
        print(f"  - {db.database_name} (UUID: {db_uuid})")

def demo_idempotent_import():
    """演示幂等性导入"""
    print("\n=== 幂等性导入演示 ===")
    
    database_config = {
        'uuid': 'fixed-uuid-for-demo',
        'database_name': 'idempotent_test_db',
        'sqlalchemy_uri': 'sqlite:///test.db',
        'extra': '{}',
        'allow_file_upload': False,
        'version': '1.0.0'
    }
    
    contents = {
        'databases/test_db.yaml': yaml.safe_dump(database_config)
    }
    
    # 第一次导入
    print("第一次导入:")
    import_command1 = DatabaseImportCommand(contents, overwrite=False)
    import_command1.run()
    print(f"导入数据库数量: {len(import_command1.existing_databases)}")
    
    # 第二次导入（应该跳过）
    print("\n第二次导入（相同UUID，不覆盖）:")
    import_command2 = DatabaseImportCommand(contents, overwrite=False)
    import_command2.existing_databases = import_command1.existing_databases.copy()
    import_command2.run()
    print(f"导入数据库数量: {len(import_command2.existing_databases)}")
    
    # 第三次导入（强制覆盖）
    print("\n第三次导入（强制覆盖）:")
    database_config['database_name'] = 'updated_db_name'
    contents['databases/test_db.yaml'] = yaml.safe_dump(database_config)
    import_command3 = DatabaseImportCommand(contents, overwrite=True)
    import_command3.existing_databases = import_command2.existing_databases.copy()
    import_command3.run()
    
    updated_db = list(import_command3.existing_databases.values())[0]
    print(f"更新后的数据库名称: {updated_db.database_name}")

def demo_zip_export_import():
    """演示ZIP文件导入导出"""
    print("\n=== ZIP文件导入导出演示 ===")
    
    # 导出到ZIP
    export_manager = ZipExportManager()
    export_requests = {
        'databases': [1, 2],
        'charts': [101, 102],
        'dashboards': [201]
    }
    
    zip_data = export_manager.export_to_zip(export_requests, "demo_export.zip")
    print(f"导出ZIP文件大小: {len(zip_data)} 字节")
    
    # 从ZIP导入
    import_manager = ZipImportManager()
    imported_objects = import_manager.import_from_zip(zip_data, overwrite=False)
    
    print("导入结果:")
    for resource_type, objects in imported_objects.items():
        print(f"  {resource_type}: {len(objects)} 个对象")

def demo_custom_export():
    """演示自定义导出命令"""
    print("\n=== 自定义导出演示 ===")
    
    # JSON格式导出
    custom_export = CustomExportCommand(
        model_ids=[1, 2],
        export_format='json',
        include_metadata=True,
        custom_fields=['custom_field_1', 'custom_field_2']
    )
    
    print("自定义JSON导出:")
    for file_name, content_func in custom_export.run():
        if not file_name.endswith('metadata.yaml'):
            print(f"  文件: {file_name}")
            content = content_func()
            # 解析JSON并美化输出
            try:
                parsed = json.loads(content)
                print(f"  自定义字段: {parsed.get('custom_field_1', 'N/A')}")
                print(f"  导出时间: {parsed.get('_export_metadata', {}).get('exported_at', 'N/A')}")
            except:
                print(f"  内容预览: {content[:100]}...")

def demo_dependency_handling():
    """演示依赖关系处理"""
    print("\n=== 依赖关系处理演示 ===")
    
    # 创建完整的依赖链配置
    db_uuid = str(uuid.uuid4())
    dataset_uuid = str(uuid.uuid4())
    chart_uuid = str(uuid.uuid4())
    
    # 数据库配置
    database_config = {
        'uuid': db_uuid,
        'database_name': 'analytics_db',
        'sqlalchemy_uri': 'postgresql://user:pass@host/analytics',
        'extra': '{}',
        'version': '1.0.0'
    }
    
    # 数据集配置
    dataset_config = {
        'uuid': dataset_uuid,
        'table_name': 'sales_data',
        'database_uuid': db_uuid,
        'schema': 'public',
        'sql': 'SELECT * FROM sales',
        'version': '1.0.0'
    }
    
    # 图表配置
    chart_config = {
        'uuid': chart_uuid,
        'slice_name': 'Sales by Region',
        'dataset_uuid': dataset_uuid,
        'viz_type': 'bar',
        'params': {'metric': 'sum_sales', 'groupby': ['region']},
        'version': '1.0.0'
    }
    
    # 仪表板配置
    dashboard_config = {
        'uuid': str(uuid.uuid4()),
        'dashboard_title': 'Sales Dashboard',
        'position': {
            'CHART-1': {
                'type': 'CHART',
                'meta': {
                    'uuid': chart_uuid,
                    'chartId': 0,  # 将在导入时更新
                    'width': 12,
                    'height': 6
                }
            }
        },
        'metadata': {'native_filter_configuration': []},
        'version': '1.0.0'
    }
    
    # 组装导入内容
    contents = {
        'databases/analytics_db.yaml': yaml.safe_dump(database_config),
        'datasets/sales_data.yaml': yaml.safe_dump(dataset_config),
        'charts/sales_by_region.yaml': yaml.safe_dump(chart_config),
        'dashboards/sales_dashboard.yaml': yaml.safe_dump(dashboard_config)
    }
    
    # 执行完整导入
    full_import = FullImportCommand(contents, overwrite=False)
    full_import.run()
    
    print("依赖关系导入完成:")
    print(f"  数据库: {len(full_import.existing_objects['databases'])} 个")
    print(f"  数据集: {len(full_import.existing_objects['datasets'])} 个")
    print(f"  图表: {len(full_import.existing_objects['charts'])} 个")
    print(f"  仪表板: {len(full_import.existing_objects['dashboards'])} 个")

def demo_connection_testing():
    """演示连接测试机制"""
    print("\n=== 连接测试演示 ===")
    
    # 成功连接的数据库
    good_db_config = {
        'uuid': str(uuid.uuid4()),
        'database_name': 'good_connection_db',
        'sqlalchemy_uri': 'postgresql://user:pass@host/good_db',
        'extra': '{}',
        'version': '1.0.0'
    }
    
    # 连接失败的数据库
    bad_db_config = {
        'uuid': str(uuid.uuid4()),
        'database_name': 'bad_connection_db',
        'sqlalchemy_uri': 'postgresql://user:pass@host/fail_connection',
        'extra': '{}',
        'version': '1.0.0'
    }
    
    contents = {
        'databases/good_db.yaml': yaml.safe_dump(good_db_config),
        'databases/bad_db.yaml': yaml.safe_dump(bad_db_config)
    }
    
    # 导入并观察连接测试结果
    import_command = DatabaseImportCommand(contents, overwrite=False)
    import_command.run()
    
    print("连接测试结果:")
    for db_uuid, db in import_command.existing_objects.get('databases', {}).items():
        status = "成功" if 'fail_connection' not in db.sqlalchemy_uri else "失败"
        print(f"  {db.database_name}: {status}")

if __name__ == "__main__":
    """主演示程序"""
    print("Superset Import/Export Framework 实战演示")
    print("=" * 50)
    
    # 运行所有演示
    demo_basic_export()
    demo_basic_import()
    demo_idempotent_import()
    demo_zip_export_import()
    demo_custom_export()
    demo_dependency_handling()
    demo_connection_testing()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    
    # 清理临时文件
    temp_files = ["demo_export.zip"]
    for file_path in temp_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"已清理临时文件: {file_path}") 