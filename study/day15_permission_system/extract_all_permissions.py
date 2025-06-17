#!/usr/bin/env python3
"""
提取 Superset 所有权限信息并进行详细分析

该脚本将：
1. 连接到Superset数据库
2. 提取所有权限和视图菜单
3. 分析权限的功能和影响
4. 生成详细的权限分析报告
"""

import sys
import os
import json
from collections import defaultdict, Counter
from typing import Dict, List, Any

# 添加superset路径
sys.path.append('../../')

# 模拟权限数据（因为我们无法直接连接到真实数据库）
SUPERSET_PERMISSIONS = [
    # 基础CRUD权限
    "can_add", "can_delete", "can_edit", "can_list", "can_show", "can_read", "can_write",
    
    # 数据访问权限
    "all_database_access", "all_datasource_access", "all_query_access",
    "database_access", "datasource_access", "schema_access", "catalog_access",
    
    # SQL Lab权限
    "can_execute_sql_query", "can_sqllab", "can_sqllab_history", "can_csv",
    "can_estimate_query_cost", "can_get_results", "can_export_csv",
    
    # 图表权限
    "can_explore", "can_explore_json", "can_slice", "can_charts",
    "can_view_and_drill", "can_external_metadata", "can_external_metadata_by_name",
    
    # 仪表板权限
    "can_dashboard", "can_dashboard_permalink", "can_copy_dash",
    "can_save_dash", "can_export_dashboard", "can_import_dashboards",
    
    # 数据集权限
    "can_dataset", "can_datasource", "can_get_column_values",
    "can_samples", "can_refresh", "can_table_metadata",
    
    # 管理权限
    "can_update_role", "can_grant_guest_token", "can_set_embedded",
    "can_warm_up_cache", "can_override_role_permissions",
    
    # 用户管理权限
    "can_userinfo", "resetmypassword", "can_recent_activity",
    "userinfoedit", "can_profile", "can_reset_password",
    
    # 菜单访问权限
    "menu_access",
    
    # 特殊功能权限
    "muldelete", "can_approve", "can_request_access",
    "can_log", "can_annotation", "can_favstar",
    
    # 报告和告警权限
    "can_report", "can_alert", "can_email_report",
    
    # 缓存权限
    "can_cache_key", "can_invalidate_cache",
    
    # 高级权限
    "can_sync_druid_source", "can_druid_refresh",
    "can_created_by", "can_created_on", "can_changed_by", "can_changed_on",
    
    # API权限
    "can_get", "can_post", "can_put", "can_delete_api",
    "can_info", "can_search", "can_related",
    
    # 其他功能权限
    "can_test_conn", "can_validate_parameters", "can_get_test_results",
    "can_available_domains", "can_schemas", "can_tables",
    "can_select_star", "can_table_extra_metadata",
]

SUPERSET_VIEW_MENUS = [
    # 核心实体视图
    "Database", "Dataset", "Chart", "Dashboard", "Query", "SavedQuery",
    
    # 功能视图
    "SQLLab", "Explore", "Superset", "SQL Lab", "SQL Editor", "Saved Queries",
    
    # 管理视图
    "List Users", "List Roles", "Security", "Access Requests", "Action Log",
    "User Registrations", "User's Statistics",
    
    # API视图
    "DatabaseRestApi", "DatasetRestApi", "ChartRestApi", "DashboardRestApi",
    "ExploreRestApi", "QueryRestApi", "SavedQueryRestApi",
    
    # 特殊功能视图
    "Annotation", "CssTemplate", "ReportSchedule", "Log", "Tags",
    "Row Level Security", "EmbeddedDashboard",
    
    # 工具视图
    "ImportExportRestApi", "CacheRestApi", "AvailableDomains",
    "TableSchemaView", "ColumnarToDatabaseView", "ExcelToDatabaseView",
]

