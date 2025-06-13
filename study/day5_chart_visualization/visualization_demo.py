#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 5: 图表系统与可视化引擎演示
=====================================

本演示脚本展示 Superset 图表系统的核心功能：
- 图表类型注册和管理
- 数据处理流水线
- 性能优化策略
- 缓存系统实现
- 图表调试工具

使用方法：
python visualization_demo.py
"""

import pandas as pd
import numpy as np
import json
import time
import hashlib
from typing import Dict, List, Any, Optional
# 可选的可视化库（演示中未使用）
# import matplotlib.pyplot as plt
# import seaborn as sns


class DemoVisualizationRegistry:
    """演示用的可视化注册表"""
    
    def __init__(self):
        self.viz_types = {}
        self.stats = {
            'registered_types': 0,
            'render_count': 0,
            'total_render_time': 0
        }
    
    def register(self, viz_class):
        """注册图表类型"""
        self.viz_types[viz_class.viz_type] = viz_class
        self.stats['registered_types'] += 1
        print(f"✓ 注册图表类型: {viz_class.viz_type} - {viz_class.verbose_name}")
        return viz_class
    
    def get_viz(self, viz_type: str):
        """获取图表类"""
        return self.viz_types.get(viz_type)
    
    def list_types(self):
        """列出所有注册的图表类型"""
        return list(self.viz_types.keys())
    
    def get_stats(self):
        """获取注册表统计信息"""
        avg_render_time = (self.stats['total_render_time'] / self.stats['render_count'] 
                          if self.stats['render_count'] > 0 else 0)
        return {
            **self.stats,
            'avg_render_time': f"{avg_render_time:.3f}s"
        }


# 全局注册表
registry = DemoVisualizationRegistry()


class BaseViz:
    """基础可视化类"""
    
    viz_type = None
    verbose_name = "Base Visualization"
    is_timeseries = False
    default_fillna = 0
    
    def __init__(self, datasource, form_data):
        self.datasource = datasource
        self.form_data = form_data
    
    def query_obj(self):
        """构建查询对象"""
        return {
            'columns': self.form_data.get('groupby', []),
            'metrics': self.form_data.get('metrics', []),
            'filters': self.form_data.get('filters', []),
            'row_limit': self.form_data.get('row_limit', 10000),
        }
    
    def get_data(self, df):
        """处理数据 - 子类需要实现"""
        raise NotImplementedError()
    
    def run_query(self):
        """执行查询"""
        start_time = time.time()
        
        # 获取数据
        df = self.datasource.get_data()
        
        # 处理数据
        result = self.get_data(df)
        
        # 更新统计
        render_time = time.time() - start_time
        registry.stats['render_count'] += 1
        registry.stats['total_render_time'] += render_time
        
        return {
            'data': result,
            'render_time': f"{render_time:.3f}s",
            'rows_processed': len(df)
        }


@registry.register
class CardViz(BaseViz):
    """卡片图表 - 显示单个关键指标"""
    
    viz_type = 'card'
    verbose_name = 'Card Chart'
    
    def get_data(self, df):
        if df.empty:
            return {'value': 0, 'error': 'No data'}
        
        # 获取第一个数值列
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return {'value': 0, 'error': 'No numeric data'}
        
        value = df[numeric_cols[0]].sum()
        
        return {
            'value': value,
            'formatted_value': self._format_value(value),
            'metric_name': numeric_cols[0],
            'chart_type': 'card'
        }
    
    def _format_value(self, value):
        """格式化数值"""
        if value >= 1000000:
            return f"{value/1000000:.1f}M"
        elif value >= 1000:
            return f"{value/1000:.1f}K"
        else:
            return f"{value:.0f}"


@registry.register
class TableViz(BaseViz):
    """表格视图"""
    
    viz_type = 'table'
    verbose_name = 'Table View'
    
    def get_data(self, df):
        return {
            'records': df.head(100).to_dict('records'),  # 限制显示行数
            'columns': [
                {'key': col, 'label': col, 'type': str(df[col].dtype)}
                for col in df.columns
            ],
            'total_count': len(df),
            'display_count': min(100, len(df))
        }


@registry.register
class BarChartViz(BaseViz):
    """柱状图"""
    
    viz_type = 'bar'
    verbose_name = 'Bar Chart'
    
    def get_data(self, df):
        groupby_cols = self.form_data.get('groupby', [])
        metrics = self.form_data.get('metrics', [])
        
        if not groupby_cols or not metrics:
            return {'error': 'Missing groupby or metrics'}
        
        # 简单聚合
        if groupby_cols[0] in df.columns and metrics[0] in df.columns:
            grouped = df.groupby(groupby_cols[0])[metrics[0]].sum().reset_index()
            
            return {
                'categories': grouped[groupby_cols[0]].tolist(),
                'series': [{
                    'name': metrics[0],
                    'data': grouped[metrics[0]].tolist()
                }]
            }
        
        return {'error': 'Invalid columns'}


class MockDataSource:
    """模拟数据源"""
    
    def __init__(self, name: str):
        self.name = name
        self.data = self._generate_sample_data()
    
    def _generate_sample_data(self):
        """生成示例数据"""
        np.random.seed(42)
        
        if self.name == 'orders':
            return pd.DataFrame({
                'order_date': pd.date_range('2023-01-01', periods=1000, freq='1H'),
                'category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Home'], 1000),
                'sales_amount': np.random.exponential(100, 1000),
                'order_count': np.random.poisson(5, 1000),
                'customer_id': np.random.randint(1, 500, 1000)
            })
        elif self.name == 'products':
            return pd.DataFrame({
                'product_id': range(1, 201),
                'category': np.random.choice(['A', 'B', 'C', 'D'], 200),
                'price': np.random.uniform(10, 1000, 200),
                'stock': np.random.randint(0, 100, 200),
                'rating': np.random.uniform(1, 5, 200)
            })
        else:
            return pd.DataFrame({
                'date': pd.date_range('2023-01-01', periods=100, freq='1D'),
                'value': np.random.randn(100) * 100 + 1000,
                'category': np.random.choice(['X', 'Y', 'Z'], 100)
            })
    
    def get_data(self):
        """获取数据"""
        return self.data.copy()


class DataProcessingPipeline:
    """数据处理流水线"""
    
    def __init__(self):
        self.processors = []
        self.processing_stats = {
            'steps_executed': 0,
            'total_processing_time': 0,
            'rows_processed': 0
        }
    
    def add_processor(self, processor):
        """添加处理器"""
        self.processors.append(processor)
        return self
    
    def process(self, df, form_data):
        """执行处理流水线"""
        start_time = time.time()
        original_rows = len(df)
        
        for i, processor in enumerate(self.processors):
            step_start = time.time()
            df = processor.process(df, form_data)
            step_time = time.time() - step_start
            
            print(f"  步骤 {i+1}: {processor.__class__.__name__} - "
                  f"{len(df)}行 - {step_time:.3f}s")
        
        processing_time = time.time() - start_time
        
        # 更新统计
        self.processing_stats['steps_executed'] += len(self.processors)
        self.processing_stats['total_processing_time'] += processing_time
        self.processing_stats['rows_processed'] += original_rows
        
        return df
    
    def get_stats(self):
        """获取处理统计"""
        return self.processing_stats


class NullProcessor:
    """空值处理器"""
    
    def process(self, df, form_data):
        strategy = form_data.get('null_strategy', 'fill_zero')
        
        if strategy == 'fill_zero':
            return df.fillna(0)
        elif strategy == 'drop':
            return df.dropna()
        else:
            return df


class SamplingProcessor:
    """采样处理器"""
    
    def process(self, df, form_data):
        sample_rate = form_data.get('sample_rate', 1.0)
        
        if sample_rate < 1.0 and len(df) > 1000:
            sample_size = max(100, int(len(df) * sample_rate))
            return df.sample(n=min(sample_size, len(df)), random_state=42)
        
        return df


class AggregationProcessor:
    """聚合处理器"""
    
    def process(self, df, form_data):
        groupby_cols = form_data.get('groupby', [])
        metrics = form_data.get('metrics', [])
        
        if not groupby_cols or not metrics:
            return df
        
        # 检查列是否存在
        valid_groupby = [col for col in groupby_cols if col in df.columns]
        valid_metrics = [col for col in metrics if col in df.columns]
        
        if valid_groupby and valid_metrics:
            agg_dict = {metric: 'sum' for metric in valid_metrics}
            return df.groupby(valid_groupby).agg(agg_dict).reset_index()
        
        return df


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.optimization_stats = {
            'optimizations_applied': 0,
            'data_reduction_ratio': [],
            'time_saved': 0
        }
    
    def optimize(self, df, form_data):
        """优化数据集"""
        start_time = time.time()
        original_size = len(df)
        
        optimized_df = df.copy()
        optimizations = []
        
        # 1. 数据采样优化
        if len(df) > 10000:
            sample_rate = min(0.5, 5000 / len(df))
            optimized_df = optimized_df.sample(frac=sample_rate, random_state=42)
            optimizations.append(f"采样: {len(df)} → {len(optimized_df)} 行")
        
        # 2. 列裁剪优化
        required_cols = set()
        required_cols.update(form_data.get('groupby', []))
        required_cols.update(form_data.get('metrics', []))
        
        if required_cols:
            available_cols = [col for col in required_cols if col in optimized_df.columns]
            if available_cols and len(available_cols) < len(optimized_df.columns):
                optimized_df = optimized_df[available_cols]
                optimizations.append(f"列裁剪: {len(df.columns)} → {len(available_cols)} 列")
        
        # 3. 数据类型优化
        for col in optimized_df.select_dtypes(include=['float64']).columns:
            if optimized_df[col].max() < 1e6:  # 小数值可以用 float32
                optimized_df[col] = optimized_df[col].astype('float32')
        
        optimization_time = time.time() - start_time
        reduction_ratio = (original_size - len(optimized_df)) / original_size
        
        # 更新统计
        self.optimization_stats['optimizations_applied'] += 1
        self.optimization_stats['data_reduction_ratio'].append(reduction_ratio)
        self.optimization_stats['time_saved'] += optimization_time
        
        return optimized_df, {
            'original_size': original_size,
            'optimized_size': len(optimized_df),
            'reduction_ratio': f"{reduction_ratio:.2%}",
            'optimization_time': f"{optimization_time:.3f}s",
            'optimizations': optimizations
        }
    
    def get_stats(self):
        """获取优化统计"""
        avg_reduction = (sum(self.optimization_stats['data_reduction_ratio']) / 
                        len(self.optimization_stats['data_reduction_ratio'])
                        if self.optimization_stats['data_reduction_ratio'] else 0)
        
        return {
            **self.optimization_stats,
            'avg_reduction_ratio': f"{avg_reduction:.2%}"
        }


class SimpleCacheManager:
    """简单缓存管理器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0
        }
    
    def get_cache_key(self, slice_id, form_data):
        """生成缓存键"""
        key_data = {'slice_id': slice_id, 'form_data': form_data}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    def get(self, cache_key):
        """获取缓存"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() < entry['expires_at']:
                self.cache_stats['hits'] += 1
                return entry['data']
            else:
                del self.cache[cache_key]
        
        self.cache_stats['misses'] += 1
        return None
    
    def set(self, cache_key, data, ttl=300):
        """设置缓存"""
        self.cache[cache_key] = {
            'data': data,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        self.cache_stats['sets'] += 1
    
    def get_stats(self):
        """获取缓存统计"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100 
                   if total_requests > 0 else 0)
        
        return {
            **self.cache_stats,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': len(self.cache)
        }


