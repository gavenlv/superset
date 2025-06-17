# Superset 完整权限系统分析报告

## 权限统计总览

- 总权限数量: 84
- 总视图菜单数量: 39
- 权限分类数量: 10

## 权限分类详情

### CRUD (7个权限)

#### `can_add`
- **功能**: 执行add操作的权限
- **影响**: 控制用户是否能执行add操作
- **缺少时**: 无法执行add操作

#### `can_delete`
- **功能**: 删除权限
- **影响**: 控制用户是否能删除资源
- **缺少时**: 无法删除任何资源，可能导致资源堆积
- **使用示例**: 删除图表, 删除仪表板, 清理查询历史

#### `can_edit`
- **功能**: 编辑/修改权限
- **影响**: 控制用户是否能修改现有资源
- **缺少时**: 只能查看，无法修改任何现有资源
- **使用示例**: 编辑图表配置, 修改仪表板布局, 更新数据集属性

#### `can_list`
- **功能**: 执行list操作的权限
- **影响**: 控制用户是否能执行list操作
- **缺少时**: 无法执行list操作

#### `can_read`
- **功能**: 读取/查看权限
- **影响**: 控制用户是否能查看数据和界面
- **缺少时**: 无法查看任何数据和界面内容
- **使用示例**: 查看仪表板列表, 查看图表详情, 浏览数据集

#### `can_show`
- **功能**: 执行show操作的权限
- **影响**: 控制用户是否能执行show操作
- **缺少时**: 无法执行show操作

#### `can_write`
- **功能**: 写入/创建权限
- **影响**: 控制用户是否能创建新的资源
- **缺少时**: 无法创建任何新的资源对象
- **使用示例**: 创建新图表, 保存查询, 创建仪表板

### Global Access (3个权限)

#### `all_database_access`
- **功能**: 所有数据库访问权限
- **影响**: 拥有此权限用户可以访问系统中所有数据库
- **缺少时**: 只能访问被明确授权的特定数据库
- **使用示例**: 连接任意数据库, 执行跨库查询, 管理所有数据源

#### `all_datasource_access`
- **功能**: 所有数据源访问权限
- **影响**: 用户可以查询系统中的任何数据表
- **缺少时**: 只能访问被明确授权的特定数据表
- **使用示例**: 查询任意表, 创建基于任意表的图表, 数据探索

#### `all_query_access`
- **功能**: 访问all_query的权限
- **影响**: 控制用户是否能访问all_query
- **缺少时**: 无法访问all_query资源

### Resource Access (5个权限)

#### `catalog_access`
- **功能**: 访问catalog的权限
- **影响**: 控制用户是否能访问catalog
- **缺少时**: 无法访问catalog资源

#### `database_access`
- **功能**: 访问database的权限
- **影响**: 控制用户是否能访问database
- **缺少时**: 无法访问database资源

#### `datasource_access`
- **功能**: 特定数据源访问权限
- **影响**: 细粒度控制用户对特定表的访问
- **缺少时**: 无法访问该特定数据表
- **使用示例**: 访问sales_table, 基于user_table创建图表

#### `menu_access`
- **功能**: 菜单访问权限
- **影响**: 控制用户能否看到和访问特定的菜单项
- **缺少时**: 相关菜单项不可见，无法访问对应功能
- **使用示例**: SQL Lab菜单, 图表菜单, 设置菜单

#### `schema_access`
- **功能**: 访问schema的权限
- **影响**: 控制用户是否能访问schema
- **缺少时**: 无法访问schema资源

### SQL Lab (4个权限)

#### `can_csv`
- **功能**: 执行csv操作的权限
- **影响**: 控制用户是否能执行csv操作
- **缺少时**: 无法执行csv操作

#### `can_execute_sql_query`
- **功能**: 执行SQL查询权限
- **影响**: 控制用户是否能在SQL Lab中执行查询
- **缺少时**: 无法在SQL Lab中执行任何查询
- **使用示例**: SELECT * FROM table, 复杂SQL分析, 数据验证

#### `can_get_results`
- **功能**: 获取查询结果权限
- **影响**: 控制用户是否能看到SQL查询的执行结果
- **缺少时**: 能执行查询但看不到结果
- **使用示例**: 查看SELECT结果, 下载查询数据, 分页浏览大结果集

#### `can_sqllab`
- **功能**: SQL Lab访问权限
- **影响**: 控制用户是否能访问SQL Lab功能
- **缺少时**: 无法看到或使用SQL Lab功能
- **使用示例**: 打开SQL Lab, 使用SQL编辑器, 管理查询历史