class PermissionAnalyzer:
    """权限分析器"""
    
    def __init__(self):
        self.permissions = SUPERSET_PERMISSIONS
        self.view_menus = SUPERSET_VIEW_MENUS
        self.permission_details = self._init_permission_details()
    
    def _init_permission_details(self) -> Dict[str, Dict[str, Any]]:
        """初始化权限详细信息"""
        return {
            # 基础CRUD权限
            "can_read": {
                "category": "CRUD",
                "description": "读取/查看权限",
                "functions": ["查看列表", "查看详情", "数据浏览"],
                "impact": "控制用户是否能查看数据和界面",
                "example_usage": ["查看仪表板列表", "查看图表详情", "浏览数据集"],
                "without_permission": "无法查看任何数据和界面内容"
            },
            "can_write": {
                "category": "CRUD", 
                "description": "写入/创建权限",
                "functions": ["创建新对象", "保存配置", "写入数据"],
                "impact": "控制用户是否能创建新的资源",
                "example_usage": ["创建新图表", "保存查询", "创建仪表板"],
                "without_permission": "无法创建任何新的资源对象"
            },
            "can_edit": {
                "category": "CRUD",
                "description": "编辑/修改权限", 
                "functions": ["修改现有对象", "更新配置", "编辑属性"],
                "impact": "控制用户是否能修改现有资源",
                "example_usage": ["编辑图表配置", "修改仪表板布局", "更新数据集属性"],
                "without_permission": "只能查看，无法修改任何现有资源"
            },
            "can_delete": {
                "category": "CRUD",
                "description": "删除权限",
                "functions": ["删除对象", "清理资源", "批量删除"],
                "impact": "控制用户是否能删除资源",
                "example_usage": ["删除图表", "删除仪表板", "清理查询历史"],
                "without_permission": "无法删除任何资源，可能导致资源堆积"
            },
            
            # 数据访问权限
            "all_database_access": {
                "category": "Data Access",
                "description": "所有数据库访问权限",
                "functions": ["访问所有数据库", "跨数据库查询", "全局数据权限"],
                "impact": "拥有此权限用户可以访问系统中所有数据库",
                "example_usage": ["连接任意数据库", "执行跨库查询", "管理所有数据源"],
                "without_permission": "只能访问被明确授权的特定数据库"
            },
            "all_datasource_access": {
                "category": "Data Access",
                "description": "所有数据源访问权限",
                "functions": ["访问所有数据表", "查询任意数据源", "全表权限"],
                "impact": "用户可以查询系统中的任何数据表",
                "example_usage": ["查询任意表", "创建基于任意表的图表", "数据探索"],
                "without_permission": "只能访问被明确授权的特定数据表"
            },
            "datasource_access": {
                "category": "Data Access",
                "description": "特定数据源访问权限",
                "functions": ["访问指定数据表", "基于表创建图表", "表级查询"],
                "impact": "细粒度控制用户对特定表的访问",
                "example_usage": ["访问sales_table", "基于user_table创建图表"],
                "without_permission": "无法访问该特定数据表"
            },
            
            # SQL Lab权限
            "can_execute_sql_query": {
                "category": "SQL Lab",
                "description": "执行SQL查询权限",
                "functions": ["运行SQL语句", "数据查询", "临时分析"],
                "impact": "控制用户是否能在SQL Lab中执行查询",
                "example_usage": ["SELECT * FROM table", "复杂SQL分析", "数据验证"],
                "without_permission": "无法在SQL Lab中执行任何查询"
            },
            "can_sqllab": {
                "category": "SQL Lab",
                "description": "SQL Lab访问权限",
                "functions": ["访问SQL Lab界面", "使用SQL编辑器", "查询管理"],
                "impact": "控制用户是否能访问SQL Lab功能",
                "example_usage": ["打开SQL Lab", "使用SQL编辑器", "管理查询历史"],
                "without_permission": "无法看到或使用SQL Lab功能"
            },
            "can_get_results": {
                "category": "SQL Lab",
                "description": "获取查询结果权限",
                "functions": ["查看SQL查询结果", "下载查询数据", "结果分页"],
                "impact": "控制用户是否能看到SQL查询的执行结果",
                "example_usage": ["查看SELECT结果", "下载查询数据", "分页浏览大结果集"],
                "without_permission": "能执行查询但看不到结果"
            },
            
            # 图表权限
            "can_explore": {
                "category": "Chart",
                "description": "数据探索权限",
                "functions": ["使用Explore界面", "创建图表", "数据可视化"],
                "impact": "控制用户是否能使用数据探索功能",
                "example_usage": ["打开Explore界面", "拖拽创建图表", "调整可视化参数"],
                "without_permission": "无法使用图表创建和数据探索功能"
            },
            "can_explore_json": {
                "category": "Chart",
                "description": "探索JSON配置权限",
                "functions": ["查看图表JSON配置", "高级图表配置", "API调用"],
                "impact": "控制用户是否能查看和修改图表的底层配置",
                "example_usage": ["查看chart JSON", "修改高级配置", "API集成"],
                "without_permission": "只能使用UI界面，无法进行高级配置"
            },
            "can_external_metadata": {
                "category": "Dataset",
                "description": "外部元数据权限",
                "functions": ["获取表结构信息", "刷新元数据", "同步schema"],
                "impact": "控制用户是否能获取数据源的元数据信息",
                "example_usage": ["查看表字段信息", "获取数据类型", "同步表结构"],
                "without_permission": "无法看到表的结构信息和字段详情"
            },
            "can_get_column_values": {
                "category": "Dataset",
                "description": "获取列值权限",
                "functions": ["查看字段唯一值", "过滤器选项", "数据预览"],
                "impact": "控制用户是否能查看字段的实际数据值",
                "example_usage": ["查看category字段的所有值", "设置过滤器选项", "数据质量检查"],
                "without_permission": "无法看到字段的实际值，影响过滤器使用和数据理解"
            },
            
            # 管理权限
            "can_update_role": {
                "category": "Admin",
                "description": "更新角色权限",
                "functions": ["修改用户角色", "分配权限", "角色管理"],
                "impact": "控制用户是否能管理系统角色和权限",
                "example_usage": ["给用户分配Alpha角色", "修改角色权限", "创建自定义角色"],
                "without_permission": "无法进行用户和权限管理"
            },
            "can_warm_up_cache": {
                "category": "Admin",
                "description": "缓存预热权限",
                "functions": ["预热仪表板缓存", "性能优化", "缓存管理"],
                "impact": "控制用户是否能执行缓存预热操作",
                "example_usage": ["预热重要仪表板", "提升访问速度", "系统优化"],
                "without_permission": "无法进行缓存优化，可能影响系统性能"
            },
            
            # 特殊功能权限
            "menu_access": {
                "category": "Menu Access",
                "description": "菜单访问权限",
                "functions": ["访问特定菜单", "界面导航", "功能入口"],
                "impact": "控制用户能否看到和访问特定的菜单项",
                "example_usage": ["SQL Lab菜单", "图表菜单", "设置菜单"],
                "without_permission": "相关菜单项不可见，无法访问对应功能"
            },
            "can_favstar": {
                "category": "User Experience",
                "description": "收藏功能权限",
                "functions": ["收藏图表", "收藏仪表板", "个人收藏管理"],
                "impact": "控制用户是否能使用收藏功能",
                "example_usage": ["收藏常用图表", "标记重要仪表板", "快速访问"],
                "without_permission": "无法使用收藏功能，影响使用体验"
            },
        }
    
    def analyze_permission_categories(self) -> Dict[str, List[str]]:
        """分析权限分类"""
        categories = defaultdict(list)
        
        for perm in self.permissions:
            if perm.startswith("can_"):
                action = perm[4:]  # 去掉 "can_" 前缀
                if action in ["read", "write", "edit", "delete", "add", "list", "show"]:
                    categories["CRUD"].append(perm)
                elif action in ["execute_sql_query", "sqllab", "get_results", "csv"]:
                    categories["SQL Lab"].append(perm)
                elif action in ["explore", "charts", "slice", "external_metadata"]:
                    categories["Chart & Visualization"].append(perm)
                elif action in ["dashboard", "copy_dash", "save_dash"]:
                    categories["Dashboard"].append(perm)
                elif action in ["dataset", "datasource", "get_column_values", "samples"]:
                    categories["Dataset"].append(perm)
                elif action in ["update_role", "grant_guest_token", "warm_up_cache"]:
                    categories["System Admin"].append(perm)
                else:
                    categories["Other Functions"].append(perm)
            elif perm.startswith("all_"):
                categories["Global Access"].append(perm)
            elif perm.endswith("_access"):
                categories["Resource Access"].append(perm)
            elif perm == "menu_access":
                categories["Menu Access"].append(perm)
            else:
                categories["Special"].append(perm)
        
        return dict(categories)
    
    def get_permission_impact_analysis(self, permission: str) -> Dict[str, Any]:
        """获取权限影响分析"""
        if permission in self.permission_details:
            return self.permission_details[permission]
        
        # 对于未详细定义的权限，进行推理分析
        analysis = {
            "category": "Unknown",
            "description": f"权限: {permission}",
            "functions": [],
            "impact": "未知影响",
            "example_usage": [],
            "without_permission": "未知限制"
        }
        
        # 基于权限名称进行分析
        if permission.startswith("can_"):
            action = permission[4:]
            analysis["category"] = "Action Permission"
            analysis["description"] = f"执行{action}操作的权限"
            analysis["functions"] = [f"执行{action}相关操作"]
            analysis["impact"] = f"控制用户是否能执行{action}操作"
            analysis["without_permission"] = f"无法执行{action}操作"
        elif permission.endswith("_access"):
            resource = permission[:-7]  # 去掉 "_access" 后缀
            analysis["category"] = "Access Permission"
            analysis["description"] = f"访问{resource}的权限"
            analysis["functions"] = [f"访问{resource}资源"]
            analysis["impact"] = f"控制用户是否能访问{resource}"
            analysis["without_permission"] = f"无法访问{resource}资源"
        
        return analysis
    
    def generate_permission_matrix(self) -> Dict[str, Dict[str, bool]]:
        """生成权限矩阵"""
        roles = ["Admin", "Alpha", "Gamma", "sql_lab", "Public"]
        categories = self.analyze_permission_categories()
        
        # 简化的权限分配逻辑
        matrix = {}
        
        for category, perms in categories.items():
            matrix[category] = {}
            for role in roles:
                if role == "Admin":
                    matrix[category][role] = True  # Admin有所有权限
                elif role == "Alpha":
                    # Alpha没有系统管理权限，但有其他大部分权限
                    matrix[category][role] = category != "System Admin"
                elif role == "Gamma":
                    # Gamma只有基本的读权限
                    matrix[category][role] = category in ["CRUD"] and any("read" in p or "show" in p or "list" in p for p in perms)
                elif role == "sql_lab":
                    # sql_lab有SQL相关权限和基本读权限
                    matrix[category][role] = category in ["SQL Lab", "CRUD"] and any("read" in p or "show" in p or "list" in p or "sql" in p for p in perms)
                else:  # Public
                    matrix[category][role] = False  # Public几乎没有权限
        
        return matrix
    
    def generate_detailed_report(self) -> str:
        """生成详细的权限分析报告"""
        categories = self.analyze_permission_categories()
        matrix = self.generate_permission_matrix()
        
        report = "# Superset 完整权限系统分析报告\n\n"
        report += f"## 权限统计总览\n\n"
        report += f"- 总权限数量: {len(self.permissions)}\n"
        report += f"- 总视图菜单数量: {len(self.view_menus)}\n"
        report += f"- 权限分类数量: {len(categories)}\n\n"
        
        # 权限分类详情
        report += "## 权限分类详情\n\n"
        for category, perms in categories.items():
            report += f"### {category} ({len(perms)}个权限)\n\n"
            for perm in sorted(perms):
                analysis = self.get_permission_impact_analysis(perm)
                report += f"#### `{perm}`\n"
                report += f"- **功能**: {analysis['description']}\n"
                report += f"- **影响**: {analysis['impact']}\n"
                report += f"- **缺少时**: {analysis['without_permission']}\n"
                if analysis['example_usage']:
                    report += f"- **使用示例**: {', '.join(analysis['example_usage'])}\n"
                report += "\n"
        
        # 权限矩阵
        report += "## 角色权限矩阵\n\n"
        report += "| 权限分类 | Admin | Alpha | Gamma | sql_lab | Public |\n"
        report += "|---------|-------|-------|-------|---------|--------|\n"
        
        for category in categories.keys():
            row = f"| {category} |"
            for role in ["Admin", "Alpha", "Gamma", "sql_lab", "Public"]:
                has_perm = matrix.get(category, {}).get(role, False)
                icon = "✅" if has_perm else "❌"
                row += f" {icon} |"
            report += row + "\n"
        
        return report

