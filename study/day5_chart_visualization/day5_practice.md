# Day 5 实践指南：图表系统与可视化引擎实战 🚀

本实践指南将带你深入 Superset 图表系统的核心机制，通过实际操作掌握图表开发、数据处理和性能优化。

## 🎯 实践目标

完成本实践后，你将能够：
- **创建自定义图表类型**：扩展 Superset 的可视化能力
- **优化图表性能**：处理大数据量图表的渲染问题
- **理解数据流转**：掌握从查询到渲染的完整流程
- **实现缓存策略**：提升图表加载速度
- **调试图表问题**：快速定位和解决图表异常

---

## 📋 实践练习

### 练习 1：创建自定义图表类型 (⭐⭐⭐)

**目标**：实现一个自定义的卡片图表，显示关键指标

**步骤**：

#### 1.1 创建卡片图表类
```python
# custom_card_viz.py
from superset.viz import BaseViz, register_viz
import pandas as pd

@register_viz
class CardViz(BaseViz):
    """卡片图表 - 显示单个关键指标"""
    viz_type = 'card'
    verbose_name = 'Card Chart'
    is_timeseries = False
    
    def query_obj(self):
        """构建查询对象"""
        query_obj = super().query_obj()
        
        # 卡片图表只需要一个指标
        metrics = self.form_data.get('metrics', [])
        if len(metrics) > 1:
            query_obj['metrics'] = metrics[:1]  # 只取第一个指标
        
        # 不需要分组，只要聚合结果
        query_obj['columns'] = []
        query_obj['row_limit'] = 1  # 只需要一行结果
        
        return query_obj
    
    def get_data(self, df):
        """处理数据，转换为卡片格式"""
        if df.empty:
            return {
                'value': 0,
                'error': 'No data available'
            }
        
        # 获取第一个数值列的值
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) == 0:
            return {
                'value': 0,
                'error': 'No numeric data'
            }
        
        value = df[numeric_columns[0]].iloc[0]
        metric_name = numeric_columns[0]
        
        # 格式化显示
        formatted_value = self._format_value(value)
        
        return {
            'value': value,
            'formatted_value': formatted_value,
            'metric_name': metric_name,
            'total_records': len(df),
            'chart_type': 'card'
        }
    
    def _format_value(self, value):
        """格式化数值显示"""
        if value >= 1000000:
            return f"{value/1000000:.1f}M"
        elif value >= 1000:
            return f"{value/1000:.1f}K"
        else:
            return f"{value:.2f}"
```

#### 1.2 测试自定义图表
```python
# test_custom_chart.py
from custom_card_viz import CardViz
import pandas as pd

def test_card_viz():
    """测试卡片图表"""
    
    # 模拟数据源
    class MockDataSource:
        def query(self, query_obj):
            # 模拟查询结果
            class QueryResult:
                def __init__(self):
                    self.df = pd.DataFrame({
                        'total_sales': [1234567],
                        'order_count': [8921]
                    })
                    self.error_message = None
            return QueryResult()
    
    # 测试数据
    form_data = {
        'metrics': ['total_sales'],
        'viz_type': 'card'
    }
    
    # 创建图表实例
    datasource = MockDataSource()
    viz = CardViz(datasource, form_data)
    
    # 获取数据
    result = viz.run_query()
    print("Card Chart Result:")
    print(f"Value: {result['value']}")
    print(f"Formatted: {result['formatted_value']}")
    print(f"Metric: {result['metric_name']}")
    
    return result

if __name__ == "__main__":
    test_card_viz()
```

### 练习 2：数据处理流水线优化 (⭐⭐⭐⭐)

**目标**：实现高效的数据处理流水线，支持复杂的数据转换

