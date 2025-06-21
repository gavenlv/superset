#!/usr/bin/env python3
"""
Day 17: Chart SQL生成逻辑演示代码

本文件演示Superset中Chart如何根据用户选择的条件生成SQL，
包括filter、order、formatting以及自定义聚合函数和窗口函数的实现。
"""

import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, DateTime, Numeric, text, literal_column
from sqlalchemy.sql import select, func, and_, or_, asc, desc
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json

print("=" * 80)
print("Day 17: Chart SQL生成逻辑演示")
print("=" * 80)

# ================================
# 1. 核心SQL生成组件模拟
# ================================

class MockColumn:
    """模拟TableColumn"""
    
    def __init__(self, column_name: str, column_type: str, is_dttm: bool = False):
        self.column_name = column_name
        self.type = column_type
        self.is_dttm = is_dttm
        self.is_numeric = column_type in ['INTEGER', 'NUMERIC', 'FLOAT']
        self.is_string = column_type in ['VARCHAR', 'TEXT']
    
    def get_sqla_col(self, template_processor=None):
        """获取SQLAlchemy列对象"""
        return Column(self.column_name, eval(self.type) if hasattr(sa, self.type) else String)
    
    def get_timestamp_expression(self, time_grain=None, label=None, template_processor=None):
        """获取时间表达式"""
        col = self.get_sqla_col()
        if time_grain == 'month':
            return func.date_trunc('month', col).label(label or self.column_name)
        elif time_grain == 'day':
            return func.date_trunc('day', col).label(label or self.column_name)
        else:
            return col.label(label or self.column_name)

class MockMetric:
    """模拟SqlMetric"""
    
    def __init__(self, metric_name: str, expression: str):
        self.metric_name = metric_name
        self.expression = expression
    
    def get_sqla_col(self, template_processor=None):
        """获取SQLAlchemy指标表达式"""
        return literal_column(self.expression).label(self.metric_name)

