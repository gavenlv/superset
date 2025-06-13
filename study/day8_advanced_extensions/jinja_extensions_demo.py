#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 8 Jinja模板扩展演示：自定义函数和宏定义
=========================================

本脚本演示如何扩展 Superset 的Jinja模板系统：
- 自定义模板函数
- 安全沙箱机制
- 宏定义扩展
- 上下文管理
"""

import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from abc import ABC, abstractmethod
from jinja2 import Environment, Template, DebugUndefined
from jinja2.sandbox import SandboxedEnvironment
from functools import partial, lru_cache


# 允许的返回类型
ALLOWED_TYPES = {
    "bool", "dict", "float", "int", "list", "NoneType", "str", "tuple"
}

COLLECTION_TYPES = {"dict", "list", "tuple"}


class SupersetTemplateException(Exception):
    """Superset模板异常"""
    pass


def safe_proxy(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """安全代理函数，确保返回值类型安全"""
    return_value = func(*args, **kwargs)
    value_type = type(return_value).__name__
    
    if value_type not in ALLOWED_TYPES:
        raise SupersetTemplateException(
            f"Unsafe return type for function {func.__name__}: {value_type}"
        )
    
    if value_type in COLLECTION_TYPES:
        try:
            # 确保集合类型可以JSON序列化
            return_value = json.loads(json.dumps(return_value))
        except TypeError as ex:
            raise SupersetTemplateException(
                f"Unsupported return value for method {func.__name__}"
            ) from ex
    
    return return_value


class ExtraCache:
    """扩展缓存类，管理模板上下文中的缓存键"""
    
    def __init__(
        self,
        extra_cache_keys: Optional[List[Any]] = None,
        applied_filters: Optional[List[str]] = None,
        removed_filters: Optional[List[str]] = None,
    ):
        self.extra_cache_keys = extra_cache_keys or []
        self.applied_filters = applied_filters or []
        self.removed_filters = removed_filters or []
        self._cache_keys: List[str] = []
    
    def cache_key_wrapper(self, key: Any) -> Any:
        """缓存键包装器"""
        self._cache_keys.append(str(key))
        return key
    
    def current_user_id(self, add_to_cache_keys: bool = True) -> int:
        """获取当前用户ID"""
        user_id = 1  # 模拟用户ID
        if add_to_cache_keys:
            self.cache_key_wrapper(f"user_id:{user_id}")
        return user_id
    
    def current_username(self, add_to_cache_keys: bool = True) -> str:
        """获取当前用户名"""
        username = "demo_user"  # 模拟用户名
        if add_to_cache_keys:
            self.cache_key_wrapper(f"username:{username}")
        return username
    
    def current_user_email(self, add_to_cache_keys: bool = True) -> str:
        """获取当前用户邮箱"""
        email = "demo@example.com"  # 模拟邮箱
        if add_to_cache_keys:
            self.cache_key_wrapper(f"email:{email}")
        return email
    
    def url_param(self, param: str, default: Any = None) -> Any:
        """获取URL参数"""
        # 模拟URL参数
        url_params = {
            "country": "US",
            "region": "west",
            "year": "2023",
            "quarter": "Q4",
        }
        value = url_params.get(param, default)
        self.cache_key_wrapper(f"url_param:{param}:{value}")
        return value
    
    def filter_values(self, column: str, default: Optional[List] = None) -> List:
        """获取过滤器值"""
        # 模拟过滤器值
        filter_values = {
            "country": ["US", "CA", "UK"],
            "category": ["Electronics", "Clothing", "Books"],
            "status": ["Active", "Pending"],
        }
        values = filter_values.get(column, default or [])
        self.cache_key_wrapper(f"filter_values:{column}:{','.join(map(str, values))}")
        return values
    
    def get_filters(self) -> List[Dict[str, Any]]:
        """获取所有过滤器"""
        filters = [
            {"col": "country", "op": "IN", "val": ["US", "CA"]},
            {"col": "date", "op": ">=", "val": "2023-01-01"},
            {"col": "amount", "op": ">", "val": 1000},
        ]
        return filters


class BaseTemplateProcessor(ABC):
    """模板处理器基类"""
    
    engine: Optional[str] = None
    
    def __init__(self, **kwargs: Any):
        self._context: Dict[str, Any] = {}
        self.env: Environment = SandboxedEnvironment(undefined=DebugUndefined)
        self.set_context(**kwargs)
        
        # 添加自定义过滤器
        self.env.filters.update({
            "where_in": self._where_in_filter,
            "format_number": self._format_number_filter,
            "format_date": self._format_date_filter,
            "truncate": self._truncate_filter,
        })
    
    def set_context(self, **kwargs: Any) -> None:
        """设置模板上下文"""
        self._context.update(kwargs)
        self._context.update(self._get_context_addons())
    
    def process_template(self, sql: str, **kwargs: Any) -> str:
        """处理SQL模板"""
        template = self.env.from_string(sql)
        kwargs.update(self._context)
        
        # 验证上下文安全性
        context = self._validate_template_context(kwargs)
        return template.render(context)
    
    def _get_context_addons(self) -> Dict[str, Any]:
        """获取上下文附加项"""
        return {
            "datetime": datetime,
            "timedelta": timedelta,
            "time": time,
            "json": json,
            "re": re,
        }
    
    def _validate_template_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """验证模板上下文安全性"""
        # 在实际实现中，这里会进行更严格的安全检查
        return context
    
    def _where_in_filter(self, values: List[Any]) -> str:
        """WHERE IN过滤器"""
        if not values:
            return "1=0"  # 空值返回false条件
        
        # 处理字符串值
        formatted_values = []
        for value in values:
            if isinstance(value, str):
                formatted_values.append(f"'{value}'")
            else:
                formatted_values.append(str(value))
        
        return f"({', '.join(formatted_values)})"
    
    def _format_number_filter(self, value: Union[int, float], format_spec: str = ".2f") -> str:
        """数字格式化过滤器"""
        try:
            return format(float(value), format_spec)
        except (ValueError, TypeError):
            return str(value)
    
    def _format_date_filter(self, value: datetime, format_spec: str = "%Y-%m-%d") -> str:
        """日期格式化过滤器"""
        if isinstance(value, datetime):
            return value.strftime(format_spec)
        return str(value)
    
    def _truncate_filter(self, value: str, length: int = 50, suffix: str = "...") -> str:
        """字符串截断过滤器"""
        if len(value) <= length:
            return value
        return value[:length - len(suffix)] + suffix


class JinjaTemplateProcessor(BaseTemplateProcessor):
    """Jinja模板处理器"""
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        
        # 创建扩展缓存
        self.extra_cache = ExtraCache()
        
        # 添加Superset特定的宏
        self._add_superset_macros()
    
    def _add_superset_macros(self) -> None:
        """添加Superset特定的宏"""
        self._context.update({
            # 用户信息宏
            "current_user_id": partial(safe_proxy, self.extra_cache.current_user_id),
            "current_username": partial(safe_proxy, self.extra_cache.current_username),
            "current_user_email": partial(safe_proxy, self.extra_cache.current_user_email),
            
            # URL参数宏
            "url_param": partial(safe_proxy, self.extra_cache.url_param),
            
            # 过滤器宏
            "filter_values": partial(safe_proxy, self.extra_cache.filter_values),
            "get_filters": partial(safe_proxy, self.extra_cache.get_filters),
            
            # 缓存宏
            "cache_key_wrapper": partial(safe_proxy, self.extra_cache.cache_key_wrapper),
            
            # 数据集和指标宏
            "dataset": partial(safe_proxy, self._dataset_macro),
            "metric": partial(safe_proxy, self._metric_macro),
            
            # 自定义业务宏
            "business_days": partial(safe_proxy, self._business_days_macro),
            "format_currency": partial(safe_proxy, self._format_currency_macro),
            "get_fiscal_year": partial(safe_proxy, self._get_fiscal_year_macro),
            "calculate_growth": partial(safe_proxy, self._calculate_growth_macro),
        })
    
    def _dataset_macro(
        self,
        dataset_id: int,
        include_metrics: bool = False,
        columns: Optional[List[str]] = None,
        from_dttm: Optional[datetime] = None,
        to_dttm: Optional[datetime] = None,
    ) -> str:
        """数据集宏"""
        # 模拟数据集查询生成
        columns = columns or ["id", "name", "value", "created_at"]
        
        select_clause = ", ".join(columns)
        if include_metrics:
            select_clause += ", COUNT(*) as record_count, SUM(value) as total_value"
        
        where_clause = "1=1"
        if from_dttm:
            where_clause += f" AND created_at >= '{from_dttm.isoformat()}'"
        if to_dttm:
            where_clause += f" AND created_at <= '{to_dttm.isoformat()}'"
        
        sql = f"""
        (
            SELECT {select_clause}
            FROM dataset_{dataset_id}
            WHERE {where_clause}
        ) AS dataset_{dataset_id}
        """
        
        return sql.strip()
    
    def _metric_macro(self, metric_key: str, dataset_id: Optional[int] = None) -> str:
        """指标宏"""
        # 模拟指标表达式
        metric_expressions = {
            "total_sales": "SUM(sales_amount)",
            "avg_order_value": "AVG(order_value)",
            "customer_count": "COUNT(DISTINCT customer_id)",
            "conversion_rate": "COUNT(DISTINCT orders.customer_id) / COUNT(DISTINCT visits.customer_id) * 100",
            "revenue_growth": "(SUM(current_revenue) - SUM(previous_revenue)) / SUM(previous_revenue) * 100",
        }
        
        expression = metric_expressions.get(metric_key)
        if not expression:
            raise SupersetTemplateException(f"Metric '{metric_key}' not found")
        
        return expression
    
    def _business_days_macro(self, start_date: str, end_date: str) -> int:
        """计算工作日数量"""
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            # 简化的工作日计算
            total_days = (end - start).days
            weeks = total_days // 7
            remaining_days = total_days % 7
            
            # 假设每周5个工作日
            business_days = weeks * 5
            
            # 处理剩余天数
            for i in range(remaining_days):
                day = (start + timedelta(days=weeks * 7 + i)).weekday()
                if day < 5:  # 周一到周五
                    business_days += 1
            
            return business_days
        except Exception:
            return 0
    
    def _format_currency_macro(self, amount: float, currency: str = "USD") -> str:
        """格式化货币"""
        currency_symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CNY": "¥",
        }
        
        symbol = currency_symbols.get(currency, currency)
        
        if amount >= 1_000_000:
            return f"{symbol}{amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"{symbol}{amount/1_000:.1f}K"
        else:
            return f"{symbol}{amount:.2f}"
    
    def _get_fiscal_year_macro(self, date_str: str, fiscal_start_month: int = 4) -> int:
        """获取财政年度"""
        try:
            date = datetime.fromisoformat(date_str)
            if date.month >= fiscal_start_month:
                return date.year
            else:
                return date.year - 1
        except Exception:
            return datetime.now().year
    
    def _calculate_growth_macro(self, current: float, previous: float) -> float:
        """计算增长率"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100


