#!/usr/bin/env python3
"""
Layout Engine Demo - 布局引擎演示

这个脚本演示了 Superset 仪表板布局引擎的核心概念和实现原理，
包括网格系统、组件布局、响应式设计等功能。
"""

import json
import math
import copy
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class ComponentType(Enum):
    """组件类型枚举"""
    DASHBOARD_ROOT = "DASHBOARD_ROOT"
    DASHBOARD_GRID = "DASHBOARD_GRID"
    ROW = "ROW"
    COLUMN = "COLUMN"
    CHART = "CHART"
    MARKDOWN = "MARKDOWN"
    TABS = "TABS"
    TAB = "TAB"
    HEADER = "HEADER"
    DIVIDER = "DIVIDER"


@dataclass
class ComponentMeta:
    """组件元数据"""
    width: int = 12
    height: int = 8
    background: str = "BACKGROUND_TRANSPARENT"
    chart_id: Optional[int] = None
    slice_name: Optional[str] = None
    slice_name_override: Optional[str] = None
    text: Optional[str] = None
    code: Optional[str] = None


@dataclass
class LayoutPosition:
    """布局位置信息"""
    x: int = 0
    y: int = 0
    w: int = 12
    h: int = 8
    min_w: int = 1
    min_h: int = 1
    max_w: Optional[int] = None
    max_h: Optional[int] = None
    static: bool = False
    is_draggable: bool = True
    is_resizable: bool = True


@dataclass
class DashboardComponent:
    """仪表板组件"""
    id: str
    type: ComponentType
    meta: ComponentMeta
    children: List[str]
    parents: List[str]


