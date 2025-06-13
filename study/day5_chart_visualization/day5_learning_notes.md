# Day 5 深度学习：图表系统与可视化引擎 📊

欢迎来到第五天的学习！今天我们将深入探索 Apache Superset 的图表系统和可视化引擎。

## 🎯 学习目标

- **图表系统架构**：理解插件化图表设计
- **可视化引擎设计**：掌握数据到视觉的转换流程
- **图表插件系统**：学习可扩展的图表架构
- **数据处理流水线**：理解查询结果的处理机制
- **前后端交互**：掌握图表渲染的协作模式
- **性能优化策略**：学习大数据量优化技术

---

## 1. 图表系统架构概览

### 1.1 整体架构设计

**核心理念**：Superset 采用插件化的图表架构，将数据获取、数据处理、图表渲染分离。

#### 架构层次图

```
Frontend (React)
├── Chart Components (echarts, d3)
├── Control Panel (配置参数)
└── Chart API Interface

Backend (Python) 
├── Chart API Layer
├── Visualization Registry
├── Chart Processing Engine
└── Data Layer
```

#### 核心组件

**1. Slice 模型** - 图表的数据模型
```python
class Slice(Model):
    """图表/切片模型"""
    id = Column(Integer, primary_key=True)
    slice_name = Column(String(250), nullable=False)
    datasource_id = Column(Integer)
    viz_type = Column(String(250))  # 图表类型
    params = Column(Text)  # JSON格式的配置参数
    
    @property
    def form_data(self):
        """获取图表配置"""
        return json.loads(self.params) if self.params else {}
    
    @property
    def viz(self):
        """获取可视化对象"""
        return viz_types[self.viz_type](
            datasource=self.datasource,
            form_data=self.form_data
        )
```

**2. BaseViz 基础可视化类**
```python
class BaseViz:
    """可视化基类"""
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
            'datasource': {
                'type': self.datasource.type,
                'id': self.datasource.id
            },
            'columns': self.form_data.get('groupby', []),
            'metrics': self.form_data.get('metrics', []),
            'filters': self.form_data.get('filters', []),
            'row_limit': self.form_data.get('row_limit', 10000),
        }
    
    def get_data(self, df):
        """处理查询结果，转换为图表数据"""
        raise NotImplementedError()
    
    def run_query(self):
        """执行查询并获取数据"""
        query_result = self.datasource.query(self.query_obj())
        return self.get_data(query_result.df)
```

### 1.2 可视化注册系统

#### Viz 类型注册机制

```python
viz_types = {}  # 全局图表类型注册表

def register_viz(viz_class):
    """注册可视化类型"""
    viz_types[viz_class.viz_type] = viz_class
    return viz_class

@register_viz
class TableViz(BaseViz):
    """表格视图"""
    viz_type = 'table'
    verbose_name = 'Table View'
    
    def get_data(self, df):
        return {
            'records': df.to_dict('records'),
            'columns': [
                {'key': col, 'label': col, 'dataType': str(df[col].dtype)}
                for col in df.columns
            ],
            'totalCount': len(df)
        }

@register_viz
class LineChartViz(BaseViz):
    """折线图"""
    viz_type = 'line'
    verbose_name = 'Line Chart'
    is_timeseries = True
    
    def get_data(self, df):
        time_col = self.form_data.get('granularity_sqla')
        metrics = self.form_data.get('metrics', [])
        
        series_data = []
        for metric in metrics:
            if metric in df.columns:
                series_data.append({
                    'name': metric,
                    'data': [[row[time_col], row[metric]] for _, row in df.iterrows()]
                })
        
        return {
            'series': series_data,
            'xAxis': {'type': 'time'},
            'yAxis': {'type': 'value'}
        }
```

## 2. 数据处理流水线

### 2.1 查询结果后处理

```python
class DataProcessor:
    """数据处理器"""
    
    def __init__(self, viz):
        self.viz = viz
        self.form_data = viz.form_data
    
    def process(self, df):
        """数据处理主流程"""
        # 1. 空值处理
        df = self._handle_null_values(df)
        
        # 2. 时间序列处理
        if self.viz.is_timeseries:
            df = self._process_timeseries(df)
        
        # 3. 聚合计算
        df = self._apply_aggregations(df)
        
        # 4. 排序和限制
        df = self._apply_ordering_and_limit(df)
        
        return df
    
    def _handle_null_values(self, df):
        """处理空值"""
        fillna_value = self.form_data.get('fillna_value', self.viz.default_fillna)
        
        # 数值列填充默认值
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(fillna_value)
        
        # 分类列填充空字符串
        categorical_columns = df.select_dtypes(include=['object']).columns
        df[categorical_columns] = df[categorical_columns].fillna('')
        
        return df
    
    def _process_timeseries(self, df):
        """时间序列处理"""
        time_col = self.form_data.get('granularity_sqla')
        if time_col and time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.sort_values(time_col)
        return df
```

### 2.2 图表特定数据转换

