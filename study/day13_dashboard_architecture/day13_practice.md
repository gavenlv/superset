# Day 13: 仪表板架构实践练习 🏗️

本文档提供了一系列循序渐进的练习，帮助你深入理解和掌握 Superset 仪表板架构的核心概念和实现技术。

## 📋 目录

1. [基础练习：布局系统理解](#1-基础练习布局系统理解)
2. [中级练习：组件开发](#2-中级练习组件开发)
3. [高级练习：交互功能实现](#3-高级练习交互功能实现)
4. [专家练习：性能优化](#4-专家练习性能优化)
5. [项目练习：完整仪表板开发](#5-项目练习完整仪表板开发)

---

## 1. 基础练习：布局系统理解

### 练习 1.1：分析现有仪表板结构

**目标**：理解 Superset 仪表板的组件层次结构。

**任务**：
1. 在 Superset 中创建一个新的仪表板
2. 添加 3-4 个不同类型的图表
3. 使用浏览器开发者工具检查 DOM 结构
4. 分析组件的层次关系

**分析要点**：
```javascript
// 在浏览器控制台中运行，分析仪表板结构
function analyzeDashboardStructure() {
  const dashboardGrid = document.querySelector('.dashboard-grid');
  const components = dashboardGrid.querySelectorAll('.dashboard-component');
  
  console.log('仪表板结构分析:');
  console.log(`- 网格容器: ${dashboardGrid ? '存在' : '不存在'}`);
  console.log(`- 组件数量: ${components.length}`);
  
  components.forEach((component, index) => {
    const type = component.dataset.testId || component.className;
    const size = {
      width: component.offsetWidth,
      height: component.offsetHeight
    };
    console.log(`  组件 ${index + 1}: ${type}, 尺寸: ${size.width}x${size.height}`);
  });
}

analyzeDashboardStructure();
```

**预期输出**：
- 组件层次结构图
- 各组件的尺寸和位置信息
- 布局计算逻辑的理解

### 练习 1.2：网格系统实验

**目标**：理解网格系统的工作原理。

**任务**：
1. 修改 `GRID_COLUMN_COUNT` 常量
2. 观察布局变化
3. 测试不同的 gutter 大小设置

**代码修改**：
```javascript
// 在 superset-frontend/src/dashboard/util/constants.js 中实验
export const GRID_COLUMN_COUNT = 16; // 原来是 12
export const GRID_GUTTER_SIZE = 20;  // 原来是 16

// 观察以下计算逻辑的变化
const columnPlusGutterWidth = (width + GRID_GUTTER_SIZE) / GRID_COLUMN_COUNT;
const columnWidth = columnPlusGutterWidth - GRID_GUTTER_SIZE;
```

**观察记录**：
- 列数变化对组件布局的影响
- Gutter 大小对视觉效果的影响
- 响应式行为的变化

### 练习 1.3：响应式断点测试

**目标**：理解响应式布局的实现机制。

**任务**：
1. 在不同屏幕尺寸下测试仪表板
2. 记录断点切换时的布局变化
3. 自定义断点配置

**测试代码**：
```javascript
// 测试响应式断点
function testBreakpoints() {
  const breakpoints = {
    lg: 1200,
    md: 996,
    sm: 768,
    xs: 480,
    xxs: 0,
  };
  
  const currentWidth = window.innerWidth;
  let activeBreakpoint = 'xxs';
  
  for (const [bp, minWidth] of Object.entries(breakpoints).reverse()) {
    if (currentWidth >= minWidth) {
      activeBreakpoint = bp;
      break;
    }
  }
  
  console.log(`当前屏幕宽度: ${currentWidth}px`);
  console.log(`激活断点: ${activeBreakpoint}`);
  
  // 模拟不同断点
  Object.keys(breakpoints).forEach(bp => {
    const width = breakpoints[bp] + 50;
    console.log(`${bp} 断点 (${width}px) 下的列数:`, getCols(bp));
  });
}

function getCols(breakpoint) {
  const cols = {
    lg: 12, md: 10, sm: 6, xs: 4, xxs: 2,
  };
  return cols[breakpoint] || 2;
}

testBreakpoints();
```

---

## 2. 中级练习：组件开发

### 练习 2.1：创建自定义仪表板组件

**目标**：开发一个可重用的仪表板组件。

**任务**：创建一个"数据卡片"组件，显示关键指标。

**实现步骤**：

1. **创建组件文件**：
```typescript
// superset-frontend/src/dashboard/components/gridComponents/DataCard.tsx
import React, { memo } from 'react';
import { styled, css, useTheme } from '@superset-ui/core';
import { componentShape } from 'src/dashboard/util/propShapes';

interface DataCardProps {
  id: string;
  component: any;
  parentId: string;
  index: number;
  depth: number;
  editMode: boolean;
  // ... 其他 props
}

const DataCardContainer = styled.div`
  ${({ theme }) => css`
    background: linear-gradient(135deg, ${theme.colors.primary.light4}, ${theme.colors.primary.light3});
    border-radius: ${theme.borderRadius * 2}px;
    padding: ${theme.gridUnit * 4}px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    box-shadow: ${theme.boxShadow};
    
    .data-value {
      font-size: 3rem;
      font-weight: bold;
      color: ${theme.colors.primary.dark1};
      margin-bottom: ${theme.gridUnit * 2}px;
    }
    
    .data-label {
      font-size: 1.2rem;
      color: ${theme.colors.grayscale.dark1};
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    
    .data-change {
      font-size: 0.9rem;
      margin-top: ${theme.gridUnit}px;
      
      &.positive {
        color: ${theme.colors.success.base};
      }
      
      &.negative {
        color: ${theme.colors.error.base};
      }
    }
  `}
`;

const DataCard: React.FC<DataCardProps> = memo(({
  id,
  component,
  editMode,
  // ... 其他 props
}) => {
  const theme = useTheme();
  const { value, label, change, changeType } = component.meta;

  return (
    <DataCardContainer>
      <div className="data-value">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div className="data-label">{label}</div>
      {change && (
        <div className={`data-change ${changeType}`}>
          {changeType === 'positive' ? '↗' : '↘'} {change}
        </div>
      )}
    </DataCardContainer>
  );
});

export default DataCard;
```

2. **注册组件类型**：
```javascript
// superset-frontend/src/dashboard/util/componentTypes.js
export const DATA_CARD_TYPE = 'DATA_CARD';

// 添加到组件映射中
export const componentTypes = {
  // ... 现有类型
  [DATA_CARD_TYPE]: DATA_CARD_TYPE,
};
```

3. **添加到组件工厂**：
```javascript
// superset-frontend/src/dashboard/containers/DashboardComponent.jsx
import DataCard from '../components/gridComponents/DataCard';
import { DATA_CARD_TYPE } from '../util/componentTypes';

// 在组件映射中添加
const componentLookup = {
  // ... 现有组件
  [DATA_CARD_TYPE]: DataCard,
};
```

### 练习 2.2：实现可调整大小的组件

**目标**：为自定义组件添加调整大小功能。

**任务**：扩展上面的 DataCard 组件，使其支持拖拽调整大小。

**实现代码**：
```typescript
import ResizableContainer from 'src/dashboard/components/resizable/ResizableContainer';

const DataCardWithResize: React.FC<DataCardProps> = ({
  // ... props
  onResizeStart,
  onResize,
  onResizeStop,
  columnWidth,
  availableColumnCount,
}) => {
  const widthMultiple = component.meta.width || 4;
  const heightMultiple = component.meta.height || 6;

  return (
    <ResizableContainer
      id={component.id}
      adjustableWidth={true}
      adjustableHeight={true}
      widthStep={columnWidth}
      heightStep={24} // GRID_BASE_UNIT
      widthMultiple={widthMultiple}
      heightMultiple={heightMultiple}
      minWidthMultiple={2}
      minHeightMultiple={4}
      maxWidthMultiple={availableColumnCount}
      onResizeStart={onResizeStart}
      onResize={onResize}
      onResizeStop={onResizeStop}
      editMode={editMode}
    >
      <DataCard {...props} />
    </ResizableContainer>
  );
};
```

### 练习 2.3：添加拖拽功能

**目标**：为组件添加拖拽移动功能。

**实现步骤**：
```typescript
import { Draggable } from 'src/dashboard/components/dnd/DragDroppable';

const DraggableDataCard: React.FC<DataCardProps> = (props) => {
  return (
    <Draggable component={props.component} editMode={props.editMode}>
      {({ dragSourceRef, isDragging }) => (
        <div 
          ref={dragSourceRef}
          style={{ opacity: isDragging ? 0.5 : 1 }}
        >
          <DataCardWithResize {...props} />
        </div>
      )}
    </Draggable>
  );
};
```

---

## 3. 高级练习：交互功能实现

### 练习 3.1：实现 Cross-Filtering

**目标**：在自定义组件中实现交叉过滤功能。

**任务**：创建一个可以触发和响应交叉过滤的图表组件。

**实现代码**：
```typescript
// InteractiveChart.tsx
import { useDispatch, useSelector } from 'react-redux';
import { updateDataMask } from 'src/dataMask/actions';
import { DataMask, FilterState } from '@superset-ui/core';

interface InteractiveChartProps {
  chartId: number;
  onCrossFilter?: (dataMask: DataMask) => void;
}

const InteractiveChart: React.FC<InteractiveChartProps> = ({
  chartId,
  onCrossFilter,
}) => {
  const dispatch = useDispatch();
  const dataMask = useSelector(state => state.dataMask[chartId]);

  const handleDataPointClick = useCallback((dataPoint: any) => {
    const newDataMask: DataMask = {
      extraFormData: {
        filters: [{
          col: dataPoint.column,
          op: 'IN',
          val: [dataPoint.value],
        }],
      },
      filterState: {
        value: [dataPoint.value],
        selectedValues: [dataPoint.value],
      },
    };

    // 更新 Redux store
    dispatch(updateDataMask(chartId, newDataMask));
    
    // 触发回调
    onCrossFilter?.(newDataMask);
  }, [chartId, dispatch, onCrossFilter]);

  const handleClearFilter = useCallback(() => {
    const emptyDataMask: DataMask = {
      extraFormData: { filters: [] },
      filterState: { value: null, selectedValues: null },
    };

    dispatch(updateDataMask(chartId, emptyDataMask));
    onCrossFilter?.(emptyDataMask);
  }, [chartId, dispatch, onCrossFilter]);

  return (
    <div className="interactive-chart">
      {/* 图表内容 */}
      <div onClick={handleDataPointClick}>
        {/* 可点击的数据点 */}
      </div>
      
      {/* 清除过滤器按钮 */}
      {dataMask?.filterState?.value && (
        <button onClick={handleClearFilter}>
          Clear Filter
        </button>
      )}
    </div>
  );
};
```

### 练习 3.2：实现钻取功能

**目标**：添加数据钻取功能。

**实现思路**：
```typescript
interface DrilldownConfig {
  levels: string[];
  currentLevel: number;
  maxLevel: number;
}

const DrilldownChart: React.FC<{
  drilldownConfig: DrilldownConfig;
  onDrilldown: (level: number, filters: any[]) => void;
}> = ({ drilldownConfig, onDrilldown }) => {
  const [currentPath, setCurrentPath] = useState<string[]>([]);

  const handleDrillDown = (value: string) => {
    const newPath = [...currentPath, value];
    setCurrentPath(newPath);
    
    const filters = newPath.map((pathValue, index) => ({
      col: drilldownConfig.levels[index],
      op: 'EQUALS',
      val: pathValue,
    }));
    
    onDrilldown(newPath.length, filters);
  };

  const handleDrillUp = () => {
    const newPath = currentPath.slice(0, -1);
    setCurrentPath(newPath);
    
    const filters = newPath.map((pathValue, index) => ({
      col: drilldownConfig.levels[index],
      op: 'EQUALS', 
      val: pathValue,
    }));
    
    onDrilldown(newPath.length, filters);
  };

  return (
    <div className="drilldown-chart">
      {/* 面包屑导航 */}
      <div className="breadcrumb">
        {currentPath.map((value, index) => (
          <span key={index}>
            {index > 0 && ' > '}
            <button onClick={() => {
              const newPath = currentPath.slice(0, index + 1);
              setCurrentPath(newPath);
            }}>
              {value}
            </button>
          </span>
        ))}
      </div>
      
      {/* 图表内容 */}
      <div className="chart-content">
        {/* 渲染当前层级的数据 */}
      </div>
    </div>
  );
};
```

### 练习 3.3：实现实时数据更新

**目标**：添加实时数据更新功能。

**实现方案**：
```typescript
import { useEffect, useRef } from 'react';

interface RealTimeChartProps {
  chartId: number;
  updateInterval: number; // 秒
  enableRealTime: boolean;
}

const RealTimeChart: React.FC<RealTimeChartProps> = ({
  chartId,
  updateInterval = 30,
  enableRealTime,
}) => {
  const intervalRef = useRef<NodeJS.Timeout>();
  const dispatch = useDispatch();

  useEffect(() => {
    if (!enableRealTime) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      return;
    }

    const refreshData = () => {
      dispatch({
        type: 'REFRESH_CHART',
        payload: { chartId, force: true },
      });
    };

    intervalRef.current = setInterval(refreshData, updateInterval * 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [chartId, updateInterval, enableRealTime, dispatch]);

  return (
    <div className="realtime-chart">
      <div className="realtime-indicator">
        {enableRealTime && (
          <span className="status-indicator active">
            🔴 Live
          </span>
        )}
      </div>
      
      {/* 图表内容 */}
    </div>
  );
};
```

---

## 4. 专家练习：性能优化

### 练习 4.1：组件虚拟化

**目标**：实现大型仪表板的虚拟化渲染。

**任务**：创建一个虚拟化的组件容器，只渲染可见区域的组件。

**实现代码**：
```typescript
import { FixedSizeList, VariableSizeList } from 'react-window';
import { useState, useEffect, useCallback } from 'react';

interface VirtualizedDashboardProps {
  components: DashboardComponent[];
  containerHeight: number;
  itemHeight?: number;
}

const VirtualizedDashboard: React.FC<VirtualizedDashboardProps> = ({
  components,
  containerHeight,
  itemHeight = 300,
}) => {
  const [visibleComponents, setVisibleComponents] = useState<Set<number>>(new Set());

  const Row = useCallback(({ index, style }) => {
    const component = components[index];
    const isVisible = visibleComponents.has(index);

    useEffect(() => {
      // 标记组件为可见
      setVisibleComponents(prev => new Set(prev).add(index));
      
      return () => {
        // 清理不可见组件
        setVisibleComponents(prev => {
          const newSet = new Set(prev);
          newSet.delete(index);
          return newSet;
        });
      };
    }, [index]);

    return (
      <div style={style}>
        {isVisible ? (
          <DashboardComponent
            id={component.id}
            component={component}
            // ... 其他 props
          />
        ) : (
          <div className="component-placeholder">
            Loading...
          </div>
        )}
      </div>
    );
  }, [components, visibleComponents]);

  return (
    <FixedSizeList
      height={containerHeight}
      itemCount={components.length}
      itemSize={itemHeight}
      overscanCount={2} // 预渲染前后2个组件
    >
      {Row}
    </FixedSizeList>
  );
};
```

### 练习 4.2：缓存策略实现

**目标**：实现智能缓存策略以提高性能。

**实现方案**：
```typescript
import { useMemo, useRef } from 'react';
import { LRUCache } from 'lru-cache';

// 创建缓存实例
const componentCache = new LRUCache<string, React.ReactElement>({
  max: 100, // 最多缓存100个组件
  ttl: 1000 * 60 * 5, // 5分钟过期
});

const renderCache = new LRUCache<string, any>({
  max: 500,
  ttl: 1000 * 60 * 10, // 10分钟过期
});

interface CachedDashboardComponentProps {
  component: DashboardComponent;
  cacheKey: string;
  dependencies: any[];
}

const CachedDashboardComponent: React.FC<CachedDashboardComponentProps> = ({
  component,
  cacheKey,
  dependencies,
}) => {
  const previousDeps = useRef(dependencies);
  
  const renderedComponent = useMemo(() => {
    // 检查依赖是否改变
    const depsChanged = !dependencies.every((dep, index) => 
      dep === previousDeps.current[index]
    );
    
    if (!depsChanged) {
      const cached = componentCache.get(cacheKey);
      if (cached) {
        console.log(`缓存命中: ${cacheKey}`);
        return cached;
      }
    }
    
    console.log(`重新渲染: ${cacheKey}`);
    
    // 渲染新组件
    const newComponent = (
      <DashboardComponent
        key={component.id}
        component={component}
        // ... 其他 props
      />
    );
    
    // 存入缓存
    componentCache.set(cacheKey, newComponent);
    previousDeps.current = dependencies;
    
    return newComponent;
  }, [component, cacheKey, dependencies]);

  return renderedComponent;
};

// 使用示例
const OptimizedDashboard: React.FC = () => {
  const components = useSelector(state => state.dashboardLayout.present);
  
  return (
    <div className="optimized-dashboard">
      {Object.values(components).map(component => {
        const cacheKey = `${component.id}-${component.meta?.chartId}`;
        const dependencies = [
          component.meta,
          component.children,
          // 其他影响渲染的依赖
        ];
        
        return (
          <CachedDashboardComponent
            key={component.id}
            component={component}
            cacheKey={cacheKey}
            dependencies={dependencies}
          />
        );
      })}
    </div>
  );
};
```

### 练习 4.3：防抖和节流优化

**目标**：对频繁触发的操作进行防抖和节流处理。

**实现方案**：
```typescript
import { useMemo, useCallback } from 'react';
import { debounce, throttle } from 'lodash';

const OptimizedLayoutEngine: React.FC = () => {
  const dispatch = useDispatch();

  // 防抖布局更新
  const debouncedLayoutUpdate = useMemo(
    () => debounce((layout: any[]) => {
      dispatch({
        type: 'UPDATE_DASHBOARD_LAYOUT',
        payload: layout,
      });
    }, 300),
    [dispatch]
  );

  // 节流滚动处理
  const throttledScrollHandler = useMemo(
    () => throttle((scrollTop: number) => {
      // 处理滚动事件，如懒加载
      console.log('Scroll position:', scrollTop);
    }, 100),
    []
  );

  // 防抖搜索
  const debouncedSearch = useMemo(
    () => debounce((query: string) => {
      dispatch({
        type: 'SEARCH_COMPONENTS',
        payload: query,
      });
    }, 500),
    [dispatch]
  );

  const handleLayoutChange = useCallback((newLayout: any[]) => {
    debouncedLayoutUpdate(newLayout);
  }, [debouncedLayoutUpdate]);

  const handleScroll = useCallback((event: React.UIEvent) => {
    const scrollTop = event.currentTarget.scrollTop;
    throttledScrollHandler(scrollTop);
  }, [throttledScrollHandler]);

  return (
    <div className="optimized-layout-engine" onScroll={handleScroll}>
      {/* 布局内容 */}
    </div>
  );
};
```

---

## 5. 项目练习：完整仪表板开发

### 项目 5.1：销售数据仪表板

**项目描述**：创建一个完整的销售数据仪表板，包含多种图表类型、过滤器和交互功能。

**需求规格**：

1. **布局要求**：
   - 顶部：标题和关键指标卡片
   - 左侧：过滤器面板
   - 主区域：图表展示区
   - 底部：详细数据表格

2. **功能要求**：
   - 时间范围选择器
   - 地区和产品分类过滤器
   - 图表间的交叉过滤
   - 数据钻取功能
   - 导出功能

3. **图表类型**：
   - 销售趋势线图
   - 产品销量柱状图
   - 地区分布饼图
   - 销售排行榜

**实现步骤**：

1. **创建基础布局**：
```typescript
// SalesDashboard.tsx
import React, { useState, useCallback } from 'react';
import { Layout } from 'react-grid-layout';

const SalesDashboard: React.FC = () => {
  const [layout, setLayout] = useState<Layout[]>([
    // 标题区域
    { i: 'header', x: 0, y: 0, w: 12, h: 2, static: true },
    // 关键指标
    { i: 'kpi-1', x: 0, y: 2, w: 3, h: 4 },
    { i: 'kpi-2', x: 3, y: 2, w: 3, h: 4 },
    { i: 'kpi-3', x: 6, y: 2, w: 3, h: 4 },
    { i: 'kpi-4', x: 9, y: 2, w: 3, h: 4 },
    // 主要图表
    { i: 'trend-chart', x: 0, y: 6, w: 8, h: 8 },
    { i: 'category-chart', x: 8, y: 6, w: 4, h: 8 },
    // 详细图表
    { i: 'region-chart', x: 0, y: 14, w: 6, h: 6 },
    { i: 'ranking-chart', x: 6, y: 14, w: 6, h: 6 },
  ]);

  const [filters, setFilters] = useState({
    dateRange: ['2023-01-01', '2023-12-31'],
    regions: [],
    categories: [],
  });

  return (
    <div className="sales-dashboard">
      <FilterPanel 
        filters={filters}
        onFilterChange={setFilters}
      />
      
      <GridLayout
        layout={layout}
        onLayoutChange={setLayout}
      >
        <HeaderComponent key="header" />
        <KPICard key="kpi-1" metric="total-sales" filters={filters} />
        <KPICard key="kpi-2" metric="total-orders" filters={filters} />
        <KPICard key="kpi-3" metric="avg-order-value" filters={filters} />
        <KPICard key="kpi-4" metric="growth-rate" filters={filters} />
        
        <TrendChart key="trend-chart" filters={filters} />
        <CategoryChart key="category-chart" filters={filters} />
        <RegionChart key="region-chart" filters={filters} />
        <RankingChart key="ranking-chart" filters={filters} />
      </GridLayout>
    </div>
  );
};
```

2. **实现关键指标卡片**：
```typescript
// KPICard.tsx
interface KPICardProps {
  metric: string;
  filters: any;
  onCrossFilter?: (filter: any) => void;
}

const KPICard: React.FC<KPICardProps> = ({ metric, filters }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKPIData(metric, filters)
      .then(setData)
      .finally(() => setLoading(false));
  }, [metric, filters]);

  if (loading) return <LoadingSpinner />;

  return (
    <Card className="kpi-card">
      <div className="kpi-value">
        {formatValue(data.value, data.format)}
      </div>
      <div className="kpi-label">{data.label}</div>
      <div className={`kpi-change ${data.changeType}`}>
        {data.change > 0 ? '↗' : '↘'} {Math.abs(data.change)}%
      </div>
    </Card>
  );
};
```

3. **实现图表组件**：
```typescript
// TrendChart.tsx
import { Line } from '@ant-design/plots';

const TrendChart: React.FC<{ filters: any }> = ({ filters }) => {
  const [data, setData] = useState([]);

  const config = {
    data,
    xField: 'date',
    yField: 'sales',
    seriesField: 'category',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    interactions: [
      {
        type: 'brush-x',
        cfg: {
          showEnable: [
            { trigger: 'plot:mouseenter', action: 'cursor:crosshair' },
            { trigger: 'mask:mouseenter', action: 'cursor:move' },
          ],
        },
      },
    ],
  };

  const handleBrushEnd = useCallback((evt: any) => {
    const { minX, maxX } = evt.view.getCoordinate().convert(evt);
    // 实现时间范围过滤
    onCrossFilter?.({
      type: 'date-range',
      value: [minX, maxX],
    });
  }, []);

  return (
    <Card title="销售趋势" extra={<ExportButton data={data} />}>
      <Line {...config} onBrushEnd={handleBrushEnd} />
    </Card>
  );
};
```

### 项目 5.2：实时监控大屏

**项目描述**：创建一个适合大屏显示的实时监控仪表板。

**技术要求**：
- 全屏显示适配
- 实时数据更新
- 告警通知系统
- 自动轮播功能

**关键实现**：

1. **全屏适配**：
```typescript
// FullScreenDashboard.tsx
const FullScreenDashboard: React.FC = () => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoRotate, setAutoRotate] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const enterFullscreen = async () => {
    try {
      await document.documentElement.requestFullscreen();
    } catch (error) {
      console.error('无法进入全屏模式:', error);
    }
  };

  return (
    <div className={`fullscreen-dashboard ${isFullscreen ? 'fullscreen' : ''}`}>
      <ControlBar>
        <button onClick={enterFullscreen}>全屏</button>
        <button onClick={() => setAutoRotate(!autoRotate)}>
          自动轮播: {autoRotate ? '开' : '关'}
        </button>
      </ControlBar>
      
      <DashboardContent>
        {/* 大屏内容 */}
      </DashboardContent>
    </div>
  );
};
```

2. **实时数据更新**：
```typescript
// RealTimeDataProvider.tsx
import { io, Socket } from 'socket.io-client';

const RealTimeDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  useEffect(() => {
    const newSocket = io(process.env.REACT_APP_WEBSOCKET_URL);
    
    newSocket.on('connect', () => {
      setConnectionStatus('connected');
      console.log('WebSocket 连接成功');
    });
    
    newSocket.on('disconnect', () => {
      setConnectionStatus('disconnected');
      console.log('WebSocket 连接断开');
    });
    
    newSocket.on('data-update', (data) => {
      // 分发数据更新到相关组件
      dispatch({
        type: 'UPDATE_REALTIME_DATA',
        payload: data,
      });
    });

    setSocket(newSocket);

    return () => newSocket.close();
  }, []);

  return (
    <WebSocketContext.Provider value={{ socket, connectionStatus }}>
      {children}
    </WebSocketContext.Provider>
  );
};
```

3. **告警系统**：
```typescript
// AlertSystem.tsx
interface Alert {
  id: string;
  type: 'warning' | 'error' | 'info';
  message: string;
  timestamp: Date;
  acknowledged: boolean;
}

const AlertSystem: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [showAlerts, setShowAlerts] = useState(false);

  const addAlert = useCallback((alert: Omit<Alert, 'id' | 'timestamp' | 'acknowledged'>) => {
    const newAlert: Alert = {
      ...alert,
      id: uuid(),
      timestamp: new Date(),
      acknowledged: false,
    };
    
    setAlerts(prev => [newAlert, ...prev]);
    
    // 显示通知
    if (alert.type === 'error') {
      notification.error({
        message: '系统告警',
        description: alert.message,
        duration: 0, // 不自动关闭
      });
    }
  }, []);

  return (
    <div className="alert-system">
      <AlertIndicator 
        count={alerts.filter(a => !a.acknowledged).length}
        onClick={() => setShowAlerts(true)}
      />
      
      <AlertModal
        visible={showAlerts}
        alerts={alerts}
        onClose={() => setShowAlerts(false)}
        onAcknowledge={(alertId) => {
          setAlerts(prev => 
            prev.map(alert => 
              alert.id === alertId 
                ? { ...alert, acknowledged: true }
                : alert
            )
          );
        }}
      />
    </div>
  );
};
```

## 📊 练习总结

通过这些练习，你应该掌握了：

### 基础技能
- ✅ 理解仪表板组件层次结构
- ✅ 掌握网格布局系统
- ✅ 实现响应式设计

### 中级技能
- ✅ 开发自定义仪表板组件
- ✅ 实现拖拽和调整大小功能
- ✅ 集成组件到仪表板系统

### 高级技能
- ✅ 实现交叉过滤和钻取功能
- ✅ 添加实时数据更新
- ✅ 优化性能和用户体验

### 专家技能
- ✅ 组件虚拟化和缓存策略
- ✅ 防抖节流优化
- ✅ 大型项目架构设计

## 🎯 下一步建议

1. **深入源码学习**：研究 Superset 的更多高级功能实现
2. **性能测试**：在大数据量下测试仪表板性能
3. **用户体验优化**：关注可访问性和交互设计
4. **生产环境部署**：学习仪表板的部署和监控

继续探索 Superset 的更多可能性，创建更加强大和用户友好的数据可视化解决方案！ 