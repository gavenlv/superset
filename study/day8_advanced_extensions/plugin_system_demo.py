#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 8 插件系统演示：图表插件扩展机制
=====================================

本脚本演示如何扩展 Superset 的图表插件系统：
- 自定义图表类型
- 插件注册机制
- 前端组件集成
- 数据转换处理
"""

import pandas as pd
import numpy as np
import json
import time
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ChartType(Enum):
    """图表类型枚举"""
    GAUGE = "gauge"
    RADAR = "radar"
    TREEMAP = "treemap"
    WATERFALL = "waterfall"
    CUSTOM_KPI = "custom_kpi"


@dataclass
class ChartMetadata:
    """图表元数据"""
    name: str
    description: str
    category: str
    tags: List[str]
    supports_annotations: bool = False
    supports_time_series: bool = False
    datasource_count: int = 1


@dataclass
class ControlPanelConfig:
    """控制面板配置"""
    sections: List[Dict[str, Any]]
    control_overrides: Dict[str, Any]


class BaseChartPlugin(ABC):
    """图表插件基类"""
    
    def __init__(self, metadata: ChartMetadata):
        self.metadata = metadata
        self.viz_type = metadata.name.lower().replace(' ', '_')
        
    @abstractmethod
    def transform_props(self, chart_props: Dict[str, Any]) -> Dict[str, Any]:
        """转换图表属性"""
        pass
    
    @abstractmethod
    def build_query(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建查询对象"""
        pass
    
    @abstractmethod
    def get_control_panel(self) -> ControlPanelConfig:
        """获取控制面板配置"""
        pass
    
    def register(self, registry: 'ChartPluginRegistry') -> None:
        """注册插件到注册表"""
        registry.register_plugin(self)