#### 2.1 创建数据处理管道
```python
# data_pipeline.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any

class DataPipeline:
    """数据处理管道"""
    
    def __init__(self, form_data: Dict):
        self.form_data = form_data
        self.processors = []
    
    def add_processor(self, processor):
        """添加数据处理器"""
        self.processors.append(processor)
        return self
    
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """执行数据处理管道"""
        for processor in self.processors:
            df = processor.process(df, self.form_data)
        return df

class NullValueProcessor:
    """空值处理器"""
    
    def process(self, df: pd.DataFrame, form_data: Dict) -> pd.DataFrame:
        strategy = form_data.get('null_strategy', 'fill_zero')
        
        if strategy == 'fill_zero':
            return df.fillna(0)
        elif strategy == 'fill_mean':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
            return df
        elif strategy == 'drop':
            return df.dropna()
        else:
            return df

class OutlierProcessor:
    """异常值处理器"""
    
    def process(self, df: pd.DataFrame, form_data: Dict) -> pd.DataFrame:
        method = form_data.get('outlier_method', 'iqr')
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if method == 'iqr':
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                df[col] = df[col].clip(lower, upper)
        
        return df

class AggregationProcessor:
    """聚合处理器"""
    
    def process(self, df: pd.DataFrame, form_data: Dict) -> pd.DataFrame:
        groupby_cols = form_data.get('groupby', [])
        metrics = form_data.get('metrics', [])
        
        if not groupby_cols or not metrics:
            return df
        
        # 构建聚合字典
        agg_dict = {}
        for metric in metrics:
            if isinstance(metric, str) and metric in df.columns:
                agg_dict[metric] = 'sum'
            elif isinstance(metric, dict):
                col = metric.get('column')
                func = metric.get('aggregate', 'sum')
                if col in df.columns:
                    agg_dict[col] = func
        
        if agg_dict and all(col in df.columns for col in groupby_cols):
            df = df.groupby(groupby_cols).agg(agg_dict).reset_index()
        
        return df

def test_data_pipeline():
    """测试数据处理管道"""
    
    # 创建测试数据
    data = {
        'category': ['A', 'B', 'A', 'C', 'B', 'A'],
        'sales': [100, 200, np.nan, 150, 300, 1000],  # 包含空值和异常值
        'orders': [10, 20, 15, 12, 25, 18]
    }
    df = pd.DataFrame(data)
    
    print("Original Data:")
    print(df)
    print()
    
    # 配置表单数据
    form_data = {
        'null_strategy': 'fill_mean',
        'outlier_method': 'iqr',
        'groupby': ['category'],
        'metrics': ['sales', 'orders']
    }
    
    # 创建处理管道
    pipeline = DataPipeline(form_data)
    pipeline.add_processor(NullValueProcessor()) \
           .add_processor(OutlierProcessor()) \
           .add_processor(AggregationProcessor())
    
    # 执行处理
    processed_df = pipeline.process(df)
    
    print("Processed Data:")
    print(processed_df)
    
    return processed_df

if __name__ == "__main__":
    test_data_pipeline()
```

### 练习 3：图表性能优化 (⭐⭐⭐⭐⭐)

**目标**：实现智能的数据采样和渲染优化

