# 高级透视表插件使用指南

## 概述

我们已经成功创建了一个全新的高级透视表插件，它具有类似Tableau的功能，包括：

- 多层次分层结构
- 树形视图
- 固定列
- 增强的分组功能
- 混合视图模式
- 高级过滤和搜索

## 插件结构

插件位于：`superset-frontend/plugins/plugin-chart-advanced-pivot-table/`

### 主要文件：

1. **核心组件**
   - `src/AdvancedPivotTableChart.tsx` - 主要图表组件
   - `src/types.ts` - TypeScript类型定义

2. **子组件**
   - `src/components/TreeViewRenderer.tsx` - 树形视图渲染器
   - `src/components/TableViewRenderer.tsx` - 表格视图渲染器  
   - `src/components/HybridViewRenderer.tsx` - 混合视图渲染器
   - `src/components/ToolbarControls.tsx` - 工具栏控件
   - `src/components/HierarchyManager.tsx` - 层次管理器
   - `src/components/PinnedColumnsManager.tsx` - 固定列管理器

3. **插件配置**
   - `src/plugin/index.ts` - 插件主入口
   - `src/plugin/controlPanel.tsx` - 控制面板配置
   - `src/plugin/buildQuery.ts` - 查询构建器
   - `src/plugin/transformProps.ts` - 属性转换器

## 如何使用

### 1. 插件已经注册

插件已经在 `superset-frontend/src/visualizations/presets/MainPreset.js` 中注册，键名为 `'advanced_pivot_table'`。

### 2. 启动Superset

```bash
# 在superset-frontend目录中
npm run dev-server

# 在superset根目录中启动后端
python -m superset run -p 8088 --with-threads --reload --debugger
```

### 3. 创建新图表

1. 在Superset中，点击 "Charts" → "+" 创建新图表
2. 选择数据源
3. 在图表类型中查找 "Advanced Pivot Table"
4. 配置你的数据：
   - **行分组**: 选择要作为行的字段
   - **列分组**: 选择要作为列的字段
   - **指标**: 选择要聚合的数值字段

### 4. 配置高级功能

在控制面板中，你可以配置：

#### 视图选项
- **视图模式**: 选择表格、树形或混合视图
- **层次模式**: 单层次或多层次
- **虚拟滚动**: 启用以提高大数据集性能

#### 表格功能
- **全局搜索**: 启用全局搜索功能
- **列过滤**: 启用列级过滤
- **多列排序**: 启用多列排序

#### 透视选项
- **聚合函数**: 选择Sum、Mean、Count等
- **显示总计**: 显示行/列总计
- **显示小计**: 显示分组小计

#### 格式化选项
- **数值格式**: 配置数值显示格式
- **货币格式**: 配置货币显示
- **日期格式**: 配置日期显示

### 5. 使用交互功能

#### 树形视图
- 点击节点展开/折叠
- 支持多层次导航
- 显示层次线条

#### 固定列
- 使用侧边栏管理固定列
- 支持左侧和右侧固定
- 可调整列宽

#### 搜索和过滤
- 使用全局搜索框
- 列级过滤器
- 实时过滤结果

## 功能特性

### 1. 多视图模式
- **表格视图**: 传统的表格显示
- **树形视图**: 分层数据的树形显示
- **混合视图**: 结合树形导航和详细表格

### 2. 高级层次管理
- 多层次分组
- 可配置的层次深度
- 动态展开/折叠

### 3. 固定列功能
- 左侧/右侧固定列
- 可调整列宽
- 保持滚动时的可见性

### 4. 性能优化
- 虚拟滚动支持大数据集
- 延迟加载
- 智能渲染

### 5. 导出功能
- CSV导出
- Excel导出
- 保持格式化

## 故障排除

### 常见问题

1. **插件未出现在图表类型中**
   - 确保插件已正确注册在MainPreset.js中
   - 检查前端开发服务器是否正在运行
   - 清除浏览器缓存

2. **依赖错误**
   - 运行 `npm install --legacy-peer-deps` 解决依赖冲突
   - 确保所有必需的依赖都已安装

3. **构建错误**
   - 检查TypeScript类型错误
   - 确保所有导入路径正确

### 开发调试

如果需要修改插件：

1. 修改源代码文件
2. 重启开发服务器
3. 刷新浏览器页面
4. 检查浏览器控制台的错误信息

## 下一步

插件现在已经可以在Superset中使用了！你可以：

1. 创建测试图表验证功能
2. 根据需要调整样式和功能
3. 添加更多自定义功能
4. 优化性能

## 支持

如果遇到问题，请检查：
- 浏览器控制台的错误信息
- Superset后端日志
- 插件源代码中的注释和文档 