class CustomTemplateProcessor(BaseTemplateProcessor):
    """自定义模板处理器（支持$宏语法）"""
    
    engine = "custom"
    
    def process_template(self, sql: str, **kwargs: Any) -> str:
        """处理自定义模板（$宏语法）"""
        # 添加自定义宏函数
        macros = {
            "DATE": self._date_macro,
            "USER": self._user_macro,
            "FILTER": self._filter_macro,
            "PARAM": self._param_macro,
        }
        
        # 更新宏定义
        macros.update(self._context)
        macros.update(kwargs)
        
        def replacer(match):
            """替换$宏"""
            macro_name, args_str = match.groups()
            args = [a.strip() for a in args_str.split(",") if a.strip()]
            
            func = macros.get(macro_name[1:])  # 移除$前缀
            if func:
                return str(func(*args))
            else:
                return match.group(0)  # 保持原样
        
        # 匹配$宏模式
        macro_names = ["$" + name for name in macros.keys()]
        pattern = r"(%s)\s*\(([^()]*)\)" % "|".join(re.escape(name) for name in macro_names)
        
        return re.sub(pattern, replacer, sql)
    
    def _date_macro(self, *args) -> str:
        """日期宏"""
        if not args:
            return datetime.now().strftime("%Y-%m-%d")
        elif len(args) == 1:
            try:
                days_offset = int(args[0])
                date = datetime.now() + timedelta(days=days_offset)
                return date.strftime("%Y-%m-%d")
            except ValueError:
                return args[0]
        else:
            return datetime.now().strftime("%Y-%m-%d")
    
    def _user_macro(self, *args) -> str:
        """用户宏"""
        if not args:
            return "demo_user"
        
        attr = args[0].lower()
        user_info = {
            "id": "1",
            "name": "demo_user",
            "email": "demo@example.com",
            "role": "admin",
        }
        
        return user_info.get(attr, "unknown")
    
    def _filter_macro(self, column: str, *args) -> str:
        """过滤器宏"""
        # 模拟过滤器值
        filter_values = {
            "country": ["US", "CA"],
            "status": ["active"],
            "category": ["electronics", "books"],
        }
        
        values = filter_values.get(column, [])
        if values:
            formatted_values = [f"'{v}'" for v in values]
            return f"{column} IN ({', '.join(formatted_values)})"
        else:
            return "1=1"
    
    def _param_macro(self, param_name: str, default: str = "") -> str:
        """参数宏"""
        # 模拟参数值
        params = {
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "limit": "100",
            "offset": "0",
        }
        
        return params.get(param_name, default)