#### 3.1 实现性能优化器
```python
# performance_optimizer.py
import pandas as pd
import numpy as np
from typing import Dict, Any
import hashlib
import json
import time

class ChartPerformanceOptimizer:
    """图表性能优化器"""
    
    def __init__(self, viz_type: str, form_data: Dict):
        self.viz_type = viz_type
        self.form_data = form_data
        self.cache = {}
        
    def optimize_query(self, df: pd.DataFrame) -> pd.DataFrame:
        """优化查询结果"""
        # 1. 估算数据大小
        data_size = self._estimate_data_size(df)
        
        # 2. 根据数据大小选择优化策略
        if data_size > 10000:  # 超过1万行
            df = self._apply_sampling(df)
        
        if data_size > 50000:  # 超过5万行
            df = self._apply_aggregation(df)
        
        return df
    
    def optimize_rendering(self, chart_data: Dict) -> Dict:
        """优化渲染数据"""
        # 1. 限制数据点数量
        chart_data = self._limit_data_points(chart_data)
        
        # 2. 优化数据精度
        chart_data = self._optimize_precision(chart_data)
        
        # 3. 压缩重复数据
        chart_data = self._compress_data(chart_data)
        
        return chart_data
    
    def _estimate_data_size(self, df: pd.DataFrame) -> int:
        """估算数据大小"""
        return len(df)
    
    def _apply_sampling(self, df: pd.DataFrame, sample_rate: float = 0.3) -> pd.DataFrame:
        """应用数据采样"""
        if len(df) == 0:
            return df
        
        sample_size = max(1000, int(len(df) * sample_rate))
        
        if self.viz_type in ['line', 'area']:
            # 时间序列图表保持时间顺序
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp')
                step = len(df) // sample_size
                return df.iloc[::step]
        
        # 随机采样
        return df.sample(n=min(sample_size, len(df)), random_state=42)
    
    def _apply_aggregation(self, df: pd.DataFrame) -> pd.DataFrame:
        """应用预聚合"""
        groupby_cols = self.form_data.get('groupby', [])
        
        if not groupby_cols:
            return df
        
        # 只保留必要的列
        metrics = self.form_data.get('metrics', [])
        keep_cols = groupby_cols + metrics
        keep_cols = [col for col in keep_cols if col in df.columns]
        
        if keep_cols:
            df = df[keep_cols]
            
        return df
    
    def _limit_data_points(self, chart_data: Dict) -> Dict:
        """限制数据点数量"""
        max_points = 2000
        
        if 'series' in chart_data:
            for series in chart_data['series']:
                if 'data' in series and len(series['data']) > max_points:
                    # 均匀抽样
                    step = len(series['data']) // max_points
                    series['data'] = series['data'][::step]
        
        return chart_data
    
    def _optimize_precision(self, chart_data: Dict) -> Dict:
        """优化数值精度"""
        def round_number(value):
            if isinstance(value, (int, float)):
                if abs(value) >= 1000:
                    return round(value, 0)
                else:
                    return round(value, 2)
            return value
        
        if 'series' in chart_data:
            for series in chart_data['series']:
                if 'data' in series:
                    series['data'] = [
                        [item[0], round_number(item[1])] if isinstance(item, list) and len(item) == 2
                        else round_number(item)
                        for item in series['data']
                    ]
        
        return chart_data
    
    def _compress_data(self, chart_data: Dict) -> Dict:
        """压缩重复数据"""
        # 移除连续的重复数据点
        if 'series' in chart_data:
            for series in chart_data['series']:
                if 'data' in series and len(series['data']) > 2:
                    compressed_data = []
                    prev_value = None
                    
                    for point in series['data']:
                        current_value = point[1] if isinstance(point, list) else point
                        
                        if current_value != prev_value:
                            compressed_data.append(point)
                            prev_value = current_value
                    
                    # 确保至少保留首尾两个点
                    if len(compressed_data) < 2 and len(series['data']) >= 2:
                        compressed_data = [series['data'][0], series['data'][-1]]
                    
                    series['data'] = compressed_data
        
        return chart_data

def test_performance_optimizer():
    """测试性能优化器"""
    
    # 创建大数据集
    np.random.seed(42)
    size = 50000
    df = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=size, freq='1min'),
        'category': np.random.choice(['A', 'B', 'C'], size),
        'value': np.random.randn(size) * 100 + 1000,
        'orders': np.random.poisson(10, size)
    })
    
    print(f"Original data size: {len(df)} rows")
    
    # 配置优化器
    form_data = {
        'viz_type': 'line',
        'groupby': ['category'],
        'metrics': ['value', 'orders'],
        'max_data_points': 1000
    }
    
    optimizer = ChartPerformanceOptimizer('line', form_data)
    
    # 测试查询优化
    start_time = time.time()
    optimized_df = optimizer.optimize_query(df)
    query_time = time.time() - start_time
    
    print(f"Optimized data size: {len(optimized_df)} rows")
    print(f"Query optimization time: {query_time:.3f}s")
    
    # 模拟图表数据
    chart_data = {
        'series': [{
            'name': 'test_series',
            'data': [[i, np.random.randn() * 100] for i in range(5000)]
        }]
    }
    
    # 测试渲染优化
    start_time = time.time()
    optimized_chart_data = optimizer.optimize_rendering(chart_data)
    render_time = time.time() - start_time
    
    print(f"Original chart points: {len(chart_data['series'][0]['data'])}")
    print(f"Optimized chart points: {len(optimized_chart_data['series'][0]['data'])}")
    print(f"Render optimization time: {render_time:.3f}s")

if __name__ == "__main__":
    test_performance_optimizer()
```