class MockSqlGenerationMixin:
    """模拟ExploreMixin的SQL生成功能"""
    
    def __init__(self):
        # 内置聚合函数映射
        self.sqla_aggregations = {
            "COUNT_DISTINCT": lambda col: func.COUNT(func.distinct(col)),
            "COUNT": func.COUNT,
            "SUM": func.SUM,
            "AVG": func.AVG,
            "MIN": func.MIN,
            "MAX": func.MAX,
            # 扩展的聚合函数
            "MEDIAN": lambda col: func.PERCENTILE_CONT(0.5).within_group(asc(col)),
            "STDDEV": func.STDDEV,
            "VARIANCE": func.VAR_POP,
        }
        
        # 模拟表结构
        self.columns = [
            MockColumn('order_date', 'DateTime', is_dttm=True),
            MockColumn('country', 'String'),
            MockColumn('product', 'String'),
            MockColumn('sales_amount', 'Numeric'),
            MockColumn('quantity', 'Integer'),
            MockColumn('customer_id', 'String'),
        ]
        
        self.metrics = [
            MockMetric('total_sales', 'SUM(sales_amount)'),
            MockMetric('avg_sales', 'AVG(sales_amount)'),
            MockMetric('order_count', 'COUNT(*)'),
            MockMetric('unique_customers', 'COUNT(DISTINCT customer_id)'),
        ]
        
        self.columns_by_name = {col.column_name: col for col in self.columns}
        self.metrics_by_name = {metric.metric_name: metric for metric in self.metrics}
    
    def adhoc_metric_to_sqla(self, metric_def: Dict[str, Any]) -> Any:
        """将即席指标转换为SQLAlchemy表达式"""
        
        expression_type = metric_def.get("expressionType", "SIMPLE")
        label = metric_def.get("label", "metric")
        
        if expression_type == "SIMPLE":
            # 简单聚合指标
            column_name = metric_def["column"]["column_name"]
            aggregate = metric_def["aggregate"]
            
            if column_name in self.columns_by_name:
                col = self.columns_by_name[column_name].get_sqla_col()
            else:
                col = literal_column(column_name)
            
            if aggregate in self.sqla_aggregations:
                sqla_metric = self.sqla_aggregations[aggregate](col)
            else:
                raise ValueError(f"Unknown aggregate: {aggregate}")
            
        elif expression_type == "SQL":
            # SQL表达式指标
            sql_expression = metric_def["sqlExpression"]
            sqla_metric = literal_column(sql_expression)
        else:
            raise ValueError(f"Invalid expression type: {expression_type}")
        
        return sqla_metric.label(label)
    
    def build_filter_clause(self, filter_obj: Dict[str, Any]) -> Any:
        """构建过滤器子句"""
        
        col_name = filter_obj["col"]
        op = filter_obj["op"].upper()
        val = filter_obj.get("val")
        
        # 获取列对象
        if col_name in self.columns_by_name:
            sqla_col = self.columns_by_name[col_name].get_sqla_col()
        else:
            sqla_col = literal_column(col_name)
        
        # 构建过滤条件
        if op == "==":
            return sqla_col == val
        elif op == "!=":
            return sqla_col != val
        elif op == ">":
            return sqla_col > val
        elif op == ">=":
            return sqla_col >= val
        elif op == "<":
            return sqla_col < val
        elif op == "<=":
            return sqla_col <= val
        elif op == "IN":
            return sqla_col.in_(val)
        elif op == "NOT IN":
            return ~sqla_col.in_(val)
        elif op == "LIKE":
            return sqla_col.like(val)
        elif op == "IS NULL":
            return sqla_col.is_(None)
        elif op == "IS NOT NULL":
            return sqla_col.isnot(None)
        else:
            raise ValueError(f"Unsupported operator: {op}")
    
    def get_sqla_query(self, **query_obj):
        """核心SQL生成方法"""
        
        print("\n" + "="*60)
        print("SQL生成过程演示")
        print("="*60)
        
        # 1. 解析查询参数
        columns = query_obj.get('columns', [])
        metrics = query_obj.get('metrics', [])
        groupby = query_obj.get('groupby', [])
        filters = query_obj.get('filter', [])
        orderby = query_obj.get('orderby', [])
        row_limit = query_obj.get('row_limit')
        
        print(f"查询参数:")
        print(f"  列: {columns}")
        print(f"  指标: {metrics}")
        print(f"  分组: {groupby}")
        print(f"  过滤器: {filters}")
        print(f"  排序: {orderby}")
        print(f"  限制: {row_limit}")
        
        # 2. 构建SELECT表达式
        select_exprs = []
        
        # 添加分组列
        for col_name in groupby or columns:
            if isinstance(col_name, str) and col_name in self.columns_by_name:
                col_obj = self.columns_by_name[col_name]
                select_exprs.append(col_obj.get_sqla_col().label(col_name))
        
        # 添加指标
        for metric in metrics:
            if isinstance(metric, str) and metric in self.metrics_by_name:
                # 预定义指标
                metric_obj = self.metrics_by_name[metric]
                select_exprs.append(metric_obj.get_sqla_col())
            elif isinstance(metric, dict):
                # 即席指标
                select_exprs.append(self.adhoc_metric_to_sqla(metric))
        
        print(f"\nSELECT表达式: {len(select_exprs)}个")
        
        # 3. 构建FROM子句
        from_clause = text("sales_table")
        
        # 4. 构建WHERE子句
        where_conditions = []
        for filter_obj in filters:
            condition = self.build_filter_clause(filter_obj)
            where_conditions.append(condition)
        
        print(f"WHERE条件: {len(where_conditions)}个")
        
        # 5. 构建GROUP BY子句
        groupby_cols = []
        for col_name in groupby:
            if col_name in self.columns_by_name:
                groupby_cols.append(self.columns_by_name[col_name].get_sqla_col())
        
        print(f"GROUP BY列: {len(groupby_cols)}个")
        
        # 6. 构建ORDER BY子句
        orderby_exprs = []
        for order_spec in orderby:
            col_name, ascending = order_spec if isinstance(order_spec, list) else (order_spec, True)
            
            if col_name in self.columns_by_name:
                col = self.columns_by_name[col_name].get_sqla_col()
            elif col_name in self.metrics_by_name:
                col = self.metrics_by_name[col_name].get_sqla_col()
            else:
                col = literal_column(col_name)
            
            orderby_exprs.append(asc(col) if ascending else desc(col))
        
        print(f"ORDER BY表达式: {len(orderby_exprs)}个")
        
        # 7. 组装最终查询
        query = select(select_exprs).select_from(from_clause)
        
        if where_conditions:
            query = query.where(and_(*where_conditions))
        
        if groupby_cols:
            query = query.group_by(*groupby_cols)
        
        if orderby_exprs:
            query = query.order_by(*orderby_exprs)
        
        if row_limit:
            query = query.limit(row_limit)
        
        return query