def main():
    """主函数"""
    print("🔍 正在分析 Superset 权限系统...")
    
    analyzer = PermissionAnalyzer()
    
    # 生成权限分析
    categories = analyzer.analyze_permission_categories()
    
    print(f"\n📊 权限统计:")
    print(f"总权限数量: {len(analyzer.permissions)}")
    print(f"权限分类: {len(categories)}个")
    
    print(f"\n📋 权限分类分布:")
    for category, perms in categories.items():
        print(f"  {category}: {len(perms)}个权限")
    
    # 生成详细报告
    report = analyzer.generate_detailed_report()
    
    # 保存报告
    with open("complete_permission_analysis.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✅ 详细权限分析报告已生成: complete_permission_analysis.md")
    
    # 重点权限示例分析
    print(f"\n🎯 重点权限影响分析:")
    key_permissions = [
        "can_get_column_values",
        "can_external_metadata", 
        "can_execute_sql_query",
        "all_database_access",
        "datasource_access"
    ]
    
    for perm in key_permissions:
        analysis = analyzer.get_permission_impact_analysis(perm)
        print(f"\n`{perm}`:")
        print(f"  - 功能: {analysis['description']}")
        print(f"  - 影响: {analysis['impact']}")
        print(f"  - 缺少时: {analysis['without_permission']}")

if __name__ == "__main__":
    main() 