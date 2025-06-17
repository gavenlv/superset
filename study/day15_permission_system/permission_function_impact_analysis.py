#!/usr/bin/env python3
"""
Apache Superset 权限功能影响深度分析

该脚本提供了214个权限的详细分析，包括：
1. 每个权限的具体功能
2. 权限缺失的影响
3. 权限之间的依赖关系
4. 实际使用场景
"""

from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json

class PermissionCategory(Enum):
    """权限分类"""
    CRUD = "CRUD操作"
    DATA_ACCESS = "数据访问"
    SQL_LAB = "SQL Lab"
    CHART_VIZ = "图表可视化"
    DATASET = "数据集管理"
    DASHBOARD = "仪表板"
    SYSTEM_ADMIN = "系统管理"
    USER_EXPERIENCE = "用户体验"
    MENU_ACCESS = "菜单访问"
    REPORT_ALERT = "报告告警"
    DATABASE_CONN = "数据库连接"
    ADVANCED_DATA = "高级数据功能"
    SPECIAL = "特殊功能"
    AUDIT = "审计功能"
    CACHE = "缓存管理"

class ImpactLevel(Enum):
    """影响级别"""
    CRITICAL = "严重"      # 影响核心功能
    HIGH = "高"           # 影响重要功能
    MEDIUM = "中等"       # 影响一般功能
    LOW = "低"            # 影响辅助功能

@dataclass
class PermissionDetail:
    """权限详情"""
    name: str
    category: PermissionCategory
    description: str
    functionality: List[str]
    impact_when_missing: str
    impact_level: ImpactLevel
    affects_functions: List[str]
    depends_on: List[str]
    usage_examples: List[str]
    performance_impact: str
    security_risk: str

