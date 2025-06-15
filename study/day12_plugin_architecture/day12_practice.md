# Day 12: 插件架构实践练习 🛠️

## 练习 1: 分析现有插件结构

### 目标
深入理解 Superset 插件的组织结构和核心组件。

### 步骤

**1. 分析 Pivot Table 插件结构**

```bash
# 导航到 pivot table 插件目录
cd superset-frontend/plugins/plugin-chart-pivot-table

# 查看目录结构
find . -type f -name "*.ts" -o -name "*.tsx" | head -20
```

**2. 理解插件核心文件**

```typescript
// 分析插件入口文件
// src/plugin/index.ts

// 关键要素：
// - ChartMetadata: 定义图表元数据
// - buildQuery: 查询构建逻辑
// - controlPanel: 控制面板配置
// - transformProps: 数据转换逻辑
// - loadChart: 图表组件加载
```

**3. 理解注册机制**

```typescript
// 插件如何注册到系统
class PivotTableChartPlugin extends ChartPlugin {
  register() {
    const key = this.config.key; // 通常是 viz_type
    
    // 注册到各个注册表
    getChartMetadataRegistry().registerValue(key, this.metadata);
    getChartComponentRegistry().registerLoader(key, this.loadChart);
    getChartControlPanelRegistry().registerValue(key, this.controlPanel);
    getChartTransformPropsRegistry().registerLoader(key, this.loadTransformProps);
  }
}
```

---

## 练习 2: 创建简单图表插件

### 目标
从零开始创建一个简单的图表插件。

### 创建 "简单数值展示" 插件

**1. 创建插件目录结构**

```bash
mkdir -p superset-frontend/plugins/plugin-chart-simple-number/src/{plugin,components,types,images}
cd superset-frontend/plugins/plugin-chart-simple-number
```

**2. 创建 package.json**

```json
{
  "name": "@superset-ui/plugin-chart-simple-number",
  "version": "0.1.0",
  "description": "Simple Number Chart Plugin for Superset",
  "main": "lib/index.js",
  "types": "lib/index.d.ts",
  "files": ["lib"],
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch"
  },
  "peerDependencies": {
    "@superset-ui/core": "*",
    "@superset-ui/chart-controls": "*",
    "react": "^16.8.0 || ^17.0.0"
  },
  "devDependencies": {
    "typescript": "^4.0.0"
  }
}
```

**3. 创建类型定义**

```typescript
// src/types/index.ts
export interface SimpleNumberFormData {
  metric: string;
  comparisonType: 'none' | 'previous_period' | 'custom';
  comparisonValue?: number;
  numberFormat: string;
  showTrend: boolean;
  colorScheme: string;
}

export interface SimpleNumberProps {
  width: number;
  height: number;
  data: Array<{ [key: string]: any }>;
  metric: string;
  comparisonType: string;
  comparisonValue?: number;
  numberFormat: string;
  showTrend: boolean;
  colorScheme: string;
}
```

**4. 创建图表组件**

```typescript
// src/components/SimpleNumber.tsx
import React from 'react';
import { styled, getNumberFormatter } from '@superset-ui/core';
import { SimpleNumberProps } from '../types';

const Container = styled.div<{ width: number; height: number }>`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: ${props => props.width}px;
  height: ${props => props.height}px;
  padding: 20px;
  background: ${({ theme }) => theme.colors.grayscale.light5};
  border-radius: 8px;
`;

const MainNumber = styled.div`
  font-size: 48px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary.dark1};
  text-align: center;
  margin-bottom: 10px;