```python
class ChartDataTransformer:
    """图表数据转换器"""
    
    @staticmethod
    def transform_for_echarts(df, chart_type):
        """为 ECharts 转换数据格式"""
        if chart_type == 'line':
            return ChartDataTransformer._transform_line_chart(df)
        elif chart_type == 'pie':
            return ChartDataTransformer._transform_pie_chart(df)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
    
    @staticmethod
    def _transform_line_chart(df):
        """折线图数据转换"""
        x_column = df.columns[0]
        y_columns = df.columns[1:]
        
        x_data = df[x_column].tolist()
        
        series = []
        for y_col in y_columns:
            series.append({
                'name': y_col,
                'type': 'line',
                'data': df[y_col].tolist(),
                'smooth': True
            })
        
        return {
            'xAxis': {'type': 'category', 'data': x_data},
            'yAxis': {'type': 'value'},
            'series': series,
            'tooltip': {'trigger': 'axis'},
            'legend': {'data': y_columns.tolist()}
        }
    
    @staticmethod
    def _transform_pie_chart(df):
        """饼图数据转换"""
        name_col = df.columns[0]
        value_col = df.columns[1]
        
        pie_data = []
        for _, row in df.iterrows():
            pie_data.append({
                'name': row[name_col],
                'value': row[value_col]
            })
        
        return {
            'series': [{
                'type': 'pie',
                'radius': '50%',
                'data': pie_data
            }],
            'tooltip': {
                'trigger': 'item',
                'formatter': '{a} <br/>{b}: {c} ({d}%)'
            },
            'legend': {
                'orient': 'vertical',
                'left': 'left',
                'data': df[name_col].tolist()
            }
        }
```

## 3. 前后端交互协议

### 3.1 图表数据 API 设计

```python
class ChartDataAPI(Resource):
    """图表数据API"""
    
    @expose('/chart_data', methods=['POST'])
    def chart_data(self):
        """获取图表数据"""
        try:
            # 解析请求参数
            form_data = request.json.get('form_data', {})
            slice_id = request.json.get('slice_id')
            
            # 获取或创建图表对象
            if slice_id:
                slice_obj = db.session.query(Slice).get(slice_id)
                slice_obj.form_data.update(form_data)
            else:
                slice_obj = self._create_temp_slice(form_data)
            
            # 执行查询和数据处理
            viz_obj = slice_obj.viz
            chart_data = viz_obj.get_json_data()
            
            # 构建响应
            response_data = {
                'chart_data': chart_data,
                'slice_id': slice_id,
                'form_data': slice_obj.form_data,
                'cache_key': self._generate_cache_key(slice_obj),
            }
            
            return self.response(200, **response_data)
            
        except Exception as e:
            return self.response_400(message=str(e))
```

## 4. 图表性能优化

### 4.1 大数据量处理策略

```python
class LargeDatasetOptimizer:
    """大数据集优化器"""
    
    def __init__(self, viz):
        self.viz = viz
        self.form_data = viz.form_data
    
    def optimize_query(self, query_obj):
        """查询优化"""
        # 智能采样
        if self._should_use_sampling():
            query_obj = self._apply_sampling(query_obj)
        
        # 分页查询
        if self._should_use_pagination():
            query_obj = self._apply_pagination(query_obj)
        
        return query_obj
    
    def _should_use_sampling(self):
        """判断是否需要采样"""
        estimated_rows = self._estimate_result_size()
        return estimated_rows > 100000
    
    def optimize_rendering(self, data):
        """渲染优化"""
        # 数据点限制
        data = self._limit_data_points(data)
        
        # 数据精度优化
        data = self._optimize_precision(data)
        
        return data
    
    def _limit_data_points(self, data):
        """限制数据点数量"""
        max_points = self.form_data.get('max_data_points', 5000)
        
        if 'series' in data:
            for series in data['series']:
                if 'data' in series and len(series['data']) > max_points:
                    step = len(series['data']) // max_points
                    series['data'] = series['data'][::step]
        
        return data
```

### 4.2 缓存策略设计

```python
class ChartCacheManager:
    """图表缓存管理器"""
    
    def __init__(self):
        self.memory_cache = {}
        self.redis_cache = None
        self.enable_cache = True
    
    def get_chart_data(self, cache_key):
        """获取缓存的图表数据"""
        if not self.enable_cache:
            return None
        
        # 尝试内存缓存
        if cache_key in self.memory_cache:
            cache_info = self.memory_cache[cache_key]
            if not self._is_expired(cache_info):
                return cache_info['data']
        
        # 尝试Redis缓存
        if self.redis_cache:
            try:
                cached_data = self.redis_cache.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    self._set_memory_cache(cache_key, data, 300)
                    return data
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        return None
    
    def set_chart_data(self, cache_key, data, timeout=3600):
        """设置图表数据缓存"""
        if not self.enable_cache:
            return
        
        # 设置内存缓存（小数据）
        data_size = len(json.dumps(data))
        if data_size < 1024 * 1024:  # 小于1MB
            self._set_memory_cache(cache_key, data, min(timeout, 600))
        
        # 设置Redis缓存
        if self.redis_cache:
            try:
                self.redis_cache.setex(
                    cache_key, 
                    timeout, 
                    json.dumps(data, default=str)
                )
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
```

---

## 📚 学习小结

### 核心概念掌握 ✅

1. **图表系统架构**：理解插件化设计的优势
2. **可视化引擎**：掌握数据到图表的转换流程
3. **数据处理流水线**：理解查询后的数据处理
4. **前后端协作**：掌握图表渲染的协作模式
5. **性能优化**：学习大数据量优化策略
6. **缓存系统**：理解多层次缓存设计

### 架构设计理解 ✅

- 插件化架构的可扩展性
- 数据处理流水线的模块化
- 前后端分离的协作机制
- 性能优化的多层次策略

### 实际应用能力 ✅

- 理解图表类型的扩展
- 掌握图表数据的处理
- 具备性能优化思维
- 理解缓存策略设计

**下一步**：通过实际操作验证理论知识，创建自定义图表、优化性能！ 