# ================================
# 2. 演示基础SQL生成
# ================================

def demo_basic_sql_generation():
    """演示基础SQL生成功能"""
    
    print("\n" + "="*60)
    print("2. 基础SQL生成演示")
    print("="*60)
    
    sql_generator = MockSqlGenerationMixin()
    
    # 示例1: 简单的分组聚合查询
    query_obj_1 = {
        'columns': ['country', 'product'],
        'metrics': ['total_sales', 'order_count'],
        'groupby': ['country', 'product'],
        'filter': [
            {'col': 'order_date', 'op': '>=', 'val': '2023-01-01'},
            {'col': 'sales_amount', 'op': '>', 'val': 100}
        ],
        'orderby': [['total_sales', False]],  # 降序
        'row_limit': 100
    }
    
    print("\n示例1: 基础分组聚合查询")
    query1 = sql_generator.get_sqla_query(**query_obj_1)
    print(f"生成的查询对象: {type(query1)}")
    
    # 示例2: 包含即席指标的查询
    query_obj_2 = {
        'columns': ['country'],
        'metrics': [
            {
                'expressionType': 'SIMPLE',
                'column': {'column_name': 'sales_amount'},
                'aggregate': 'AVG',
                'label': 'avg_sales_amount'
            },
            {
                'expressionType': 'SQL',
                'sqlExpression': 'SUM(sales_amount) / SUM(quantity)',
                'label': 'avg_unit_price'
            }
        ],
        'groupby': ['country'],
        'orderby': [['avg_sales_amount', True]],  # 升序
    }
    
    print("\n示例2: 即席指标查询")
    query2 = sql_generator.get_sqla_query(**query_obj_2)
    print(f"生成的查询对象: {type(query2)}")

# ================================
# 3. 聚合函数扩展演示
# ================================

class ExtendedAggregations(MockSqlGenerationMixin):
    """扩展聚合函数的演示"""
    
    def __init__(self):
        super().__init__()
        
        # 添加自定义聚合函数
        self.sqla_aggregations.update({
            "PERCENTILE_95": lambda col: func.PERCENTILE_CONT(0.95).within_group(asc(col)),
            "MODE": lambda col: func.MODE().within_group(asc(col)),
            "GEOMEAN": lambda col: func.EXP(func.AVG(func.LN(func.NULLIF(col, 0)))),
            "HARMONIC_MEAN": lambda col: 1.0 / func.AVG(1.0 / func.NULLIF(col, 0)),
            "RANGE": lambda col: func.MAX(col) - func.MIN(col),
            "COEFF_VAR": lambda col: func.STDDEV(col) / func.AVG(col),
        })

def demo_extended_aggregations():
    """演示扩展聚合函数"""
    
    print("\n" + "="*60)
    print("3. 扩展聚合函数演示")
    print("="*60)
    
    extended_generator = ExtendedAggregations()
    
    # 展示所有可用的聚合函数
    print("\n可用聚合函数:")
    for i, (name, func_obj) in enumerate(extended_generator.sqla_aggregations.items(), 1):
        print(f"  {i:2d}. {name}")
    
    # 使用扩展聚合函数的查询
    query_obj = {
        'columns': ['country'],
        'metrics': [
            {
                'expressionType': 'SIMPLE',
                'column': {'column_name': 'sales_amount'},
                'aggregate': 'MEDIAN',
                'label': 'median_sales'
            },
            {
                'expressionType': 'SIMPLE',
                'column': {'column_name': 'sales_amount'},
                'aggregate': 'PERCENTILE_95',
                'label': 'p95_sales'
            },
            {
                'expressionType': 'SIMPLE',
                'column': {'column_name': 'sales_amount'},
                'aggregate': 'GEOMEAN',
                'label': 'geomean_sales'
            },
            {
                'expressionType': 'SIMPLE',
                'column': {'column_name': 'sales_amount'},
                'aggregate': 'COEFF_VAR',
                'label': 'cv_sales'
            }
        ],
        'groupby': ['country'],
        'orderby': [['median_sales', False]]
    }
    
    print("\n扩展聚合函数查询示例:")
    query = extended_generator.get_sqla_query(**query_obj)
    print(f"成功生成包含 {len(query_obj['metrics'])} 个扩展聚合函数的查询")