def demo_jinja_template_processor():
    """演示Jinja模板处理器"""
    print("🎨 Jinja模板处理器演示")
    print("=" * 60)
    
    processor = JinjaTemplateProcessor()
    
    # 演示基础宏
    print("1. 基础宏演示:")
    basic_template = """
    SELECT 
        user_id,
        username,
        created_at
    FROM users 
    WHERE user_id = {{ current_user_id() }}
      AND username = '{{ current_username() }}'
      AND email = '{{ current_user_email() }}'
    """
    
    result = processor.process_template(basic_template)
    print(f"基础宏结果:\n{result}")
    
    # 演示URL参数宏
    print("\n2. URL参数宏演示:")
    url_template = """
    SELECT * FROM sales 
    WHERE country = '{{ url_param('country', 'US') }}'
      AND region = '{{ url_param('region', 'all') }}'
      AND year = {{ url_param('year', 2023) }}
    """
    
    result = processor.process_template(url_template)
    print(f"URL参数宏结果:\n{result}")
    
    # 演示过滤器宏
    print("\n3. 过滤器宏演示:")
    filter_template = """
    SELECT * FROM products 
    WHERE category {{ filter_values('category') | where_in }}
      AND status {{ filter_values('status') | where_in }}
    """
    
    result = processor.process_template(filter_template)
    print(f"过滤器宏结果:\n{result}")
    
    # 演示数据集宏
    print("\n4. 数据集宏演示:")
    dataset_template = """
    SELECT * FROM {{ dataset(123, include_metrics=True, columns=['id', 'name', 'value']) }}
    WHERE created_at >= '2023-01-01'
    """
    
    result = processor.process_template(dataset_template)
    print(f"数据集宏结果:\n{result}")
    
    # 演示指标宏
    print("\n5. 指标宏演示:")
    metric_template = """
    SELECT 
        date_trunc('month', order_date) as month,
        {{ metric('total_sales') }} as total_sales,
        {{ metric('avg_order_value') }} as avg_order_value,
        {{ metric('customer_count') }} as customer_count
    FROM orders 
    GROUP BY month
    """
    
    result = processor.process_template(metric_template)
    print(f"指标宏结果:\n{result}")
    
    # 演示自定义业务宏
    print("\n6. 自定义业务宏演示:")
    business_template = """
    SELECT 
        '{{ format_currency(1234567.89, 'USD') }}' as formatted_amount,
        {{ business_days('2023-01-01', '2023-12-31') }} as business_days,
        {{ get_fiscal_year('2023-06-15', 4) }} as fiscal_year,
        {{ calculate_growth(1200, 1000) }} as growth_rate
    """
    
    result = processor.process_template(business_template)
    print(f"业务宏结果:\n{result}")
    
    return processor


