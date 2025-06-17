/**
 * Advanced Dashboard Demo - 高级仪表板组件实现演示
 * 
 * 这个文件展示了如何创建一个功能丰富的仪表板组件，
 * 包括拖拽布局、实时过滤、组件协作等高级功能。
 */

import React, {
    useState,
    useCallback,
    useMemo,
    useEffect,
    useRef
} from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
    css,
    styled,
    useTheme,
    DataMask,
    FilterState,
    ChartConfiguration,
} from '@superset-ui/core';
import { Layout, Responsive, WidthProvider } from 'react-grid-layout';
import { debounce } from 'lodash';

// 组件导入
import ChartRenderer from './components/ChartRenderer';
import FilterPanel from './components/FilterPanel';
import TabsContainer from './components/TabsContainer';
import ToolbarComponent from './components/ToolbarComponent';
import ResizeHandle from './components/ResizeHandle';

// 类型定义
interface DashboardComponent {
    id: string;
    type: 'chart' | 'filter' | 'text' | 'tabs' | 'divider';
    title?: string;
    config: Record<string, any>;
    meta: {
        width: number;
        height: number;
        chartId?: number;
        formData?: Record<string, any>;
    };
}

interface DashboardLayout extends Layout {
    component: DashboardComponent;
    children?: string[];
    isResizable?: boolean;
    isDraggable?: boolean;
}

interface AdvancedDashboardProps {
    dashboardId: string;
    initialLayout: DashboardLayout[];
    editMode?: boolean;
    filterBarOrientation?: 'horizontal' | 'vertical';
    enableCrossFilters?: boolean;
    enableRealTimeUpdates?: boolean;
    theme?: 'light' | 'dark';
    onLayoutChange?: (layout: DashboardLayout[]) => void;
    onFilterChange?: (filterId: string, filterState: FilterState) => void;
}

// 样式定义
const DashboardContainer = styled.div<{
    editMode: boolean;
    filterBarOrientation: string;
}>`
  ${({ theme, editMode, filterBarOrientation }) => css`
    display: flex;
    flex-direction: ${filterBarOrientation === 'horizontal' ? 'column' : 'row'};
    height: 100vh;
    background-color: ${theme.colors.grayscale.light5};
    
    .dashboard-content {
      flex: 1;
      position: relative;
      overflow: auto;
      padding: ${theme.gridUnit * 4}px;
      
      ${editMode && `
        padding-right: ${theme.gridUnit * 20}px;
      `}
    }
    
    .react-grid-layout {
      position: relative;
    }
    
    .react-grid-item {
      background: ${theme.colors.grayscale.light4};
      border-radius: ${theme.borderRadius}px;
      box-shadow: ${theme.boxShadow};
      transition: all 0.2s ease;
      
      &.react-grid-item--editing {
        border: 2px dashed ${theme.colors.primary.base};
      }
      
      &:hover {
        box-shadow: ${theme.boxShadowHover};
      }
    }
    
    .react-grid-placeholder {
      background: ${theme.colors.primary.light3};
      border: 2px dashed ${theme.colors.primary.base};
      border-radius: ${theme.borderRadius}px;
      opacity: 0.7;
    }
  `}
`;

const FilterBar = styled.div<{ orientation: string; width?: number }>`
  ${({ theme, orientation, width = 300 }) => css`
    background: ${theme.colors.grayscale.light4};
    border-right: ${orientation === 'vertical' ? `1px solid ${theme.colors.grayscale.light2}` : 'none'};
    border-bottom: ${orientation === 'horizontal' ? `1px solid ${theme.colors.grayscale.light2}` : 'none'};
    
    ${orientation === 'vertical' ? `
      width: ${width}px;
      min-width: 250px;
      max-width: 400px;
      height: 100%;
      overflow-y: auto;
    ` : `
      width: 100%;
      height: 80px;
      overflow-x: auto;
      display: flex;
      align-items: center;
      padding: 0 ${theme.gridUnit * 4}px;
    `}
  `}
`;

const EditingSidebar = styled.div`
  ${({ theme }) => css`
    position: fixed;
    right: 0;
    top: 0;
    bottom: 0;
    width: 320px;
    background: ${theme.colors.grayscale.light4};
    border-left: 1px solid ${theme.colors.grayscale.light2};
    z-index: 1000;
    overflow-y: auto;
    padding: ${theme.gridUnit * 4}px;
    
    .component-library {
      margin-bottom: ${theme.gridUnit * 6}px;
      
      h3 {
        margin-bottom: ${theme.gridUnit * 3}px;
        color: ${theme.colors.grayscale.dark1};
      }
      
      .component-item {
        display: flex;
        align-items: center;
        padding: ${theme.gridUnit * 2}px;
        margin-bottom: ${theme.gridUnit * 2}px;
        background: ${theme.colors.grayscale.light5};
        border-radius: ${theme.borderRadius}px;
        cursor: grab;
        
        &:hover {
          background: ${theme.colors.primary.light4};
        }
        
        &:active {
          cursor: grabbing;
        }
      }
    }
  `}
`;