`;

const ComparisonText = styled.div<{ positive: boolean }>`
  font-size: 18px;
  color: ${props => props.positive ? '#28a745' : '#dc3545'};
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 5px;
`;

const MetricLabel = styled.div`
  font-size: 14px;
  color: ${({ theme }) => theme.colors.grayscale.base};
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 10px;
`;

export default function SimpleNumber({
  width,
  height,
  data,
  metric,
  comparisonType,
  comparisonValue,
  numberFormat = '.3~s',
  showTrend = false,
  colorScheme = 'blue',
}: SimpleNumberProps) {
  // 获取主要数值
  const mainValue = data[0]?.[metric] || 0;
  const formatter = getNumberFormatter(numberFormat);
  
  // 计算比较值
  let comparison = null;
  if (comparisonType !== 'none' && comparisonValue !== undefined) {
    const diff = mainValue - comparisonValue;
    const percentChange = comparisonValue !== 0 ? (diff / comparisonValue) * 100 : 0;
    const isPositive = diff >= 0;
    
    comparison = {
      value: diff,
      percent: percentChange,
      isPositive,
    };
  }

  return (
    <Container width={width} height={height}>
      <MainNumber>
        {formatter(mainValue)}
      </MainNumber>
      
      {comparison && (
        <ComparisonText positive={comparison.isPositive}>
          {comparison.isPositive ? '↗' : '↘'}
          {formatter(Math.abs(comparison.value))} ({Math.abs(comparison.percent).toFixed(1)}%)
        </ComparisonText>
      )}
      
      <MetricLabel>
        {metric}
      </MetricLabel>
    </Container>
  );
}
```

**5. 创建控制面板**

```typescript
// src/plugin/controlPanel.ts
import { ControlPanelConfig, sharedControls, validateNonEmpty } from '@superset-ui/chart-controls';
import { t } from '@superset-ui/core';

const controlPanel: ControlPanelConfig = {
  controlPanelSections: [
    {
      label: t('Query'),
      expanded: true,
      controlSetRows: [
        [{
          name: 'metric',
          config: {
            ...sharedControls.metric,
            label: t('Metric'),
            description: t('Select the metric to display'),
            validators: [validateNonEmpty],
          },
        }],
        ['adhoc_filters'],
      ],
    },
    {
      label: t('Options'),
      expanded: true,
      controlSetRows: [
        [{
          name: 'numberFormat',
          config: {
            type: 'SelectControl',
            freeForm: true,
            label: t('Number format'),
            renderTrigger: true,
            default: '.3~s',
            choices: [
              ['.3~s', 'Adaptive (12.3k)'],
              [',.0f', 'Comma (12,345)'],
              ['.1%', 'Percentage (12.3%)'],
              ['$,.0f', 'Currency ($12,345)'],
            ],
            description: t('D3 format syntax: https://github.com/d3/d3-format'),
          },
        }],
        [{
          name: 'comparisonType',
          config: {
            type: 'SelectControl',
            label: t('Comparison'),
            default: 'none',
            choices: [
              ['none', t('None')],
              ['previous_period', t('Previous Period')],
              ['custom', t('Custom Value')],
            ],
            description: t('Compare the metric to another value'),
          },
        }],
        [{
          name: 'comparisonValue',
          config: {
            type: 'TextControl',
            label: t('Comparison Value'),
            isInt: false,
            visibility: ({ controls }) => controls?.comparisonType?.value === 'custom',
            description: t('Value to compare against'),
          },
        }],
        [{
          name: 'showTrend',
          config: {
            type: 'CheckboxControl',
            label: t('Show Trend'),
            default: false,
            description: t('Show trend indicator with comparison'),
          },
        }],
      ],
    },
  ],
};

export default controlPanel;
```

**6. 创建数据转换函数**

```typescript
// src/plugin/transformProps.ts
import { ChartProps } from '@superset-ui/core';
import { SimpleNumberFormData, SimpleNumberProps } from '../types';

export default function transformProps(
  chartProps: ChartProps<SimpleNumberFormData>
): SimpleNumberProps {
  const { width, height, queriesData, formData } = chartProps;
  const { data } = queriesData[0];
  
  const {
    metric,
    comparisonType = 'none',
    comparisonValue,
    numberFormat = '.3~s',
    showTrend = false,
    colorScheme = 'blue',
  } = formData;

  return {
    width,
    height,
    data,
    metric,
    comparisonType,
    comparisonValue: comparisonValue ? Number(comparisonValue) : undefined,
    numberFormat,
    showTrend,
    colorScheme,
  };
}
```