### 练习 4：图表缓存系统 (⭐⭐⭐⭐)

**目标**：实现智能的多层缓存系统

#### 4.1 实现缓存管理器
```python
# chart_cache_system.py
import json
import hashlib
import time
from typing import Dict, Any, Optional
import threading

class ChartCacheSystem:
    """图表缓存系统"""
    
    def __init__(self):
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
        self.max_memory_size = 100  # 最大缓存条目数
        self.default_ttl = 3600  # 默认1小时过期
        self.lock = threading.Lock()
    
    def generate_cache_key(self, slice_id: int, form_data: Dict, user_id: int = None) -> str:
        """生成缓存键"""
        key_data = {
            'slice_id': slice_id,
            'form_data': form_data,
            'user_id': user_id
        }
        
        # 排序确保一致性
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"chart_{slice_id}_{key_hash}"
    
    def get(self, cache_key: str) -> Optional[Dict]:
        """获取缓存数据"""
        with self.lock:
            if cache_key not in self.memory_cache:
                self.cache_stats['misses'] += 1
                return None
            
            cache_entry = self.memory_cache[cache_key]
            
            # 检查是否过期
            if time.time() > cache_entry['expires_at']:
                del self.memory_cache[cache_key]
                self.cache_stats['misses'] += 1
                self.cache_stats['evictions'] += 1
                return None
            
            # 更新访问时间
            cache_entry['last_accessed'] = time.time()
            self.cache_stats['hits'] += 1
            
            return cache_entry['data']
    
    def set(self, cache_key: str, data: Dict, ttl: int = None) -> None:
        """设置缓存数据"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self.lock:
            # 检查缓存大小限制
            if len(self.memory_cache) >= self.max_memory_size:
                self._evict_lru()
            
            cache_entry = {
                'data': data,
                'created_at': time.time(),
                'last_accessed': time.time(),
                'expires_at': time.time() + ttl,
                'size': len(json.dumps(data))
            }
            
            self.memory_cache[cache_key] = cache_entry
            self.cache_stats['sets'] += 1
    
    def _evict_lru(self) -> None:
        """淘汰最久未使用的缓存"""
        if not self.memory_cache:
            return
        
        # 找到最久未访问的键
        lru_key = min(
            self.memory_cache.keys(),
            key=lambda k: self.memory_cache[k]['last_accessed']
        )
        
        del self.memory_cache[lru_key]
        self.cache_stats['evictions'] += 1
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.memory_cache.clear()
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            'hit_rate': f"{hit_rate:.2f}%",
            'cache_size': len(self.memory_cache),
            'total_requests': total_requests
        }

class CachedChartService:
    """带缓存的图表服务"""
    
    def __init__(self):
        self.cache = ChartCacheSystem()
    
    def get_chart_data(self, slice_id: int, form_data: Dict, user_id: int = None) -> Dict:
        """获取图表数据（带缓存）"""
        # 生成缓存键
        cache_key = self.cache.generate_cache_key(slice_id, form_data, user_id)
        
        # 尝试从缓存获取
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"Cache HIT for key: {cache_key[:20]}...")
            return cached_data
        
        print(f"Cache MISS for key: {cache_key[:20]}...")
        
        # 模拟数据查询（实际中会调用数据库）
        chart_data = self._query_chart_data(slice_id, form_data)
        
        # 缓存结果
        cache_ttl = self._get_cache_ttl(form_data)
        self.cache.set(cache_key, chart_data, cache_ttl)
        
        return chart_data
    
    def _query_chart_data(self, slice_id: int, form_data: Dict) -> Dict:
        """模拟图表数据查询"""
        # 模拟查询延迟
        time.sleep(0.1)
        
        return {
            'slice_id': slice_id,
            'data': {
                'series': [{
                    'name': 'Sample Data',
                    'data': [[i, i * 10] for i in range(100)]
                }]
            },
            'query_time': 0.1,
            'timestamp': time.time()
        }
    
    def _get_cache_ttl(self, form_data: Dict) -> int:
        """根据查询类型确定缓存时间"""
        if form_data.get('time_range') == 'Last hour':
            return 300  # 5分钟
        elif form_data.get('time_range') == 'Last day':
            return 1800  # 30分钟
        else:
            return 3600  # 1小时

def test_cache_system():
    """测试缓存系统"""
    service = CachedChartService()
    
    # 测试数据
    slice_id = 123
    form_data_1 = {
        'viz_type': 'line',
        'metrics': ['sales'],
        'time_range': 'Last day'
    }
    form_data_2 = {
        'viz_type': 'bar',
        'metrics': ['orders'],
        'time_range': 'Last hour'
    }
    
    print("=== 测试缓存系统 ===")
    
    # 第一次请求 - 应该是缓存未命中
    start_time = time.time()
    data1 = service.get_chart_data(slice_id, form_data_1, user_id=1)
    first_request_time = time.time() - start_time
    
    # 第二次相同请求 - 应该是缓存命中
    start_time = time.time()
    data2 = service.get_chart_data(slice_id, form_data_1, user_id=1)
    cached_request_time = time.time() - start_time
    
    # 不同请求 - 应该是缓存未命中
    data3 = service.get_chart_data(slice_id, form_data_2, user_id=1)
    
    print(f"\n首次请求时间: {first_request_time:.3f}s")
    print(f"缓存请求时间: {cached_request_time:.3f}s")
    print(f"加速比: {first_request_time/cached_request_time:.1f}x")
    
    # 显示缓存统计
    print(f"\n缓存统计: {service.cache.get_stats()}")
    
    return service

if __name__ == "__main__":
    test_cache_system()
```

