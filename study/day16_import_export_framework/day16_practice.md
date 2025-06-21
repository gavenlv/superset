# Day 16: Import/Export Framework 实践练习

## 练习概述

通过以下练习深入掌握Superset的Import/Export框架，包括基础操作、高级特性和二次开发技巧。

## Level 1: 基础练习

### 练习1.1: 理解导出格式

**目标**: 熟悉YAML导出格式和文件结构

**任务**:
1. 导出一个简单的数据库配置
2. 分析YAML文件结构
3. 理解各字段含义

**期望结果**:
```yaml
database_name: example_db
sqlalchemy_uri: postgresql://user:pass@host/db
uuid: 12345678-1234-1234-1234-123456789abc
extra:
  engine_params:
    pool_size: 10
allow_file_upload: true
version: 1.0.0
```

**练习代码**:
```python
# 运行演示程序中的 demo_basic_export()
python day16_import_export_demo.py
```

### 练习1.2: 基础导入操作

**目标**: 掌握基本的导入操作和幂等性

**任务**:
1. 创建一个数据库配置文件
2. 执行导入操作
3. 验证幂等性（重复导入相同配置）

**关键代码**:
```python
def practice_basic_import():
    """练习基础导入"""
    config = {
        'uuid': 'practice-db-uuid',
        'database_name': 'practice_db',
        'sqlalchemy_uri': 'sqlite:///practice.db',
        'extra': '{}',
        'version': '1.0.0'
    }
    
    contents = {
        'databases/practice_db.yaml': yaml.safe_dump(config)
    }
    
    # 第一次导入
    import_cmd = DatabaseImportCommand(contents)
    import_cmd.run()
    
    # 第二次导入 - 应该跳过
    import_cmd2 = DatabaseImportCommand(contents)
    import_cmd2.existing_databases = import_cmd.existing_databases
    import_cmd2.run()
```

### 练习1.3: 依赖关系分析

**目标**: 理解资源间的依赖关系

**任务**:
1. 分析仪表板→图表→数据集→数据库的依赖链
2. 创建一个完整的依赖链配置
3. 验证导入顺序的重要性

**思考问题**:
- 为什么必须先导入数据库再导入数据集？
- 如果缺少某个依赖会发生什么？
- UUID引用系统如何解决跨环境问题？

## Level 2: 中级练习

### 练习2.1: 批量导入导出

**目标**: 掌握批量操作和ZIP文件处理

**任务**:
1. 创建多个数据库、数据集、图表配置
2. 使用ZIP管理器进行批量导出
3. 在"新环境"中批量导入

**实现步骤**:
```python
def practice_batch_operations():
    """练习批量操作"""
    # 1. 准备多个资源
    resources = {
        'databases': [
            {'name': 'analytics_db', 'uri': 'postgresql://...'},
            {'name': 'warehouse_db', 'uri': 'mysql://...'}
        ],
        'datasets': [
            {'name': 'users', 'table': 'dim_users'},
            {'name': 'orders', 'table': 'fact_orders'}
        ],
        'charts': [
            {'name': 'User Growth', 'type': 'line'},
            {'name': 'Sales Summary', 'type': 'bar'}
        ]
    }
    
    # 2. 批量导出
    export_manager = ZipExportManager()
    export_requests = {
        'databases': [1, 2],
        'datasets': [10, 11],
        'charts': [100, 101]
    }
    zip_data = export_manager.export_to_zip(export_requests)
    
    # 3. 批量导入
    import_manager = ZipImportManager()
    result = import_manager.import_from_zip(zip_data)
    
    return result
```

### 练习2.2: 错误处理和恢复

**目标**: 掌握导入过程中的错误处理

**任务**:
1. 模拟各种导入错误（连接失败、配置错误等）
2. 实现错误恢复机制
3. 记录和分析错误日志

**错误场景**:
- 数据库连接失败
- 无效的配置格式
- 缺少依赖资源
- 权限不足

### 练习2.3: 配置验证和安全检查

**目标**: 实现导入前的验证机制

**任务**:
1. 实现数据库URI安全检查
2. 验证配置文件完整性
3. 检查版本兼容性

**实现示例**:
```python
class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_database_uri(uri: str) -> bool:
        """验证数据库URI安全性"""
        unsafe_patterns = ['drop', 'delete', 'truncate']
        return not any(pattern in uri.lower() for pattern in unsafe_patterns)
    
    @staticmethod
    def validate_config_completeness(config: dict, required_fields: list) -> bool:
        """验证配置完整性"""
        return all(field in config for field in required_fields)
    
    @staticmethod
    def validate_version_compatibility(config_version: str, supported_versions: list) -> bool:
        """验证版本兼容性"""
        return config_version in supported_versions
```

## Level 3: 高级练习

### 练习3.1: 自定义导入导出格式

**目标**: 扩展框架支持新的导出格式

**任务**:
1. 实现JSON格式导出
2. 添加自定义元数据字段
3. 支持增量导出

**实现框架**:
```python
class CustomFormatExporter(BaseExportCommand):
    """自定义格式导出器"""
    
    def __init__(self, model_ids, format_type='json', include_metadata=True):
        super().__init__(model_ids)
        self.format_type = format_type
        self.include_metadata = include_metadata
    
    def _file_content(self, model: MockModel) -> str:
        """生成自定义格式内容"""
        data = model.export_to_dict()
        
        if self.include_metadata:
            data['_metadata'] = {
                'exported_at': datetime.now().isoformat(),
                'format_version': '2.0.0',
                'custom_field': 'custom_value'
            }
        
        if self.format_type == 'json':
            return json.dumps(data, indent=2)
        elif self.format_type == 'yaml':
            return yaml.safe_dump(data)
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")
```