**7. 创建插件主文件**

```typescript
// src/plugin/index.ts
import {
  ChartMetadata,
  ChartPlugin,
  t,
  Behavior,
} from '@superset-ui/core';
import controlPanel from './controlPanel';
import transformProps from './transformProps';
import { SimpleNumberFormData } from '../types';

export default class SimpleNumberChartPlugin extends ChartPlugin<SimpleNumberFormData> {
  constructor() {
    const metadata = new ChartMetadata({
      behaviors: [Behavior.InteractiveChart],
      category: t('KPI'),
      description: t('A simple number display with optional comparison and trend'),
      name: t('Simple Number'),
      tags: [t('Business'), t('KPI'), t('Simple'), t('Number')],
      thumbnail: '/static/assets/images/viz_types/big_number.png',
    });

    super({
      loadChart: () => import('../components/SimpleNumber'),
      metadata,
      transformProps,
      controlPanel,
    });
  }
}
```

**8. 创建入口文件**

```typescript
// src/index.ts
export { default } from './plugin';
export * from './types';
```

---

## 练习 3: 注册和测试插件

### 目标
将创建的插件注册到 Superset 系统中并进行测试。

### 步骤

**1. 修改 MainPreset**

```typescript
// superset-frontend/src/visualizations/presets/MainPreset.js

// 添加导入
import SimpleNumberChartPlugin from '../../../plugins/plugin-chart-simple-number/src';

// 在 plugins 数组中添加
export default class MainPreset extends Preset {
  constructor() {
    super({
      name: 'Legacy charts',
      plugins: [
        // ... 其他插件
        new SimpleNumberChartPlugin().configure({ key: 'simple_number' }),
        // ... 
      ],
    });
  }
}
```

**2. 构建插件**

```bash
cd superset-frontend/plugins/plugin-chart-simple-number
npm run build
```

**3. 启动开发服务器**

```bash
cd superset-frontend
npm run dev-server
```

**4. 测试插件**

1. 登录 Superset
2. 创建新图表
3. 在图表类型选择器中找到 "Simple Number"
4. 配置数据源和指标
5. 测试各种配置选项

---

## 练习 4: 增强插件功能

### 目标
为简单数值插件添加更多高级功能。

### 增强功能清单

**1. 添加动画效果**

```typescript
// 在 SimpleNumber 组件中添加
import { useSpring, animated } from 'react-spring';

const AnimatedNumber = animated(MainNumber);

// 在组件中使用
const animatedValue = useSpring({
  from: { number: 0 },
  to: { number: mainValue },
  config: { tension: 100, friction: 50 },
});

return (
  <Container width={width} height={height}>
    <AnimatedNumber>
      {animatedValue.number.to(n => formatter(n))}
    </AnimatedNumber>
    {/* ... */}
  </Container>
);
```

**2. 添加点击事件处理**

```typescript
const handleClick = useCallback(() => {
  if (onContextMenu) {
    onContextMenu({
      metric,
      value: mainValue,
      filters: selectedFilters,
    });
  }
}, [metric, mainValue, selectedFilters, onContextMenu]);

return (
  <Container 
    width={width} 
    height={height}
    onClick={handleClick}
    style={{ cursor: 'pointer' }}
  >
    {/* ... */}
  </Container>
);
```

**3. 添加主题支持**

```typescript
const Container = styled.div<{ 
  width: number; 
  height: number; 
  theme: any;
  colorScheme: string;
}>`
  /* ... */
  background: ${props => getThemeColor(props.theme, props.colorScheme)};
  border: 2px solid ${props => getBorderColor(props.theme, props.colorScheme)};
`;

function getThemeColor(theme: any, colorScheme: string) {
  const colors = {
    blue: theme.colors.primary.light5,
    green: theme.colors.success.light5,
    red: theme.colors.error.light5,
    orange: theme.colors.warning.light5,
  };
  return colors[colorScheme] || colors.blue;
}
```

