#!/usr/bin/env python3
"""
Superset 插件系统架构演示
这个文件展示了 Superset 后端插件系统的核心概念和实现方式
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd

# ============================================================================
# 1. 核心插件基类和接口
# ============================================================================

class PluginType(Enum):
    CHART = "chart"
    FILTER = "filter" 
    DATABASE = "database"
    DATASOURCE = "datasource"

@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    min_superset_version: str = "1.0.0"
    thumbnail_url: Optional[str] = None
    example_url: Optional[str] = None

class BasePlugin(ABC):
    """插件基类"""
    
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.is_registered = False
        self.config = {}
    
    def configure(self, config: Dict[str, Any]) -> 'BasePlugin':
        """配置插件"""
        self.config.update(config)
        return self
    
    @abstractmethod
    def register(self) -> bool:
        """注册插件"""
        pass
    
    @abstractmethod
    def unregister(self) -> bool:
        """注销插件"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """验证插件"""
        pass

# ============================================================================
# 2. 图表插件系统
# ============================================================================

@dataclass
class ChartFormData:
    """图表表单数据"""
    datasource: str
    viz_type: str
    metrics: List[str] = field(default_factory=list)
    groupby: List[str] = field(default_factory=list)
    filters: List[Dict] = field(default_factory=list)
    row_limit: int = 10000
    order_desc: bool = True

@dataclass 
class QueryContext:
    """查询上下文"""
    datasource: str
    queries: List[Dict[str, Any]]
    form_data: ChartFormData
    result_format: str = "json"
    result_type: str = "full"

@dataclass
class ChartProps:
    """图表属性"""
    width: int
    height: int
    form_data: ChartFormData
    query_data: Dict[str, Any]
    theme: Dict[str, Any] = field(default_factory=dict)

class BaseChartPlugin(BasePlugin):
    """图表插件基类"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.viz_type = metadata.name.lower().replace(' ', '_')
        self.control_panel_config = {}
        
    @abstractmethod
    def build_query(self, form_data: ChartFormData) -> QueryContext:
        """构建查询"""
        pass
    
    @abstractmethod
    def transform_props(self, chart_props: ChartProps) -> Dict[str, Any]:
        """转换属性"""
        pass
    
    @abstractmethod
    def process_data(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据"""
        pass
    
    def get_control_panel_config(self) -> Dict[str, Any]:
        """获取控制面板配置"""
        return self.control_panel_config
    
    def set_control_panel_config(self, config: Dict[str, Any]):
        """设置控制面板配置"""
        self.control_panel_config = config

# ============================================================================
# 3. 注册表系统
# ============================================================================

class PluginRegistry:
    """插件注册表"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.metadata_registry: Dict[str, PluginMetadata] = {}
        self.type_registry: Dict[PluginType, List[str]] = {
            plugin_type: [] for plugin_type in PluginType
        }
    
    def register_plugin(self, plugin: BasePlugin) -> bool:
        """注册插件"""
        try:
            # 验证插件
            if not plugin.validate():
                raise ValueError(f"Plugin validation failed: {plugin.metadata.name}")
            
            # 检查依赖
            self._check_dependencies(plugin)
            
            # 注册到各个注册表
            key = self._get_plugin_key(plugin)
            self.plugins[key] = plugin
            self.metadata_registry[key] = plugin.metadata
            self.type_registry[plugin.metadata.plugin_type].append(key)
            
            # 调用插件的注册方法
            plugin.register()
            plugin.is_registered = True
            
            print(f"✓ 成功注册插件: {plugin.metadata.name} ({key})")
            return True
            
        except Exception as e:
            print(f"✗ 插件注册失败: {plugin.metadata.name} - {str(e)}")
            return False
    
    def unregister_plugin(self, plugin_key: str) -> bool:
        """注销插件"""
        if plugin_key not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_key]
        plugin.unregister()
        plugin.is_registered = False
        
        # 从注册表中移除
        del self.plugins[plugin_key]
        del self.metadata_registry[plugin_key]
        
        plugin_type = plugin.metadata.plugin_type
        if plugin_key in self.type_registry[plugin_type]:
            self.type_registry[plugin_type].remove(plugin_key)
        
        print(f"✓ 成功注销插件: {plugin.metadata.name}")
        return True
    
    def get_plugin(self, plugin_key: str) -> Optional[BasePlugin]:
        """获取插件"""
        return self.plugins.get(plugin_key)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """按类型获取插件"""
        keys = self.type_registry.get(plugin_type, [])
        return [self.plugins[key] for key in keys if key in self.plugins]
    
    def list_plugins(self) -> List[str]:
        """列出所有插件"""
        return list(self.plugins.keys())
    
    def get_plugin_info(self, plugin_key: str) -> Optional[Dict[str, Any]]:
        """获取插件信息"""
        if plugin_key not in self.plugins:
            return None
        
        plugin = self.plugins[plugin_key]
        return {
            'key': plugin_key,
            'metadata': plugin.metadata.__dict__,
            'config': plugin.config,
            'is_registered': plugin.is_registered,
        }
    
    def _get_plugin_key(self, plugin: BasePlugin) -> str:
        """生成插件键"""
        if isinstance(plugin, BaseChartPlugin):
            return plugin.viz_type
        return plugin.metadata.name.lower().replace(' ', '_')
    
    def _check_dependencies(self, plugin: BasePlugin):
        """检查插件依赖"""
        for dep in plugin.metadata.dependencies:
            if dep not in self.plugins:
                raise ValueError(f"Missing dependency: {dep}")