### Other Functions (48个权限)

#### `can_alert`
- **功能**: 执行alert操作的权限
- **影响**: 控制用户是否能执行alert操作
- **缺少时**: 无法执行alert操作

#### `can_annotation`
- **功能**: 执行annotation操作的权限
- **影响**: 控制用户是否能执行annotation操作
- **缺少时**: 无法执行annotation操作

#### `can_approve`
- **功能**: 执行approve操作的权限
- **影响**: 控制用户是否能执行approve操作
- **缺少时**: 无法执行approve操作

#### `can_available_domains`
- **功能**: 执行available_domains操作的权限
- **影响**: 控制用户是否能执行available_domains操作
- **缺少时**: 无法执行available_domains操作

#### `can_cache_key`
- **功能**: 执行cache_key操作的权限
- **影响**: 控制用户是否能执行cache_key操作
- **缺少时**: 无法执行cache_key操作

#### `can_changed_by`
- **功能**: 执行changed_by操作的权限
- **影响**: 控制用户是否能执行changed_by操作
- **缺少时**: 无法执行changed_by操作

#### `can_changed_on`
- **功能**: 执行changed_on操作的权限
- **影响**: 控制用户是否能执行changed_on操作
- **缺少时**: 无法执行changed_on操作

#### `can_created_by`
- **功能**: 执行created_by操作的权限
- **影响**: 控制用户是否能执行created_by操作
- **缺少时**: 无法执行created_by操作

#### `can_created_on`
- **功能**: 执行created_on操作的权限
- **影响**: 控制用户是否能执行created_on操作
- **缺少时**: 无法执行created_on操作

#### `can_dashboard_permalink`
- **功能**: 执行dashboard_permalink操作的权限
- **影响**: 控制用户是否能执行dashboard_permalink操作
- **缺少时**: 无法执行dashboard_permalink操作

#### `can_delete_api`
- **功能**: 执行delete_api操作的权限
- **影响**: 控制用户是否能执行delete_api操作
- **缺少时**: 无法执行delete_api操作

#### `can_druid_refresh`
- **功能**: 执行druid_refresh操作的权限
- **影响**: 控制用户是否能执行druid_refresh操作
- **缺少时**: 无法执行druid_refresh操作

#### `can_email_report`
- **功能**: 执行email_report操作的权限
- **影响**: 控制用户是否能执行email_report操作
- **缺少时**: 无法执行email_report操作

#### `can_estimate_query_cost`
- **功能**: 执行estimate_query_cost操作的权限
- **影响**: 控制用户是否能执行estimate_query_cost操作
- **缺少时**: 无法执行estimate_query_cost操作

#### `can_explore_json`
- **功能**: 探索JSON配置权限
- **影响**: 控制用户是否能查看和修改图表的底层配置
- **缺少时**: 只能使用UI界面，无法进行高级配置
- **使用示例**: 查看chart JSON, 修改高级配置, API集成

#### `can_export_csv`
- **功能**: 执行export_csv操作的权限
- **影响**: 控制用户是否能执行export_csv操作
- **缺少时**: 无法执行export_csv操作

#### `can_export_dashboard`
- **功能**: 执行export_dashboard操作的权限
- **影响**: 控制用户是否能执行export_dashboard操作
- **缺少时**: 无法执行export_dashboard操作

#### `can_external_metadata_by_name`
- **功能**: 执行external_metadata_by_name操作的权限
- **影响**: 控制用户是否能执行external_metadata_by_name操作
- **缺少时**: 无法执行external_metadata_by_name操作

#### `can_favstar`
- **功能**: 收藏功能权限
- **影响**: 控制用户是否能使用收藏功能
- **缺少时**: 无法使用收藏功能，影响使用体验
- **使用示例**: 收藏常用图表, 标记重要仪表板, 快速访问

#### `can_get`
- **功能**: 执行get操作的权限
- **影响**: 控制用户是否能执行get操作
- **缺少时**: 无法执行get操作

#### `can_get_test_results`
- **功能**: 执行get_test_results操作的权限
- **影响**: 控制用户是否能执行get_test_results操作
- **缺少时**: 无法执行get_test_results操作

#### `can_import_dashboards`
- **功能**: 执行import_dashboards操作的权限
- **影响**: 控制用户是否能执行import_dashboards操作
- **缺少时**: 无法执行import_dashboards操作

#### `can_info`
- **功能**: 执行info操作的权限
- **影响**: 控制用户是否能执行info操作
- **缺少时**: 无法执行info操作

