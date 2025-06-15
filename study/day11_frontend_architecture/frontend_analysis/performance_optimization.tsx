
// 性能优化示例
import React, { memo, useMemo, useCallback, lazy, Suspense } from 'react';
import { debounce } from 'lodash';

// 1. React.memo优化
const ChartComponent = memo<ChartProps>(({ 
  chart, 
  formData, 
  onFilterChange 
}) => {
  const processedData = useMemo(() => {
    return processChartData(chart.data, formData);
  }, [chart.data, formData]);
  
  const debouncedFilterChange = useMemo(
    () => debounce(onFilterChange, 300),
    [onFilterChange]
  );
  
  return (
    <div className="chart-container">
      <ChartRenderer data={processedData} />
    </div>
  );
}, (prevProps, nextProps) => {
  return (
    prevProps.chart.id === nextProps.chart.id &&
    isEqual(prevProps.formData, nextProps.formData)
  );
});

// 2. 懒加载组件
const LazyDashboard = lazy(() => 
  import(
    /* webpackChunkName: "Dashboard" */
    './Dashboard'
  )
);

const LazyExplore = lazy(() =>
  import(
    /* webpackChunkName: "Explore" */
    './Explore'
  )
);

// 3. 代码分割路由
const AppRouter: React.FC = () => (
  <Router>
    <Suspense fallback={<Loading />}>
      <Switch>
        <Route 
          path="/dashboard/:id" 
          component={LazyDashboard} 
        />
        <Route 
          path="/explore" 
          component={LazyExplore} 
        />
      </Switch>
    </Suspense>
  </Router>
);

// 4. 虚拟化长列表
import { FixedSizeList as List } from 'react-window';

const VirtualizedList: React.FC<{ items: any[] }> = ({ items }) => (
  <List
    height={600}
    itemCount={items.length}
    itemSize={50}
    itemData={items}
  >
    {({ index, style, data }) => (
      <div style={style}>
        <ListItem item={data[index]} />
      </div>
    )}
  </List>
);
            