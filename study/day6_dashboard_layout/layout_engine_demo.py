#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 6 布局引擎演示
================

本脚本演示高级布局引擎功能：
- 响应式布局
- 拖拽系统
- 碰撞检测
- 自动布局算法
- 布局优化
"""

import math
import time
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class BreakPoint(Enum):
    """响应式断点"""
    XXS = 0
    XS = 480
    SM = 768
    MD = 996
    LG = 1200
    XL = 1600


@dataclass
class LayoutItem:
    """布局项"""
    i: str  # 组件ID
    x: int  # X坐标
    y: int  # Y坐标
    w: int  # 宽度
    h: int  # 高度
    minW: int = 1  # 最小宽度
    minH: int = 1  # 最小高度
    maxW: Optional[int] = None  # 最大宽度
    maxH: Optional[int] = None  # 最大高度
    static: bool = False  # 是否静态（不可移动）
    isDraggable: bool = True  # 是否可拖拽
    isResizable: bool = True  # 是否可调整大小


class CollisionDetector:
    """碰撞检测器"""
    
    @staticmethod
    def check_collision(item1: LayoutItem, item2: LayoutItem) -> bool:
        """检查两个布局项是否碰撞"""
        return not (
            item1.x + item1.w <= item2.x or
            item2.x + item2.w <= item1.x or
            item1.y + item1.h <= item2.y or
            item2.y + item2.h <= item1.y
        )
    
    @staticmethod
    def get_collisions(layout: List[LayoutItem]) -> List[Tuple[str, str]]:
        """获取所有碰撞对"""
        collisions = []
        
        for i, item1 in enumerate(layout):
            for item2 in layout[i+1:]:
                if CollisionDetector.check_collision(item1, item2):
                    collisions.append((item1.i, item2.i))
        
        return collisions
    
    @staticmethod
    def resolve_collision(moving_item: LayoutItem, static_items: List[LayoutItem]) -> LayoutItem:
        """解决碰撞"""
        resolved_item = LayoutItem(**moving_item.__dict__)
        
        # 尝试向下移动
        max_y = 0
        for static_item in static_items:
            if CollisionDetector.check_collision(resolved_item, static_item):
                max_y = max(max_y, static_item.y + static_item.h)
        
        if max_y > 0:
            resolved_item.y = max_y
        
        return resolved_item


class ResponsiveLayoutManager:
    """响应式布局管理器"""
    
    def __init__(self):
        self.breakpoints = {
            BreakPoint.LG: 12,   # 大屏幕 12列
            BreakPoint.MD: 10,   # 中屏幕 10列
            BreakPoint.SM: 6,    # 小屏幕 6列
            BreakPoint.XS: 4,    # 超小屏幕 4列
            BreakPoint.XXS: 2    # 最小屏幕 2列
        }
        self.layouts = {}  # 存储不同断点的布局
    
    def get_breakpoint(self, width: int) -> BreakPoint:
        """根据宽度获取断点"""
        for breakpoint in [BreakPoint.XL, BreakPoint.LG, BreakPoint.MD, 
                          BreakPoint.SM, BreakPoint.XS, BreakPoint.XXS]:
            if width >= breakpoint.value:
                return breakpoint
        return BreakPoint.XXS
    
    def get_columns(self, breakpoint: BreakPoint) -> int:
        """获取断点对应的列数"""
        return self.breakpoints.get(breakpoint, 12)
    
    def generate_responsive_layout(self, base_layout: List[LayoutItem], 
                                 target_breakpoint: BreakPoint) -> List[LayoutItem]:
        """生成响应式布局"""
        base_columns = 12
        target_columns = self.get_columns(target_breakpoint)
        scale_factor = target_columns / base_columns
        
        responsive_layout = []
        
        for item in base_layout:
            responsive_item = LayoutItem(
                i=item.i,
                x=max(0, min(int(item.x * scale_factor), target_columns - 1)),
                y=item.y,  # Y坐标不缩放
                w=max(1, min(int(item.w * scale_factor), target_columns)),
                h=item.h,
                minW=max(1, int(item.minW * scale_factor)),
                minH=item.minH,
                maxW=int(item.maxW * scale_factor) if item.maxW else None,
                maxH=item.maxH,
                static=item.static,
                isDraggable=item.isDraggable,
                isResizable=item.isResizable
            )
            
            # 确保组件不超出边界
            if responsive_item.x + responsive_item.w > target_columns:
                responsive_item.w = target_columns - responsive_item.x
            
            responsive_layout.append(responsive_item)
        
        return responsive_layout
    
    def compact_layout(self, layout: List[LayoutItem]) -> List[LayoutItem]:
        """压缩布局，移除空隙"""
        # 按Y坐标排序
        sorted_layout = sorted(layout, key=lambda x: (x.y, x.x))
        compacted_layout = []
        
        for item in sorted_layout:
            # 找到最高可放置位置
            min_y = 0
            for placed_item in compacted_layout:
                if (item.x < placed_item.x + placed_item.w and 
                    item.x + item.w > placed_item.x):
                    min_y = max(min_y, placed_item.y + placed_item.h)
            
            compacted_item = LayoutItem(**item.__dict__)
            compacted_item.y = min_y
            compacted_layout.append(compacted_item)
        
        return compacted_layout


class DragDropManager:
    """拖拽管理器"""
    
    def __init__(self, grid_columns: int = 12, row_height: int = 100):
        self.grid_columns = grid_columns
        self.row_height = row_height
        self.grid_width = 1200  # 假设网格总宽度
        self.col_width = self.grid_width / grid_columns
        
        self.drag_state = None
        self.collision_detector = CollisionDetector()
    
    def start_drag(self, item_id: str, layout: List[LayoutItem], 
                   mouse_pos: Tuple[int, int]) -> Dict:
        """开始拖拽"""
        dragging_item = next((item for item in layout if item.i == item_id), None)
        if not dragging_item or not dragging_item.isDraggable:
            return {'success': False, 'error': 'Item not draggable'}
        
        self.drag_state = {
            'item_id': item_id,
            'original_layout': [LayoutItem(**item.__dict__) for item in layout],
            'start_mouse_pos': mouse_pos,
            'start_item_pos': (dragging_item.x, dragging_item.y)
        }
        
        return {'success': True, 'drag_state': self.drag_state}
    
    def update_drag(self, mouse_pos: Tuple[int, int], layout: List[LayoutItem]) -> List[LayoutItem]:
        """更新拖拽位置"""
        if not self.drag_state:
            return layout
        
        # 计算鼠标移动距离
        dx = mouse_pos[0] - self.drag_state['start_mouse_pos'][0]
        dy = mouse_pos[1] - self.drag_state['start_mouse_pos'][1]
        
        # 转换为网格坐标
        grid_dx = round(dx / self.col_width)
        grid_dy = round(dy / self.row_height)
        
        # 更新拖拽项位置
        dragging_item = next(item for item in layout if item.i == self.drag_state['item_id'])
        original_pos = self.drag_state['start_item_pos']
        
        new_x = max(0, min(original_pos[0] + grid_dx, self.grid_columns - dragging_item.w))
        new_y = max(0, original_pos[1] + grid_dy)
        
        dragging_item.x = new_x
        dragging_item.y = new_y
        
        # 解决碰撞
        other_items = [item for item in layout if item.i != self.drag_state['item_id']]
        resolved_item = self.collision_detector.resolve_collision(dragging_item, other_items)
        
        # 更新布局
        for i, item in enumerate(layout):
            if item.i == self.drag_state['item_id']:
                layout[i] = resolved_item
                break
        
        return layout
    
    def end_drag(self) -> Dict:
        """结束拖拽"""
        if not self.drag_state:
            return {'success': False, 'error': 'No active drag'}
        
        result = {
            'success': True,
            'item_id': self.drag_state['item_id'],
            'original_layout': self.drag_state['original_layout']
        }
        
        self.drag_state = None
        return result


class AutoLayoutEngine:
    """自动布局引擎"""
    
    def __init__(self, grid_columns: int = 12):
        self.grid_columns = grid_columns
    
    def auto_layout(self, items: List[LayoutItem], algorithm: str = 'flow') -> List[LayoutItem]:
        """自动布局"""
        if algorithm == 'flow':
            return self._flow_layout(items)
        elif algorithm == 'grid':
            return self._grid_layout(items)
        elif algorithm == 'compact':
            return self._compact_layout(items)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def _flow_layout(self, items: List[LayoutItem]) -> List[LayoutItem]:
        """流式布局"""
        layout = []
        current_x = 0
        current_y = 0
        row_height = 0
        
        for item in items:
            # 检查是否需要换行
            if current_x + item.w > self.grid_columns:
                current_x = 0
                current_y += row_height
                row_height = 0
            
            # 放置组件
            new_item = LayoutItem(**item.__dict__)
            new_item.x = current_x
            new_item.y = current_y
            layout.append(new_item)
            
            # 更新位置
            current_x += item.w
            row_height = max(row_height, item.h)
        
        return layout
    
    def _grid_layout(self, items: List[LayoutItem]) -> List[LayoutItem]:
        """网格布局"""
        layout = []
        
        # 计算网格尺寸
        total_area = sum(item.w * item.h for item in items)
        grid_area = self.grid_columns * math.ceil(total_area / self.grid_columns)
        
        # 按面积排序（大的优先）
        sorted_items = sorted(items, key=lambda x: x.w * x.h, reverse=True)
        
        # 使用贪心算法放置
        occupied = set()
        
        for item in sorted_items:
            best_pos = self._find_best_position(item, occupied)
            
            new_item = LayoutItem(**item.__dict__)
            new_item.x = best_pos[0]
            new_item.y = best_pos[1]
            layout.append(new_item)
            
            # 标记占用区域
            for x in range(best_pos[0], best_pos[0] + item.w):
                for y in range(best_pos[1], best_pos[1] + item.h):
                    occupied.add((x, y))
        
        return layout
    
    def _compact_layout(self, items: List[LayoutItem]) -> List[LayoutItem]:
        """紧凑布局"""
        # 先进行流式布局
        layout = self._flow_layout(items)
        
        # 然后压缩空隙
        responsive_manager = ResponsiveLayoutManager()
        return responsive_manager.compact_layout(layout)
    
    def _find_best_position(self, item: LayoutItem, occupied: set) -> Tuple[int, int]:
        """找到最佳放置位置"""
        for y in range(100):  # 限制搜索范围
            for x in range(self.grid_columns - item.w + 1):
                # 检查位置是否可用
                if self._is_position_available(x, y, item.w, item.h, occupied):
                    return (x, y)
        
        # 如果找不到位置，放在最后
        max_y = max((pos[1] for pos in occupied), default=0)
        return (0, max_y + 1)
    
    def _is_position_available(self, x: int, y: int, w: int, h: int, occupied: set) -> bool:
        """检查位置是否可用"""
        for px in range(x, x + w):
            for py in range(y, y + h):
                if (px, py) in occupied:
                    return False
        return True


class LayoutOptimizer:
    """布局优化器"""
    
    def __init__(self):
        self.metrics = {}
    
    def optimize_layout(self, layout: List[LayoutItem]) -> List[LayoutItem]:
        """优化布局"""
        # 计算当前布局指标
        current_score = self._calculate_layout_score(layout)
        
        # 尝试多种优化策略
        optimized_layouts = [
            self._optimize_spacing(layout),
            self._optimize_alignment(layout),
            self._optimize_grouping(layout)
        ]
        
        # 选择最佳布局
        best_layout = layout
        best_score = current_score
        
        for opt_layout in optimized_layouts:
            score = self._calculate_layout_score(opt_layout)
            if score > best_score:
                best_layout = opt_layout
                best_score = score
        
        self.metrics = {
            'original_score': current_score,
            'optimized_score': best_score,
            'improvement': best_score - current_score
        }
        
        return best_layout
    
    def _calculate_layout_score(self, layout: List[LayoutItem]) -> float:
        """计算布局评分"""
        if not layout:
            return 0
        
        # 计算各项指标
        compactness = self._calculate_compactness(layout)
        alignment = self._calculate_alignment(layout)
        balance = self._calculate_balance(layout)
        
        # 加权平均
        score = (compactness * 0.4 + alignment * 0.3 + balance * 0.3)
        return score
    
    def _calculate_compactness(self, layout: List[LayoutItem]) -> float:
        """计算紧凑度"""
        if not layout:
            return 1.0
        
        # 计算布局的边界框
        max_x = max(item.x + item.w for item in layout)
        max_y = max(item.y + item.h for item in layout)
        
        # 计算实际占用面积
        total_area = sum(item.w * item.h for item in layout)
        bounding_area = max_x * max_y
        
        return total_area / bounding_area if bounding_area > 0 else 1.0
    
    def _calculate_alignment(self, layout: List[LayoutItem]) -> float:
        """计算对齐度"""
        if len(layout) < 2:
            return 1.0
        
        # 计算X和Y坐标的对齐情况
        x_coords = [item.x for item in layout]
        y_coords = [item.y for item in layout]
        
        x_alignment = len(set(x_coords)) / len(x_coords)
        y_alignment = len(set(y_coords)) / len(y_coords)
        
        return 1.0 - (x_alignment + y_alignment) / 2
    
    def _calculate_balance(self, layout: List[LayoutItem]) -> float:
        """计算平衡度"""
        if not layout:
            return 1.0
        
        # 计算重心
        total_weight = sum(item.w * item.h for item in layout)
        if total_weight == 0:
            return 1.0
        
        center_x = sum(item.x * item.w * item.h for item in layout) / total_weight
        center_y = sum(item.y * item.w * item.h for item in layout) / total_weight
        
        # 计算布局中心
        max_x = max(item.x + item.w for item in layout)
        max_y = max(item.y + item.h for item in layout)
        
        layout_center_x = max_x / 2
        layout_center_y = max_y / 2
        
        # 计算偏离度
        deviation = math.sqrt((center_x - layout_center_x)**2 + (center_y - layout_center_y)**2)
        max_deviation = math.sqrt(layout_center_x**2 + layout_center_y**2)
        
        return 1.0 - (deviation / max_deviation) if max_deviation > 0 else 1.0
    
    def _optimize_spacing(self, layout: List[LayoutItem]) -> List[LayoutItem]:
        """优化间距"""
        # 简单实现：压缩垂直间距
        responsive_manager = ResponsiveLayoutManager()
        return responsive_manager.compact_layout(layout)
    
    def _optimize_alignment(self, layout: List[LayoutItem]) -> List[LayoutItem]:
        """优化对齐"""
        optimized_layout = []
        
        # 按行分组
        rows = {}
        for item in layout:
            if item.y not in rows:
                rows[item.y] = []
            rows[item.y].append(item)
        
        # 对每行进行左对齐
        for y, row_items in rows.items():
            row_items.sort(key=lambda x: x.x)
            current_x = 0
            
            for item in row_items:
                new_item = LayoutItem(**item.__dict__)
                new_item.x = current_x
                optimized_layout.append(new_item)
                current_x += item.w
        
        return optimized_layout
    
    def _optimize_grouping(self, layout: List[LayoutItem]) -> List[LayoutItem]:
        """优化分组"""
        # 简单实现：按大小分组
        small_items = [item for item in layout if item.w * item.h <= 4]
        large_items = [item for item in layout if item.w * item.h > 4]
        
        auto_engine = AutoLayoutEngine()
        
        # 先放置大组件
        optimized_layout = auto_engine._flow_layout(large_items)
        
        # 再放置小组件
        if small_items:
            # 找到可用空间放置小组件
            for small_item in small_items:
                # 简单地放在最后
                max_y = max((item.y + item.h for item in optimized_layout), default=0)
                new_item = LayoutItem(**small_item.__dict__)
                new_item.x = 0
                new_item.y = max_y
                optimized_layout.append(new_item)
        
        return optimized_layout


def create_sample_layout() -> List[LayoutItem]:
    """创建示例布局"""
    return [
        LayoutItem(i="chart1", x=0, y=0, w=6, h=4, minW=3, minH=2),
        LayoutItem(i="chart2", x=6, y=0, w=6, h=4, minW=3, minH=2),
        LayoutItem(i="filter1", x=0, y=4, w=12, h=2, minW=6, minH=1),
        LayoutItem(i="chart3", x=0, y=6, w=4, h=3, minW=2, minH=2),
        LayoutItem(i="chart4", x=4, y=6, w=4, h=3, minW=2, minH=2),
        LayoutItem(i="chart5", x=8, y=6, w=4, h=3, minW=2, minH=2),
        LayoutItem(i="text1", x=0, y=9, w=12, h=2, minW=6, minH=1),
    ]


def demo_collision_detection():
    """演示碰撞检测"""
    print("\n" + "="*60)
    print("💥 碰撞检测演示")
    print("="*60)
    
    layout = create_sample_layout()
    
    # 创建一个会碰撞的布局
    layout[1].x = 4  # chart2 移动到会与 chart1 重叠的位置
    
    detector = CollisionDetector()
    collisions = detector.get_collisions(layout)
    
    print(f"🔍 检测到 {len(collisions)} 个碰撞:")
    for collision in collisions:
        print(f"  {collision[0]} ↔ {collision[1]}")
    
    if collisions:
        # 解决碰撞
        print("\n🔧 解决碰撞:")
        moving_item = next(item for item in layout if item.i == collisions[0][1])
        static_items = [item for item in layout if item.i != collisions[0][1]]
        
        resolved_item = detector.resolve_collision(moving_item, static_items)
        print(f"  {resolved_item.i}: ({moving_item.x}, {moving_item.y}) → ({resolved_item.x}, {resolved_item.y})")


def demo_responsive_layout():
    """演示响应式布局"""
    print("\n" + "="*60)
    print("📱 响应式布局演示")
    print("="*60)
    
    layout = create_sample_layout()
    manager = ResponsiveLayoutManager()
    
    # 测试不同断点
    breakpoints = [BreakPoint.LG, BreakPoint.MD, BreakPoint.SM, BreakPoint.XS]
    
    for bp in breakpoints:
        responsive_layout = manager.generate_responsive_layout(layout, bp)
        columns = manager.get_columns(bp)
        
        print(f"\n📐 {bp.name} 断点 ({columns} 列):")
        for item in responsive_layout[:3]:  # 只显示前3个
            print(f"  {item.i}: ({item.x}, {item.y}) {item.w}x{item.h}")
    
    # 演示布局压缩
    print(f"\n🗜️ 布局压缩演示:")
    original_height = max(item.y + item.h for item in layout)
    compacted_layout = manager.compact_layout(layout)
    compacted_height = max(item.y + item.h for item in compacted_layout)
    
    print(f"  原始高度: {original_height}")
    print(f"  压缩后高度: {compacted_height}")
    print(f"  节省空间: {original_height - compacted_height} 行")


def demo_drag_drop():
    """演示拖拽功能"""
    print("\n" + "="*60)
    print("🖱️ 拖拽功能演示")
    print("="*60)
    
    layout = create_sample_layout()
    drag_manager = DragDropManager()
    
    # 模拟拖拽操作
    print("🎯 开始拖拽 chart1:")
    start_result = drag_manager.start_drag("chart1", layout, (100, 100))
    print(f"  拖拽开始: {start_result['success']}")
    
    if start_result['success']:
        # 模拟鼠标移动
        print("\n🔄 模拟鼠标移动:")
        mouse_positions = [(200, 150), (300, 200), (400, 250)]
        
        for i, pos in enumerate(mouse_positions):
            updated_layout = drag_manager.update_drag(pos, layout)
            chart1 = next(item for item in updated_layout if item.i == "chart1")
            print(f"  步骤 {i+1}: chart1 位置 ({chart1.x}, {chart1.y})")
        
        # 结束拖拽
        print("\n🏁 结束拖拽:")
        end_result = drag_manager.end_drag()
        print(f"  拖拽结束: {end_result['success']}")


def demo_auto_layout():
    """演示自动布局"""
    print("\n" + "="*60)
    print("🤖 自动布局演示")
    print("="*60)
    
    # 创建随机布局的组件
    items = [
        LayoutItem(i=f"item{i}", x=0, y=0, w=3, h=2)
        for i in range(6)
    ]
    
    auto_engine = AutoLayoutEngine()
    algorithms = ['flow', 'grid', 'compact']
    
    for algorithm in algorithms:
        print(f"\n📐 {algorithm.upper()} 算法:")
        auto_layout = auto_engine.auto_layout(items, algorithm)
        
        for item in auto_layout:
            print(f"  {item.i}: ({item.x}, {item.y}) {item.w}x{item.h}")
        
        # 计算布局高度
        height = max(item.y + item.h for item in auto_layout)
        print(f"  总高度: {height} 行")


def demo_layout_optimization():
    """演示布局优化"""
    print("\n" + "="*60)
    print("⚡ 布局优化演示")
    print("="*60)
    
    # 创建一个不太优化的布局
    layout = [
        LayoutItem(i="item1", x=1, y=1, w=3, h=2),
        LayoutItem(i="item2", x=5, y=3, w=3, h=2),
        LayoutItem(i="item3", x=2, y=7, w=3, h=2),
        LayoutItem(i="item4", x=7, y=1, w=3, h=2),
    ]
    
    optimizer = LayoutOptimizer()
    
    print("📊 原始布局:")
    for item in layout:
        print(f"  {item.i}: ({item.x}, {item.y}) {item.w}x{item.h}")
    
    # 优化布局
    optimized_layout = optimizer.optimize_layout(layout)
    
    print(f"\n✨ 优化后布局:")
    for item in optimized_layout:
        print(f"  {item.i}: ({item.x}, {item.y}) {item.w}x{item.h}")
    
    # 显示优化指标
    metrics = optimizer.metrics
    print(f"\n📈 优化指标:")
    print(f"  原始评分: {metrics['original_score']:.3f}")
    print(f"  优化评分: {metrics['optimized_score']:.3f}")
    print(f"  改进程度: {metrics['improvement']:.3f}")


def demo_performance_test():
    """演示性能测试"""
    print("\n" + "="*60)
    print("🚀 性能测试演示")
    print("="*60)
    
    # 创建大量组件
    large_layout = [
        LayoutItem(i=f"item{i}", x=i%12, y=i//12, w=2, h=2)
        for i in range(100)
    ]
    
    print(f"📊 测试布局: {len(large_layout)} 个组件")
    
    # 测试碰撞检测性能
    start_time = time.time()
    detector = CollisionDetector()
    collisions = detector.get_collisions(large_layout)
    collision_time = time.time() - start_time
    
    print(f"💥 碰撞检测: {len(collisions)} 个碰撞，耗时 {collision_time:.3f}s")
    
    # 测试自动布局性能
    start_time = time.time()
    auto_engine = AutoLayoutEngine()
    auto_layout = auto_engine.auto_layout(large_layout, 'flow')
    auto_layout_time = time.time() - start_time
    
    print(f"🤖 自动布局: 耗时 {auto_layout_time:.3f}s")
    
    # 测试响应式布局性能
    start_time = time.time()
    manager = ResponsiveLayoutManager()
    responsive_layout = manager.generate_responsive_layout(large_layout, BreakPoint.SM)
    responsive_time = time.time() - start_time
    
    print(f"📱 响应式布局: 耗时 {responsive_time:.3f}s")


def main():
    """主演示函数"""
    print("🎨 Day 6 布局引擎演示")
    print("=" * 60)
    
    try:
        # 演示各个功能
        demo_collision_detection()
        demo_responsive_layout()
        demo_drag_drop()
        demo_auto_layout()
        demo_layout_optimization()
        demo_performance_test()
        
        print("\n" + "="*60)
        print("✅ 布局引擎演示完成！")
        print("\n📚 核心功能总结:")
        print("- 碰撞检测：高效的组件重叠检测和解决")
        print("- 响应式布局：多断点自适应布局系统")
        print("- 拖拽系统：流畅的拖拽交互体验")
        print("- 自动布局：多种智能布局算法")
        print("- 布局优化：基于评分的布局质量优化")
        print("- 性能优化：大规模布局的高效处理")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 