const ResponsiveGridLayout = WidthProvider(Responsive);

// 主组件
const AdvancedDashboard: React.FC<AdvancedDashboardProps> = ({
    dashboardId,
    initialLayout,
    editMode = false,
    filterBarOrientation = 'vertical',
    enableCrossFilters = true,
    enableRealTimeUpdates = false,
    theme = 'light',
    onLayoutChange,
    onFilterChange,
}) => {
    const dispatch = useDispatch();
    const themeConfig = useTheme();

    // 状态管理
    const [layout, setLayout] = useState<DashboardLayout[]>(initialLayout);
    const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
    const [filters, setFilters] = useState<Record<string, FilterState>>({});
    const [crossFilters, setCrossFilters] = useState<Record<string, DataMask>>({});
    const [isResizing, setIsResizing] = useState(false);
    const [currentBreakpoint, setCurrentBreakpoint] = useState('lg');

    // Refs
    const layoutChangeTimerRef = useRef<NodeJS.Timeout>();
    const containerRef = useRef<HTMLDivElement>(null);

    // Redux 状态
    const dashboardState = useSelector((state: any) => state.dashboard);
    const chartsData = useSelector((state: any) => state.charts);

    // 断点配置
    const breakpoints = useMemo(() => ({
        lg: 1200,
        md: 996,
        sm: 768,
        xs: 480,
        xxs: 0,
    }), []);

    const cols = useMemo(() => ({
        lg: 12,
        md: 10,
        sm: 6,
        xs: 4,
        xxs: 2,
    }), []);

    // 防抖的布局变更处理
    const debouncedLayoutChange = useMemo(
        () => debounce((newLayout: Layout[]) => {
            const updatedLayout = newLayout.map(item => {
                const component = layout.find(l => l.i === item.i);
                return {
                    ...item,
                    component: component?.component,
                } as DashboardLayout;
            });

            setLayout(updatedLayout);
            onLayoutChange?.(updatedLayout);
        }, 300),
        [layout, onLayoutChange]
    );

    // 布局变更处理
    const handleLayoutChange = useCallback((newLayout: Layout[], allLayouts: { [key: string]: Layout[] }) => {
        if (!editMode) return;

        debouncedLayoutChange(newLayout);
    }, [editMode, debouncedLayoutChange]);

    // 断点变更处理
    const handleBreakpointChange = useCallback((breakpoint: string) => {
        setCurrentBreakpoint(breakpoint);
    }, []);

    // 组件选择处理
    const handleComponentClick = useCallback((componentId: string) => {
        if (editMode) {
            setSelectedComponent(componentId === selectedComponent ? null : componentId);
        }
    }, [editMode, selectedComponent]);

    // 过滤器变更处理
    const handleFilterChange = useCallback((filterId: string, filterState: FilterState) => {
        setFilters(prev => ({
            ...prev,
            [filterId]: filterState,
        }));

        onFilterChange?.(filterId, filterState);

        // 如果启用了交叉过滤，更新相关图表
        if (enableCrossFilters) {
            // 实现交叉过滤逻辑
            const affectedCharts = getAffectedCharts(filterId, filterState);
            affectedCharts.forEach(chartId => {
                // 触发图表重新查询
                dispatch({ type: 'REFRESH_CHART', payload: { chartId } });
            });
        }
    }, [onFilterChange, enableCrossFilters, dispatch]);

    // 交叉过滤处理
    const handleCrossFilter = useCallback((
        sourceChartId: string,
        dataMask: DataMask
    ) => {
        setCrossFilters(prev => ({
            ...prev,
            [sourceChartId]: dataMask,
        }));

        // 更新受影响的图表
        const affectedCharts = getChartsInScope(sourceChartId, layout);
        affectedCharts.forEach(chartId => {
            dispatch({
                type: 'UPDATE_CHART_DATA_MASK',
                payload: { chartId, dataMask }
            });
        });
    }, [layout, dispatch]);

    // 组件添加处理
    const handleAddComponent = useCallback((componentType: string) => {
        const newComponent: DashboardComponent = {
            id: `component-${Date.now()}`,
            type: componentType as any,
            title: `New ${componentType}`,
            config: getDefaultConfig(componentType),
            meta: {
                width: getDefaultWidth(componentType),
                height: getDefaultHeight(componentType),
            },
        };

        const newLayoutItem: DashboardLayout = {
            i: newComponent.id,
            x: 0,
            y: Infinity, // 添加到底部
            w: newComponent.meta.width,
            h: newComponent.meta.height,
            component: newComponent,
            isResizable: true,
            isDraggable: true,
        };

        setLayout(prev => [...prev, newLayoutItem]);
    }, []);

    // 组件删除处理
    const handleRemoveComponent = useCallback((componentId: string) => {
        setLayout(prev => prev.filter(item => item.i !== componentId));
        setSelectedComponent(null);
    }, []);

    // 实时更新处理
    useEffect(() => {
        if (!enableRealTimeUpdates) return;

        const interval = setInterval(() => {
            // 检查是否有需要刷新的图表
            layout.forEach(item => {
                if (item.component.type === 'chart' && item.component.meta.chartId) {
                    const chartId = item.component.meta.chartId;
                    const lastUpdate = chartsData[chartId]?.lastUpdate;
                    const now = Date.now();

                    // 如果数据超过 5 分钟，则刷新
                    if (!lastUpdate || now - lastUpdate > 300000) {
                        dispatch({
                            type: 'REFRESH_CHART',
                            payload: { chartId }
                        });
                    }
                }
            });
        }, 60000); // 每分钟检查一次

        return () => clearInterval(interval);
    }, [enableRealTimeUpdates, layout, chartsData, dispatch]);

    // 渲染组件内容
    const renderComponentContent = useCallback((item: DashboardLayout) => {
        const { component } = item;
        const isSelected = selectedComponent === component.id;

        const commonProps = {
            id: component.id,
            editMode,
            isSelected,
            onClick: () => handleComponentClick(component.id),
            onRemove: () => handleRemoveComponent(component.id),
        };

        switch (component.type) {
            case 'chart':
                return (
                    <ChartRenderer
                        {...commonProps}
                        chartId={component.meta.chartId}
                        formData={component.meta.formData}
                        filters={filters}
                        crossFilters={crossFilters}
                        onCrossFilter={handleCrossFilter}
                        width={item.w}
                        height={item.h}
                    />
                );

            case 'filter':
                return (
                    <FilterPanel
                        {...commonProps}
                        filterId={component.id}
                        filterConfig={component.config}
                        filterState={filters[component.id]}
                        onFilterChange={(filterState) => handleFilterChange(component.id, filterState)}
                    />
                );

            case 'tabs':
                return (
                    <TabsContainer
                        {...commonProps}
                        tabsConfig={component.config}
                        children={component.children || []}
                    />
                );

            case 'text':
                return (
                    <div className="text-component">
                        {editMode ? (
                            <textarea
                                value={component.config.text || ''}
                                onChange={(e) => updateComponentConfig(component.id, { text: e.target.value })}
                                placeholder="Enter text..."
                            />
                        ) : (
                            <div dangerouslySetInnerHTML={{ __html: component.config.text || '' }} />
                        )}
                    </div>
                );

            default:
                return <div>Unknown component type: {component.type}</div>;
        }
    }, [
        selectedComponent,
        editMode,
        filters,
        crossFilters,
        handleComponentClick,
        handleRemoveComponent,
        handleCrossFilter,
        handleFilterChange,
    ]);

    // 渲染过滤器栏
    const renderFilterBar = () => {
        const filterComponents = layout.filter(item => item.component.type === 'filter');

        return (
            <FilterBar orientation={filterBarOrientation}>
                {filterComponents.map(item => (
                    <div key={item.i} className="filter-bar-item">
                        {renderComponentContent(item)}
                    </div>
                ))}
            </FilterBar>
        );
    };

    // 渲染编辑侧边栏
    const renderEditingSidebar = () => {
        if (!editMode) return null;

        const componentTypes = [
            { type: 'chart', icon: '📊', label: 'Chart' },
            { type: 'filter', icon: '🔍', label: 'Filter' },
            { type: 'text', icon: '📝', label: 'Text' },
            { type: 'tabs', icon: '📑', label: 'Tabs' },
            { type: 'divider', icon: '➖', label: 'Divider' },
        ];

        return (
            <EditingSidebar>
                <div className="component-library">
                    <h3>Components</h3>
                    {componentTypes.map(({ type, icon, label }) => (
                        <div
                            key={type}
                            className="component-item"
                            onClick={() => handleAddComponent(type)}
                        >
                            <span className="icon">{icon}</span>
                            <span className="label">{label}</span>
                        </div>
                    ))}
                </div>

                {selectedComponent && (
                    <div className="component-properties">
                        <h3>Properties</h3>
                        <ComponentPropertiesEditor
                            component={layout.find(item => item.i === selectedComponent)?.component}
                            onUpdate={(config) => updateComponentConfig(selectedComponent, config)}
                        />
                    </div>
                )}
            </EditingSidebar>
        );
    };

    return (
        <DashboardContainer
            ref={containerRef}
            editMode={editMode}
            filterBarOrientation={filterBarOrientation}
        >
            {/* 工具栏 */}
            <ToolbarComponent
                editMode={editMode}
                onToggleEditMode={() => {/* 处理编辑模式切换 */ }}
                onSave={() => {/* 处理保存 */ }}
                onExport={() => {/* 处理导出 */ }}
                selectedComponent={selectedComponent}
                onDeleteComponent={() => selectedComponent && handleRemoveComponent(selectedComponent)}
            />

            {/* 过滤器栏 */}
            {filterBarOrientation === 'horizontal' && renderFilterBar()}

            <div className="dashboard-main">
                {/* 垂直过滤器栏 */}
                {filterBarOrientation === 'vertical' && renderFilterBar()}

                {/* 主要内容区域 */}
                <div className="dashboard-content">
                    <ResponsiveGridLayout
                        className="layout"
                        layouts={{ [currentBreakpoint]: layout }}
                        breakpoints={breakpoints}
                        cols={cols}
                        rowHeight={30}
                        onLayoutChange={handleLayoutChange}
                        onBreakpointChange={handleBreakpointChange}
                        isDraggable={editMode}
                        isResizable={editMode}
                        compactType="vertical"
                        preventCollision={false}
                        margin={[16, 16]}
                        containerPadding={[0, 0]}
                        useCSSTransforms={true}
                        onResizeStart={() => setIsResizing(true)}
                        onResizeStop={() => setIsResizing(false)}
                    >
                        {layout.map(item => (
                            <div
                                key={item.i}
                                className={`
                  react-grid-item
                  ${editMode ? 'react-grid-item--editing' : ''}
                  ${selectedComponent === item.i ? 'selected' : ''}
                `}
                            >
                                {renderComponentContent(item)}

                                {/* 调整大小手柄 */}
                                {editMode && (
                                    <ResizeHandle
                                        onResize={(width, height) => {
                                            // 处理组件大小调整
                                        }}
                                    />
                                )}
                            </div>
                        ))}
                    </ResponsiveGridLayout>
                </div>
            </div>

            {/* 编辑侧边栏 */}
            {renderEditingSidebar()}
        </DashboardContainer>
    );
};