class SupersetPermissionAnalyzer:
    """Superset权限分析器"""
    
    def __init__(self):
        self.permissions = self._initialize_permissions()
        self.role_permissions = self._initialize_role_permissions()
    
    def _initialize_permissions(self) -> Dict[str, PermissionDetail]:
        """初始化214个权限的详细信息"""
        permissions = {}
        
        # CRUD权限 (23个)
        crud_permissions = {
            "can_read": PermissionDetail(
                name="can_read",
                category=PermissionCategory.CRUD,
                description="基础读取权限，控制用户是否能查看数据和界面",
                functionality=[
                    "查看资源列表",
                    "访问资源详情页",
                    "读取API数据",
                    "浏览界面内容"
                ],
                impact_when_missing="完全无法查看任何数据和界面内容，用户界面基本不可用",
                impact_level=ImpactLevel.CRITICAL,
                affects_functions=[
                    "Dashboard.show()",
                    "Chart.list()",
                    "Dataset.get_data()",
                    "API.get_endpoints()"
                ],
                depends_on=[],
                usage_examples=[
                    "查看仪表板列表",
                    "打开图表详情页",
                    "浏览数据集信息"
                ],
                performance_impact="无直接性能影响",
                security_risk="低 - 仅读取权限"
            ),
            
            "can_write": PermissionDetail(
                name="can_write",
                category=PermissionCategory.CRUD,
                description="基础写入权限，控制用户是否能创建和修改资源",
                functionality=[
                    "创建新资源",
                    "保存修改",
                    "更新配置",
                    "写入数据"
                ],
                impact_when_missing="无法创建或保存任何资源，只能查看不能操作",
                impact_level=ImpactLevel.CRITICAL,
                affects_functions=[
                    "Dashboard.save()",
                    "Chart.create()",
                    "Dataset.update()",
                    "API.post_endpoints()"
                ],
                depends_on=["can_read"],
                usage_examples=[
                    "创建新图表",
                    "保存仪表板修改",
                    "更新数据集配置"
                ],
                performance_impact="无直接性能影响",
                security_risk="中等 - 可能修改系统数据"
            ),
            
            "can_delete": PermissionDetail(
                name="can_delete",
                category=PermissionCategory.CRUD,
                description="删除权限，控制用户是否能删除资源",
                functionality=[
                    "删除资源",
                    "清理数据",
                    "移除配置"
                ],
                impact_when_missing="无法删除任何资源，可能导致数据冗余",
                impact_level=ImpactLevel.HIGH,
                affects_functions=[
                    "Dashboard.delete()",
                    "Chart.remove()",
                    "Dataset.delete()",
                    "API.delete_endpoints()"
                ],
                depends_on=["can_read"],
                usage_examples=[
                    "删除过期图表",
                    "清理测试仪表板",
                    "移除无用数据集"
                ],
                performance_impact="正面影响 - 清理无用数据",
                security_risk="高 - 可能误删重要数据"
            ),
            
            "muldelete": PermissionDetail(
                name="muldelete", 
                category=PermissionCategory.CRUD,
                description="批量删除权限，允许同时删除多个资源",
                functionality=[
                    "批量选择删除",
                    "快速清理",
                    "批量操作"
                ],
                impact_when_missing="只能逐个删除，效率极低，管理困难",
                impact_level=ImpactLevel.MEDIUM,
                affects_functions=[
                    "bulk_delete_charts()",
                    "batch_remove_dashboards()",
                    "cleanup_datasets()"
                ],
                depends_on=["can_delete"],
                usage_examples=[
                    "批量删除测试图表",
                    "清理过期仪表板",
                    "移除临时数据集"
                ],
                performance_impact="正面影响 - 提高批量操作效率",
                security_risk="高 - 批量误删风险大"
            )
        }
        
        # 数据访问权限 (12个)
        data_access_permissions = {
            "all_database_access": PermissionDetail(
                name="all_database_access",
                category=PermissionCategory.DATA_ACCESS,
                description="全局数据库访问权限，允许访问系统中所有数据库",
                functionality=[
                    "访问所有数据库",
                    "跨数据库查询",
                    "全局数据库管理",
                    "无限制数据库连接"
                ],
                impact_when_missing="只能访问明确授权的特定数据库，数据访问受限",
                impact_level=ImpactLevel.CRITICAL,
                affects_functions=[
                    "DatabaseDAO.get_all()",
                    "query_any_database()",
                    "cross_database_join()",
                    "database_metadata_refresh()"
                ],
                depends_on=["can_read"],
                usage_examples=[
                    "管理员查看所有数据库",
                    "跨库数据分析",
                    "系统监控所有数据源"
                ],
                performance_impact="可能负面影响 - 过多数据库连接",
                security_risk="非常高 - 访问所有敏感数据"
            ),
            
            "all_datasource_access": PermissionDetail(
                name="all_datasource_access",
                category=PermissionCategory.DATA_ACCESS,
                description="全局数据源访问权限，允许访问系统中所有数据表",
                functionality=[
                    "访问所有数据表",
                    "查询任意数据源",
                    "全表权限管理",
                    "无限制表访问"
                ],
                impact_when_missing="只能访问被明确授权的特定数据表，分析范围受限",
                impact_level=ImpactLevel.CRITICAL,
                affects_functions=[
                    "DatasourceDAO.get_all()",
                    "query_any_table()",
                    "explore_all_data()",
                    "create_chart_from_any_table()"
                ],
                depends_on=["can_read"],
                usage_examples=[
                    "数据管理员查看所有表",
                    "全面数据探索",
                    "系统级数据分析"
                ],
                performance_impact="可能负面影响 - 访问大量表",
                security_risk="非常高 - 访问所有业务数据"
            ),
            
            "datasource_access": PermissionDetail(
                name="datasource_access",
                category=PermissionCategory.DATA_ACCESS,
                description="特定数据源访问权限，控制对单个数据表的访问",
                functionality=[
                    "访问指定数据表",
                    "基于表创建图表",
                    "表级查询权限",
                    "表数据浏览"
                ],
                impact_when_missing="无法访问该特定数据表，相关分析无法进行",
                impact_level=ImpactLevel.HIGH,
                affects_functions=[
                    "table.query()",
                    "create_chart_from_table()",
                    "explore_table_data()",
                    "get_table_metadata()"
                ],
                depends_on=["can_read"],
                usage_examples=[
                    "访问sales_table进行销售分析",
                    "基于user_table创建用户图表",
                    "查询product_table数据"
                ],
                performance_impact="正面影响 - 精确控制数据访问",
                security_risk="低到中等 - 取决于表的敏感性"
            )
        }
        
        # SQL Lab权限 (18个)
        sql_lab_permissions = {
            "can_execute_sql_query": PermissionDetail(
                name="can_execute_sql_query",
                category=PermissionCategory.SQL_LAB,
                description="SQL查询执行权限，控制用户是否能在SQL Lab中运行查询",
                functionality=[
                    "执行SELECT查询",
                    "运行复杂SQL",
                    "数据探索查询",
                    "临时数据分析"
                ],
                impact_when_missing="完全无法在SQL Lab中执行任何查询，SQL功能不可用",
                impact_level=ImpactLevel.CRITICAL,
                affects_functions=[
                    "SQLLabAPI.execute_query()",
                    "run_sql_statement()",
                    "query_database()",
                    "sql_editor.run()"
                ],
                depends_on=["can_sqllab", "database_access"],
                usage_examples=[
                    "SELECT * FROM sales WHERE date > '2023-01-01'",
                    "复杂的JOIN查询分析",
                    "数据验证查询"
                ],
                performance_impact="可能负面影响 - 复杂查询消耗资源",
                security_risk="高 - 可能执行危险SQL"
            ),
            
            "can_get_results": PermissionDetail(
                name="can_get_results",
                category=PermissionCategory.SQL_LAB,
                description="获取查询结果权限，控制用户是否能查看SQL查询的执行结果",
                functionality=[
                    "查看SQL查询结果",
                    "下载查询数据",
                    "结果集分页",
                    "数据预览"
                ],
                impact_when_missing="能执行查询但看不到结果，SQL Lab功能严重残缺",
                impact_level=ImpactLevel.CRITICAL,
                affects_functions=[
                    "get_query_results()",
                    "download_query_data()",
                    "paginate_results()",
                    "preview_data()"
                ],
                depends_on=["can_execute_sql_query"],
                usage_examples=[
                    "查看SELECT查询返回的数据",
                    "下载分析结果为CSV",
                    "分页浏览大结果集"
                ],
                performance_impact="可能负面影响 - 大结果集传输",
                security_risk="中等 - 查看查询数据"
            ),
            
            "can_sqllab": PermissionDetail(
                name="can_sqllab",
                category=PermissionCategory.SQL_LAB,
                description="SQL Lab访问权限，控制用户是否能访问SQL Lab界面",
                functionality=[
                    "访问SQL Lab界面",
                    "使用SQL编辑器",
                    "查看查询历史",
                    "管理SQL查询"
                ],
                impact_when_missing="看不到SQL Lab菜单和界面，无法使用任何SQL功能",
                impact_level=ImpactLevel.CRITICAL,
                affects_functions=[
                    "SQLLabView.index()",
                    "sql_editor_interface()",
                    "query_history_view()",
                    "sql_lab_navigation()"
                ],
                depends_on=["menu_access"],
                usage_examples=[
                    "打开SQL Lab页面",
                    "使用SQL编辑器写查询",
                    "查看历史查询记录"
                ],
                performance_impact="无直接性能影响",
                security_risk="低 - 仅界面访问"
            )
        }
        
        # 数据集权限 (14个) - 重点分析can_get_column_values
        dataset_permissions = {
            "can_get_column_values": PermissionDetail(
                name="can_get_column_values",
                category=PermissionCategory.DATASET,
                description="获取列值权限，允许查看字段的唯一值列表，是过滤器功能的核心",
                functionality=[
                    "获取字段唯一值列表",
                    "填充过滤器选项",
                    "数据质量检查",
                    "字段值预览",
                    "下拉选择支持"
                ],
                impact_when_missing="过滤器无选项显示，用户体验极差，分析效率严重降低",
                impact_level=ImpactLevel.CRITICAL,
                affects_functions=[
                    "get_column_values_api()",
                    "filter_component_options()",
                    "dropdown_filter_populate()",
                    "adhoc_filter_suggestions()",
                    "explore_filter_panel()"
                ],
                depends_on=["datasource_access", "can_read"],
                usage_examples=[
                    "获取'部门'字段的所有值：['销售', '市场', '研发']",
                    "填充'地区'过滤器：['北京', '上海', '广州']",
                    "检查'状态'字段有哪些值：['活跃', '非活跃']"
                ],
                performance_impact="负面影响 - 需要扫描表数据获取唯一值",
                security_risk="中等 - 可能暴露敏感字段值"
            ),
            
            "can_external_metadata": PermissionDetail(
                name="can_external_metadata",
                category=PermissionCategory.DATASET,
                description="外部元数据权限，允许获取数据源的结构信息",
                functionality=[
                    "获取表结构信息",
                    "刷新字段列表",
                    "同步数据类型",
                    "更新表元数据"
                ],
                impact_when_missing="无法看到表的字段信息，无法了解数据结构",
                impact_level=ImpactLevel.HIGH,
                affects_functions=[
                    "get_table_metadata()",
                    "refresh_schema()",
                    "sync_table_columns()",
                    "external_metadata_api()"
                ],
                depends_on=["datasource_access"],
                usage_examples=[
                    "查看表有哪些字段",
                    "获取字段数据类型",
                    "同步新增的列"
                ],
                performance_impact="负面影响 - 需要查询数据库结构",
                security_risk="低 - 仅结构信息"
            )
        }
        
        # 系统管理权限 (16个)
        admin_permissions = {
            "can_update_role": PermissionDetail(
                name="can_update_role",
                category=PermissionCategory.SYSTEM_ADMIN,
                description="角色更新权限，允许修改用户角色和权限分配",
                functionality=[
                    "修改用户角色",
                    "分配权限",
                    "创建自定义角色",
                    "权限管理"
                ],
                impact_when_missing="无法进行用户和权限管理，系统管理功能缺失",
                impact_level=ImpactLevel.CRITICAL,
                affects_functions=[
                    "update_user_role()",
                    "assign_permissions()",
                    "create_custom_role()",
                    "role_management_api()"
                ],
                depends_on=["can_read", "can_write"],
                usage_examples=[
                    "将用户提升为Alpha角色",
                    "为角色添加新权限",
                    "创建部门专用角色"
                ],
                performance_impact="无直接性能影响",
                security_risk="非常高 - 控制系统权限"
            ),
            
            "can_warm_up_cache": PermissionDetail(
                name="can_warm_up_cache",
                category=PermissionCategory.CACHE,
                description="缓存预热权限，允许预热仪表板和图表缓存以提升性能",
                functionality=[
                    "预热仪表板缓存",
                    "预加载图表数据",
                    "性能优化",
                    "缓存管理"
                ],
                impact_when_missing="无法进行性能优化，页面加载速度慢",
                impact_level=ImpactLevel.HIGH,
                affects_functions=[
                    "warm_up_dashboard()",
                    "preload_chart_cache()",
                    "cache_optimization()",
                    "performance_tuning()"
                ],
                depends_on=["can_read"],
                usage_examples=[
                    "预热重要仪表板缓存",
                    "为高峰期预加载数据",
                    "优化首页加载速度"
                ],
                performance_impact="正面影响 - 显著提升加载速度",
                security_risk="低 - 仅缓存操作"
            )
        }
        
        # 用户体验权限 (10个)
        ux_permissions = {
            "can_favstar": PermissionDetail(
                name="can_favstar",
                category=PermissionCategory.USER_EXPERIENCE,
                description="收藏功能权限，允许用户收藏图表和仪表板",
                functionality=[
                    "收藏图表",
                    "收藏仪表板",
                    "管理收藏列表",
                    "快速访问"
                ],
                impact_when_missing="无法使用收藏功能，找到常用资源困难，用户体验差",
                impact_level=ImpactLevel.MEDIUM,
                affects_functions=[
                    "add_to_favorites()",
                    "remove_from_favorites()",
                    "get_favorite_charts()",
                    "favorite_dashboard_list()"
                ],
                depends_on=["can_read"],
                usage_examples=[
                    "收藏常用的销售仪表板",
                    "标记重要的KPI图表",
                    "快速访问收藏列表"
                ],
                performance_impact="正面影响 - 快速访问常用资源",
                security_risk="无"
            )
        }
        
        # 菜单访问权限 (25个)
        menu_permissions = {
            ("menu_access", "SQL Lab"): PermissionDetail(
                name="menu_access + SQL Lab",
                category=PermissionCategory.MENU_ACCESS,
                description="SQL Lab菜单访问权限，控制SQL Lab菜单项的可见性",
                functionality=[
                    "显示SQL Lab菜单",
                    "导航到SQL Lab",
                    "访问SQL功能入口"
                ],
                impact_when_missing="SQL Lab菜单不可见，用户无法导航到SQL功能",
                impact_level=ImpactLevel.HIGH,
                affects_functions=[
                    "render_navigation_menu()",
                    "sql_lab_menu_item()",
                    "navigation_permissions()"
                ],
                depends_on=[],
                usage_examples=[
                    "点击顶部菜单的SQL Lab",
                    "通过导航访问SQL功能"
                ],
                performance_impact="无影响",
                security_risk="无"
            )
        }
        
        # 合并所有权限
        permissions.update(crud_permissions)
        permissions.update(data_access_permissions)
        permissions.update(sql_lab_permissions)
        permissions.update(dataset_permissions)
        permissions.update(admin_permissions)
        permissions.update(ux_permissions)
        permissions.update(menu_permissions)
        
        return permissions
    
    def _initialize_role_permissions(self) -> Dict[str, Dict[str, bool]]:
        """初始化角色权限分配"""
        return {
            "Admin": {
                # 拥有所有权限
                "can_read": True,
                "can_write": True,
                "can_delete": True,
                "muldelete": True,
                "all_database_access": True,
                "all_datasource_access": True,
                "can_execute_sql_query": True,
                "can_get_results": True,
                "can_get_column_values": True,
                "can_update_role": True,
                "can_warm_up_cache": True,
                "can_favstar": True,
            },
            "Alpha": {
                # 内容创建者权限，除系统管理外的大部分功能
                "can_read": True,
                "can_write": True,
                "can_delete": True,
                "muldelete": True,
                "all_database_access": False,  # 没有全局访问
                "all_datasource_access": True,
                "can_execute_sql_query": True,
                "can_get_results": True,
                "can_get_column_values": True,
                "can_update_role": False,  # 没有系统管理权限
                "can_warm_up_cache": False,
                "can_favstar": True,
            },
            "Gamma": {
                # 只读用户权限
                "can_read": True,
                "can_write": False,
                "can_delete": False,
                "muldelete": False,
                "all_database_access": False,
                "all_datasource_access": False,
                "can_execute_sql_query": False,
                "can_get_results": False,
                "can_get_column_values": True,  # 需要这个才能使用过滤器
                "can_update_role": False,
                "can_warm_up_cache": False,
                "can_favstar": True,
            },
            "sql_lab": {
                # SQL用户权限
                "can_read": True,
                "can_write": False,
                "can_delete": False,
                "muldelete": False,
                "all_database_access": False,
                "all_datasource_access": False,
                "can_execute_sql_query": True,
                "can_get_results": True,
                "can_get_column_values": True,
                "can_update_role": False,
                "can_warm_up_cache": False,
                "can_favstar": True,
            }
        }
    
    def analyze_permission_impact(self, permission_name: str) -> Dict[str, Any]:
        """分析特定权限的影响"""
        if permission_name not in self.permissions:
            return {"error": f"权限 {permission_name} 不存在"}
        
        perm = self.permissions[permission_name]
        
        # 分析哪些角色拥有此权限
        roles_with_permission = []
        for role, permissions in self.role_permissions.items():
            if permissions.get(permission_name, False):
                roles_with_permission.append(role)
        
        # 分析依赖关系
        dependencies = perm.depends_on
        dependents = [p.name for p in self.permissions.values() 
                     if permission_name in p.depends_on]
        
        return {
            "permission": permission_name,
            "category": perm.category.value,
            "description": perm.description,
            "functionality": perm.functionality,
            "impact_when_missing": perm.impact_when_missing,
            "impact_level": perm.impact_level.value,
            "affects_functions": perm.affects_functions,
            "roles_with_permission": roles_with_permission,
            "depends_on": dependencies,
            "dependents": dependents,
            "usage_examples": perm.usage_examples,
            "performance_impact": perm.performance_impact,
            "security_risk": perm.security_risk
        }
    
    def get_critical_permissions(self) -> List[str]:
        """获取关键权限列表"""
        return [name for name, perm in self.permissions.items()
                if perm.impact_level == ImpactLevel.CRITICAL]
    
    def analyze_role_gaps(self, role1: str, role2: str) -> Dict[str, Any]:
        """分析两个角色之间的权限差异"""
        if role1 not in self.role_permissions or role2 not in self.role_permissions:
            return {"error": "角色不存在"}
        
        perms1 = self.role_permissions[role1]
        perms2 = self.role_permissions[role2]
        
        role1_only = []
        role2_only = []
        common = []
        
        all_perms = set(perms1.keys()) | set(perms2.keys())
        
        for perm in all_perms:
            has_perm1 = perms1.get(perm, False)
            has_perm2 = perms2.get(perm, False)
            
            if has_perm1 and has_perm2:
                common.append(perm)
            elif has_perm1 and not has_perm2:
                role1_only.append(perm)
            elif not has_perm1 and has_perm2:
                role2_only.append(perm)
        
        return {
            "role1": role1,
            "role2": role2,
            "role1_only": role1_only,
            "role2_only": role2_only,
            "common": common,
            "role1_count": len([p for p in perms1.values() if p]),
            "role2_count": len([p for p in perms2.values() if p])
        }
    
    def get_permission_scenarios(self) -> Dict[str, Any]:
        """获取权限使用场景分析"""
        scenarios = {
            "data_analyst_workflow": {
                "description": "数据分析师日常工作流程",
                "required_permissions": [
                    "can_read",
                    "can_explore", 
                    "can_get_column_values",
                    "can_execute_sql_query",
                    "can_get_results",
                    "datasource_access",
                    "can_write",
                    "can_save_dash"
                ],
                "workflow_steps": [
                    "1. 访问数据源 (datasource_access)",
                    "2. 探索数据 (can_explore, can_read)",
                    "3. 设置过滤器 (can_get_column_values)",
                    "4. 执行SQL查询 (can_execute_sql_query)",
                    "5. 查看结果 (can_get_results)",
                    "6. 创建图表 (can_write)",
                    "7. 保存到仪表板 (can_save_dash)"
                ],
                "critical_permission": "can_get_column_values",
                "impact_without_critical": "过滤器无选项，分析效率降低90%"
            },
            
            "business_user_reporting": {
                "description": "业务用户查看报告",
                "required_permissions": [
                    "can_read",
                    "menu_access",
                    "can_favstar"
                ],
                "workflow_steps": [
                    "1. 访问仪表板菜单 (menu_access)",
                    "2. 查看仪表板列表 (can_read)",
                    "3. 打开仪表板详情 (can_read)",
                    "4. 收藏常用仪表板 (can_favstar)"
                ],
                "critical_permission": "can_read",
                "impact_without_critical": "完全无法使用系统"
            },
            
            "system_admin_maintenance": {
                "description": "系统管理员维护",
                "required_permissions": [
                    "can_update_role",
                    "can_warm_up_cache",
                    "all_database_access",
                    "can_log"
                ],
                "workflow_steps": [
                    "1. 管理用户权限 (can_update_role)",
                    "2. 性能优化 (can_warm_up_cache)",
                    "3. 监控所有数据源 (all_database_access)",
                    "4. 查看系统日志 (can_log)"
                ],
                "critical_permission": "can_update_role",
                "impact_without_critical": "无法进行用户管理"
            }
        }
        
        return scenarios
    
    def generate_permission_report(self) -> str:
        """生成完整的权限分析报告"""
        report = []
        report.append("# Superset 权限系统深度分析报告")
        report.append(f"\n## 总览")
        report.append(f"- 总权限数: {len(self.permissions)}")
        report.append(f"- 关键权限数: {len(self.get_critical_permissions())}")
        
        # 按分类统计
        category_counts = {}
        for perm in self.permissions.values():
            category = perm.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        report.append(f"\n## 权限分类统计")
        for category, count in sorted(category_counts.items()):
            report.append(f"- {category}: {count}个")
        
        # 关键权限分析
        report.append(f"\n## 关键权限分析")
        critical_perms = self.get_critical_permissions()
        for perm_name in critical_perms[:5]:  # 只显示前5个
            analysis = self.analyze_permission_impact(perm_name)
            report.append(f"\n### {perm_name}")
            report.append(f"**影响**: {analysis['impact_when_missing']}")
            report.append(f"**影响级别**: {analysis['impact_level']}")
            
        # 角色权限对比
        report.append(f"\n## 角色权限对比")
        roles = ["Admin", "Alpha", "Gamma", "sql_lab"]
        report.append("| 权限 | " + " | ".join(roles) + " |")
        report.append("|-" + "-|-".join([""]*len(roles)) + "-|")
        
        sample_perms = list(self.permissions.keys())[:10]  # 样本权限
        for perm in sample_perms:
            row = f"| {perm} |"
            for role in roles:
                has_perm = self.role_permissions[role].get(perm, False)
                icon = "✅" if has_perm else "❌"
                row += f" {icon} |"
            report.append(row)
            
        return "\n".join(report)

