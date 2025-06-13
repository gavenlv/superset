#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 6 仪表板系统演示
==================

本脚本演示 Superset 仪表板系统的核心功能：
- 仪表板组件管理
- 布局引擎
- 组件交互
- 状态管理
- 性能优化
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


@dataclass
class ComponentConfig:
    """组件配置"""
    id: str
    type: str
    x: int
    y: int
    width: int
    height: int
    min_width: int = 2
    min_height: int = 2
    title: str = ""
    config: Dict = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class DashboardComponent(ABC):
    """仪表板组件基类"""
    
    def __init__(self, config: ComponentConfig):
        self.config = config
        self.data = None
        self.loading = False
        self.error = None
    
    @abstractmethod
    def render(self) -> Dict:
        """渲染组件"""
        pass
    
    def update_data(self, data: Any):
        """更新组件数据"""
        self.data = data
        self.loading = False
        self.error = None
    
    def set_error(self, error: str):
        """设置错误状态"""
        self.error = error
        self.loading = False


class ChartComponent(DashboardComponent):
    """图表组件"""
    
    def render(self) -> Dict:
        return {
            'id': self.config.id,
            'type': 'chart',
            'title': self.config.title,
            'data': self.data,
            'loading': self.loading,
            'error': self.error,
            'config': self.config.config
        }


class FilterComponent(DashboardComponent):
    """过滤器组件"""
    
    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.selected_values = []
    
    def render(self) -> Dict:
        return {
            'id': self.config.id,
            'type': 'filter',
            'title': self.config.title,
            'options': self.data or [],
            'selected': self.selected_values,
            'loading': self.loading,
            'error': self.error
        }
    
    def set_selected_values(self, values: List):
        """设置选中的值"""
        self.selected_values = values


class TextComponent(DashboardComponent):
    """文本组件"""
    
    def render(self) -> Dict:
        return {
            'id': self.config.id,
            'type': 'text',
            'title': self.config.title,
            'content': self.config.config.get('content', ''),
            'style': self.config.config.get('style', {})
        }


class GridLayoutEngine:
    """网格布局引擎"""
    
    GRID_COLUMNS = 12
    GRID_ROW_HEIGHT = 100
    GRID_MARGIN = [10, 10]
    
    def __init__(self):
        self.components = {}
        self.layout = []
    
    def add_component(self, component: DashboardComponent):
        """添加组件"""
        self.components[component.config.id] = component
        
        layout_item = {
            'i': component.config.id,
            'x': component.config.x,
            'y': component.config.y,
            'w': component.config.width,
            'h': component.config.height,
            'minW': component.config.min_width,
            'minH': component.config.min_height
        }
        
        self.layout.append(layout_item)
        print(f"✓ 添加组件: {component.config.id} ({component.config.type})")
    
    def remove_component(self, component_id: str):
        """移除组件"""
        if component_id in self.components:
            del self.components[component_id]
            self.layout = [item for item in self.layout if item['i'] != component_id]
            print(f"✓ 移除组件: {component_id}")
    
    def update_layout(self, new_layout: List[Dict]):
        """更新布局"""
        layout_dict = {item['i']: item for item in new_layout}
        
        for item in self.layout:
            if item['i'] in layout_dict:
                item.update(layout_dict[item['i']])
        
        print(f"✓ 更新布局: {len(new_layout)} 个组件")
    
    def get_layout(self) -> List[Dict]:
        """获取当前布局"""
        return self.layout.copy()
    
    def detect_collisions(self) -> List[tuple]:
        """检测布局冲突"""
        collisions = []
        
        for i, item1 in enumerate(self.layout):
            for j, item2 in enumerate(self.layout[i+1:], i+1):
                if self._check_overlap(item1, item2):
                    collisions.append((item1['i'], item2['i']))
        
        return collisions
    
    def _check_overlap(self, item1: Dict, item2: Dict) -> bool:
        """检查两个组件是否重叠"""
        return not (
            item1['x'] + item1['w'] <= item2['x'] or
            item2['x'] + item2['w'] <= item1['x'] or
            item1['y'] + item1['h'] <= item2['y'] or
            item2['y'] + item2['h'] <= item1['y']
        )
    
    def auto_layout(self):
        """自动布局"""
        print("🔄 执行自动布局...")
        
        # 按Y坐标排序
        sorted_items = sorted(self.layout, key=lambda x: (x['y'], x['x']))
        
        current_y = 0
        current_x = 0
        
        for item in sorted_items:
            # 检查当前行是否有足够空间
            if current_x + item['w'] > self.GRID_COLUMNS:
                current_y += max(item['h'] for item in sorted_items 
                               if item['y'] == current_y) if sorted_items else 4
                current_x = 0
            
            item['x'] = current_x
            item['y'] = current_y
            current_x += item['w']
        
        print("✓ 自动布局完成")


