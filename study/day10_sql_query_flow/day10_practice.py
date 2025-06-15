#!/usr/bin/env python3
"""
Day 10: Superset SQL查询流程实践练习

本文件包含理解和测试SQL查询流程的实践代码
"""

import json
import logging
import time
from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLQueryFlowTracer:
    """
    SQL查询流程追踪器
    用于理解和调试SQL查询的完整执行路径
    """
    
    def __init__(self):
        self.trace_logs = []
        self.current_context = {}
    
    def log_step(self, step_name: str, class_name: str, method_name: str, 
                 data: Optional[Dict[str, Any]] = None):
        """记录执行步骤"""
        timestamp = time.time()
        log_entry = {
            'timestamp': timestamp,
            'step': step_name,
            'class': class_name,
            'method': method_name,
            'data': data or {},
            'context': self.current_context.copy()
        }
        self.trace_logs.append(log_entry)
        logger.info(f"[{step_name}] {class_name}.{method_name}()")
    
    def set_context(self, **kwargs):
        """设置当前上下文"""
        self.current_context.update(kwargs)
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """获取追踪摘要"""
        return {
            'total_steps': len(self.trace_logs),
            'execution_time': self.trace_logs[-1]['timestamp'] - self.trace_logs[0]['timestamp'] if self.trace_logs else 0,
            'steps': self.trace_logs
        }

class MockChartQueryFlow:
    """模拟图表查询流程"""
    
    def __init__(self, tracer: SQLQueryFlowTracer):
        self.tracer = tracer
    
    def simulate_chart_data_request(self, form_data: Dict[str, Any]):
        """模拟图表数据请求"""
        self.tracer.set_context(query_type='chart', datasource_id=form_data.get('datasource'))
        
        # 1. 前端构建查询上下文
        self.tracer.log_step(
            "前端构建查询", "ChartComponent", "buildQuery",
            {"form_data_keys": list(form_data.keys())}
        )
        
        # 2. API接收请求
        self.tracer.log_step(
            "API接收请求", "ChartDataRestApi", "data",
            {"endpoint": "/api/v1/chart/data", "method": "POST"}
        )
        
        # 3. 创建查询上下文
        query_context = self._create_query_context(form_data)
        
        # 4. 执行查询
        result = self._execute_query(query_context)
        
        return result
    
    def _create_query_context(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建查询上下文"""
        self.tracer.log_step(
            "创建查询上下文", "ChartDataRestApi", "_create_query_context_from_form",
            {"form_data_size": len(json.dumps(form_data))}
        )
        
        self.tracer.log_step(
            "验证查询上下文", "ChartDataQueryContextSchema", "load",
            {"datasource": form_data.get('datasource')}
        )
        
        return {
            'datasource': form_data.get('datasource'),
            'queries': [form_data],
            'force': False,
            'result_type': 'full'
        }
    
    def _execute_query(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行查询"""
        self.tracer.log_step("获取查询结果", "QueryContext", "get_query_result")
        
        self.tracer.log_step(
            "数据集查询", "SqlaTable", "query",
            {"datasource_id": query_context['datasource']}
        )
        
        self.tracer.log_step("生成SQL", "SqlaTable", "get_query_str_extended")
        
        # 模拟SQL执行
        sql = "SELECT * FROM table WHERE conditions"
        self.tracer.log_step(
            "执行SQL", "Database", "get_df",
            {"sql_length": len(sql)}
        )
        
        self.tracer.log_step("数据库执行", "BaseEngineSpec", "execute_with_cursor")
        self.tracer.log_step("获取数据", "BaseEngineSpec", "fetch_data")
        
        self.tracer.log_step(
            "构建结果集", "SupersetResultSet", "__init__",
            {"rows": 100, "columns": 5}
        )
        
        return {
            'status': 'success',
            'data': [[1, 2, 3], [4, 5, 6]],
            'columns': ['col1', 'col2', 'col3'],
            'query': sql
        }

def demonstrate_query_flows():
    """演示查询流程"""
    print("=" * 80)
    print("Superset SQL查询流程演示")
    print("=" * 80)
    
    tracer = SQLQueryFlowTracer()
    
    # 1. 演示图表查询流程
    print("\n1. 图表查询流程:")
    print("-" * 40)
    
    chart_flow = MockChartQueryFlow(tracer)
    form_data = {
        'datasource': '1__table',
        'viz_type': 'table',
        'metrics': ['count'],
        'groupby': ['category'],
        'row_limit': 1000
    }
    
    chart_result = chart_flow.simulate_chart_data_request(form_data)
    print(f"图表查询结果: {chart_result['status']}")
    
    # 4. 显示追踪摘要
    print("\n2. 查询追踪摘要:")
    print("-" * 40)
    
    summary = tracer.get_trace_summary()
    print(f"总执行步骤: {summary['total_steps']}")
    print(f"执行时间: {summary['execution_time']:.3f}秒")
    
    print("\n执行步骤详情:")
    for i, step in enumerate(summary['steps'], 1):
        print(f"{i:2d}. {step['step']} -> {step['class']}.{step['method']}()")

if __name__ == '__main__':
    # 运行演示
    demonstrate_query_flows()
    
    print(f"\n{'='*80}")
    print("练习完成！")
    print("建议:")
    print("1. 详细阅读每个类和方法的源码")
    print("2. 在实际环境中设置断点调试")
    print("3. 查看SQL执行日志了解实际流程")
    print("4. 测试不同类型查询的性能差异")
    print("=" * 80) 