# ================================
# 4. 窗口函数演示
# ================================

class WindowFunctionDemo:
    """窗口函数演示"""
    
    def __init__(self):
        self.window_functions = {
            'rolling_sum': self.rolling_sum,
            'rolling_avg': self.rolling_avg,
            'cumulative_sum': self.cumulative_sum,
            'rank': self.rank_function,
            'lag': self.lag_function,
            'lead': self.lead_function,
        }
    
    def rolling_sum(self, df: pd.DataFrame, column: str, window: int) -> pd.Series:
        """滚动求和"""
        return df[column].rolling(window=window, min_periods=1).sum()
    
    def rolling_avg(self, df: pd.DataFrame, column: str, window: int) -> pd.Series:
        """滚动平均"""
        return df[column].rolling(window=window, min_periods=1).mean()
    
    def cumulative_sum(self, df: pd.DataFrame, column: str) -> pd.Series:
        """累计求和"""
        return df[column].cumsum()
    
    def rank_function(self, df: pd.DataFrame, column: str, method: str = 'dense') -> pd.Series:
        """排名函数"""
        return df[column].rank(method=method, ascending=False)
    
    def lag_function(self, df: pd.DataFrame, column: str, periods: int = 1) -> pd.Series:
        """滞后函数"""
        return df[column].shift(periods)
    
    def lead_function(self, df: pd.DataFrame, column: str, periods: int = 1) -> pd.Series:
        """超前函数"""
        return df[column].shift(-periods)
    
    def twelve_month_cumulative(self, df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
        """12月累计值计算"""
        
        # 确保日期列是datetime类型
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # 按月分组
        df['year_month'] = df[date_col].dt.to_period('M')
        
        # 计算12月滚动累计
        df['12m_cumulative'] = df[value_col].rolling(window=12, min_periods=1).sum()
        
        return df
    
    def year_over_year_growth(self, df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
        """同比增长率计算"""
        
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # 计算去年同期值
        df['prev_year_value'] = df[value_col].shift(12)  # 假设是月度数据
        
        # 计算同比增长率
        df['yoy_growth'] = ((df[value_col] - df['prev_year_value']) / 
                           df['prev_year_value'] * 100)
        
        return df

def demo_window_functions():
    """演示窗口函数"""
    
    print("\n" + "="*60)
    print("4. 窗口函数演示")
    print("="*60)
    
    # 创建示例数据
    dates = pd.date_range('2022-01-01', '2023-12-31', freq='M')
    data = {
        'date': dates,
        'sales': [100 + i*10 + (i%12)*5 for i in range(len(dates))],
        'country': ['USA'] * 12 + ['China'] * 12,
    }
    df = pd.DataFrame(data)
    
    print(f"示例数据: {len(df)} 行")
    print(df.head())
    
    window_demo = WindowFunctionDemo()
    
    # 演示各种窗口函数
    print("\n窗口函数演示:")
    
    # 1. 滚动求和
    df['rolling_3m_sum'] = window_demo.rolling_sum(df, 'sales', 3)
    print("1. 3月滚动求和 - 完成")
    
    # 2. 滚动平均
    df['rolling_6m_avg'] = window_demo.rolling_avg(df, 'sales', 6)
    print("2. 6月滚动平均 - 完成")
    
    # 3. 累计求和
    df['cumulative_sum'] = window_demo.cumulative_sum(df, 'sales')
    print("3. 累计求和 - 完成")
    
    # 4. 12月累计值
    df = window_demo.twelve_month_cumulative(df, 'date', 'sales')
    print("4. 12月累计值 - 完成")
    
    # 5. 同比增长率
    df = window_demo.year_over_year_growth(df, 'date', 'sales')
    print("5. 同比增长率 - 完成")
    
    # 显示结果
    print("\n窗口函数结果预览:")
    print(df[['date', 'sales', 'rolling_3m_sum', 'rolling_6m_avg', 'cumulative_sum', 
              '12m_cumulative', 'yoy_growth']].tail(10))

# ================================
# 5. 高级扩展演示
# ================================

class AdvancedExtensions:
    """高级扩展功能演示"""
    
    def __init__(self):
        self.custom_functions = {}
        self.permissions = {}
    
    def register_custom_function(self, name: str, function: callable, 
                                required_permission: str = None):
        """注册自定义函数"""
        self.custom_functions[name] = {
            'function': function,
            'permission': required_permission
        }
        print(f"已注册自定义函数: {name}")
    
    def create_configurable_aggregation(self, config: Dict[str, Any]) -> callable:
        """创建可配置的聚合函数"""
        
        template = config['template']
        params = config.get('parameters', {})
        
        def configurable_function(column_name, **kwargs):
            # 简化的模板渲染
            sql = template.format(
                column=column_name,
                **params,
                **kwargs
            )
            return literal_column(sql)
        
        return configurable_function
    
    def database_specific_functions(self, db_type: str) -> Dict[str, callable]:
        """数据库特定函数"""
        
        if db_type == 'postgresql':
            return {
                'STRING_AGG': lambda col, sep=',': func.STRING_AGG(col, sep),
                'ARRAY_AGG': func.ARRAY_AGG,
                'JSON_AGG': func.JSON_AGG,
            }
        elif db_type == 'mysql':
            return {
                'GROUP_CONCAT': lambda col, sep=',': func.GROUP_CONCAT(col, sep),
            }
        elif db_type == 'bigquery':
            return {
                'APPROX_COUNT_DISTINCT': func.APPROX_COUNT_DISTINCT,
                'APPROX_QUANTILES': lambda col, n: func.APPROX_QUANTILES(col, n),
            }
        else:
            return {}

def demo_advanced_extensions():
    """演示高级扩展功能"""
    
    print("\n" + "="*60)
    print("5. 高级扩展功能演示")
    print("="*60)
    
    extensions = AdvancedExtensions()
    
    # 1. 可配置聚合函数
    print("\n1. 可配置聚合函数:")
    
    weighted_avg_config = {
        'template': 'SUM({column} * {weight_column}) / SUM({weight_column})',
        'parameters': {'weight_column': 'quantity'}
    }
    
    weighted_avg_func = extensions.create_configurable_aggregation(weighted_avg_config)
    extensions.register_custom_function('WEIGHTED_AVG', weighted_avg_func)
    
    percentile_config = {
        'template': 'PERCENTILE_CONT({percentile}) WITHIN GROUP (ORDER BY {column})',
        'parameters': {'percentile': 0.9}
    }
    
    percentile_90_func = extensions.create_configurable_aggregation(percentile_config)
    extensions.register_custom_function('PERCENTILE_90', percentile_90_func)
    
    # 2. 数据库特定函数
    print("\n2. 数据库特定函数:")
    
    for db_type in ['postgresql', 'mysql', 'bigquery']:
        db_functions = extensions.database_specific_functions(db_type)
        print(f"  {db_type.upper()}: {list(db_functions.keys())}")
    
    # 3. 自定义业务函数
    print("\n3. 自定义业务函数:")
    
    def customer_lifetime_value(customer_col, sales_col, time_col):
        """客户生命周期价值计算"""
        return literal_column(f"""
            SUM({sales_col}) / 
            (EXTRACT(DAYS FROM MAX({time_col}) - MIN({time_col})) / 365.0)
        """)
    
    def cohort_retention_rate(user_col, signup_date, activity_date, period_months):
        """队列留存率计算"""
        return literal_column(f"""
            COUNT(DISTINCT CASE 
                WHEN {activity_date} BETWEEN {signup_date} 
                AND {signup_date} + INTERVAL {period_months} MONTH 
                THEN {user_col} END) * 100.0 / COUNT(DISTINCT {user_col})
        """)
    
    extensions.register_custom_function('CLV', customer_lifetime_value, 'advanced_analytics')
    extensions.register_custom_function('COHORT_RETENTION', cohort_retention_rate, 'advanced_analytics')
    
    print(f"已注册 {len(extensions.custom_functions)} 个自定义函数")

# ================================
# 6. 性能优化演示
# ================================

class PerformanceOptimization:
    """性能优化演示"""
    
    @staticmethod
    def analyze_query_performance():
        """分析查询性能"""
        
        optimization_strategies = {
            'sql_level': {
                'indexing': '为常用的groupby和order by列创建索引',
                'partitioning': '使用分区表优化大数据集查询',
                'materialized_views': '为复杂聚合创建物化视图',
                'query_rewriting': '优化复杂子查询为JOIN操作'
            },
            'application_level': {
                'caching': '缓存频繁访问的查询结果',
                'pagination': '实现智能分页减少数据传输',
                'async_processing': '异步处理复杂的窗口函数计算',
                'batch_operations': '批量处理多个相似查询'
            },
            'data_processing': {
                'vectorization': '使用向量化操作替代循环',
                'parallel_processing': '并行处理多个指标计算',
                'memory_optimization': '优化内存使用减少GC压力',
                'streaming': '流式处理大数据集'
            }
        }
        
        return optimization_strategies
    
    @staticmethod
    def benchmark_window_functions():
        """窗口函数性能基准测试"""
        
        import time
        
        # 创建大数据集
        n_rows = 100000
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=n_rows, freq='H'),
            'value': range(n_rows),
            'group': [f'group_{i%100}' for i in range(n_rows)]
        })
        
        benchmark_results = {}
        
        # 测试不同窗口函数的性能
        functions_to_test = [
            ('rolling_sum_100', lambda df: df['value'].rolling(100).sum()),
            ('rolling_mean_1000', lambda df: df['value'].rolling(1000).mean()),
            ('cumsum', lambda df: df['value'].cumsum()),
            ('rank', lambda df: df['value'].rank()),
        ]
        
        for func_name, func in functions_to_test:
            start_time = time.time()
            result = func(df)
            end_time = time.time()
            
            benchmark_results[func_name] = {
                'time': end_time - start_time,
                'result_size': len(result)
            }
        
        return benchmark_results