class LayoutEngine:
    """布局引擎"""
    
    # 网格系统常量
    GRID_COLUMN_COUNT = 12
    GRID_GUTTER_SIZE = 16
    GRID_BASE_UNIT = 24
    GRID_MIN_COLUMN_COUNT = 1
    GRID_MIN_ROW_UNITS = 1
    
    # 响应式断点
    BREAKPOINTS = {
        'lg': 1200,
        'md': 996,
        'sm': 768,
        'xs': 480,
        'xxs': 0,
    }
    
    # 各断点的列数
    COLS = {
        'lg': 12,
        'md': 10,
        'sm': 6,
        'xs': 4,
        'xxs': 2,
    }
    
    def __init__(self):
        self.components: Dict[str, DashboardComponent] = {}
        self.layouts: Dict[str, List[LayoutPosition]] = {}
        self.current_breakpoint = 'lg'
        
    def add_component(self, component: DashboardComponent) -> None:
        """添加组件到布局"""
        self.components[component.id] = component
        
    def remove_component(self, component_id: str) -> None:
        """从布局中移除组件"""
        if component_id in self.components:
            component = self.components[component_id]
            
            # 从父组件中移除引用
            for parent_id in component.parents:
                if parent_id in self.components:
                    parent = self.components[parent_id]
                    if component_id in parent.children:
                        parent.children.remove(component_id)
            
            # 递归删除子组件
            for child_id in component.children[:]:
                self.remove_component(child_id)
            
            del self.components[component_id]
    
    def move_component(self, source_id: str, target_parent_id: str, index: int) -> None:
        """移动组件到新位置"""
        if source_id not in self.components or target_parent_id not in self.components:
            return
            
        source_component = self.components[source_id]
        target_parent = self.components[target_parent_id]
        
        # 从原父组件中移除
        for parent_id in source_component.parents:
            if parent_id in self.components:
                parent = self.components[parent_id]
                if source_id in parent.children:
                    parent.children.remove(source_id)
        
        # 添加到新父组件
        target_parent.children.insert(index, source_id)
        source_component.parents = [target_parent_id]
    
    def resize_component(self, component_id: str, width: int, height: int) -> None:
        """调整组件大小"""
        if component_id in self.components:
            component = self.components[component_id]
            component.meta.width = max(self.GRID_MIN_COLUMN_COUNT, min(width, self.GRID_COLUMN_COUNT))
            component.meta.height = max(self.GRID_MIN_ROW_UNITS, height)
    
    def calculate_layout(self, container_width: int) -> List[LayoutPosition]:
        """计算布局位置"""
        breakpoint = self.get_breakpoint(container_width)
        self.current_breakpoint = breakpoint
        
        column_count = self.COLS[breakpoint]
        column_width = (container_width - (column_count - 1) * self.GRID_GUTTER_SIZE) / column_count
        
        layout_positions = []
        current_y = 0
        
        # 遍历根组件的子组件
        root_component = self.get_root_component()
        if root_component:
            self._calculate_component_positions(
                root_component.children, 
                layout_positions, 
                current_y, 
                column_width,
                column_count
            )
        
        return layout_positions
    
    def _calculate_component_positions(self, 
                                     component_ids: List[str], 
                                     positions: List[LayoutPosition],
                                     start_y: int,
                                     column_width: float,
                                     column_count: int) -> int:
        """递归计算组件位置"""
        current_y = start_y
        current_x = 0
        max_height_in_row = 0
        
        for component_id in component_ids:
            if component_id not in self.components:
                continue
                
            component = self.components[component_id]
            
            # 计算组件宽度和高度
            component_width = min(component.meta.width, column_count)
            component_height = component.meta.height
            
            # 检查是否需要换行
            if current_x + component_width > column_count:
                current_y += max_height_in_row
                current_x = 0
                max_height_in_row = 0
            
            # 创建位置信息
            position = LayoutPosition(
                x=current_x,
                y=current_y,
                w=component_width,
                h=component_height,
                min_w=self.GRID_MIN_COLUMN_COUNT,
                min_h=self.GRID_MIN_ROW_UNITS,
                is_draggable=component.type != ComponentType.DASHBOARD_ROOT,
                is_resizable=component.type in [ComponentType.CHART, ComponentType.MARKDOWN],
            )
            
            positions.append(position)
            
            # 更新位置
            current_x += component_width
            max_height_in_row = max(max_height_in_row, component_height)
            
            # 递归处理子组件
            if component.children:
                child_y = self._calculate_component_positions(
                    component.children,
                    positions,
                    current_y,
                    column_width,
                    column_count
                )
                max_height_in_row = max(max_height_in_row, child_y - current_y)
        
        return current_y + max_height_in_row
    
    def get_breakpoint(self, width: int) -> str:
        """根据宽度获取断点"""
        for breakpoint, min_width in sorted(self.BREAKPOINTS.items(), 
                                          key=lambda x: x[1], 
                                          reverse=True):
            if width >= min_width:
                return breakpoint
        return 'xxs'
    
    def get_root_component(self) -> Optional[DashboardComponent]:
        """获取根组件"""
        for component in self.components.values():
            if component.type == ComponentType.DASHBOARD_ROOT:
                return component
        return None
    
    def validate_layout(self) -> List[str]:
        """验证布局完整性"""
        errors = []
        
        # 检查根组件
        root_components = [c for c in self.components.values() 
                          if c.type == ComponentType.DASHBOARD_ROOT]
        if len(root_components) != 1:
            errors.append(f"应该有且仅有一个根组件，当前有 {len(root_components)} 个")
        
        # 检查组件引用完整性
        for component_id, component in self.components.items():
            for child_id in component.children:
                if child_id not in self.components:
                    errors.append(f"组件 {component_id} 的子组件 {child_id} 不存在")
                else:
                    child = self.components[child_id]
                    if component_id not in child.parents:
                        errors.append(f"子组件 {child_id} 的父组件引用不正确")
            
            for parent_id in component.parents:
                if parent_id not in self.components:
                    errors.append(f"组件 {component_id} 的父组件 {parent_id} 不存在")
                else:
                    parent = self.components[parent_id]
                    if component_id not in parent.children:
                        errors.append(f"父组件 {parent_id} 的子组件引用不正确")
        
        return errors
    
    def to_json(self) -> str:
        """导出为 JSON 格式"""
        data = {
            'components': {
                comp_id: {
                    'id': comp.id,
                    'type': comp.type.value,
                    'meta': asdict(comp.meta),
                    'children': comp.children,
                    'parents': comp.parents,
                }
                for comp_id, comp in self.components.items()
            },
            'current_breakpoint': self.current_breakpoint,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def from_json(self, json_str: str) -> None:
        """从 JSON 格式导入"""
        data = json.loads(json_str)
        self.components = {}
        
        for comp_id, comp_data in data['components'].items():
            component = DashboardComponent(
                id=comp_data['id'],
                type=ComponentType(comp_data['type']),
                meta=ComponentMeta(**comp_data['meta']),
                children=comp_data['children'],
                parents=comp_data['parents'],
            )
            self.components[comp_id] = component
        
        self.current_breakpoint = data.get('current_breakpoint', 'lg')


class DashboardBuilder:
    """仪表板构建器"""
    
    def __init__(self):
        self.layout_engine = LayoutEngine()
        self.component_counter = 0
    
    def create_empty_dashboard(self) -> str:
        """创建空仪表板"""
        # 创建根组件
        root_id = self._generate_id()
        root_component = DashboardComponent(
            id=root_id,
            type=ComponentType.DASHBOARD_ROOT,
            meta=ComponentMeta(),
            children=[],
            parents=[],
        )
        
        # 创建网格组件
        grid_id = self._generate_id()
        grid_component = DashboardComponent(
            id=grid_id,
            type=ComponentType.DASHBOARD_GRID,
            meta=ComponentMeta(),
            children=[],
            parents=[root_id],
        )
        
        root_component.children.append(grid_id)
        
        self.layout_engine.add_component(root_component)
        self.layout_engine.add_component(grid_component)
        
        return root_id
    
    def add_chart(self, chart_id: int, chart_name: str, width: int = 6, height: int = 8) -> str:
        """添加图表组件"""
        component_id = self._generate_id()
        
        component = DashboardComponent(
            id=component_id,
            type=ComponentType.CHART,
            meta=ComponentMeta(
                width=width,
                height=height,
                chart_id=chart_id,
                slice_name=chart_name,
            ),
            children=[],
            parents=[],
        )
        
        # 添加到网格中
        grid_component = self._get_grid_component()
        if grid_component:
            grid_component.children.append(component_id)
            component.parents.append(grid_component.id)
        
        self.layout_engine.add_component(component)
        return component_id
    
    def add_markdown(self, text: str, width: int = 12, height: int = 4) -> str:
        """添加文本组件"""
        component_id = self._generate_id()
        
        component = DashboardComponent(
            id=component_id,
            type=ComponentType.MARKDOWN,
            meta=ComponentMeta(
                width=width,
                height=height,
                text=text,
            ),
            children=[],
            parents=[],
        )
        
        # 添加到网格中
        grid_component = self._get_grid_component()
        if grid_component:
            grid_component.children.append(component_id)
            component.parents.append(grid_component.id)
        
        self.layout_engine.add_component(component)
        return component_id
    
    def add_row(self) -> str:
        """添加行组件"""
        component_id = self._generate_id()
        
        component = DashboardComponent(
            id=component_id,
            type=ComponentType.ROW,
            meta=ComponentMeta(width=12, height=1),
            children=[],
            parents=[],
        )
        
        # 添加到网格中
        grid_component = self._get_grid_component()
        if grid_component:
            grid_component.children.append(component_id)
            component.parents.append(grid_component.id)
        
        self.layout_engine.add_component(component)
        return component_id
    
    def add_tabs(self, tab_names: List[str]) -> str:
        """添加标签页组件"""
        tabs_id = self._generate_id()
        
        tabs_component = DashboardComponent(
            id=tabs_id,
            type=ComponentType.TABS,
            meta=ComponentMeta(width=12, height=10),
            children=[],
            parents=[],
        )
        
        # 创建标签页
        for tab_name in tab_names:
            tab_id = self._generate_id()
            tab_component = DashboardComponent(
                id=tab_id,
                type=ComponentType.TAB,
                meta=ComponentMeta(width=12, height=8, text=tab_name),
                children=[],
                parents=[tabs_id],
            )
            
            tabs_component.children.append(tab_id)
            self.layout_engine.add_component(tab_component)
        
        # 添加到网格中
        grid_component = self._get_grid_component()
        if grid_component:
            grid_component.children.append(tabs_id)
            tabs_component.parents.append(grid_component.id)
        
        self.layout_engine.add_component(tabs_component)
        return tabs_id
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        self.component_counter += 1
        return f"component_{self.component_counter}_{uuid.uuid4().hex[:8]}"
    
    def _get_grid_component(self) -> Optional[DashboardComponent]:
        """获取网格组件"""
        for component in self.layout_engine.components.values():
            if component.type == ComponentType.DASHBOARD_GRID:
                return component
        return None


def demo_basic_layout():
    """基础布局演示"""
    print("=== 基础布局演示 ===")
    
    builder = DashboardBuilder()
    
    # 创建空仪表板
    root_id = builder.create_empty_dashboard()
    print(f"创建仪表板，根组件ID: {root_id}")
    
    # 添加图表
    chart1_id = builder.add_chart(1, "销售趋势图", width=8, height=6)
    chart2_id = builder.add_chart(2, "产品分布图", width=4, height=6)
    chart3_id = builder.add_chart(3, "地区销售额", width=6, height=8)
    
    print(f"添加图表: {chart1_id}, {chart2_id}, {chart3_id}")
    
    # 添加文本组件
    text_id = builder.add_markdown("## 销售数据看板\n这是一个销售数据的可视化展示。", width=12, height=2)
    print(f"添加文本组件: {text_id}")
    
    # 计算布局
    layout_positions = builder.layout_engine.calculate_layout(1200)
    print(f"\n布局计算结果 (断点: {builder.layout_engine.current_breakpoint}):")
    for i, pos in enumerate(layout_positions):
        print(f"  组件 {i+1}: x={pos.x}, y={pos.y}, w={pos.w}, h={pos.h}")
    
    # 验证布局
    errors = builder.layout_engine.validate_layout()
    if errors:
        print(f"\n布局验证错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ 布局验证通过")
    
    return builder


def demo_responsive_layout():
    """响应式布局演示"""
    print("\n=== 响应式布局演示 ===")
    
    builder = demo_basic_layout()
    
    # 测试不同屏幕尺寸下的布局
    screen_sizes = [1920, 1200, 996, 768, 480, 320]
    
    for width in screen_sizes:
        layout_positions = builder.layout_engine.calculate_layout(width)
        breakpoint = builder.layout_engine.get_breakpoint(width)
        column_count = builder.layout_engine.COLS[breakpoint]
        
        print(f"\n屏幕宽度: {width}px, 断点: {breakpoint}, 列数: {column_count}")
        for i, pos in enumerate(layout_positions):
            print(f"  组件 {i+1}: x={pos.x}, y={pos.y}, w={pos.w}, h={pos.h}")


def demo_advanced_features():
    """高级功能演示"""
    print("\n=== 高级功能演示 ===")
    
    builder = DashboardBuilder()
    root_id = builder.create_empty_dashboard()
    
    # 创建复杂布局
    header_id = builder.add_markdown("# 企业数据大屏", width=12, height=2)
    
    # 添加标签页
    tabs_id = builder.add_tabs(["销售分析", "产品分析", "客户分析"])
    
    # 添加图表到标签页中
    for i in range(3):
        chart_id = builder.add_chart(i+10, f"图表 {i+1}", width=6, height=8)
    
    print("创建了包含标签页的复杂布局")
    
    # 组件移动演示
    print("\n演示组件移动:")
    components = list(builder.layout_engine.components.keys())
    if len(components) >= 2:
        builder.layout_engine.move_component(components[1], components[0], 0)
        print("移动了一个组件")
    
    # 组件调整大小演示
    print("\n演示组件调整大小:")
    chart_components = [comp for comp in builder.layout_engine.components.values() 
                       if comp.type == ComponentType.CHART]
    if chart_components:
        chart_id = chart_components[0].id
        builder.layout_engine.resize_component(chart_id, 10, 12)
        print(f"调整了图表 {chart_id} 的大小")
    
    # 导出和导入演示
    print("\n演示导出和导入:")
    json_data = builder.layout_engine.to_json()
    print("导出为 JSON (前100字符):", json_data[:100] + "...")
    
    # 创建新的布局引擎并导入
    new_engine = LayoutEngine()
    new_engine.from_json(json_data)
    print("✅ 成功导入布局数据")
    
    return builder


def demo_performance_optimization():
    """性能优化演示"""
    print("\n=== 性能优化演示 ===")
    
    builder = DashboardBuilder()
    root_id = builder.create_empty_dashboard()
    
    # 创建大量组件测试性能
    import time
    
    start_time = time.time()
    component_ids = []
    
    # 添加100个图表组件
    for i in range(100):
        chart_id = builder.add_chart(i, f"图表 {i}", width=3, height=4)
        component_ids.append(chart_id)
    
    creation_time = time.time() - start_time
    print(f"创建100个组件耗时: {creation_time:.3f}秒")
    
    # 测试布局计算性能
    start_time = time.time()
    layout_positions = builder.layout_engine.calculate_layout(1200)
    calculation_time = time.time() - start_time
    print(f"布局计算耗时: {calculation_time:.3f}秒")
    
    # 测试组件移动性能
    start_time = time.time()
    for i in range(10):
        if len(component_ids) >= 2:
            builder.layout_engine.move_component(
                component_ids[i], 
                builder.layout_engine.get_root_component().id, 
                0
            )
    move_time = time.time() - start_time
    print(f"10次组件移动耗时: {move_time:.3f}秒")
    
    # 内存使用情况
    import sys
    memory_usage = sys.getsizeof(builder.layout_engine.components)
    print(f"组件数据内存使用: {memory_usage} 字节")


def demo_layout_algorithms():
    """布局算法演示"""
    print("\n=== 布局算法演示 ===")
    
    builder = DashboardBuilder()
    root_id = builder.create_empty_dashboard()
    
    # 创建不同尺寸的组件
    components = [
        (2, 4, "小图表1"),
        (4, 6, "中图表1"),
        (6, 8, "大图表1"),
        (3, 4, "小图表2"),
        (4, 4, "正方形图表"),
        (8, 6, "宽图表"),
        (2, 8, "高图表"),
    ]
    
    for width, height, name in components:
        builder.add_chart(len(builder.layout_engine.components), name, width, height)
    
    print("创建了不同尺寸的组件，演示自动排列算法:")
    layout_positions = builder.layout_engine.calculate_layout(1200)
    
    for i, pos in enumerate(layout_positions):
        component_name = components[i][2] if i < len(components) else f"组件{i+1}"
        print(f"  {component_name}: 位置({pos.x}, {pos.y}), 大小({pos.w}×{pos.h})")
    
    # 可视化布局
    print("\n布局可视化 (简化版):")
    grid = [[' ' for _ in range(12)] for _ in range(20)]
    
    for i, pos in enumerate(layout_positions[:len(components)]):
        char = str(i + 1)
        for y in range(pos.y, min(pos.y + pos.h, 20)):
            for x in range(pos.x, min(pos.x + pos.w, 12)):
                grid[y][x] = char
    
    for row in grid:
        if any(cell != ' ' for cell in row):
            print(''.join(row))


if __name__ == "__main__":
    print("Superset 仪表板布局引擎演示")
    print("=" * 50)
    
    # 运行所有演示
    demo_basic_layout()
    demo_responsive_layout()
    demo_advanced_features()
    demo_performance_optimization()
    demo_layout_algorithms()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print("\n主要功能演示:")
    print("✅ 基础布局创建和管理")
    print("✅ 响应式布局计算")
    print("✅ 组件移动和调整大小")
    print("✅ 布局验证和错误检查")
    print("✅ JSON 导出和导入")
    print("✅ 性能优化测试")
    print("✅ 自动布局算法")
    print("\n🎯 学习收获:")
    print("- 理解了网格布局系统的实现原理")
    print("- 掌握了响应式设计的断点计算")
    print("- 学会了组件层次结构的管理")
    print("- 了解了布局引擎的性能优化策略") 