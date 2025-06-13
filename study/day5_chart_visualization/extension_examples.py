#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 5 扩展示例：图表系统扩展机制演示
====================================

本脚本演示如何扩展 Superset 图表系统：
- 自定义图表类型
- 数据处理器扩展
- 缓存策略扩展
- API端点扩展
"""

import pandas as pd
import numpy as np
import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod


class ExtendedVisualizationRegistry:
    """扩展的可视化注册表"""
    
    def __init__(self):
        self.viz_types = {}
        self.processors = {}
        self.cache_strategies = {}
        self.extension_metadata = {}
    
    def register_viz(self, viz_class, metadata=None):
        """注册图表类型"""
        # 验证图表类
        self._validate_viz_class(viz_class)
        
        # 注册
        self.viz_types[viz_class.viz_type] = viz_class
        self.extension_metadata[viz_class.viz_type] = metadata or {}
        
        print(f"✓ 注册图表类型: {viz_class.viz_type} - {viz_class.verbose_name}")
        
        # 扩展点：注册后回调
        self._on_viz_registered(viz_class)
        
        return viz_class
    
    def register_processor(self, name, processor_class):
        """注册数据处理器"""
        self.processors[name] = processor_class
        print(f"✓ 注册数据处理器: {name}")
    
    def register_cache_strategy(self, name, strategy_class):
        """注册缓存策略"""
        self.cache_strategies[name] = strategy_class
        print(f"✓ 注册缓存策略: {name}")
    
    def _validate_viz_class(self, viz_class):
        """验证图表类规范"""
        required_attrs = ['viz_type', 'verbose_name']
        required_methods = ['get_data']
        
        for attr in required_attrs:
            if not hasattr(viz_class, attr):
                raise ValueError(f"Missing required attribute: {attr}")
        
        for method in required_methods:
            if not callable(getattr(viz_class, method, None)):
                raise ValueError(f"Missing required method: {method}")
    
    def _on_viz_registered(self, viz_class):
        """扩展点：注册后回调"""
        # 可以在这里执行注册后的逻辑
        # 比如：更新前端配置、通知其他系统等
        pass
    
    def get_extension_info(self):
        """获取扩展信息"""
        return {
            'viz_types': len(self.viz_types),
            'processors': len(self.processors),
            'cache_strategies': len(self.cache_strategies),
            'registered_types': list(self.viz_types.keys())
        }


# 全局扩展注册表
extended_registry = ExtendedVisualizationRegistry()


class BaseViz(ABC):
    """扩展的基础可视化类"""
    
    viz_type = None
    verbose_name = "Base Visualization"
    is_timeseries = False
    category = "basic"  # 扩展：图表分类
    requires_time_column = False  # 扩展：是否需要时间列
    supports_annotations = False  # 扩展：是否支持注释
    
    def __init__(self, datasource, form_data):
        self.datasource = datasource
        self.form_data = form_data
        self.processors = []
        self.cache_strategy = None
        
        # 扩展点：初始化处理器
        self._init_processors()
        
        # 扩展点：初始化缓存策略
        self._init_cache_strategy()
    
    def _init_processors(self):
        """初始化数据处理器"""
        processor_names = self.form_data.get('processors', [])
        for name in processor_names:
            if name in extended_registry.processors:
                processor_class = extended_registry.processors[name]
                self.processors.append(processor_class())
    
    def _init_cache_strategy(self):
        """初始化缓存策略"""
        strategy_name = self.form_data.get('cache_strategy', 'default')
        if strategy_name in extended_registry.cache_strategies:
            strategy_class = extended_registry.cache_strategies[strategy_name]
            self.cache_strategy = strategy_class()
    
    def get_json_data(self):
        """获取图表数据 - 模板方法"""
        try:
            # 扩展点：前置处理
            self._before_query()
            
            # 获取数据
            df = self.datasource.get_data()
            
            # 扩展点：应用处理器
            df = self._apply_processors(df)
            
            # 扩展点：中间处理
            self._before_transform(df)
            
            # 转换数据
            chart_data = self.get_data(df)
            
            # 扩展点：后置处理
            chart_data = self._after_transform(chart_data)
            
            return chart_data
            
        except Exception as e:
            return self._handle_error(e)
    
    def _before_query(self):
        """扩展点：查询前处理"""
        pass
    
    def _before_transform(self, df):
        """扩展点：转换前处理"""
        pass
    
    def _after_transform(self, chart_data):
        """扩展点：转换后处理"""
        return chart_data
    
    def _apply_processors(self, df):
        """应用数据处理器"""
        for processor in self.processors:
            df = processor.process(df, self.form_data)
        return df
    
    def _handle_error(self, error):
        """错误处理"""
        return {
            'error': str(error),
            'viz_type': self.viz_type,
            'error_type': type(error).__name__
        }
    
    @abstractmethod
    def get_data(self, df):
        """抽象方法：获取图表数据"""
        pass


# =============================================================================
# 扩展示例 1：自定义图表类型
# =============================================================================

@extended_registry.register_viz
class RadarChartViz(BaseViz):
    """雷达图"""
    
    viz_type = 'radar'
    verbose_name = 'Radar Chart'
    category = 'advanced'
    supports_annotations = True
    
    def get_data(self, df):
        """雷达图数据转换"""
        dimensions = self.form_data.get('dimensions', [])
        metrics = self.form_data.get('metrics', [])
        
        if not dimensions or not metrics:
            return {'error': 'Missing dimensions or metrics'}
        
        # 构建雷达图数据结构
        radar_data = {
            'indicator': [],  # 雷达图指标
            'series': []      # 数据系列
        }
        
        # 设置雷达图指标
        for metric in metrics:
            if metric in df.columns:
                max_val = df[metric].max()
                radar_data['indicator'].append({
                    'name': metric,
                    'max': max_val * 1.2  # 设置最大值稍大于数据最大值
                })
        
        # 按维度分组数据
        if len(dimensions) == 1 and dimensions[0] in df.columns:
            grouped = df.groupby(dimensions[0])
            
            for name, group in grouped:
                series_data = []
                for metric in metrics:
                    if metric in group.columns:
                        # 取平均值作为该组的值
                        series_data.append(float(group[metric].mean()))
                    else:
                        series_data.append(0)
                
                radar_data['series'].append({
                    'name': str(name),
                    'value': series_data,
                    'itemStyle': {
                        'color': self._get_color_for_series(name)
                    }
                })
        
        return radar_data
    
    def _get_color_for_series(self, name):
        """为数据系列生成颜色"""
        # 简单的颜色生成算法
        hash_obj = hashlib.md5(str(name).encode())
        hash_hex = hash_obj.hexdigest()
        return f"#{hash_hex[:6]}"


@extended_registry.register_viz
class GaugeChartViz(BaseViz):
    """仪表盘图表"""
    
    viz_type = 'gauge'
    verbose_name = 'Gauge Chart'
    category = 'kpi'
    
    def get_data(self, df):
        """仪表盘数据转换"""
        if df.empty:
            return {'value': 0, 'error': 'No data'}
        
        # 获取指标值
        metric = self.form_data.get('metric')
        if not metric or metric not in df.columns:
            return {'value': 0, 'error': 'Invalid metric'}
        
        # 计算当前值
        current_value = float(df[metric].sum())
        
        # 获取配置参数
        min_val = self.form_data.get('gauge_min', 0)
        max_val = self.form_data.get('gauge_max', 100)
        thresholds = self.form_data.get('thresholds', [])
        
        # 构建仪表盘数据
        gauge_data = {
            'value': current_value,
            'min': min_val,
            'max': max_val,
            'title': self.form_data.get('gauge_title', metric),
            'unit': self.form_data.get('gauge_unit', ''),
            'thresholds': thresholds,
            'color_ranges': self._calculate_color_ranges(min_val, max_val, thresholds),
            'percentage': (current_value - min_val) / (max_val - min_val) * 100
        }
        
        return gauge_data
    
    def _calculate_color_ranges(self, min_val, max_val, thresholds):
        """计算颜色范围"""
        if not thresholds:
            return [{'color': '#5cb85c', 'range': [min_val, max_val]}]
        
        color_ranges = []
        colors = ['#d9534f', '#f0ad4e', '#5cb85c']  # 红、黄、绿
        
        # 添加阈值区间
        prev_val = min_val
        for i, threshold in enumerate(sorted(thresholds)):
            if i < len(colors):
                color_ranges.append({
                    'color': colors[i],
                    'range': [prev_val, threshold]
                })
                prev_val = threshold
        
        # 添加最后一个区间
        if prev_val < max_val and len(color_ranges) < len(colors):
            color_ranges.append({
                'color': colors[len(color_ranges)],
                'range': [prev_val, max_val]
            })
        
        return color_ranges


@extended_registry.register_viz
class TreemapViz(BaseViz):
    """树图"""
    
    viz_type = 'treemap'
    verbose_name = 'Treemap Chart'
    category = 'hierarchical'
    
    def get_data(self, df):
        """树图数据转换"""
        hierarchy_cols = self.form_data.get('hierarchy', [])
        value_col = self.form_data.get('value_column')
        
        if not hierarchy_cols or not value_col:
            return {'error': 'Missing hierarchy or value column'}
        
        if value_col not in df.columns:
            return {'error': f'Value column {value_col} not found'}
        
        # 构建层次结构
        tree_data = self._build_hierarchy(df, hierarchy_cols, value_col)
        
        return {
            'data': tree_data,
            'breadcrumb': hierarchy_cols
        }
    
    def _build_hierarchy(self, df, hierarchy_cols, value_col):
        """构建层次结构数据"""
        if not hierarchy_cols:
            return []
        
        # 按层次分组
        first_level = hierarchy_cols[0]
        if first_level not in df.columns:
            return []
        
        grouped = df.groupby(first_level)
        tree_nodes = []
        
        for name, group in grouped:
            # 计算当前节点的值
            node_value = float(group[value_col].sum())
            
            node = {
                'name': str(name),
                'value': node_value,
                'itemStyle': {
                    'color': self._get_color_for_value(node_value)
                }
            }
            
            # 递归构建子节点
            if len(hierarchy_cols) > 1:
                children = self._build_hierarchy(group, hierarchy_cols[1:], value_col)
                if children:
                    node['children'] = children
            
            tree_nodes.append(node)
        
        return tree_nodes
    
    def _get_color_for_value(self, value):
        """根据值生成颜色"""
        # 简单的颜色映射
        normalized = min(value / 1000, 1.0)  # 归一化到0-1
        red = int(255 * (1 - normalized))
        green = int(255 * normalized)
        return f"rgb({red}, {green}, 100)"


# =============================================================================
# 扩展示例 2：数据处理器扩展
# =============================================================================

class DataProcessor(ABC):
    """数据处理器基类"""
    
    @abstractmethod
    def process(self, df: pd.DataFrame, form_data: Dict) -> pd.DataFrame:
        pass


class StatisticalProcessor(DataProcessor):
    """统计分析处理器"""
    
    def process(self, df: pd.DataFrame, form_data: Dict) -> pd.DataFrame:
        """添加统计指标"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if form_data.get('add_moving_average'):
            window = form_data.get('ma_window', 7)
            for col in numeric_cols:
                df[f'{col}_ma'] = df[col].rolling(window=window).mean()
        
        if form_data.get('add_percentiles'):
            for col in numeric_cols:
                df[f'{col}_percentile'] = df[col].rank(pct=True)
        
        if form_data.get('add_zscore'):
            for col in numeric_cols:
                mean_val = df[col].mean()
                std_val = df[col].std()
                if std_val > 0:
                    df[f'{col}_zscore'] = (df[col] - mean_val) / std_val
        
        return df