def demo_performance_optimization():
    """演示性能优化"""
    
    print("\n" + "="*60)
    print("6. 性能优化演示")
    print("="*60)
    
    # 1. 优化策略分析
    strategies = PerformanceOptimization.analyze_query_performance()
    
    print("\n优化策略概览:")
    for level, strategies_dict in strategies.items():
        print(f"\n{level.upper()}:")
        for strategy, description in strategies_dict.items():
            print(f"  • {strategy}: {description}")
    
    # 2. 性能基准测试
    print("\n性能基准测试:")
    print("正在运行窗口函数性能测试...")
    
    try:
        benchmark_results = PerformanceOptimization.benchmark_window_functions()
        
        print("\n基准测试结果:")
        for func_name, result in benchmark_results.items():
            print(f"  {func_name}: {result['time']:.4f}秒 ({result['result_size']}行)")
    except Exception as e:
        print(f"基准测试跳过: {e}")
    
    # 3. 优化建议
    print("\n性能优化建议:")
    recommendations = [
        "1. 对常用的GROUP BY列创建复合索引",
        "2. 使用列式存储优化聚合查询性能",
        "3. 实现查询结果缓存机制",
        "4. 对大数据集使用采样和近似算法",
        "5. 优化前端分页和懒加载策略",
        "6. 使用异步处理复杂的分析查询"
    ]
    
    for recommendation in recommendations:
        print(f"  {recommendation}")

# ================================
# 7. 主函数执行
# ================================

def main():
    """主函数 - 执行所有演示"""
    
    print("Chart SQL生成逻辑全面演示")
    print("包含基础生成、聚合扩展、窗口函数、高级扩展和性能优化")
    
    # 执行所有演示
    demo_basic_sql_generation()
    demo_extended_aggregations()
    demo_window_functions()
    demo_advanced_extensions()
    demo_performance_optimization()
    
    print("\n" + "="*80)
    print("Day 17演示完成！")
    print("="*80)
    print("\n主要演示内容:")
    print("1. ✅ 基础SQL生成逻辑")
    print("2. ✅ 扩展聚合函数系统")
    print("3. ✅ 窗口函数实现")
    print("4. ✅ 高级扩展功能")
    print("5. ✅ 性能优化策略")
    
    print("\n学习成果:")
    print("• 深入理解SQL生成的完整流程")
    print("• 掌握聚合函数的扩展方法")
    print("• 学会实现复杂的窗口函数")
    print("• 具备企业级扩展开发能力")
    print("• 了解性能优化的最佳实践")

if __name__ == "__main__":
    main() 