# ============================================================================
# 4. 具体插件实现示例
# ============================================================================

class EnhancedPivotTablePlugin(BaseChartPlugin):
    """增强型数据透视表插件"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="Enhanced Pivot Table",
            version="1.0.0",
            description="Enhanced pivot table with data bars, heatmaps, and conditional formatting",
            author="Superset Community",
            plugin_type=PluginType.CHART,
            tags=["table", "pivot", "enhanced", "business-intelligence"],
        )
        super().__init__(metadata)
        
        # 设置控制面板配置
        self.set_control_panel_config({
            'groupby_rows': {
                'type': 'SelectControl',
                'label': 'Rows',
                'description': 'Columns to group by on the rows',
                'multi': True,
                'required': True,
            },
            'groupby_columns': {
                'type': 'SelectControl', 
                'label': 'Columns',
                'description': 'Columns to group by on the columns',
                'multi': True,
            },
            'metrics': {
                'type': 'MetricsControl',
                'label': 'Metrics',
                'description': 'One or many metrics to display',
                'multi': True,
                'required': True,
            },
            'aggregate_function': {
                'type': 'SelectControl',
                'label': 'Aggregation Function',
                'choices': [
                    ('sum', 'Sum'),
                    ('avg', 'Average'),
                    ('count', 'Count'),
                    ('min', 'Minimum'),
                    ('max', 'Maximum'),
                ],
                'default': 'sum',
            },
            'enable_data_bars': {
                'type': 'CheckboxControl',
                'label': 'Enable Data Bars',
                'description': 'Show horizontal data bars in cells',
                'default': False,
            },
            'data_bars_color': {
                'type': 'ColorPickerControl',
                'label': 'Data Bars Color',
                'default': '#1f77b4',
            },
            'enable_heatmap': {
                'type': 'CheckboxControl',
                'label': 'Enable Heatmap',
                'description': 'Color cells based on values',
                'default': False,
            },
            'heatmap_color_scheme': {
                'type': 'SelectControl',
                'label': 'Heatmap Color Scheme',
                'choices': [
                    ('blues', 'Blues'),
                    ('reds', 'Reds'),
                    ('greens', 'Greens'),
                ],
                'default': 'blues',
            },
        })
    
    def build_query(self, form_data: ChartFormData) -> QueryContext:
        """构建查询"""
        groupby_all = (form_data.groupby or []) + (getattr(form_data, 'groupby_columns', []) or [])
        
        query = {
            'metrics': form_data.metrics,
            'groupby': groupby_all,
            'filters': form_data.filters,
            'row_limit': form_data.row_limit,
            'order_desc': form_data.order_desc,
        }
        
        return QueryContext(
            datasource=form_data.datasource,
            queries=[query],
            form_data=form_data,
        )
    
    def process_data(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据 - 创建透视表"""
        data = query_data.get('data', [])
        if not data:
            return {'pivot_data': [], 'statistics': {}}
        
        # 转换为 DataFrame
        df = pd.DataFrame(data)
        
        # 模拟透视表处理
        # 在实际实现中，这里会有复杂的透视表逻辑
        processed_data = {
            'pivot_data': data,
            'row_count': len(data),
            'column_count': len(df.columns) if not df.empty else 0,
            'statistics': self._calculate_statistics(df),
        }
        
        return processed_data
    
    def transform_props(self, chart_props: ChartProps) -> Dict[str, Any]:
        """转换属性"""
        processed_data = self.process_data(chart_props.query_data)
        
        return {
            'width': chart_props.width,
            'height': chart_props.height,
            'data': processed_data['pivot_data'],
            'statistics': processed_data['statistics'],
            'groupby_rows': getattr(chart_props.form_data, 'groupby_rows', []),
            'groupby_columns': getattr(chart_props.form_data, 'groupby_columns', []),
            'metrics': chart_props.form_data.metrics,
            'aggregate_function': getattr(chart_props.form_data, 'aggregate_function', 'sum'),
            'enable_data_bars': getattr(chart_props.form_data, 'enable_data_bars', False),
            'data_bars_color': getattr(chart_props.form_data, 'data_bars_color', '#1f77b4'),
            'enable_heatmap': getattr(chart_props.form_data, 'enable_heatmap', False),
            'heatmap_color_scheme': getattr(chart_props.form_data, 'heatmap_color_scheme', 'blues'),
        }
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算统计信息"""
        if df.empty:
            return {}
        
        numeric_columns = df.select_dtypes(include=['number']).columns
        stats = {}
        
        for col in numeric_columns:
            stats[col] = {
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'count': int(df[col].count()),
            }
        
        return stats
    
    def register(self) -> bool:
        """注册插件"""
        print(f"注册图表插件: {self.metadata.name}")
        return True
    
    def unregister(self) -> bool:
        """注销插件"""
        print(f"注销图表插件: {self.metadata.name}")
        return True
    
    def validate(self) -> bool:
        """验证插件"""
        # 检查必需的方法是否实现
        required_methods = ['build_query', 'transform_props', 'process_data']
        for method in required_methods:
            if not hasattr(self, method):
                return False
        
        # 检查控制面板配置
        if not self.control_panel_config:
            return False
        
        return True

class SimpleNumberPlugin(BaseChartPlugin):
    """简单数值显示插件"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="Simple Number",
            version="1.0.0", 
            description="Display a single number with optional comparison",
            author="Superset Community",
            plugin_type=PluginType.CHART,
            tags=["number", "kpi", "simple"],
        )
        super().__init__(metadata)
        
        self.set_control_panel_config({
            'metric': {
                'type': 'MetricControl',
                'label': 'Metric',
                'description': 'Choose a metric',
                'required': True,
            },
            'comparison_type': {
                'type': 'SelectControl',
                'label': 'Comparison',
                'choices': [
                    ('none', 'None'),
                    ('previous_period', 'Previous Period'),
                    ('custom', 'Custom Value'),
                ],
                'default': 'none',
            },
            'number_format': {
                'type': 'SelectControl',
                'label': 'Number Format',
                'choices': [
                    ('.3~s', 'Adaptive (12.3k)'),
                    (',.0f', 'Comma (12,345)'),
                    ('.1%', 'Percentage (12.3%)'),
                ],
                'default': '.3~s',
            },
        })
    
    def build_query(self, form_data: ChartFormData) -> QueryContext:
        """构建查询"""
        query = {
            'metrics': form_data.metrics[:1],  # 只取第一个指标
            'row_limit': 1,
        }
        
        return QueryContext(
            datasource=form_data.datasource,
            queries=[query],
            form_data=form_data,
        )
    
    def process_data(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据"""
        data =query_data.get('data', [])
        if not data:
            return {'value': 0}
        
        # 获取第一行第一个指标的值
        first_row = data[0]
        metric_keys = [k for k in first_row.keys() if not k.startswith('__')]
        value = first_row.get(metric_keys[0], 0) if metric_keys else 0
        
        return {'value': value}
    
    def transform_props(self, chart_props: ChartProps) -> Dict[str, Any]:
        """转换属性"""
        processed_data = self.process_data(chart_props.query_data)
        
        return {
            'width': chart_props.width,
            'height': chart_props.height,
            'value': processed_data['value'],
            'metric': chart_props.form_data.metrics[0] if chart_props.form_data.metrics else '',
            'number_format': getattr(chart_props.form_data, 'number_format', '.3~s'),
            'comparison_type': getattr(chart_props.form_data, 'comparison_type', 'none'),
        }
    
    def register(self) -> bool:
        """注册插件"""
        print(f"注册图表插件: {self.metadata.name}")
        return True
    
    def unregister(self) -> bool:
        """注销插件"""
        print(f"注销图表插件: {self.metadata.name}")
        return True
    
    def validate(self) -> bool:
        """验证插件"""
        return True

# ============================================================================
# 5. 插件管理器
# ============================================================================

class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.registry = PluginRegistry()
        self.loaded_plugins = {}
        self.plugin_stats = {
            'total_registered': 0,
            'by_type': {plugin_type.value: 0 for plugin_type in PluginType},
            'registration_history': [],
        }
    
    def register_plugin(self, plugin: BasePlugin) -> bool:
        """注册插件"""
        success = self.registry.register_plugin(plugin)
        if success:
            self.plugin_stats['total_registered'] += 1
            self.plugin_stats['by_type'][plugin.metadata.plugin_type.value] += 1
            self.plugin_stats['registration_history'].append({
                'name': plugin.metadata.name,
                'type': plugin.metadata.plugin_type.value,
                'timestamp': time.time(),
            })
        return success
    
    def unregister_plugin(self, plugin_key: str) -> bool:
        """注销插件"""
        plugin = self.registry.get_plugin(plugin_key)
        if plugin:
            success = self.registry.unregister_plugin(plugin_key)
            if success:
                self.plugin_stats['total_registered'] -= 1
                self.plugin_stats['by_type'][plugin.metadata.plugin_type.value] -= 1
            return success
        return False
    
    def get_chart_plugins(self) -> List[BaseChartPlugin]:
        """获取所有图表插件"""
        return self.registry.get_plugins_by_type(PluginType.CHART)
    
    def get_plugin_metadata(self) -> Dict[str, Any]:
        """获取插件元数据"""
        metadata = {}
        for key, plugin in self.registry.plugins.items():
            metadata[key] = {
                'name': plugin.metadata.name,
                'description': plugin.metadata.description,
                'version': plugin.metadata.version,
                'type': plugin.metadata.plugin_type.value,
                'tags': plugin.metadata.tags,
                'control_panel': getattr(plugin, 'control_panel_config', {}),
            }
        return metadata
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.plugin_stats.copy()
    
    def export_config(self) -> Dict[str, Any]:
        """导出配置"""
        return {
            'plugins': self.get_plugin_metadata(),
            'stats': self.get_stats(),
            'registry_info': {
                'total_plugins': len(self.registry.plugins),
                'plugins_by_type': {
                    ptype.value: len(plugins) 
                    for ptype, plugins in self.registry.type_registry.items()
                },
            },
        }

# ============================================================================
# 6. 演示和测试
# ============================================================================

def demo_plugin_system():
    """演示插件系统"""
    print("=" * 60)
    print("Superset 插件系统演示")
    print("=" * 60)
    
    # 创建插件管理器
    manager = PluginManager()
    
    # 创建并注册插件
    print("\n1. 注册插件:")
    print("-" * 30)
    
    enhanced_pivot = EnhancedPivotTablePlugin()
    simple_number = SimpleNumberPlugin()
    
    manager.register_plugin(enhanced_pivot)
    manager.register_plugin(simple_number)
    
    # 显示注册的插件
    print("\n2. 已注册的插件:")
    print("-" * 30)
    for plugin_key in manager.registry.list_plugins():
        info = manager.registry.get_plugin_info(plugin_key)
        print(f"• {info['metadata']['name']} ({plugin_key})")
        print(f"  类型: {info['metadata']['plugin_type']}")
        print(f"  版本: {info['metadata']['version']}")
        print(f"  描述: {info['metadata']['description']}")
        print()
    
    # 显示图表插件的控制面板配置
    print("3. 图表插件控制面板配置:")
    print("-" * 30)
    chart_plugins = manager.get_chart_plugins()
    for plugin in chart_plugins:
        print(f"\n{plugin.metadata.name} 控制面板:")
        config = plugin.get_control_panel_config()
        for control_name, control_config in config.items():
            print(f"  • {control_name}: {control_config.get('label', 'N/A')}")
            print(f"    类型: {control_config.get('type', 'N/A')}")
            if 'description' in control_config:
                print(f"    描述: {control_config['description']}")
    
    # 演示查询构建
    print("\n4. 演示查询构建:")
    print("-" * 30)
    
    # 模拟表单数据
    form_data = ChartFormData(
        datasource="examples.birth_names",
        viz_type="enhanced_pivot_table",
        metrics=["sum__num"],
        groupby=["name", "gender"],
        row_limit=1000,
    )
    
    # 使用增强透视表插件构建查询
    query_context = enhanced_pivot.build_query(form_data)
    print(f"数据源: {query_context.datasource}")
    print(f"查询数量: {len(query_context.queries)}")
    print(f"第一个查询: {json.dumps(query_context.queries[0], indent=2)}")
    
    # 演示数据处理
    print("\n5. 演示数据处理:")
    print("-" * 30)
    
    # 模拟查询结果数据
    mock_data = [
        {"name": "Alice", "gender": "F", "sum__num": 100},
        {"name": "Bob", "gender": "M", "sum__num": 150},
        {"name": "Charlie", "gender": "M", "sum__num": 200},
        {"name": "Diana", "gender": "F", "sum__num": 120},
    ]
    
    query_data = {"data": mock_data}
    processed_data = enhanced_pivot.process_data(query_data)
    
    print(f"处理后的数据行数: {processed_data['row_count']}")
    print(f"统计信息: {json.dumps(processed_data['statistics'], indent=2)}")
    
    # 演示属性转换
    print("\n6. 演示属性转换:")
    print("-" * 30)
    
    chart_props = ChartProps(
        width=800,
        height=600,
        form_data=form_data,
        query_data=query_data,
    )
    
    transformed_props = enhanced_pivot.transform_props(chart_props)
    print("转换后的属性:")
    for key, value in transformed_props.items():
        if key != 'data':  # 跳过数据字段以节省空间
            print(f"  {key}: {value}")
    
    # 显示统计信息
    print("\n7. 插件系统统计:")
    print("-" * 30)
    stats = manager.get_stats()
    print(f"总注册插件数: {stats['total_registered']}")
    print("按类型分布:")
    for ptype, count in stats['by_type'].items():
        if count > 0:
            print(f"  • {ptype}: {count}")
    
    # 导出配置
    print("\n8. 导出配置:")
    print("-" * 30)
    config = manager.export_config()
    print(f"配置文件大小: {len(json.dumps(config))} 字符")
    print("包含的插件:")
    for plugin_key, plugin_info in config['plugins'].items():
        print(f"  • {plugin_info['name']} ({plugin_key})")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)

if __name__ == "__main__":
    demo_plugin_system() 