#### `can_invalidate_cache`
- **功能**: 执行invalidate_cache操作的权限
- **影响**: 控制用户是否能执行invalidate_cache操作
- **缺少时**: 无法执行invalidate_cache操作

#### `can_log`
- **功能**: 执行log操作的权限
- **影响**: 控制用户是否能执行log操作
- **缺少时**: 无法执行log操作

#### `can_override_role_permissions`
- **功能**: 执行override_role_permissions操作的权限
- **影响**: 控制用户是否能执行override_role_permissions操作
- **缺少时**: 无法执行override_role_permissions操作

#### `can_post`
- **功能**: 执行post操作的权限
- **影响**: 控制用户是否能执行post操作
- **缺少时**: 无法执行post操作

#### `can_profile`
- **功能**: 执行profile操作的权限
- **影响**: 控制用户是否能执行profile操作
- **缺少时**: 无法执行profile操作

#### `can_put`
- **功能**: 执行put操作的权限
- **影响**: 控制用户是否能执行put操作
- **缺少时**: 无法执行put操作

#### `can_recent_activity`
- **功能**: 执行recent_activity操作的权限
- **影响**: 控制用户是否能执行recent_activity操作
- **缺少时**: 无法执行recent_activity操作

#### `can_refresh`
- **功能**: 执行refresh操作的权限
- **影响**: 控制用户是否能执行refresh操作
- **缺少时**: 无法执行refresh操作

#### `can_related`
- **功能**: 执行related操作的权限
- **影响**: 控制用户是否能执行related操作
- **缺少时**: 无法执行related操作

#### `can_report`
- **功能**: 执行report操作的权限
- **影响**: 控制用户是否能执行report操作
- **缺少时**: 无法执行report操作

#### `can_request_access`
- **功能**: 执行request_access操作的权限
- **影响**: 控制用户是否能执行request_access操作
- **缺少时**: 无法执行request_access操作

#### `can_reset_password`
- **功能**: 执行reset_password操作的权限
- **影响**: 控制用户是否能执行reset_password操作
- **缺少时**: 无法执行reset_password操作

#### `can_schemas`
- **功能**: 执行schemas操作的权限
- **影响**: 控制用户是否能执行schemas操作
- **缺少时**: 无法执行schemas操作

#### `can_search`
- **功能**: 执行search操作的权限
- **影响**: 控制用户是否能执行search操作
- **缺少时**: 无法执行search操作

#### `can_select_star`
- **功能**: 执行select_star操作的权限
- **影响**: 控制用户是否能执行select_star操作
- **缺少时**: 无法执行select_star操作

#### `can_set_embedded`
- **功能**: 执行set_embedded操作的权限
- **影响**: 控制用户是否能执行set_embedded操作
- **缺少时**: 无法执行set_embedded操作

#### `can_sqllab_history`
- **功能**: 执行sqllab_history操作的权限
- **影响**: 控制用户是否能执行sqllab_history操作
- **缺少时**: 无法执行sqllab_history操作

#### `can_sync_druid_source`
- **功能**: 执行sync_druid_source操作的权限
- **影响**: 控制用户是否能执行sync_druid_source操作
- **缺少时**: 无法执行sync_druid_source操作

#### `can_table_extra_metadata`
- **功能**: 执行table_extra_metadata操作的权限
- **影响**: 控制用户是否能执行table_extra_metadata操作
- **缺少时**: 无法执行table_extra_metadata操作

#### `can_table_metadata`
- **功能**: 执行table_metadata操作的权限
- **影响**: 控制用户是否能执行table_metadata操作
- **缺少时**: 无法执行table_metadata操作

#### `can_tables`
- **功能**: 执行tables操作的权限
- **影响**: 控制用户是否能执行tables操作
- **缺少时**: 无法执行tables操作

#### `can_test_conn`
- **功能**: 执行test_conn操作的权限
- **影响**: 控制用户是否能执行test_conn操作
- **缺少时**: 无法执行test_conn操作

#### `can_userinfo`
- **功能**: 执行userinfo操作的权限
- **影响**: 控制用户是否能执行userinfo操作
- **缺少时**: 无法执行userinfo操作

#### `can_validate_parameters`
- **功能**: 执行validate_parameters操作的权限
- **影响**: 控制用户是否能执行validate_parameters操作
- **缺少时**: 无法执行validate_parameters操作

#### `can_view_and_drill`
- **功能**: 执行view_and_drill操作的权限
- **影响**: 控制用户是否能执行view_and_drill操作
- **缺少时**: 无法执行view_and_drill操作