**4. 添加加载状态**

```typescript
const SimpleNumber = ({ loading = false, ...props }) => {
  if (loading) {
    return (
      <Container width={props.width} height={props.height}>
        <Skeleton.Input active size="large" />
      </Container>
    );
  }

  return (
    // ... 正常渲染
  );
};
```

---

## 练习 5: 创建增强版 Pivot Table 插件

### 目标
基于现有的 Pivot Table 插件，创建一个具有数据条、热力图、条件格式化等高级功能的增强版本。

### 核心增强功能

**1. 数据条 (Data Bars)**
- 在单元格中显示横向数据条
- 可配置颜色
- 基于列的最大值计算百分比

**2. 热力图 (Heatmap)**
- 根据数值大小为单元格着色
- 多种颜色方案
- 自动计算颜色强度

**3. 条件格式化 (Conditional Formatting)**
- 支持多种条件规则
- 自定义背景色和文字颜色
- 按指标应用规则

**4. 高级交互**
- 可排序的列标题
- 上下文菜单
- 钻取功能
- 交叉过滤

### 实现步骤

**1. 复制并修改现有插件**

```bash
cp -r superset-frontend/plugins/plugin-chart-pivot-table \
      superset-frontend/plugins/plugin-chart-enhanced-pivot-table
```

**2. 更新包信息**

```json
{
  "name": "@superset-ui/plugin-chart-enhanced-pivot-table",
  "description": "Enhanced Pivot Table with advanced visualization features"
}
```

**3. 扩展类型定义**

参考前面提供的 `enhanced_pivot_plugin.tsx` 文件中的类型定义。

**4. 实现增强组件**

参考前面提供的完整实现代码。

**5. 配置控制面板**

添加新的控制选项：
- 启用数据条
- 数据条颜色
- 启用热力图
- 热力图颜色方案
- 条件格式化规则

**6. 注册插件**

```typescript
// 在 MainPreset 中添加
new EnhancedPivotTableChartPlugin().configure({ 
  key: 'enhanced_pivot_table' 
}),
```

---

## 练习 6: 性能优化

### 目标
为插件添加性能优化功能。

### 优化策略

**1. 虚拟化渲染**

```typescript
import { FixedSizeGrid as Grid } from 'react-window';

const VirtualizedPivotTable = ({ data, width, height }) => {
  const Cell = ({ columnIndex, rowIndex, style }) => (
    <div style={style}>
      {/* 渲染单元格内容 */}
    </div>
  );

  return (
    <Grid
      columnCount={columnCount}
      columnWidth={100}
      height={height}
      rowCount={rowCount}
      rowHeight={35}
      width={width}
    >
      {Cell}
    </Grid>
  );
};
```

**2. 数据缓存**

```typescript
import { useMemo } from 'react';

const processedData = useMemo(() => {
  return processLargeDataset(data, groupbyRows, groupbyColumns);
}, [data, groupbyRows, groupbyColumns]);
```

**3. 懒加载**

```typescript
const LazyEnhancedFeatures = lazy(() => import('./EnhancedFeatures'));

const EnhancedPivotTable = (props) => {
  return (
    <div>
      <BasicPivotTable {...props} />
      <Suspense fallback={<Loading />}>
        {props.enableEnhancedFeatures && (
          <LazyEnhancedFeatures {...props} />
        )}
      </Suspense>
    </div>
  );
};
```

---

## 练习总结

通过这些练习，你将学会：

1. **插件结构理解**：掌握 Superset 插件的基本组织结构
2. **简单插件开发**：从零创建一个功能完整的图表插件
3. **插件注册机制**：理解插件如何集成到 Superset 系统
4. **功能增强技巧**：为插件添加动画、交互、主题等高级功能
5. **复杂插件开发**：创建具有多种高级功能的复杂插件
6. **性能优化方法**：应用虚拟化、缓存、懒加载等优化技术

这些练习将帮助你深入理解 Superset 的插件架构，并具备开发高质量自定义插件的能力。 🚀 