def demo_chart_registry():
    """演示图表注册系统"""
    print("\n" + "="*50)
    print("📊 图表注册系统演示")
    print("="*50)
    
    print(f"已注册的图表类型: {registry.list_types()}")
    print(f"注册统计: {registry.get_stats()}")
    
    # 测试不同图表类型
    datasource = MockDataSource('orders')
    
    test_cases = [
        {
            'name': '卡片图表',
            'viz_type': 'card',
            'form_data': {'metrics': ['sales_amount']}
        },
        {
            'name': '表格视图',
            'viz_type': 'table',
            'form_data': {}
        },
        {
            'name': '柱状图',
            'viz_type': 'bar',
            'form_data': {
                'groupby': ['category'],
                'metrics': ['sales_amount']
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 测试 {test_case['name']}:")
        
        viz_class = registry.get_viz(test_case['viz_type'])
        if viz_class:
            viz = viz_class(datasource, test_case['form_data'])
            result = viz.run_query()
            
            print(f"  ✓ 渲染时间: {result['render_time']}")
            print(f"  ✓ 处理行数: {result['rows_processed']}")
            
            # 显示部分结果
            if isinstance(result['data'], dict):
                if 'value' in result['data']:
                    print(f"  ✓ 结果值: {result['data']['formatted_value']}")
                elif 'total_count' in result['data']:
                    print(f"  ✓ 表格行数: {result['data']['total_count']}")
                elif 'categories' in result['data']:
                    print(f"  ✓ 分类数: {len(result['data']['categories'])}")
        else:
            print(f"  ✗ 未找到图表类型: {test_case['viz_type']}")


def demo_data_pipeline():
    """演示数据处理流水线"""
    print("\n" + "="*50)
    print("🔄 数据处理流水线演示")
    print("="*50)
    
    # 创建测试数据
    datasource = MockDataSource('orders')
    df = datasource.get_data()
    
    # 添加一些空值和异常值
    df.loc[50:60, 'sales_amount'] = np.nan
    df.loc[100, 'sales_amount'] = 999999  # 异常值
    
    print(f"原始数据: {len(df)} 行, {len(df.columns)} 列")
    print(f"空值数量: {df.isnull().sum().sum()}")
    
    # 创建处理流水线
    pipeline = DataProcessingPipeline()
    pipeline.add_processor(NullProcessor()) \
           .add_processor(SamplingProcessor()) \
           .add_processor(AggregationProcessor())
    
    # 测试配置
    form_data = {
        'null_strategy': 'fill_zero',
        'sample_rate': 0.7,
        'groupby': ['category'],
        'metrics': ['sales_amount', 'order_count']
    }
    
    print(f"\n处理流水线执行:")
    processed_df = pipeline.process(df, form_data)
    
    print(f"\n处理结果: {len(processed_df)} 行")
    print(f"处理统计: {pipeline.get_stats()}")
    
    # 显示结果样本
    print("\n结果预览:")
    print(processed_df.head().to_string())


def demo_performance_optimization():
    """演示性能优化"""
    print("\n" + "="*50)
    print("⚡ 性能优化演示")
    print("="*50)
    
    # 创建大数据集
    np.random.seed(42)
    large_df = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=50000, freq='1min'),
        'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], 50000),
        'value1': np.random.randn(50000) * 100,
        'value2': np.random.exponential(50, 50000),
        'value3': np.random.uniform(0, 1000, 50000),
        'extra_col1': np.random.randn(50000),
        'extra_col2': np.random.randn(50000),
        'extra_col3': np.random.randn(50000)
    })
    
    print(f"大数据集: {len(large_df):,} 行, {len(large_df.columns)} 列")
    print(f"内存使用: {large_df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    
    # 优化配置
    form_data = {
        'groupby': ['category'],
        'metrics': ['value1', 'value2'],
        'viz_type': 'line'
    }
    
    # 执行优化
    optimizer = PerformanceOptimizer()
    optimized_df, optimization_info = optimizer.optimize(large_df, form_data)
    
    print(f"\n优化结果:")
    for key, value in optimization_info.items():
        print(f"  {key}: {value}")
    
    print(f"\n优化后内存使用: {optimized_df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    
    # 性能对比
    start_time = time.time()
    _ = large_df.groupby('category')['value1'].sum()
    original_time = time.time() - start_time
    
    start_time = time.time()
    _ = optimized_df.groupby('category')['value1'].sum()
    optimized_time = time.time() - start_time
    
    print(f"\n聚合操作性能对比:")
    print(f"  原始数据: {original_time:.3f}s")
    print(f"  优化数据: {optimized_time:.3f}s")
    print(f"  加速比: {original_time / optimized_time:.1f}x")


def demo_caching_system():
    """演示缓存系统"""
    print("\n" + "="*50)
    print("💾 缓存系统演示")
    print("="*50)
    
    cache_manager = SimpleCacheManager()
    
    # 模拟图表查询
    def simulate_chart_query(slice_id, form_data):
        """模拟图表查询（耗时操作）"""
        time.sleep(0.1)  # 模拟查询延迟
        return {
            'data': {'value': slice_id * 100},
            'timestamp': time.time()
        }
    
    # 测试缓存效果
    test_queries = [
        (1, {'viz_type': 'card', 'metrics': ['sales']}),
        (2, {'viz_type': 'bar', 'metrics': ['orders']}),
        (1, {'viz_type': 'card', 'metrics': ['sales']}),  # 重复查询
        (3, {'viz_type': 'line', 'metrics': ['revenue']}),
        (2, {'viz_type': 'bar', 'metrics': ['orders']}),  # 重复查询
    ]
    
    print("执行查询序列:")
    for i, (slice_id, form_data) in enumerate(test_queries):
        cache_key = cache_manager.get_cache_key(slice_id, form_data)
        
        start_time = time.time()
        
        # 尝试从缓存获取
        cached_result = cache_manager.get(cache_key)
        
        if cached_result:
            result = cached_result
            cache_status = "HIT"
        else:
            result = simulate_chart_query(slice_id, form_data)
            cache_manager.set(cache_key, result)
            cache_status = "MISS"
        
        query_time = time.time() - start_time
        
        print(f"  查询 {i+1}: Slice#{slice_id} - {cache_status} - {query_time:.3f}s")
    
    print(f"\n缓存统计: {cache_manager.get_stats()}")


def demo_chart_debugging():
    """演示图表调试"""
    print("\n" + "="*50)
    print("🔧 图表调试演示")
    print("="*50)
    
    def analyze_chart_config(form_data):
        """分析图表配置"""
        issues = []
        warnings = []
        
        # 检查必需字段
        if not form_data.get('viz_type'):
            issues.append("缺少图表类型 (viz_type)")
        
        if not form_data.get('metrics') and not form_data.get('groupby'):
            issues.append("缺少指标或分组字段")
        
        # 检查性能问题
        if form_data.get('row_limit', 0) > 50000:
            warnings.append(f"行数限制过大: {form_data['row_limit']}")
        
        if len(form_data.get('groupby', [])) > 5:
            warnings.append(f"分组字段过多: {len(form_data['groupby'])}")
        
        return issues, warnings
    
    # 测试用例
    test_configs = [
        {
            'name': '正常配置',
            'form_data': {
                'viz_type': 'bar',
                'metrics': ['sales'],
                'groupby': ['category'],
                'row_limit': 1000
            }
        },
        {
            'name': '有问题的配置',
            'form_data': {
                'metrics': [],
                'groupby': ['col1', 'col2', 'col3', 'col4', 'col5', 'col6'],
                'row_limit': 100000
            }
        },
        {
            'name': '不支持的图表类型',
            'form_data': {
                'viz_type': 'unknown_chart',
                'metrics': ['value']
            }
        }
    ]
    
    for test_config in test_configs:
        print(f"\n🔍 分析: {test_config['name']}")
        
        issues, warnings = analyze_chart_config(test_config['form_data'])
        
        if issues:
            print("  ❌ 问题:")
            for issue in issues:
                print(f"    - {issue}")
        
        if warnings:
            print("  ⚠️  警告:")
            for warning in warnings:
                print(f"    - {warning}")
        
        if not issues and not warnings:
            print("  ✅ 配置正常")
        
        # 检查图表类型是否支持
        viz_type = test_config['form_data'].get('viz_type')
        if viz_type and viz_type not in registry.list_types():
            print(f"  ❌ 不支持的图表类型: {viz_type}")
            print(f"     支持的类型: {', '.join(registry.list_types())}")


def create_performance_visualization():
    """创建性能对比可视化"""
    print("\n" + "="*50)
    print("📈 性能对比可视化")
    print("="*50)
    
    # 模拟不同数据量的性能测试
    data_sizes = [1000, 5000, 10000, 25000, 50000]
    original_times = []
    optimized_times = []
    
    for size in data_sizes:
        # 创建测试数据
        test_df = pd.DataFrame({
            'category': np.random.choice(['A', 'B', 'C'], size),
            'value': np.random.randn(size) * 100
        })
        
        # 原始处理时间
        start_time = time.time()
        _ = test_df.groupby('category')['value'].sum()
        original_time = time.time() - start_time
        original_times.append(original_time)
        
        # 优化处理时间（采样）
        if size > 1000:
            sampled_df = test_df.sample(n=min(1000, size), random_state=42)
        else:
            sampled_df = test_df
        
        start_time = time.time()
        _ = sampled_df.groupby('category')['value'].sum()
        optimized_time = time.time() - start_time
        optimized_times.append(optimized_time)
    
    # 显示结果
    print("数据量 | 原始耗时 | 优化耗时 | 加速比")
    print("-" * 40)
    for i, size in enumerate(data_sizes):
        speedup = original_times[i] / optimized_times[i] if optimized_times[i] > 0 else 1
        print(f"{size:6d} | {original_times[i]:8.3f}s | {optimized_times[i]:8.3f}s | {speedup:6.1f}x")


def main():
    """主演示函数"""
    print("🎨 Apache Superset 图表系统与可视化引擎演示")
    print("=" * 60)
    
    try:
        # 演示各个功能模块
        demo_chart_registry()
        demo_data_pipeline()
        demo_performance_optimization()
        demo_caching_system()
        demo_chart_debugging()
        create_performance_visualization()
        
        # 综合统计
        print("\n" + "="*50)
        print("📊 综合统计")
        print("="*50)
        print(f"图表注册统计: {registry.get_stats()}")
        
        print("\n✅ 演示完成！")
        print("\n关键收获:")
        print("- 理解了图表系统的插件化架构")
        print("- 掌握了数据处理流水线的实现")
        print("- 学会了性能优化的策略和技巧")
        print("- 了解了缓存系统的设计原理")
        print("- 具备了图表调试的能力")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 