### Chart & Visualization (4个权限)

#### `can_charts`
- **功能**: 执行charts操作的权限
- **影响**: 控制用户是否能执行charts操作
- **缺少时**: 无法执行charts操作

#### `can_explore`
- **功能**: 数据探索权限
- **影响**: 控制用户是否能使用数据探索功能
- **缺少时**: 无法使用图表创建和数据探索功能
- **使用示例**: 打开Explore界面, 拖拽创建图表, 调整可视化参数

#### `can_external_metadata`
- **功能**: 外部元数据权限
- **影响**: 控制用户是否能获取数据源的元数据信息
- **缺少时**: 无法看到表的结构信息和字段详情
- **使用示例**: 查看表字段信息, 获取数据类型, 同步表结构

#### `can_slice`
- **功能**: 执行slice操作的权限
- **影响**: 控制用户是否能执行slice操作
- **缺少时**: 无法执行slice操作

### Dashboard (3个权限)

#### `can_copy_dash`
- **功能**: 执行copy_dash操作的权限
- **影响**: 控制用户是否能执行copy_dash操作
- **缺少时**: 无法执行copy_dash操作

#### `can_dashboard`
- **功能**: 执行dashboard操作的权限
- **影响**: 控制用户是否能执行dashboard操作
- **缺少时**: 无法执行dashboard操作

#### `can_save_dash`
- **功能**: 执行save_dash操作的权限
- **影响**: 控制用户是否能执行save_dash操作
- **缺少时**: 无法执行save_dash操作

### Dataset (4个权限)

#### `can_dataset`
- **功能**: 执行dataset操作的权限
- **影响**: 控制用户是否能执行dataset操作
- **缺少时**: 无法执行dataset操作

#### `can_datasource`
- **功能**: 执行datasource操作的权限
- **影响**: 控制用户是否能执行datasource操作
- **缺少时**: 无法执行datasource操作

#### `can_get_column_values`
- **功能**: 获取列值权限
- **影响**: 控制用户是否能查看字段的实际数据值
- **缺少时**: 无法看到字段的实际值，影响过滤器使用和数据理解
- **使用示例**: 查看category字段的所有值, 设置过滤器选项, 数据质量检查

#### `can_samples`
- **功能**: 执行samples操作的权限
- **影响**: 控制用户是否能执行samples操作
- **缺少时**: 无法执行samples操作

### System Admin (3个权限)

#### `can_grant_guest_token`
- **功能**: 执行grant_guest_token操作的权限
- **影响**: 控制用户是否能执行grant_guest_token操作
- **缺少时**: 无法执行grant_guest_token操作

#### `can_update_role`
- **功能**: 更新角色权限
- **影响**: 控制用户是否能管理系统角色和权限
- **缺少时**: 无法进行用户和权限管理
- **使用示例**: 给用户分配Alpha角色, 修改角色权限, 创建自定义角色

#### `can_warm_up_cache`
- **功能**: 缓存预热权限
- **影响**: 控制用户是否能执行缓存预热操作
- **缺少时**: 无法进行缓存优化，可能影响系统性能
- **使用示例**: 预热重要仪表板, 提升访问速度, 系统优化

### Special (3个权限)

#### `muldelete`
- **功能**: 权限: muldelete
- **影响**: 未知影响
- **缺少时**: 未知限制

#### `resetmypassword`
- **功能**: 权限: resetmypassword
- **影响**: 未知影响
- **缺少时**: 未知限制

#### `userinfoedit`
- **功能**: 权限: userinfoedit
- **影响**: 未知影响
- **缺少时**: 未知限制

## 角色权限矩阵

| 权限分类 | Admin | Alpha | Gamma | sql_lab | Public |
|---------|-------|-------|-------|---------|--------|
| CRUD | ✅ | ✅ | ✅ | ✅ | ❌ |
| Global Access | ✅ | ✅ | ❌ | ❌ | ❌ |
| Resource Access | ✅ | ✅ | ❌ | ❌ | ❌ |
| SQL Lab | ✅ | ✅ | ❌ | ✅ | ❌ |
| Other Functions | ✅ | ✅ | ❌ | ❌ | ❌ |
| Chart & Visualization | ✅ | ✅ | ❌ | ❌ | ❌ |
| Dashboard | ✅ | ✅ | ❌ | ❌ | ❌ |
| Dataset | ✅ | ✅ | ❌ | ❌ | ❌ |
| System Admin | ✅ | ❌ | ❌ | ❌ | ❌ |
| Special | ✅ | ✅ | ❌ | ❌ | ❌ |