class GaugeChartPlugin(BaseChartPlugin):
    """仪表盘图表插件"""
    
    def __init__(self):
        metadata = ChartMetadata(
            name="Gauge Chart",
            description="Display a single metric as a gauge",
            category="KPI",
            tags=["gauge", "kpi", "metric"],
            supports_annotations=False,
            supports_time_series=False,
            datasource_count=1
        )
        super().__init__(metadata)
    
    def transform_props(self, chart_props: Dict[str, Any]) -> Dict[str, Any]:
        """转换仪表盘图表属性"""
        form_data = chart_props.get('formData', {})
        query_data = chart_props.get('queryData', {})
        
        # 提取配置
        min_val = form_data.get('gauge_min', 0)
        max_val = form_data.get('gauge_max', 100)
        target_val = form_data.get('gauge_target')
        color_scheme = form_data.get('color_scheme', 'default')
        
        # 处理数据
        data = query_data.get('data', [])
        if data:
            current_value = data[0].get('value', 0)
        else:
            current_value = 0
        
        # 计算百分比
        percentage = ((current_value - min_val) / (max_val - min_val)) * 100
        percentage = max(0, min(100, percentage))
        
        # 确定颜色
        color = self._get_gauge_color(percentage, color_scheme)
        
        return {
            'value': current_value,
            'min': min_val,
            'max': max_val,
            'target': target_val,
            'percentage': percentage,
            'color': color,
            'title': form_data.get('gauge_title', 'Gauge'),
            'unit': form_data.get('gauge_unit', ''),
            'showTarget': target_val is not None,
            'animation': form_data.get('gauge_animation', True),
        }
    
    def build_query(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建仪表盘查询"""
        return {
            'metrics': form_data.get('metrics', []),
            'groupby': [],
            'columns': [],
            'row_limit': 1,
            'order_desc': True,
            'timeseries_limit': 0,
            'time_range': form_data.get('time_range'),
        }
    
    def get_control_panel(self) -> ControlPanelConfig:
        """获取仪表盘控制面板"""
        return ControlPanelConfig(
            sections=[
                {
                    'label': 'Query',
                    'expanded': True,
                    'controlSetRows': [
                        ['metrics'],
                        ['adhoc_filters'],
                    ]
                },
                {
                    'label': 'Gauge Configuration',
                    'expanded': True,
                    'controlSetRows': [
                        ['gauge_min', 'gauge_max'],
                        ['gauge_target'],
                        ['gauge_title', 'gauge_unit'],
                        ['color_scheme'],
                        ['gauge_animation'],
                    ]
                }
            ],
            control_overrides={
                'gauge_min': {
                    'type': 'TextControl',
                    'label': 'Minimum Value',
                    'default': 0,
                    'description': 'Minimum value for the gauge'
                },
                'gauge_max': {
                    'type': 'TextControl',
                    'label': 'Maximum Value',
                    'default': 100,
                    'description': 'Maximum value for the gauge'
                },
                'gauge_target': {
                    'type': 'TextControl',
                    'label': 'Target Value',
                    'description': 'Target value to display on gauge'
                },
                'gauge_title': {
                    'type': 'TextControl',
                    'label': 'Title',
                    'default': 'Gauge',
                    'description': 'Title for the gauge'
                },
                'gauge_unit': {
                    'type': 'TextControl',
                    'label': 'Unit',
                    'description': 'Unit to display with the value'
                },
                'gauge_animation': {
                    'type': 'CheckboxControl',
                    'label': 'Enable Animation',
                    'default': True,
                    'description': 'Enable gauge animation'
                }
            }
        )
    
    def _get_gauge_color(self, percentage: float, color_scheme: str) -> str:
        """根据百分比和配色方案获取颜色"""
        if color_scheme == 'traffic_light':
            if percentage < 33:
                return '#ff4d4f'  # 红色
            elif percentage < 66:
                return '#faad14'  # 黄色
            else:
                return '#52c41a'  # 绿色
        elif color_scheme == 'blue_gradient':
            if percentage < 50:
                return '#1890ff'  # 浅蓝
            else:
                return '#0050b3'  # 深蓝
        else:
            return '#1890ff'  # 默认蓝色


class RadarChartPlugin(BaseChartPlugin):
    """雷达图插件"""
    
    def __init__(self):
        metadata = ChartMetadata(
            name="Radar Chart",
            description="Display multiple metrics in a radar/spider chart",
            category="Comparison",
            tags=["radar", "spider", "multi-metric"],
            supports_annotations=False,
            supports_time_series=False,
            datasource_count=1
        )
        super().__init__(metadata)
    
    def transform_props(self, chart_props: Dict[str, Any]) -> Dict[str, Any]:
        """转换雷达图属性"""
        form_data = chart_props.get('formData', {})
        query_data = chart_props.get('queryData', {})
        
        # 处理数据
        data = query_data.get('data', [])
        
        # 转换为雷达图数据格式
        radar_data = []
        if data:
            for row in data:
                radar_data.append({
                    'axis': row.get('metric', ''),
                    'value': row.get('value', 0),
                    'max': form_data.get('radar_max_value', 100)
                })
        
        return {
            'data': radar_data,
            'showLegend': form_data.get('show_legend', True),
            'showLabels': form_data.get('show_labels', True),
            'colorScheme': form_data.get('color_scheme', 'default'),
            'fillOpacity': form_data.get('fill_opacity', 0.3),
            'strokeWidth': form_data.get('stroke_width', 2),
        }
    
    def build_query(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建雷达图查询"""
        return {
            'metrics': form_data.get('metrics', []),
            'groupby': form_data.get('groupby', []),
            'columns': [],
            'row_limit': form_data.get('row_limit', 100),
            'order_desc': True,
            'timeseries_limit': 0,
            'time_range': form_data.get('time_range'),
        }
    
    def get_control_panel(self) -> ControlPanelConfig:
        """获取雷达图控制面板"""
        return ControlPanelConfig(
            sections=[
                {
                    'label': 'Query',
                    'expanded': True,
                    'controlSetRows': [
                        ['metrics'],
                        ['groupby'],
                        ['adhoc_filters'],
                        ['row_limit'],
                    ]
                },
                {
                    'label': 'Radar Configuration',
                    'expanded': True,
                    'controlSetRows': [
                        ['radar_max_value'],
                        ['show_legend', 'show_labels'],
                        ['color_scheme'],
                        ['fill_opacity', 'stroke_width'],
                    ]
                }
            ],
            control_overrides={
                'radar_max_value': {
                    'type': 'TextControl',
                    'label': 'Maximum Value',
                    'default': 100,
                    'description': 'Maximum value for radar chart axes'
                },
                'fill_opacity': {
                    'type': 'SliderControl',
                    'label': 'Fill Opacity',
                    'min': 0,
                    'max': 1,
                    'step': 0.1,
                    'default': 0.3,
                    'description': 'Opacity of the filled area'
                },
                'stroke_width': {
                    'type': 'SliderControl',
                    'label': 'Stroke Width',
                    'min': 1,
                    'max': 5,
                    'step': 1,
                    'default': 2,
                    'description': 'Width of the stroke lines'
                }
            }
        )


class CustomKPIPlugin(BaseChartPlugin):
    """自定义KPI插件"""
    
    def __init__(self):
        metadata = ChartMetadata(
            name="Custom KPI",
            description="Display multiple KPIs with custom formatting",
            category="KPI",
            tags=["kpi", "metrics", "dashboard"],
            supports_annotations=False,
            supports_time_series=True,
            datasource_count=1
        )
        super().__init__(metadata)
    
    def transform_props(self, chart_props: Dict[str, Any]) -> Dict[str, Any]:
        """转换KPI属性"""
        form_data = chart_props.get('formData', {})
        query_data = chart_props.get('queryData', {})
        
        # 处理数据
        data = query_data.get('data', [])
        
        # 构建KPI数据
        kpis = []
        for i, row in enumerate(data):
            kpi = {
                'title': row.get('metric', f'KPI {i+1}'),
                'value': row.get('value', 0),
                'format': form_data.get('number_format', '.2f'),
                'prefix': form_data.get('value_prefix', ''),
                'suffix': form_data.get('value_suffix', ''),
                'trend': self._calculate_trend(row),
                'color': self._get_kpi_color(row, form_data),
            }
            kpis.append(kpi)
        
        return {
            'kpis': kpis,
            'layout': form_data.get('kpi_layout', 'horizontal'),
            'showTrend': form_data.get('show_trend', True),
            'showSparkline': form_data.get('show_sparkline', False),
            'backgroundColor': form_data.get('background_color', '#ffffff'),
        }
    
    def build_query(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建KPI查询"""
        return {
            'metrics': form_data.get('metrics', []),
            'groupby': form_data.get('groupby', []),
            'columns': [],
            'row_limit': form_data.get('row_limit', 10),
            'order_desc': True,
            'timeseries_limit': 0,
            'time_range': form_data.get('time_range'),
            'time_grain_sqla': form_data.get('time_grain_sqla'),
        }
    
    def get_control_panel(self) -> ControlPanelConfig:
        """获取KPI控制面板"""
        return ControlPanelConfig(
            sections=[
                {
                    'label': 'Query',
                    'expanded': True,
                    'controlSetRows': [
                        ['metrics'],
                        ['groupby'],
                        ['adhoc_filters'],
                        ['row_limit'],
                    ]
                },
                {
                    'label': 'KPI Configuration',
                    'expanded': True,
                    'controlSetRows': [
                        ['kpi_layout'],
                        ['number_format'],
                        ['value_prefix', 'value_suffix'],
                        ['show_trend', 'show_sparkline'],
                        ['background_color'],
                    ]
                }
            ],
            control_overrides={
                'kpi_layout': {
                    'type': 'SelectControl',
                    'label': 'Layout',
                    'choices': [
                        ('horizontal', 'Horizontal'),
                        ('vertical', 'Vertical'),
                        ('grid', 'Grid'),
                    ],
                    'default': 'horizontal',
                    'description': 'Layout for multiple KPIs'
                },
                'value_prefix': {
                    'type': 'TextControl',
                    'label': 'Value Prefix',
                    'description': 'Prefix to display before the value'
                },
                'value_suffix': {
                    'type': 'TextControl',
                    'label': 'Value Suffix',
                    'description': 'Suffix to display after the value'
                },
                'background_color': {
                    'type': 'ColorPickerControl',
                    'label': 'Background Color',
                    'default': '#ffffff',
                    'description': 'Background color for KPI cards'
                }
            }
        )
    
    def _calculate_trend(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """计算趋势"""
        # 简化的趋势计算
        current = row.get('value', 0)
        previous = row.get('previous_value')
        
        if previous is not None and previous != 0:
            change = ((current - previous) / previous) * 100
            return {
                'direction': 'up' if change > 0 else 'down' if change < 0 else 'flat',
                'percentage': abs(change),
                'value': current - previous
            }
        return None
    
    def _get_kpi_color(self, row: Dict[str, Any], form_data: Dict[str, Any]) -> str:
        """获取KPI颜色"""
        value = row.get('value', 0)
        thresholds = form_data.get('color_thresholds', [])
        
        for threshold in thresholds:
            if value >= threshold.get('min', 0) and value <= threshold.get('max', float('inf')):
                return threshold.get('color', '#1890ff')
        
        return '#1890ff'  # 默认颜色


class ChartPluginRegistry:
    """图表插件注册表"""
    
    def __init__(self):
        self.plugins: Dict[str, BaseChartPlugin] = {}
        self.metadata_registry: Dict[str, ChartMetadata] = {}
        self.control_panel_registry: Dict[str, ControlPanelConfig] = {}
        
    def register_plugin(self, plugin: BaseChartPlugin) -> None:
        """注册插件"""
        viz_type = plugin.viz_type
        
        # 验证插件
        self._validate_plugin(plugin)
        
        # 注册插件
        self.plugins[viz_type] = plugin
        self.metadata_registry[viz_type] = plugin.metadata
        self.control_panel_registry[viz_type] = plugin.get_control_panel()
        
        print(f"✓ 注册图表插件: {viz_type} - {plugin.metadata.name}")
    
    def get_plugin(self, viz_type: str) -> Optional[BaseChartPlugin]:
        """获取插件"""
        return self.plugins.get(viz_type)
    
    def get_metadata(self, viz_type: str) -> Optional[ChartMetadata]:
        """获取元数据"""
        return self.metadata_registry.get(viz_type)
    
    def get_control_panel(self, viz_type: str) -> Optional[ControlPanelConfig]:
        """获取控制面板"""
        return self.control_panel_registry.get(viz_type)
    
    def list_plugins(self) -> List[str]:
        """列出所有插件"""
        return list(self.plugins.keys())
    
    def get_plugins_by_category(self, category: str) -> List[str]:
        """按类别获取插件"""
        return [
            viz_type for viz_type, metadata in self.metadata_registry.items()
            if metadata.category == category
        ]
    
    def _validate_plugin(self, plugin: BaseChartPlugin) -> None:
        """验证插件"""
        if not plugin.metadata.name:
            raise ValueError("Plugin metadata must have a name")
        
        if not plugin.viz_type:
            raise ValueError("Plugin must have a viz_type")
        
        # 检查必需方法
        required_methods = ['transform_props', 'build_query', 'get_control_panel']
        for method in required_methods:
            if not hasattr(plugin, method) or not callable(getattr(plugin, method)):
                raise ValueError(f"Plugin must implement {method} method")
    
    def export_frontend_config(self) -> Dict[str, Any]:
        """导出前端配置"""
        config = {
            'plugins': {},
            'metadata': {},
            'controlPanels': {}
        }
        
        for viz_type, plugin in self.plugins.items():
            config['plugins'][viz_type] = {
                'name': plugin.metadata.name,
                'description': plugin.metadata.description,
                'category': plugin.metadata.category,
                'tags': plugin.metadata.tags,
            }
            config['metadata'][viz_type] = plugin.metadata.__dict__
            config['controlPanels'][viz_type] = plugin.get_control_panel().__dict__
        
        return config


class ChartRenderer:
    """图表渲染器"""
    
    def __init__(self, registry: ChartPluginRegistry):
        self.registry = registry
    
    def render_chart(
        self, 
        viz_type: str, 
        form_data: Dict[str, Any], 
        query_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """渲染图表"""
        plugin = self.registry.get_plugin(viz_type)
        if not plugin:
            raise ValueError(f"Unknown chart type: {viz_type}")
        
        # 构建图表属性
        chart_props = {
            'formData': form_data,
            'queryData': query_data,
            'width': form_data.get('width', 800),
            'height': form_data.get('height', 600),
        }
        
        # 转换属性
        transformed_props = plugin.transform_props(chart_props)
        
        # 添加元数据
        result = {
            'vizType': viz_type,
            'metadata': plugin.metadata.__dict__,
            'props': transformed_props,
            'timestamp': time.time(),
        }
        
        return result


def demo_plugin_system():
    """演示插件系统"""
    print("🎨 图表插件系统演示")
    print("=" * 60)
    
    # 创建注册表
    registry = ChartPluginRegistry()
    
    # 注册插件
    gauge_plugin = GaugeChartPlugin()
    radar_plugin = RadarChartPlugin()
    kpi_plugin = CustomKPIPlugin()
    
    gauge_plugin.register(registry)
    radar_plugin.register(registry)
    kpi_plugin.register(registry)
    
    print(f"\n📊 已注册插件: {registry.list_plugins()}")
    
    # 按类别列出插件
    kpi_plugins = registry.get_plugins_by_category("KPI")
    print(f"📈 KPI类插件: {kpi_plugins}")
    
    # 创建渲染器
    renderer = ChartRenderer(registry)
    
    # 演示仪表盘图表
    print("\n🎯 演示仪表盘图表:")
    gauge_form_data = {
        'metrics': ['sales_amount'],
        'gauge_min': 0,
        'gauge_max': 1000000,
        'gauge_target': 800000,
        'gauge_title': 'Sales Performance',
        'gauge_unit': '$',
        'color_scheme': 'traffic_light',
        'gauge_animation': True,
    }
    gauge_query_data = {
        'data': [{'value': 750000}]
    }
    
    gauge_result = renderer.render_chart('gauge_chart', gauge_form_data, gauge_query_data)
    print(f"仪表盘结果: {json.dumps(gauge_result['props'], indent=2)}")
    
    # 演示雷达图
    print("\n🕸️ 演示雷达图:")
    radar_form_data = {
        'metrics': ['sales', 'marketing', 'support', 'development'],
        'radar_max_value': 100,
        'show_legend': True,
        'show_labels': True,
        'color_scheme': 'default',
        'fill_opacity': 0.3,
        'stroke_width': 2,
    }
    radar_query_data = {
        'data': [
            {'metric': 'Sales', 'value': 85},
            {'metric': 'Marketing', 'value': 70},
            {'metric': 'Support', 'value': 90},
            {'metric': 'Development', 'value': 75},
        ]
    }
    
    radar_result = renderer.render_chart('radar_chart', radar_form_data, radar_query_data)
    print(f"雷达图结果: {json.dumps(radar_result['props'], indent=2)}")
    
    # 导出前端配置
    print("\n⚙️ 前端配置:")
    frontend_config = registry.export_frontend_config()
    print(f"配置大小: {len(json.dumps(frontend_config))} 字符")
    
    return registry, renderer


def demo_plugin_development():
    """演示插件开发流程"""
    print("\n🔧 插件开发流程演示")
    print("=" * 60)
    
    # 1. 定义插件元数据
    print("1. 定义插件元数据")
    metadata = ChartMetadata(
        name="Custom Waterfall",
        description="Waterfall chart for showing cumulative effects",
        category="Analysis",
        tags=["waterfall", "cumulative", "analysis"],
        supports_annotations=True,
        supports_time_series=True,
    )
    print(f"   元数据: {metadata}")
    
    # 2. 实现插件类
    print("\n2. 实现插件类")
    print("   - transform_props: 数据转换")
    print("   - build_query: 查询构建")
    print("   - get_control_panel: 控制面板")
    
    # 3. 注册插件
    print("\n3. 注册插件")
    print("   - 验证插件完整性")
    print("   - 添加到注册表")
    print("   - 生成前端配置")
    
    # 4. 前端集成
    print("\n4. 前端集成")
    print("   - React组件开发")
    print("   - 控制面板配置")
    print("   - 数据绑定")
    
    # 5. 测试和部署
    print("\n5. 测试和部署")
    print("   - 单元测试")
    print("   - 集成测试")
    print("   - 生产部署")


def main():
    """主演示函数"""
    print("🎨 Day 8 插件系统扩展机制演示")
    print("=" * 60)
    
    try:
        # 演示插件系统
        registry, renderer = demo_plugin_system()
        
        # 演示插件开发
        demo_plugin_development()
        
        print("\n" + "="*60)
        print("✅ 插件系统演示完成！")
        print("\n📚 插件系统要点总结:")
        print("- 插件注册机制：统一管理图表插件")
        print("- 元数据驱动：通过元数据描述插件特性")
        print("- 控制面板配置：动态生成用户界面")
        print("- 数据转换：标准化数据处理流程")
        print("- 前端集成：无缝集成到现有系统")
        print("- 扩展性：支持任意自定义图表类型")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 