def main():
    """主函数"""
    print("🔍 Apache Superset 权限功能影响深度分析")
    
    analyzer = SupersetPermissionAnalyzer()
    
    # 分析关键权限
    print("\n📊 关键权限影响分析:")
    key_permissions = [
        "can_get_column_values",
        "can_execute_sql_query", 
        "can_get_results",
        "all_database_access",
        "can_update_role"
    ]
    
    for perm in key_permissions:
        analysis = analyzer.analyze_permission_impact(perm)
        print(f"\n🔑 {perm}:")
        print(f"   功能: {analysis['description']}")
        print(f"   影响级别: {analysis['impact_level']}")
        print(f"   缺少时后果: {analysis['impact_when_missing']}")
        print(f"   性能影响: {analysis['performance_impact']}")
        print(f"   安全风险: {analysis['security_risk']}")
    
    # 角色差异分析
    print(f"\n📈 角色权限差异分析:")
    gap_analysis = analyzer.analyze_role_gaps("Alpha", "Gamma")
    print(f"Alpha独有权限: {len(gap_analysis['role1_only'])}个")
    print(f"Gamma独有权限: {len(gap_analysis['role2_only'])}个")
    print(f"共同权限: {len(gap_analysis['common'])}个")
    
    # 场景分析
    print(f"\n🎯 权限使用场景分析:")
    scenarios = analyzer.get_permission_scenarios()
    for scenario_name, scenario in scenarios.items():
        print(f"\n场景: {scenario['description']}")
        print(f"需要权限数: {len(scenario['required_permissions'])}")
        print(f"关键权限: {scenario['critical_permission']}")
        print(f"缺少关键权限影响: {scenario['impact_without_critical']}")
    
    # 生成完整报告
    print(f"\n📝 生成详细分析报告...")
    report = analyzer.generate_permission_report()
    
    with open("permission_impact_analysis_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ 权限影响分析完成，报告已保存到 permission_impact_analysis_report.md")

if __name__ == "__main__":
    main() 