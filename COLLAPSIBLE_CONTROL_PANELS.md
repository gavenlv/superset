# Superset Chart Controls 折叠功能

## 概述

这个修改为 Apache Superset 的 Chart 页面添加了折叠功能，让 Data/Customize 标签页可以像 Chart Source 一样折叠起来，提供更好的用户体验和更灵活的界面布局。

## 功能特性

### 1. 折叠/展开控制面板
- 在 Chart Controls 区域添加了一个标题栏，显示 "Chart Controls"
- 点击展开/折叠按钮可以隐藏或显示整个控制面板区域
- 折叠时显示一个侧边栏，点击可以重新展开

### 2. 状态持久化
- 使用 LocalStorage 保存折叠状态
- 用户的选择会在页面刷新后保持

### 3. 视觉一致性
- 折叠按钮的样式与 Chart Source 的折叠按钮保持一致
- 使用相同的图标和交互模式

## 修改的文件

### 1. `superset-frontend/src/explore/components/ControlPanelsContainer.tsx`
- 添加了折叠状态管理
- 添加了标题栏和折叠按钮
- 实现了折叠/展开逻辑
- 添加了相应的样式

### 2. `superset-frontend/src/utils/localStorageHelpers.ts`
- 添加了新的 LocalStorage 键 `IsControlPanelsCollapsed`
- 更新了类型定义

## 使用方法

1. 在 Chart 页面，找到右侧的 "Chart Controls" 标题栏
2. 点击标题栏右侧的展开/折叠按钮
3. 控制面板会折叠成一个窄的侧边栏
4. 点击侧边栏中的按钮可以重新展开控制面板

## 技术实现

### 状态管理
```typescript
const [isControlPanelsCollapsed, setIsControlPanelsCollapsed] = useState(
  getItem(LocalStorageKeys.IsControlPanelsCollapsed, false)
);
```

### 折叠切换函数
```typescript
const toggleControlPanelsCollapse = useCallback(() => {
  const newCollapsedState = !isControlPanelsCollapsed;
  setIsControlPanelsCollapsed(newCollapsedState);
  setItem(LocalStorageKeys.IsControlPanelsCollapsed, newCollapsedState);
}, [isControlPanelsCollapsed]);
```

### 条件渲染
```typescript
{!isControlPanelsCollapsed ? (
  // 显示完整的控制面板
  <ControlPanelsTabs>...</ControlPanelsTabs>
) : (
  // 显示折叠的侧边栏
  <div className="sidebar">...</div>
)}
```

## 样式特性

- 标题栏使用与 Chart Source 相同的样式
- 折叠按钮有悬停效果
- 侧边栏在折叠状态下显示为窄条
- 所有交互都有平滑的过渡动画

## 兼容性

- 完全向后兼容
- 不影响现有的控制面板功能
- 默认状态为展开（与原有行为一致）

## 测试

添加了相应的单元测试来验证：
- 折叠功能是否正确渲染
- 点击事件是否正确触发
- 状态切换是否正常工作

## 构建状态

✅ 代码编译通过  
✅ 类型检查通过  
✅ 样式正确应用  
✅ 功能测试通过  

这个修改为 Superset 用户提供了更灵活的界面布局选项，特别是在需要更多空间查看图表时非常有用。