class GeospatialProcessor(DataProcessor):
    """地理空间处理器"""
    
    def process(self, df: pd.DataFrame, form_data: Dict) -> pd.DataFrame:
        """地理空间数据处理"""
        lat_col = form_data.get('latitude_column')
        lng_col = form_data.get('longitude_column')
        
        if lat_col and lng_col and lat_col in df.columns and lng_col in df.columns:
            # 验证坐标范围
            df = df[(df[lat_col] >= -90) & (df[lat_col] <= 90)]
            df = df[(df[lng_col] >= -180) & (df[lng_col] <= 180)]
            
            # 添加地理计算字段
            if form_data.get('add_distance_from_center'):
                center_lat = form_data.get('center_latitude', 0)
                center_lng = form_data.get('center_longitude', 0)
                
                df['distance_from_center'] = self._calculate_distance(
                    df[lat_col], df[lng_col], center_lat, center_lng
                )
            
            # 空间聚合
            if form_data.get('spatial_aggregation'):
                precision = form_data.get('spatial_precision', 2)
                df[f'{lat_col}_rounded'] = df[lat_col].round(precision)
                df[f'{lng_col}_rounded'] = df[lng_col].round(precision)
        
        return df
    
    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """计算两点间距离（简化版）"""
        return np.sqrt((lat1 - lat2)**2 + (lng1 - lng2)**2) * 111  # 粗略转换为公里