### 练习3.2: 多环境部署工具

**目标**: 创建支持多环境部署的工具

**任务**:
1. 实现环境配置管理
2. 支持环境特定的配置替换
3. 创建部署流水线

**环境配置示例**:
```python
class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self):
        self.environments = {
            'dev': {
                'database_host': 'dev.db.example.com',
                'database_port': 5432,
                'ssl_mode': 'disable'
            },
            'staging': {
                'database_host': 'staging.db.example.com', 
                'database_port': 5432,
                'ssl_mode': 'require'
            },
            'prod': {
                'database_host': 'prod.db.example.com',
                'database_port': 5432,
                'ssl_mode': 'require'
            }
        }
    
    def transform_config_for_env(self, config: dict, target_env: str) -> dict:
        """为目标环境转换配置"""
        env_config = self.environments.get(target_env, {})
        
        # 替换环境特定的配置
        if 'sqlalchemy_uri' in config:
            uri = config['sqlalchemy_uri']
            # 替换主机和端口
            for key, value in env_config.items():
                if key in uri:
                    uri = uri.replace(f'{key}=old_value', f'{key}={value}')
            config['sqlalchemy_uri'] = uri
        
        return config
```

### 练习3.3: 性能优化

**目标**: 优化导入导出性能

**任务**:
1. 实现并行导出
2. 优化内存使用
3. 添加进度跟踪

**性能优化示例**:
```python
import concurrent.futures
from threading import Lock

class OptimizedExportManager:
    """优化的导出管理器"""
    
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.progress_lock = Lock()
        self.completed_items = 0
        self.total_items = 0
    
    def parallel_export(self, export_requests: dict) -> bytes:
        """并行导出"""
        self.total_items = sum(len(ids) for ids in export_requests.values())
        
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_file:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for resource_type, model_ids in export_requests.items():
                    future = executor.submit(self._export_resource_type, 
                                           resource_type, model_ids)
                    futures.append(future)
                
                # 收集结果
                for future in concurrent.futures.as_completed(futures):
                    resource_files = future.result()
                    for file_name, content in resource_files:
                        zip_file.writestr(file_name, content)
                        self._update_progress()
        
        return zip_buffer.getvalue()
    
    def _export_resource_type(self, resource_type: str, model_ids: list) -> list:
        """导出特定资源类型"""
        # 实现具体的导出逻辑
        pass
    
    def _update_progress(self):
        """更新进度"""
        with self.progress_lock:
            self.completed_items += 1
            progress = (self.completed_items / self.total_items) * 100
            print(f"导出进度: {progress:.1f}%")
```

## Level 4: 专家级练习

### 练习4.1: 增量同步系统

**目标**: 实现基于时间戳的增量同步

**任务**:
1. 跟踪资源修改时间
2. 实现增量导出
3. 处理冲突解决

### 练习4.2: 版本控制集成

**目标**: 集成Git版本控制

**任务**:
1. 将配置文件提交到Git
2. 实现基于分支的环境管理
3. 自动化部署流水线

### 练习4.3: 监控和告警

**目标**: 添加导入导出监控

**任务**:
1. 记录详细的操作日志
2. 实现失败告警
3. 性能指标监控

## 实战项目

### 项目1: 企业级备份系统

**需求**:
- 定期自动备份所有Superset资源
- 支持增量备份
- 提供恢复验证
- 多存储后端支持（本地、S3、GCS）

### 项目2: 多环境CI/CD集成

**需求**:
- 开发→测试→生产的自动化流水线
- 配置差异管理
- 回滚机制
- 审批流程

### 项目3: 配置管理平台

**需求**:
- Web界面的配置管理
- 可视化依赖关系
- 批量操作支持
- 权限控制

## 练习验证

### 验证清单

- [ ] 能够独立完成基础导入导出操作
- [ ] 理解并能处理依赖关系
- [ ] 掌握幂等性设计原理
- [ ] 能够处理常见错误场景
- [ ] 实现自定义导入导出逻辑
- [ ] 具备性能优化能力
- [ ] 能够设计企业级解决方案

### 评估标准

**初级** (Level 1-2):
- 完成基础操作
- 理解核心概念
- 能够处理简单错误

**中级** (Level 2-3):
- 实现自定义功能
- 掌握高级特性
- 能够优化性能

**高级** (Level 3-4):
- 设计企业级方案
- 具备扩展开发能力
- 能够解决复杂问题

## 学习资源

### 推荐阅读
- Superset官方文档：Import/Export部分
- SQLAlchemy文档：连接和引擎管理
- YAML/JSON格式规范

### 相关工具
- `superset export-dashboards`
- `superset import-dashboards`
- REST API端点

### 社区资源
- GitHub Issues：导入导出相关问题
- Stack Overflow：实际使用案例
- Superset Slack：社区讨论

## 下一步

完成这些练习后，你将具备：
1. 深入理解Superset导入导出机制
2. 能够二次开发自定义功能
3. 具备企业级部署经验
4. 掌握最佳实践和常见陷阱

继续学习建议：
- Day 17: 缓存系统和性能优化
- Day 18: 监控和告警系统
- Day 19: 扩展和插件开发 