### 练习 5：图表调试工具 (⭐⭐⭐)

**目标**：开发图表问题诊断和调试工具

#### 5.1 创建调试工具
```python
# chart_debugger.py
import pandas as pd
import json
import traceback
from typing import Dict, List, Any
import time

class ChartDebugger:
    """图表调试器"""
    
    def __init__(self):
        self.debug_logs = []
        self.performance_metrics = {}
    
    def debug_chart_pipeline(self, slice_id: int, form_data: Dict) -> Dict:
        """调试图表处理流水线"""
        debug_info = {
            'slice_id': slice_id,
            'form_data': form_data,
            'steps': [],
            'errors': [],
            'warnings': [],
            'performance': {}
        }
        
        try:
            # 1. 验证表单数据
            step_result = self._debug_form_validation(form_data)
            debug_info['steps'].append(step_result)
            
            # 2. 检查数据源连接
            step_result = self._debug_datasource_connection(form_data)
            debug_info['steps'].append(step_result)
            
            # 3. 分析查询对象
            step_result = self._debug_query_object(form_data)
            debug_info['steps'].append(step_result)
            
            # 4. 模拟数据处理
            step_result = self._debug_data_processing(form_data)
            debug_info['steps'].append(step_result)
            
            # 5. 检查图表渲染
            step_result = self._debug_chart_rendering(form_data)
            debug_info['steps'].append(step_result)
            
        except Exception as e:
            debug_info['errors'].append({
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc()
            })
        
        return debug_info
    
    def _debug_form_validation(self, form_data: Dict) -> Dict:
        """调试表单数据验证"""
        step = {
            'step': 'Form Validation',
            'status': 'success',
            'details': {},
            'issues': []
        }
        
        # 检查必需字段
        required_fields = ['viz_type', 'datasource']
        for field in required_fields:
            if field not in form_data:
                step['issues'].append(f"Missing required field: {field}")
                step['status'] = 'error'
        
        # 检查指标和维度
        metrics = form_data.get('metrics', [])
        groupby = form_data.get('groupby', [])
        
        if not metrics and not groupby:
            step['issues'].append("No metrics or groupby columns specified")
            step['status'] = 'warning'
        
        step['details'] = {
            'metrics_count': len(metrics),
            'groupby_count': len(groupby),
            'form_data_size': len(json.dumps(form_data))
        }
        
        return step
    
    def _debug_datasource_connection(self, form_data: Dict) -> Dict:
        """调试数据源连接"""
        step = {
            'step': 'Datasource Connection',
            'status': 'success',
            'details': {},
            'issues': []
        }
        
        datasource = form_data.get('datasource', '')
        
        if not datasource:
            step['issues'].append("No datasource specified")
            step['status'] = 'error'
            return step
        
        # 模拟连接检查
        if '__' not in datasource:
            step['issues'].append("Invalid datasource format")
            step['status'] = 'error'
        else:
            datasource_parts = datasource.split('__')
            step['details'] = {
                'datasource_id': datasource_parts[0],
                'datasource_type': datasource_parts[1] if len(datasource_parts) > 1 else 'unknown'
            }
        
        return step
    
    def _debug_query_object(self, form_data: Dict) -> Dict:
        """调试查询对象构建"""
        step = {
            'step': 'Query Object',
            'status': 'success',
            'details': {},
            'issues': []
        }
        
        # 分析查询复杂度
        metrics = form_data.get('metrics', [])
        groupby = form_data.get('groupby', [])
        filters = form_data.get('filters', [])
        row_limit = form_data.get('row_limit', 10000)
        
        # 检查行数限制
        if row_limit > 50000:
            step['issues'].append(f"Large row limit ({row_limit}) may cause performance issues")
            step['status'] = 'warning'
        
        # 检查复杂查询
        if len(groupby) > 5:
            step['issues'].append(f"Too many groupby columns ({len(groupby)}) may impact performance")
            step['status'] = 'warning'
        
        step['details'] = {
            'estimated_complexity': len(metrics) * len(groupby) + len(filters),
            'row_limit': row_limit,
            'filter_count': len(filters)
        }
        
        return step
    
    def _debug_data_processing(self, form_data: Dict) -> Dict:
        """调试数据处理"""
        step = {
            'step': 'Data Processing',
            'status': 'success',
            'details': {},
            'issues': []
        }
        
        start_time = time.time()
        
        # 模拟数据处理
        try:
            # 创建模拟数据
            sample_data = pd.DataFrame({
                'category': ['A', 'B', 'C'] * 100,
                'value': range(300),
                'timestamp': pd.date_range('2023-01-01', periods=300, freq='1H')
            })
            
            # 模拟处理时间
            time.sleep(0.01)
            
            processing_time = time.time() - start_time
            
            step['details'] = {
                'sample_rows': len(sample_data),
                'processing_time': f"{processing_time:.3f}s",
                'memory_usage': f"{sample_data.memory_usage(deep=True).sum() / 1024:.1f}KB"
            }
            
        except Exception as e:
            step['issues'].append(f"Data processing error: {str(e)}")
            step['status'] = 'error'
        
        return step
    
    def _debug_chart_rendering(self, form_data: Dict) -> Dict:
        """调试图表渲染"""
        step = {
            'step': 'Chart Rendering',
            'status': 'success',
            'details': {},
            'issues': []
        }
        
        viz_type = form_data.get('viz_type', '')
        
        # 检查图表类型支持
        supported_types = ['line', 'bar', 'pie', 'table', 'card']
        if viz_type not in supported_types:
            step['issues'].append(f"Unsupported chart type: {viz_type}")
            step['status'] = 'error'
        
        # 模拟渲染数据大小检查
        estimated_points = 1000  # 模拟值
        if estimated_points > 5000:
            step['issues'].append(f"Large number of data points ({estimated_points}) may cause slow rendering")
            step['status'] = 'warning'
        
        step['details'] = {
            'viz_type': viz_type,
            'estimated_data_points': estimated_points,
            'render_complexity': 'medium'
        }
        
        return step
    
    def generate_debug_report(self, debug_info: Dict) -> str:
        """生成调试报告"""
        report = []
        report.append("=" * 50)
        report.append("CHART DEBUG REPORT")
        report.append("=" * 50)
        report.append(f"Slice ID: {debug_info['slice_id']}")
        report.append(f"Chart Type: {debug_info['form_data'].get('viz_type', 'Unknown')}")
        report.append("")
        
        # 步骤总结
        report.append("PROCESSING STEPS:")
        report.append("-" * 20)
        for step in debug_info['steps']:
            status_icon = "✓" if step['status'] == 'success' else "⚠" if step['status'] == 'warning' else "✗"
            report.append(f"{status_icon} {step['step']}: {step['status'].upper()}")
            
            if step['issues']:
                for issue in step['issues']:
                    report.append(f"    - {issue}")
        
        report.append("")
        
        # 错误信息
        if debug_info['errors']:
            report.append("ERRORS:")
            report.append("-" * 10)
            for error in debug_info['errors']:
                report.append(f"- {error['error_type']}: {error['error_message']}")
        
        # 性能指标
        report.append("")
        report.append("PERFORMANCE METRICS:")
        report.append("-" * 20)
        for step in debug_info['steps']:
            if 'processing_time' in step['details']:
                report.append(f"- {step['step']}: {step['details']['processing_time']}")
        
        return "\n".join(report)

def test_chart_debugger():
    """测试图表调试器"""
    debugger = ChartDebugger()
    
    # 测试用例1：正常图表
    print("=== 测试正常图表 ===")
    form_data_good = {
        'viz_type': 'line',
        'datasource': '123__table',
        'metrics': ['sales'],
        'groupby': ['date'],
        'row_limit': 1000
    }
    
    debug_info = debugger.debug_chart_pipeline(1, form_data_good)
    report = debugger.generate_debug_report(debug_info)
    print(report)
    
    print("\n" + "=" * 60 + "\n")
    
    # 测试用例2：有问题的图表
    print("=== 测试有问题的图表 ===")
    form_data_bad = {
        'viz_type': 'unsupported_type',
        'metrics': [],
        'groupby': ['col1', 'col2', 'col3', 'col4', 'col5', 'col6'],  # 太多分组列
        'row_limit': 100000  # 行数太多
    }
    
    debug_info = debugger.debug_chart_pipeline(2, form_data_bad)
    report = debugger.generate_debug_report(debug_info)
    print(report)

if __name__ == "__main__":
    test_chart_debugger()
```