class ComponentEventSystem:
    """组件事件系统"""
    
    def __init__(self):
        self.listeners = {}
        self.event_history = []
    
    def subscribe(self, event_type: str, component_id: str, callback):
        """订阅事件"""
        if event_type not in self.listeners:
            self.listeners[event_type] = {}
        
        self.listeners[event_type][component_id] = callback
        print(f"✓ 组件 {component_id} 订阅事件: {event_type}")
    
    def publish(self, event_type: str, data: Any, source: str = None):
        """发布事件"""
        event = {
            'type': event_type,
            'data': data,
            'source': source,
            'timestamp': time.time()
        }
        
        self.event_history.append(event)
        
        if event_type in self.listeners:
            for component_id, callback in self.listeners[event_type].items():
                if component_id != source:  # 避免自己通知自己
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"❌ 事件回调错误: {e}")
        
        print(f"📡 发布事件: {event_type} (来源: {source})")
    
    def get_event_history(self, event_type: str = None) -> List[Dict]:
        """获取事件历史"""
        if event_type:
            return [e for e in self.event_history if e['type'] == event_type]
        return self.event_history.copy()


class DashboardStateManager:
    """仪表板状态管理器"""
    
    def __init__(self):
        self.state = {
            'metadata': {},
            'layout': [],
            'filters': {},
            'selections': {},
            'ui_state': {
                'edit_mode': False,
                'focused_component': None
            }
        }
        self.state_history = []
        self.max_history = 50
    
    def get_state(self) -> Dict:
        """获取当前状态"""
        return self.state.copy()
    
    def update_state(self, updates: Dict):
        """更新状态"""
        # 保存历史状态
        self._save_to_history()
        
        # 更新状态
        self._deep_update(self.state, updates)
        
        print(f"🔄 状态已更新: {list(updates.keys())}")
    
    def _save_to_history(self):
        """保存到历史记录"""
        self.state_history.append({
            'state': json.loads(json.dumps(self.state)),
            'timestamp': time.time()
        })
        
        # 限制历史记录数量
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
    
    def _deep_update(self, target: Dict, source: Dict):
        """深度更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def undo(self) -> bool:
        """撤销操作"""
        if self.state_history:
            previous_state = self.state_history.pop()
            self.state = previous_state['state']
            print("↶ 撤销操作成功")
            return True
        return False
    
    def get_history_summary(self) -> List[Dict]:
        """获取历史摘要"""
        return [
            {
                'timestamp': h['timestamp'],
                'keys_changed': list(h['state'].keys())
            }
            for h in self.state_history[-10:]  # 最近10条
        ]


class DashboardPerformanceMonitor:
    """仪表板性能监控器"""
    
    def __init__(self):
        self.metrics = {
            'render_times': {},
            'data_load_times': {},
            'memory_usage': [],
            'event_counts': {}
        }
    
    def start_timer(self, operation: str, component_id: str = None):
        """开始计时"""
        key = f"{operation}:{component_id}" if component_id else operation
        self.metrics[f"_start_{key}"] = time.time()
    
    def end_timer(self, operation: str, component_id: str = None):
        """结束计时"""
        key = f"{operation}:{component_id}" if component_id else operation
        start_key = f"_start_{key}"
        
        if start_key in self.metrics:
            duration = time.time() - self.metrics[start_key]
            
            if operation not in self.metrics:
                self.metrics[operation] = []
            
            self.metrics[operation].append({
                'component_id': component_id,
                'duration': duration,
                'timestamp': time.time()
            })
            
            del self.metrics[start_key]
            return duration
        
        return None
    
    def record_event(self, event_type: str):
        """记录事件"""
        if event_type not in self.metrics['event_counts']:
            self.metrics['event_counts'][event_type] = 0
        
        self.metrics['event_counts'][event_type] += 1
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        summary = {
            'total_events': sum(self.metrics['event_counts'].values()),
            'avg_render_time': 0,
            'slow_components': []
        }
        
        # 计算平均渲染时间
        if 'render' in self.metrics:
            render_times = [m['duration'] for m in self.metrics['render']]
            if render_times:
                summary['avg_render_time'] = sum(render_times) / len(render_times)
                
                # 找出慢组件
                avg_time = summary['avg_render_time']
                summary['slow_components'] = [
                    m['component_id'] for m in self.metrics['render']
                    if m['duration'] > avg_time * 2 and m['component_id']
                ]
        
        return summary


class MockDashboard:
    """模拟仪表板"""
    
    def __init__(self, dashboard_id: str = None):
        self.id = dashboard_id or str(uuid.uuid4())
        self.title = "演示仪表板"
        
        # 初始化各个系统
        self.layout_engine = GridLayoutEngine()
        self.event_system = ComponentEventSystem()
        self.state_manager = DashboardStateManager()
        self.performance_monitor = DashboardPerformanceMonitor()
        
        # 设置事件监听
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """设置事件监听器"""
        # 监听过滤器变化
        self.event_system.subscribe('filter_changed', 'dashboard', 
                                   self._handle_filter_change)
        
        # 监听组件选择
        self.event_system.subscribe('component_selected', 'dashboard',
                                   self._handle_component_selection)
    
    def _handle_filter_change(self, event):
        """处理过滤器变化"""
        filter_data = event['data']
        
        # 更新状态
        self.state_manager.update_state({
            'filters': {
                filter_data['filter_id']: filter_data['value']
            }
        })
        
        # 通知相关组件更新
        self.event_system.publish('data_refresh_needed', {
            'filter_id': filter_data['filter_id'],
            'affected_components': filter_data.get('scope', [])
        })
    
    def _handle_component_selection(self, event):
        """处理组件选择"""
        selection_data = event['data']
        
        # 更新状态
        self.state_manager.update_state({
            'selections': {
                selection_data['component_id']: selection_data['selection']
            }
        })
    
    def add_component(self, component: DashboardComponent):
        """添加组件到仪表板"""
        self.performance_monitor.start_timer('add_component', component.config.id)
        
        self.layout_engine.add_component(component)
        
        # 更新状态
        layout = self.layout_engine.get_layout()
        self.state_manager.update_state({'layout': layout})
        
        duration = self.performance_monitor.end_timer('add_component', component.config.id)
        print(f"  ⏱️ 添加耗时: {duration:.3f}s")
    
    def render_dashboard(self) -> Dict:
        """渲染整个仪表板"""
        self.performance_monitor.start_timer('render_dashboard')
        
        rendered_components = []
        
        for component in self.layout_engine.components.values():
            self.performance_monitor.start_timer('render', component.config.id)
            
            rendered_component = component.render()
            rendered_components.append(rendered_component)
            
            self.performance_monitor.end_timer('render', component.config.id)
        
        dashboard_data = {
            'id': self.id,
            'title': self.title,
            'layout': self.layout_engine.get_layout(),
            'components': rendered_components,
            'state': self.state_manager.get_state(),
            'performance': self.performance_monitor.get_performance_summary()
        }
        
        duration = self.performance_monitor.end_timer('render_dashboard')
        print(f"🎨 仪表板渲染完成，耗时: {duration:.3f}s")
        
        return dashboard_data


def demo_dashboard_creation():
    """演示仪表板创建"""
    print("\n" + "="*60)
    print("🏗️ 仪表板创建演示")
    print("="*60)
    
    # 创建仪表板
    dashboard = MockDashboard()
    print(f"✓ 创建仪表板: {dashboard.id}")
    
    # 添加图表组件
    chart1 = ChartComponent(ComponentConfig(
        id="chart_1",
        type="line",
        x=0, y=0, width=6, height=4,
        title="销售趋势图",
        config={"chart_type": "line", "metrics": ["sales"]}
    ))
    
    chart2 = ChartComponent(ComponentConfig(
        id="chart_2", 
        type="bar",
        x=6, y=0, width=6, height=4,
        title="地区分布图",
        config={"chart_type": "bar", "metrics": ["revenue"]}
    ))
    
    # 添加过滤器组件
    filter1 = FilterComponent(ComponentConfig(
        id="filter_1",
        type="select",
        x=0, y=4, width=12, height=2,
        title="时间过滤器",
        config={"filter_type": "date_range"}
    ))
    
    # 添加文本组件
    text1 = TextComponent(ComponentConfig(
        id="text_1",
        type="markdown",
        x=0, y=6, width=12, height=2,
        title="说明文档",
        config={
            "content": "# 销售数据分析\n这是一个演示仪表板，展示了销售数据的各个维度。",
            "style": {"fontSize": "14px"}
        }
    ))
    
    # 添加组件到仪表板
    dashboard.add_component(chart1)
    dashboard.add_component(chart2)
    dashboard.add_component(filter1)
    dashboard.add_component(text1)
    
    return dashboard


def demo_layout_operations(dashboard):
    """演示布局操作"""
    print("\n" + "="*60)
    print("📐 布局操作演示")
    print("="*60)
    
    # 检测布局冲突
    collisions = dashboard.layout_engine.detect_collisions()
    print(f"🔍 布局冲突检测: {len(collisions)} 个冲突")
    
    if collisions:
        print(f"  冲突组件: {collisions}")
    
    # 模拟拖拽操作
    print("\n🖱️ 模拟拖拽操作:")
    new_layout = [
        {'i': 'chart_1', 'x': 0, 'y': 0, 'w': 8, 'h': 4},
        {'i': 'chart_2', 'x': 8, 'y': 0, 'w': 4, 'h': 4},
        {'i': 'filter_1', 'x': 0, 'y': 4, 'w': 12, 'h': 2},
        {'i': 'text_1', 'x': 0, 'y': 6, 'w': 12, 'h': 2}
    ]
    
    dashboard.layout_engine.update_layout(new_layout)
    
    # 自动布局
    print("\n🔄 自动布局:")
    dashboard.layout_engine.auto_layout()
    
    # 显示最终布局
    final_layout = dashboard.layout_engine.get_layout()
    print(f"📋 最终布局: {len(final_layout)} 个组件")
    for item in final_layout:
        print(f"  {item['i']}: ({item['x']}, {item['y']}) {item['w']}x{item['h']}")


def demo_component_interaction(dashboard):
    """演示组件交互"""
    print("\n" + "="*60)
    print("🔗 组件交互演示")
    print("="*60)
    
    # 模拟过滤器变化
    print("🎛️ 模拟过滤器操作:")
    dashboard.event_system.publish('filter_changed', {
        'filter_id': 'filter_1',
        'value': {'start_date': '2023-01-01', 'end_date': '2023-12-31'},
        'scope': ['chart_1', 'chart_2']
    }, source='filter_1')
    
    # 模拟图表选择
    print("\n📊 模拟图表选择:")
    dashboard.event_system.publish('component_selected', {
        'component_id': 'chart_1',
        'selection': {'region': 'North', 'value': 1000}
    }, source='chart_1')
    
    # 显示事件历史
    event_history = dashboard.event_system.get_event_history()
    print(f"\n📜 事件历史: {len(event_history)} 个事件")
    for event in event_history[-3:]:  # 显示最近3个事件
        print(f"  {event['type']} (来源: {event['source']})")


def demo_state_management(dashboard):
    """演示状态管理"""
    print("\n" + "="*60)
    print("🗃️ 状态管理演示")
    print("="*60)
    
    # 显示当前状态
    current_state = dashboard.state_manager.get_state()
    print(f"📊 当前状态键: {list(current_state.keys())}")
    
    # 更新状态
    print("\n🔄 更新状态:")
    dashboard.state_manager.update_state({
        'ui_state': {
            'edit_mode': True,
            'focused_component': 'chart_1'
        },
        'metadata': {
            'last_modified': time.time(),
            'version': '1.0'
        }
    })
    
    # 显示历史记录
    history = dashboard.state_manager.get_history_summary()
    print(f"\n📚 状态历史: {len(history)} 条记录")
    
    # 测试撤销功能
    print("\n↶ 测试撤销功能:")
    success = dashboard.state_manager.undo()
    print(f"  撤销结果: {'成功' if success else '失败'}")


def demo_performance_monitoring(dashboard):
    """演示性能监控"""
    print("\n" + "="*60)
    print("⚡ 性能监控演示")
    print("="*60)
    
    # 渲染仪表板并监控性能
    dashboard_data = dashboard.render_dashboard()
    
    # 显示性能摘要
    performance = dashboard_data['performance']
    print(f"\n📈 性能摘要:")
    print(f"  总事件数: {performance['total_events']}")
    print(f"  平均渲染时间: {performance['avg_render_time']:.3f}s")
    
    if performance['slow_components']:
        print(f"  慢组件: {performance['slow_components']}")
    else:
        print("  ✓ 所有组件性能良好")
    
    # 显示详细指标
    monitor = dashboard.performance_monitor
    print(f"\n📊 详细指标:")
    print(f"  事件计数: {monitor.metrics['event_counts']}")


def main():
    """主演示函数"""
    print("🎨 Day 6 仪表板系统演示")
    print("=" * 60)
    
    try:
        # 创建仪表板
        dashboard = demo_dashboard_creation()
        
        # 演示各个功能
        demo_layout_operations(dashboard)
        demo_component_interaction(dashboard)
        demo_state_management(dashboard)
        demo_performance_monitoring(dashboard)
        
        print("\n" + "="*60)
        print("✅ 仪表板系统演示完成！")
        print("\n📚 核心功能总结:")
        print("- 组件化架构：支持多种类型的仪表板组件")
        print("- 布局引擎：网格系统、拖拽、自动布局")
        print("- 事件系统：组件间通信和交互")
        print("- 状态管理：统一的状态管理和历史记录")
        print("- 性能监控：实时性能分析和优化建议")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 