class TimeSeriesProcessor(DataProcessor):
    """时间序列处理器"""
    
    def process(self, df: pd.DataFrame, form_data: Dict) -> pd.DataFrame:
        """时间序列特殊处理"""
        time_col = form_data.get('time_column')
        
        if time_col and time_col in df.columns:
            # 确保时间列是datetime类型
            df[time_col] = pd.to_datetime(df[time_col])
            
            # 提取时间特征
            if form_data.get('extract_time_features'):
                df[f'{time_col}_year'] = df[time_col].dt.year
                df[f'{time_col}_month'] = df[time_col].dt.month
                df[f'{time_col}_day'] = df[time_col].dt.day
                df[f'{time_col}_weekday'] = df[time_col].dt.weekday
                df[f'{time_col}_hour'] = df[time_col].dt.hour
            
            # 重采样
            if form_data.get('resample_frequency'):
                freq = form_data['resample_frequency']
                agg_method = form_data.get('resample_method', 'mean')
                
                df = df.set_index(time_col)
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                
                if len(numeric_cols) > 0:
                    df = df[numeric_cols].resample(freq).agg(agg_method).reset_index()
            
            # 时间窗口计算
            if form_data.get('add_time_windows'):
                window_size = form_data.get('window_size', 7)
                for col in df.select_dtypes(include=[np.number]).columns:
                    if col != time_col:
                        df[f'{col}_rolling_mean'] = df[col].rolling(window=window_size).mean()
                        df[f'{col}_rolling_std'] = df[col].rolling(window=window_size).std()
        
        return df