---

## 🎓 思考题

### 基础思考题

1. **图表类型扩展**：如何为 Superset 添加一个新的雷达图图表类型？需要实现哪些关键方法？

2. **数据转换优化**：当处理包含多个时间序列的数据时，如何优化数据转换以提高性能？

3. **缓存策略选择**：什么情况下应该使用内存缓存，什么情况下应该使用Redis缓存？

### 高级思考题

1. **大数据渲染**：如何处理包含百万级数据点的图表渲染？除了采样，还有哪些优化策略？

2. **实时数据更新**：如何实现图表的实时数据更新，同时保持良好的性能？

3. **跨图表联动**：如何实现多个图表之间的数据联动和交互？

---

## ✅ 练习验证清单

完成每个练习后，请检查以下要点：

### 练习 1 验证点
- [ ] 自定义图表类能正确注册到系统中
- [ ] 图表数据处理逻辑正确
- [ ] 数值格式化显示符合预期

### 练习 2 验证点
- [ ] 数据处理管道能正确执行多个处理器
- [ ] 空值和异常值处理效果符合预期
- [ ] 聚合计算结果正确

### 练习 3 验证点
- [ ] 性能优化器能识别大数据集
- [ ] 采样和聚合策略有效减少数据量
- [ ] 渲染优化提升了处理速度

### 练习 4 验证点
- [ ] 缓存系统正确实现LRU淘汰策略
- [ ] 缓存命中率统计准确
- [ ] 性能提升明显

### 练习 5 验证点
- [ ] 调试器能识别常见配置问题
- [ ] 调试报告信息完整清晰
- [ ] 性能指标监控有效

---

**继续学习**：完成这些练习后，你已经深入掌握了 Superset 图表系统的核心机制。下一步可以尝试实际扩展 Superset 的图表功能，或者深入研究特定图表库（如 ECharts、D3）的集成方式！ 