def demo_custom_template_processor():
    """演示自定义模板处理器"""
    print("\n🔧 自定义模板处理器演示")
    print("=" * 60)
    
    processor = CustomTemplateProcessor()
    
    # 演示$宏语法
    print("1. $宏语法演示:")
    custom_template = """
    SELECT * FROM orders 
    WHERE order_date >= '$DATE(-30)'
      AND order_date <= '$DATE(0)'
      AND user_id = $USER(id)
      AND $FILTER(country)
      AND limit = $PARAM(limit, 100)
    """
    
    result = processor.process_template(custom_template)
    print(f"$宏语法结果:\n{result}")
    
    # 演示复杂$宏
    print("\n2. 复杂$宏演示:")
    complex_template = """
    SELECT 
        customer_id,
        order_date,
        amount
    FROM orders 
    WHERE customer_id = $USER(id)
      AND order_date BETWEEN '$DATE(-7)' AND '$DATE(0)'
      AND $FILTER(status)
    ORDER BY order_date DESC
    LIMIT $PARAM(limit, 50)
    """
    
    result = processor.process_template(complex_template)
    print(f"复杂$宏结果:\n{result}")
    
    return processor


def demo_template_filters():
    """演示模板过滤器"""
    print("\n🎛️ 模板过滤器演示")
    print("=" * 60)
    
    processor = JinjaTemplateProcessor()
    
    # 演示数字格式化过滤器
    print("1. 数字格式化过滤器:")
    number_template = """
    SELECT 
        '{{ 1234567.89 | format_number }}' as default_format,
        '{{ 1234567.89 | format_number('.0f') }}' as integer_format,
        '{{ 1234567.89 | format_number('.4f') }}' as precision_format
    """
    
    result = processor.process_template(number_template)
    print(f"数字格式化结果:\n{result}")
    
    # 演示日期格式化过滤器
    print("\n2. 日期格式化过滤器:")
    date_template = """
    SELECT 
        '{{ datetime(2023, 12, 25) | format_date }}' as default_date,
        '{{ datetime(2023, 12, 25) | format_date('%Y-%m-%d %H:%M:%S') }}' as datetime_format,
        '{{ datetime(2023, 12, 25) | format_date('%B %d, %Y') }}' as readable_format
    """
    
    result = processor.process_template(date_template)
    print(f"日期格式化结果:\n{result}")
    
    # 演示字符串截断过滤器
    print("\n3. 字符串截断过滤器:")
    truncate_template = """
    SELECT 
        '{{ "This is a very long string that needs to be truncated" | truncate }}' as default_truncate,
        '{{ "Short text" | truncate(20) }}' as short_text,
        '{{ "Another long string for demonstration" | truncate(15, '...') }}' as custom_suffix
    """
    
    result = processor.process_template(truncate_template)
    print(f"字符串截断结果:\n{result}")
    
    # 演示WHERE IN过滤器
    print("\n4. WHERE IN过滤器:")
    where_in_template = """
    SELECT * FROM products 
    WHERE category {{ ['Electronics', 'Books', 'Clothing'] | where_in }}
      AND status {{ ['Active', 'Featured'] | where_in }}
      AND price_range {{ [] | where_in }}
    """
    
    result = processor.process_template(where_in_template)
    print(f"WHERE IN过滤器结果:\n{result}")


