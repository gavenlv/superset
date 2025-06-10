#!/usr/bin/env python3
"""
Superset Python代码调试示例

演示各种调试技巧和工具的使用
"""

import logging
import pdb
from typing import Any, Dict

# 配置日志调试
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_example_1_basic_pdb():
    """示例1: 使用基础pdb调试"""
    print("🔍 示例1: 基础pdb调试")
    
    data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
    
    # 设置断点
    pdb.set_trace()  # 程序会在这里暂停
    
    # 你可以在pdb中执行:
    # p data  # 打印data变量
    # l      # 显示当前代码
    # n      # 下一行
    # c      # 继续执行
    
    for user in data["users"]:
        print(f"Processing user: {user['name']}")
    
    return data

def debug_example_2_ipdb():
    """示例2: 使用ipdb (增强版pdb)"""
    print("🔍 示例2: 使用ipdb调试")
    
    try:
        import ipdb
        
        dashboard_data = {
            "id": 1,
            "title": "Sales Dashboard",
            "charts": []
        }
        
        # ipdb断点 (彩色输出，自动补全)
        ipdb.set_trace()
        
        # ipdb命令:
        # pp dashboard_data  # 漂亮打印
        # ll                 # 显示长列表
        # !import json; print(json.dumps(dashboard_data, indent=2))
        
        return dashboard_data
        
    except ImportError:
        print("请安装ipdb: pip install ipdb")

def debug_example_3_conditional_breakpoint():
    """示例3: 条件断点"""
    print("🔍 示例3: 条件断点")
    
    charts = [
        {"id": 1, "type": "bar", "data_count": 100},
        {"id": 2, "type": "line", "data_count": 5000},  # 这个会触发断点
        {"id": 3, "type": "pie", "data_count": 200},
    ]
    
    for chart in charts:
        # 只在数据量大于1000时断点
        if chart["data_count"] > 1000:
            import pdb; pdb.set_trace()
        
        print(f"Chart {chart['id']}: {chart['type']} with {chart['data_count']} records")

def debug_example_4_logging_debug():
    """示例4: 使用日志调试"""
    print("🔍 示例4: 日志调试")
    
    logger.debug("开始处理仪表板数据")
    
    try:
        # 模拟Superset中的数据处理
        dashboard_config = {
            "position_json": '{"CHART_1": {"children": [], "id": "CHART_1"}}',
            "json_metadata": '{"filter_scopes": {}}'
        }
        
        logger.info(f"仪表板配置: {dashboard_config}")
        
        # 模拟解析JSON
        import json
        position_data = json.loads(dashboard_config["position_json"])
        metadata = json.loads(dashboard_config["json_metadata"])
        
        logger.debug(f"解析后的位置数据: {position_data}")
        logger.debug(f"解析后的元数据: {metadata}")
        
        return {"position": position_data, "metadata": metadata}
        
    except Exception as e:
        logger.error(f"处理仪表板数据时出错: {e}", exc_info=True)
        raise

def debug_example_5_superset_specific():
    """示例5: Superset特定的调试技巧"""
    print("🔍 示例5: Superset特定调试")
    
    # 模拟Superset中的查询构建
    query_context = {
        "datasource": {"id": 1, "type": "table"},
        "queries": [
            {
                "metrics": ["count"],
                "groupby": ["category"],
                "filters": []
            }
        ]
    }
    
    logger.debug("构建SQL查询")
    
    # 在实际Superset代码中，你可以这样调试:
    # 1. 在viz.py中添加断点查看可视化数据转换
    # 2. 在models/core.py中调试数据库连接
    # 3. 在views/api.py中调试API请求处理
    
    import pdb; pdb.set_trace()
    
    # 模拟SQL生成过程
    sql_parts = []
    sql_parts.append("SELECT category, COUNT(*) as count")
    sql_parts.append("FROM sales_data")
    sql_parts.append("GROUP BY category")
    
    generated_sql = " ".join(sql_parts)
    logger.info(f"生成的SQL: {generated_sql}")
    
    return generated_sql

def debug_example_6_exception_debugging():
    """示例6: 异常调试"""
    print("🔍 示例6: 异常调试和post-mortem")
    
    try:
        # 模拟一个会出错的Superset操作
        chart_data = [
            {"x": "2023-01", "y": 100},
            {"x": "2023-02", "y": None},  # 这里会引起问题
            {"x": "2023-03", "y": 150},
        ]
        
        total = sum(point["y"] for point in chart_data)  # TypeError!
        return total
        
    except Exception as e:
        print(f"捕获异常: {e}")
        
        # 自动进入调试模式查看异常现场
        import pdb; pdb.post_mortem()
        
        # 在post_mortem中你可以:
        # u     # 上一个堆栈帧
        # d     # 下一个堆栈帧  
        # pp locals()  # 查看当前局部变量
        # pp chart_data  # 检查出错的数据

# 实用的调试装饰器
def debug_trace(func):
    """调试装饰器：自动在函数入口和出口添加日志"""
    def wrapper(*args, **kwargs):
        logger.debug(f"进入函数 {func.__name__}")
        logger.debug(f"参数: args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 返回: {result}")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 出错: {e}")
            raise
    
    return wrapper

@debug_trace
def sample_superset_function(chart_id: int, filters: Dict[str, Any]) -> Dict[str, Any]:
    """示例Superset函数，使用调试装饰器"""
    # 模拟图表数据获取
    return {
        "chart_id": chart_id,
        "data": [{"x": 1, "y": 2}],
        "applied_filters": filters
    }

if __name__ == "__main__":
    print("🎓 Superset Python调试示例")
    print("=" * 50)
    
    print("\n选择要运行的调试示例:")
    print("1. 基础pdb调试")
    print("2. ipdb调试 (需要安装ipdb)")
    print("3. 条件断点")
    print("4. 日志调试")
    print("5. Superset特定调试")
    print("6. 异常调试")
    print("7. 装饰器调试")
    
    choice = input("\n请输入选择 (1-7): ").strip()
    
    examples = {
        "1": debug_example_1_basic_pdb,
        "2": debug_example_2_ipdb,
        "3": debug_example_3_conditional_breakpoint,
        "4": debug_example_4_logging_debug,
        "5": debug_example_5_superset_specific,
        "6": debug_example_6_exception_debugging,
        "7": lambda: sample_superset_function(123, {"country": "US"})
    }
    
    if choice in examples:
        print(f"\n🚀 运行示例 {choice}:")
        examples[choice]()
    else:
        print("❌ 无效选择")
        
    print("\n💡 调试技巧总结:")
    print("- 使用 pdb.set_trace() 设置断点")
    print("- 使用 ipdb 获得更好的调试体验")
    print("- 使用条件断点避免频繁中断")
    print("- 使用日志记录程序执行流程")
    print("- 使用 post_mortem() 调试异常") 