# 注册处理器
extended_registry.register_processor('statistical', StatisticalProcessor)
extended_registry.register_processor('geospatial', GeospatialProcessor)
extended_registry.register_processor('timeseries', TimeSeriesProcessor)


# =============================================================================
# 扩展示例 3：缓存策略扩展
# =============================================================================

class CacheStrategy(ABC):
    """缓存策略基类"""
    
    @abstractmethod
    def get_cache_key(self, viz_obj, form_data):
        pass
    
    @abstractmethod
    def get_cache_timeout(self, viz_obj, form_data):
        pass
    
    @abstractmethod
    def should_cache(self, viz_obj, form_data):
        pass


class AdaptiveCacheStrategy(CacheStrategy):
    """自适应缓存策略"""
    
    def get_cache_key(self, viz_obj, form_data):
        """生成自适应缓存键"""
        key_components = {
            'viz_type': viz_obj.viz_type,
            'form_data_hash': self._hash_form_data(form_data),
            'data_freshness': self._get_data_freshness_indicator(),
            'user_segment': self._get_user_segment()
        }
        
        key_str = json.dumps(key_components, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]
    
    def get_cache_timeout(self, viz_obj, form_data):
        """动态缓存超时"""
        base_timeout = 3600  # 1小时基础超时
        
        # 根据图表复杂度调整
        complexity_factor = self._calculate_complexity_factor(form_data)
        
        # 根据数据更新频率调整
        update_frequency = self._estimate_update_frequency(viz_obj)
        
        # 根据用户访问模式调整
        access_pattern = self._analyze_access_pattern(viz_obj)
        
        # 计算最终超时时间
        timeout = base_timeout * complexity_factor * update_frequency * access_pattern
        
        return max(300, min(86400, int(timeout)))  # 限制在5分钟到1天之间
    
    def should_cache(self, viz_obj, form_data):
        """智能缓存决策"""
        # 检查数据大小
        estimated_size = self._estimate_data_size(form_data)
        if estimated_size > 10000:  # 大数据集优先缓存
            return True
        
        # 检查查询复杂度
        complexity = self._calculate_query_complexity(form_data)
        if complexity > 3:  # 复杂查询优先缓存
            return True
        
        # 检查访问频率
        access_freq = self._get_access_frequency(viz_obj)
        if access_freq > 5:  # 高频访问优先缓存
            return True
        
        return False
    
    def _hash_form_data(self, form_data):
        """计算表单数据哈希"""
        # 移除不影响结果的字段
        stable_data = {k: v for k, v in form_data.items() 
                      if k not in ['cache_key', 'timestamp', '_']}
        
        return hashlib.md5(json.dumps(stable_data, sort_keys=True).encode()).hexdigest()
    
    def _get_data_freshness_indicator(self):
        """获取数据新鲜度指标"""
        # 简化实现，实际中可能需要查询数据库
        return int(time.time() // 3600)  # 按小时分组
    
    def _get_user_segment(self):
        """获取用户分段"""
        # 简化实现，实际中根据用户权限等分组
        return "default"
    
    def _calculate_complexity_factor(self, form_data):
        """计算复杂度因子"""
        factor = 1.0
        
        # 分组字段数量
        groupby_count = len(form_data.get('groupby', []))
        factor *= (1 + groupby_count * 0.2)
        
        # 指标数量
        metrics_count = len(form_data.get('metrics', []))
        factor *= (1 + metrics_count * 0.1)
        
        # 过滤器数量
        filters_count = len(form_data.get('filters', []))
        factor *= (1 + filters_count * 0.15)
        
        return factor
    
    def _estimate_update_frequency(self, viz_obj):
        """估计数据更新频率"""
        # 简化实现
        if hasattr(viz_obj, 'is_timeseries') and viz_obj.is_timeseries:
            return 0.5  # 时间序列数据更新频繁，缓存时间减半
        return 1.0
    
    def _analyze_access_pattern(self, viz_obj):
        """分析访问模式"""
        # 简化实现
        return 1.0
    
    def _estimate_data_size(self, form_data):
        """估计数据大小"""
        row_limit = form_data.get('row_limit', 10000)
        column_count = len(form_data.get('groupby', [])) + len(form_data.get('metrics', []))
        return row_limit * max(1, column_count)
    
    def _calculate_query_complexity(self, form_data):
        """计算查询复杂度"""
        complexity = 0
        complexity += len(form_data.get('groupby', []))
        complexity += len(form_data.get('metrics', [])) * 0.5
        complexity += len(form_data.get('filters', [])) * 0.3
        return complexity
    
    def _get_access_frequency(self, viz_obj):
        """获取访问频率"""
        # 简化实现，实际中从日志或监控系统获取
        return 1


class TieredCacheStrategy(CacheStrategy):
    """分层缓存策略"""
    
    def __init__(self):
        self.memory_cache = {}
        self.redis_cache = {}  # 模拟Redis
        self.file_cache = {}   # 模拟文件缓存
    
    def get_cache_key(self, viz_obj, form_data):
        """生成分层缓存键"""
        base_key = f"{viz_obj.viz_type}_{hash(str(form_data))}"
        return {
            'memory': f"mem_{base_key}",
            'redis': f"redis_{base_key}",
            'file': f"file_{base_key}"
        }
    
    def get_cache_timeout(self, viz_obj, form_data):
        """分层缓存超时"""
        return {
            'memory': 300,    # 5分钟
            'redis': 3600,    # 1小时
            'file': 86400     # 1天
        }
    
    def should_cache(self, viz_obj, form_data):
        """总是使用分层缓存"""
        return True
    
    def get_cached_data(self, cache_keys):
        """分层获取缓存数据"""
        # L1: 内存缓存
        if cache_keys['memory'] in self.memory_cache:
            return self.memory_cache[cache_keys['memory']]
        
        # L2: Redis缓存
        if cache_keys['redis'] in self.redis_cache:
            data = self.redis_cache[cache_keys['redis']]
            # 提升到内存缓存
            self.memory_cache[cache_keys['memory']] = data
            return data
        
        # L3: 文件缓存
        if cache_keys['file'] in self.file_cache:
            data = self.file_cache[cache_keys['file']]
            # 提升到Redis和内存缓存
            self.redis_cache[cache_keys['redis']] = data
            self.memory_cache[cache_keys['memory']] = data
            return data
        
        return None
    
    def set_cached_data(self, cache_keys, data, timeouts):
        """分层设置缓存"""
        data_size = len(json.dumps(data))
        
        # 小数据存内存
        if data_size < 102400:  # 100KB
            self.memory_cache[cache_keys['memory']] = data
        
        # 中等数据存Redis
        if data_size < 10485760:  # 10MB
            self.redis_cache[cache_keys['redis']] = data
        
        # 大数据存文件
        self.file_cache[cache_keys['file']] = data


# 注册缓存策略
extended_registry.register_cache_strategy('adaptive', AdaptiveCacheStrategy)
extended_registry.register_cache_strategy('tiered', TieredCacheStrategy)


# =============================================================================
# 模拟数据源
# =============================================================================

class MockExtendedDataSource:
    """扩展的模拟数据源"""
    
    def __init__(self, name: str):
        self.name = name
        self.id = hash(name)
        
    def get_data(self):
        """生成扩展的示例数据"""
        np.random.seed(42)
        
        if self.name == 'sales_data':
            return pd.DataFrame({
                'date': pd.date_range('2023-01-01', periods=365, freq='1D'),
                'region': np.random.choice(['North', 'South', 'East', 'West'], 365),
                'product': np.random.choice(['A', 'B', 'C', 'D'], 365),
                'sales': np.random.exponential(1000, 365),
                'orders': np.random.poisson(50, 365),
                'profit_margin': np.random.uniform(0.1, 0.3, 365),
                'customer_rating': np.random.uniform(1, 5, 365)
            })
        
        elif self.name == 'geo_data':
            return pd.DataFrame({
                'city': ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Hangzhou'] * 20,
                'latitude': [39.9, 31.2, 23.1, 22.5, 30.3] * 20,
                'longitude': [116.4, 121.5, 113.3, 114.1, 120.2] * 20,
                'population': np.random.exponential(5000000, 100),
                'gdp': np.random.exponential(1000000, 100),
                'temperature': np.random.normal(20, 10, 100)
            })
        
        else:
            return pd.DataFrame({
                'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], 100),
                'value1': np.random.randn(100) * 100 + 1000,
                'value2': np.random.exponential(50, 100),
                'value3': np.random.uniform(0, 100, 100)
            })


# =============================================================================
# 演示函数
# =============================================================================

def demo_extended_chart_types():
    """演示扩展的图表类型"""
    print("\n" + "="*60)
    print("🎨 扩展图表类型演示")
    print("="*60)
    
    datasource = MockExtendedDataSource('sales_data')
    
    # 测试雷达图
    print("\n🔍 测试雷达图:")
    form_data = {
        'dimensions': ['region'],
        'metrics': ['sales', 'orders', 'profit_margin']
    }
    
    radar_viz = extended_registry.viz_types['radar'](datasource, form_data)
    radar_result = radar_viz.get_json_data()
    
    if 'error' not in radar_result:
        print(f"  ✓ 指标数量: {len(radar_result['indicator'])}")
        print(f"  ✓ 数据系列: {len(radar_result['series'])}")
        print(f"  ✓ 系列名称: {[s['name'] for s in radar_result['series'][:3]]}")
    else:
        print(f"  ✗ 错误: {radar_result['error']}")
    
    # 测试仪表盘
    print("\n🔍 测试仪表盘:")
    form_data = {
        'metric': 'sales',
        'gauge_min': 0,
        'gauge_max': 2000,
        'thresholds': [500, 1000, 1500],
        'gauge_title': 'Daily Sales'
    }
    
    gauge_viz = extended_registry.viz_types['gauge'](datasource, form_data)
    gauge_result = gauge_viz.get_json_data()
    
    if 'error' not in gauge_result:
        print(f"  ✓ 当前值: {gauge_result['value']:.0f}")
        print(f"  ✓ 百分比: {gauge_result['percentage']:.1f}%")
        print(f"  ✓ 颜色范围: {len(gauge_result['color_ranges'])} 个")
    else:
        print(f"  ✗ 错误: {gauge_result['error']}")
    
    # 测试树图
    print("\n🔍 测试树图:")
    form_data = {
        'hierarchy': ['region', 'product'],
        'value_column': 'sales'
    }
    
    treemap_viz = extended_registry.viz_types['treemap'](datasource, form_data)
    treemap_result = treemap_viz.get_json_data()
    
    if 'error' not in treemap_result:
        print(f"  ✓ 顶级节点: {len(treemap_result['data'])} 个")
        print(f"  ✓ 层次结构: {treemap_result['breadcrumb']}")
        if treemap_result['data']:
            first_node = treemap_result['data'][0]
            child_count = len(first_node.get('children', []))
            print(f"  ✓ 第一个节点子节点: {child_count} 个")
    else:
        print(f"  ✗ 错误: {treemap_result['error']}")


def demo_data_processors():
    """演示数据处理器"""
    print("\n" + "="*60)
    print("🔄 数据处理器演示")
    print("="*60)
    
    datasource = MockExtendedDataSource('sales_data')
    df = datasource.get_data()
    
    print(f"原始数据: {len(df)} 行, {len(df.columns)} 列")
    
    # 测试统计处理器
    print("\n🔍 测试统计处理器:")
    stat_processor = extended_registry.processors['statistical']()
    form_data = {
        'add_moving_average': True,
        'ma_window': 7,
        'add_percentiles': True,
        'add_zscore': True
    }
    
    processed_df = stat_processor.process(df.copy(), form_data)
    new_cols = [col for col in processed_df.columns if col not in df.columns]
    print(f"  ✓ 新增列: {len(new_cols)} 个")
    print(f"  ✓ 新增列名: {new_cols[:5]}")  # 显示前5个
    
    # 测试地理空间处理器
    print("\n🔍 测试地理空间处理器:")
    geo_datasource = MockExtendedDataSource('geo_data')
    geo_df = geo_datasource.get_data()
    
    geo_processor = extended_registry.processors['geospatial']()
    form_data = {
        'latitude_column': 'latitude',
        'longitude_column': 'longitude',
        'add_distance_from_center': True,
        'center_latitude': 39.9,  # 北京
        'center_longitude': 116.4,
        'spatial_aggregation': True,
        'spatial_precision': 1
    }
    
    geo_processed_df = geo_processor.process(geo_df.copy(), form_data)
    geo_new_cols = [col for col in geo_processed_df.columns if col not in geo_df.columns]
    print(f"  ✓ 处理后行数: {len(geo_processed_df)}")
    print(f"  ✓ 新增列: {geo_new_cols}")
    
    # 测试时间序列处理器
    print("\n🔍 测试时间序列处理器:")
    ts_processor = extended_registry.processors['timeseries']()
    form_data = {
        'time_column': 'date',
        'extract_time_features': True,
        'add_time_windows': True,
        'window_size': 7
    }
    
    ts_processed_df = ts_processor.process(df.copy(), form_data)
    ts_new_cols = [col for col in ts_processed_df.columns if col not in df.columns]
    print(f"  ✓ 新增时间特征: {[col for col in ts_new_cols if 'date_' in col]}")
    print(f"  ✓ 新增滚动统计: {[col for col in ts_new_cols if 'rolling' in col][:3]}")


def demo_cache_strategies():
    """演示缓存策略"""
    print("\n" + "="*60)
    print("💾 缓存策略演示")
    print("="*60)
    
    datasource = MockExtendedDataSource('sales_data')
    
    # 创建测试图表对象
    class TestViz:
        def __init__(self):
            self.viz_type = 'test'
            self.is_timeseries = True
    
    test_viz = TestViz()
    
    # 测试自适应缓存策略
    print("\n🔍 测试自适应缓存策略:")
    adaptive_strategy = extended_registry.cache_strategies['adaptive']()
    
    test_cases = [
        {
            'name': '简单查询',
            'form_data': {'metrics': ['sales'], 'row_limit': 100}
        },
        {
            'name': '复杂查询',
            'form_data': {
                'metrics': ['sales', 'orders', 'profit_margin'],
                'groupby': ['region', 'product'],
                'filters': [{'col': 'date', 'op': '>', 'val': '2023-01-01'}],
                'row_limit': 50000
            }
        },
        {
            'name': '时间序列查询',
            'form_data': {
                'metrics': ['sales'],
                'groupby': ['date'],
                'row_limit': 10000
            }
        }
    ]
    
    for test_case in test_cases:
        form_data = test_case['form_data']
        
        cache_key = adaptive_strategy.get_cache_key(test_viz, form_data)
        timeout = adaptive_strategy.get_cache_timeout(test_viz, form_data)
        should_cache = adaptive_strategy.should_cache(test_viz, form_data)
        
        print(f"  {test_case['name']}:")
        print(f"    缓存键: {cache_key[:20]}...")
        print(f"    超时时间: {timeout}s ({timeout//60}分钟)")
        print(f"    是否缓存: {should_cache}")
    
    # 测试分层缓存策略
    print("\n🔍 测试分层缓存策略:")
    tiered_strategy = extended_registry.cache_strategies['tiered']()
    
    form_data = {'metrics': ['sales'], 'groupby': ['region']}
    cache_keys = tiered_strategy.get_cache_key(test_viz, form_data)
    timeouts = tiered_strategy.get_cache_timeout(test_viz, form_data)
    
    print(f"  缓存键结构: {list(cache_keys.keys())}")
    print(f"  超时时间: {timeouts}")
    
    # 模拟缓存操作
    test_data = {'result': 'test_data', 'timestamp': time.time()}
    tiered_strategy.set_cached_data(cache_keys, test_data, timeouts)
    
    cached_data = tiered_strategy.get_cached_data(cache_keys)
    print(f"  缓存测试: {'成功' if cached_data else '失败'}")


def demo_integration_example():
    """演示集成示例"""
    print("\n" + "="*60)
    print("🚀 集成示例演示")
    print("="*60)
    
    # 创建一个使用所有扩展功能的图表
    print("\n🔍 创建集成图表:")
    
    datasource = MockExtendedDataSource('sales_data')
    
    form_data = {
        'viz_type': 'radar',
        'dimensions': ['region'],
        'metrics': ['sales', 'orders'],
        'processors': ['statistical', 'timeseries'],
        'cache_strategy': 'adaptive',
        
        # 统计处理器参数
        'add_moving_average': True,
        'ma_window': 7,
        'add_percentiles': True,
        
        # 时间序列处理器参数
        'time_column': 'date',
        'extract_time_features': True,
        'add_time_windows': True,
        'window_size': 5,
        
        # 缓存策略参数
        'row_limit': 1000
    }
    
    # 创建图表实例
    viz_class = extended_registry.viz_types['radar']
    viz = viz_class(datasource, form_data)
    
    # 执行渲染
    start_time = time.time()
    result = viz.get_json_data()
    end_time = time.time()
    
    print(f"  ✓ 处理器数量: {len(viz.processors)}")
    print(f"  ✓ 缓存策略: {type(viz.cache_strategy).__name__ if viz.cache_strategy else 'None'}")
    print(f"  ✓ 渲染时间: {end_time - start_time:.3f}s")
    
    if 'error' not in result:
        print(f"  ✓ 雷达图指标: {len(result['indicator'])} 个")
        print(f"  ✓ 数据系列: {len(result['series'])} 个")
    else:
        print(f"  ✗ 错误: {result['error']}")


def main():
    """主演示函数"""
    print("🎨 Day 5 图表系统扩展机制演示")
    print("=" * 60)
    print(f"扩展信息: {extended_registry.get_extension_info()}")
    
    try:
        # 演示各个扩展功能
        demo_extended_chart_types()
        demo_data_processors()
        demo_cache_strategies()
        demo_integration_example()
        
        print("\n" + "="*60)
        print("✅ 扩展演示完成！")
        print("\n📚 扩展要点总结:")
        print("- 图表类型扩展：通过继承BaseViz实现新图表类型")
        print("- 数据处理器扩展：通过DataProcessor接口添加数据处理逻辑")
        print("- 缓存策略扩展：通过CacheStrategy接口实现智能缓存")
        print("- 插件化架构：所有扩展都通过注册表管理")
        print("- 灵活组合：不同扩展可以灵活组合使用")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 