def demo_template_security():
    """演示模板安全机制"""
    print("\n🔒 模板安全机制演示")
    print("=" * 60)
    
    processor = JinjaTemplateProcessor()
    
    # 演示安全的函数调用
    print("1. 安全函数调用:")
    try:
        safe_template = """
        SELECT 
            '{{ current_username() }}' as username,
            {{ current_user_id() }} as user_id,
            '{{ url_param('country') }}' as country
        """
        
        result = processor.process_template(safe_template)
        print(f"安全调用成功:\n{result}")
    except Exception as e:
        print(f"安全调用失败: {e}")
    
    # 演示类型检查
    print("\n2. 返回类型检查:")
    def unsafe_function():
        """返回不安全类型的函数"""
        class UnsafeType:
            pass
        return UnsafeType()
    
    try:
        # 这会触发安全检查
        safe_proxy(unsafe_function)
    except SupersetTemplateException as e:
        print(f"类型检查成功阻止: {e}")
    
    # 演示JSON序列化检查
    print("\n3. JSON序列化检查:")
    def complex_function():
        """返回复杂对象的函数"""
        return {"data": [1, 2, 3], "nested": {"key": "value"}}
    
    try:
        result = safe_proxy(complex_function)
        print(f"JSON序列化成功: {result}")
    except SupersetTemplateException as e:
        print(f"JSON序列化失败: {e}")