// 工具函数
function getAffectedCharts(filterId: string, filterState: FilterState): string[] {
    // 实现获取受过滤器影响的图表逻辑
    return [];
}

function getChartsInScope(chartId: string, layout: DashboardLayout[]): string[] {
    // 实现获取交叉过滤范围内图表的逻辑
    return [];
}

function getDefaultConfig(componentType: string): Record<string, any> {
    const configs = {
        chart: { chartType: 'table', showHeader: true },
        filter: { filterType: 'select', allowMultiple: true },
        text: { text: '', fontSize: 14 },
        tabs: { tabs: [] },
        divider: { style: 'solid', thickness: 1 },
    };
    return configs[componentType] || {};
}

function getDefaultWidth(componentType: string): number {
    const widths = {
        chart: 6,
        filter: 3,
        text: 12,
        tabs: 12,
        divider: 12,
    };
    return widths[componentType] || 6;
}

function getDefaultHeight(componentType: string): number {
    const heights = {
        chart: 8,
        filter: 4,
        text: 3,
        tabs: 10,
        divider: 1,
    };
    return heights[componentType] || 6;
}

function updateComponentConfig(componentId: string, config: Record<string, any>) {
    // 实现组件配置更新逻辑
}

// 组件属性编辑器
const ComponentPropertiesEditor: React.FC<{
    component?: DashboardComponent;
    onUpdate: (config: Record<string, any>) => void;
}> = ({ component, onUpdate }) => {
    if (!component) return null;

    return (
        <div className="properties-editor">
            <div className="property-group">
                <label>Title</label>
                <input
                    value={component.title || ''}
                    onChange={(e) => onUpdate({ title: e.target.value })}
                />
            </div>

            {/* 根据组件类型显示不同的属性编辑器 */}
            {component.type === 'chart' && (
                <div className="property-group">
                    <label>Chart Type</label>
                    <select
                        value={component.config.chartType || ''}
                        onChange={(e) => onUpdate({ chartType: e.target.value })}
                    >
                        <option value="table">Table</option>
                        <option value="bar">Bar Chart</option>
                        <option value="line">Line Chart</option>
                        <option value="pie">Pie Chart</option>
                    </select>
                </div>
            )}

            {/* 更多属性编辑器... */}
        </div>
    );
};

export default AdvancedDashboard; 