def demo_context_management():
    """演示上下文管理"""
    print("\n📋 上下文管理演示")
    print("=" * 60)
    
    # 创建带有自定义上下文的处理器
    custom_context = {
        "company_name": "Acme Corp",
        "fiscal_year_start": 4,  # 4月开始
        "default_currency": "USD",
        "business_hours": {"start": 9, "end": 17},
    }
    
    processor = JinjaTemplateProcessor(**custom_context)
    
    # 演示上下文使用
    print("1. 自定义上下文使用:")
    context_template = """
    SELECT 
        '{{ company_name }}' as company,
        {{ fiscal_year_start }} as fy_start_month,
        '{{ default_currency }}' as currency,
        {{ business_hours.start }} as business_start,
        {{ business_hours.end }} as business_end
    """
    
    result = processor.process_template(context_template)
    print(f"上下文使用结果:\n{result}")
    
    # 演示缓存键管理
    print("\n2. 缓存键管理:")
    cache_template = """
    SELECT * FROM sales 
    WHERE user_id = {{ current_user_id() }}
      AND country = '{{ url_param('country') }}'
      AND {{ cache_key_wrapper('custom_key_123') }}
    """
    
    result = processor.process_template(cache_template)
    cache_keys = processor.extra_cache._cache_keys
    print(f"缓存键结果:\n{result}")
    print(f"生成的缓存键: {cache_keys}")


def main():
    """主演示函数"""
    print("🎨 Day 8 Jinja模板扩展机制演示")
    print("=" * 60)
    
    try:
        # 演示Jinja模板处理器
        jinja_processor = demo_jinja_template_processor()
        
        # 演示自定义模板处理器
        custom_processor = demo_custom_template_processor()
        
        # 演示模板过滤器
        demo_template_filters()
        
        # 演示模板安全机制
        demo_template_security()
        
        # 演示上下文管理
        demo_context_management()
        
        print("\n" + "="*60)
        print("✅ Jinja模板扩展演示完成！")
        print("\n📚 模板扩展要点总结:")
        print("- 安全沙箱：SandboxedEnvironment确保模板安全")
        print("- 自定义宏：扩展模板功能的核心机制")
        print("- 过滤器系统：数据格式化和转换")
        print("- 上下文管理：灵活的变量和函数注入")
        print("- 类型检查：确保返回值类型安全")
        print("- 缓存机制：智能的缓存键管理")
        print("- 多语法支持：Jinja2和自定义$宏语法")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 