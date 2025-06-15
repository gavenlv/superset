/**
 * Enhanced Pivot Table Chart Plugin
 * 基于原始 Pivot Table 插件的增强版本，添加了多种高级功能
 */

// ============================================================================
// 1. 类型定义
// ============================================================================

import React, { useMemo, useCallback, useState } from 'react';
import {
    ChartPlugin,
    ChartMetadata,
    ChartProps,
    QueryFormData,
    t,
    Behavior,
    DataRecordValue,
    DataRecord,
    getNumberFormatter,
    NumberFormatter,
    styled,
    useTheme,
} from '@superset-ui/core';
import {
    ControlPanelConfig,
    sharedControls,
    validateNonEmpty,
} from '@superset-ui/chart-controls';

// 扩展的表单数据类型
interface EnhancedPivotTableFormData extends QueryFormData {
    groupbyRows: string[];
    groupbyColumns: string[];
    metrics: string[];
    aggregateFunction: string;
    enableDataBars: boolean;
    enableHeatmap: boolean;
    enableConditionalFormatting: boolean;
    dataBarsColor: string;
    heatmapColorScheme: string;
    conditionalFormattingRules: ConditionalFormattingRule[];
    showRowSubtotals: boolean;
    showColumnSubtotals: boolean;
    showGrandTotal: boolean;
    sortMetric?: string;
    sortOrder: 'asc' | 'desc';
    freezeColumns: number;
    virtualScroll: boolean;
    exportOptions: {
        excel: boolean;
        csv: boolean;
        pdf: boolean;
    };
}

// 条件格式化规则
interface ConditionalFormattingRule {
    id: string;
    condition: 'greater_than' | 'less_than' | 'between' | 'equal_to';
    value: number | [number, number];
    backgroundColor?: string;
    textColor?: string;
    metric?: string;
}

// 统计信息
interface Statistics {
    min: number;
    max: number;
    avg: number;
    sum: number;
    count: number;
}

// 组件属性
interface EnhancedPivotTableProps {
    width: number;
    height: number;
    data: DataRecord[];
    groupbyRows: string[];
    groupbyColumns: string[];
    metrics: string[];
    aggregateFunction: string;
    enableDataBars: boolean;
    enableHeatmap: boolean;
    enableConditionalFormatting: boolean;
    dataBarsColor: string;
    heatmapColorScheme: string;
    conditionalFormattingRules: ConditionalFormattingRule[];
    statistics: { [metric: string]: Statistics };
    onContextMenu?: (e: React.MouseEvent) => void;
    setDataMask?: (mask: any) => void;
    selectedFilters?: { [key: string]: DataRecordValue[] };
}

// ============================================================================
// 2. 样式组件
// ============================================================================

const EnhancedPivotTableContainer = styled.div<{
    width: number;
    height: number;
}>`
  width: ${props => props.width}px;
  height: ${props => props.height}px;
  overflow: auto;
  border: 1px solid ${({ theme }) => theme.colors.grayscale.light2};
  border-radius: 4px;
  font-family: ${({ theme }) => theme.typography.families.sansSerif};
`;

const DataBarCell = styled.div<{
    value: number;
    max: number;
    color: string;
}>`
  position: relative;
  padding: 4px 8px;
  background: linear-gradient(
    to right,
    ${props => props.color} ${props => (props.value / props.max) * 100}%,
    transparent ${props => (props.value / props.max) * 100}%
  );
  min-height: 20px;
  display: flex;
  align-items: center;
`;

const HeatmapCell = styled.div<{
    intensity: number;
    colorScheme: string;
}>`
  padding: 4px 8px;
  background-color: ${props => getHeatmapColor(props.intensity, props.colorScheme)};
  color: ${props => (props.intensity > 0.5 ? 'white' : 'black')};
  min-height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const ConditionalFormattedCell = styled.div<{
    backgroundColor?: string;
    textColor?: string;
}>`
  padding: 4px 8px;
  background-color: ${props => props.backgroundColor || 'transparent'};
  color: ${props => props.textColor || 'inherit'};
  min-height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const PivotTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;

  th, td {
    border: 1px solid ${({ theme }) => theme.colors.grayscale.light2};
    text-align: center;
    position: relative;
  }

  th {
    background-color: ${({ theme }) => theme.colors.grayscale.light4};
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .row-header {
    background-color: ${({ theme }) => theme.colors.grayscale.light5};
    font-weight: 500;
    text-align: left;
    padding: 4px 8px;
    position: sticky;
    left: 0;
    z-index: 5;
  }

  .grand-total {
    background-color: ${({ theme }) => theme.colors.primary.light2};
    font-weight: 700;
  }

  .subtotal {
    background-color: ${({ theme }) => theme.colors.grayscale.light3};
    font-weight: 600;
  }
`;

// ============================================================================
// 3. 工具函数
// ============================================================================

function getHeatmapColor(intensity: number, colorScheme: string): string {
    const schemes = {
        blues: `rgba(66, 146, 198, ${intensity})`,
        reds: `rgba(215, 48, 39, ${intensity})`,
        greens: `rgba(69, 139, 116, ${intensity})`,
        oranges: `rgba(253, 141, 60, ${intensity})`,
    };
    return schemes[colorScheme] || schemes.blues;
}

function processData(
    data: DataRecord[],
    groupbyRows: string[],
    groupbyColumns: string[],
    metrics: string[],
    aggregateFunction: string,
): any {
    // 简化的数据透视实现
    const pivotData = {};
    const rowTotals = {};
    const columnTotals = {};
    let grandTotal = 0;

    data.forEach(record => {
        const rowKey = groupbyRows.map(col => record[col]).join('|');
        const colKey = groupbyColumns.map(col => record[col]).join('|');

        if (!pivotData[rowKey]) {
            pivotData[rowKey] = {};
        }

        metrics.forEach(metric => {
            const value = Number(record[metric]) || 0;

            if (!pivotData[rowKey][colKey]) {
                pivotData[rowKey][colKey] = {};
            }

            if (!pivotData[rowKey][colKey][metric]) {
                pivotData[rowKey][colKey][metric] = [];
            }

            pivotData[rowKey][colKey][metric].push(value);

            // 计算行总计
            if (!rowTotals[rowKey]) rowTotals[rowKey] = {};
            if (!rowTotals[rowKey][metric]) rowTotals[rowKey][metric] = [];
            rowTotals[rowKey][metric].push(value);

            // 计算列总计
            if (!columnTotals[colKey]) columnTotals[colKey] = {};
            if (!columnTotals[colKey][metric]) columnTotals[colKey][metric] = [];
            columnTotals[colKey][metric].push(value);

            grandTotal += value;
        });
    });

    // 应用聚合函数
    const applyAggregation = (values: number[]) => {
        switch (aggregateFunction) {
            case 'Sum':
                return values.reduce((a, b) => a + b, 0);
            case 'Average':
                return values.reduce((a, b) => a + b, 0) / values.length;
            case 'Count':
                return values.length;
            case 'Maximum':
                return Math.max(...values);
            case 'Minimum':
                return Math.min(...values);
            default:
                return values.reduce((a, b) => a + b, 0);
        }
    };

    // 聚合数据
    Object.keys(pivotData).forEach(rowKey => {
        Object.keys(pivotData[rowKey]).forEach(colKey => {
            Object.keys(pivotData[rowKey][colKey]).forEach(metric => {
                pivotData[rowKey][colKey][metric] = applyAggregation(
                    pivotData[rowKey][colKey][metric]
                );
            });
        });
    });

    return {
        pivotData,
        rowTotals,
        columnTotals,
        grandTotal,
    };
}

function calculateStatistics(data: DataRecord[], metrics: string[]): { [metric: string]: Statistics } {
    const stats = {};

    metrics.forEach(metric => {
        const values = data
            .map(record => Number(record[metric]))
            .filter(value => !isNaN(value));

        if (values.length > 0) {
            stats[metric] = {
                min: Math.min(...values),
                max: Math.max(...values),
                avg: values.reduce((a, b) => a + b, 0) / values.length,
                sum: values.reduce((a, b) => a + b, 0),
                count: values.length,
            };
        }
    });

    return stats;
}

function applyConditionalFormatting(
    value: number,
    metric: string,
    rules: ConditionalFormattingRule[],
): { backgroundColor?: string; textColor?: string } {
    const applicableRules = rules.filter(rule => !rule.metric || rule.metric === metric);

    for (const rule of applicableRules) {
        let matches = false;

        switch (rule.condition) {
            case 'greater_than':
                matches = value > (rule.value as number);
                break;
            case 'less_than':
                matches = value < (rule.value as number);
                break;
            case 'equal_to':
                matches = value === (rule.value as number);
                break;
            case 'between':
                const [min, max] = rule.value as [number, number];
                matches = value >= min && value <= max;
                break;
        }

        if (matches) {
            return {
                backgroundColor: rule.backgroundColor,
                textColor: rule.textColor,
            };
        }
    }

    return {};
}

// ============================================================================
// 4. 主要组件
// ============================================================================

const EnhancedPivotTableChart: React.FC<EnhancedPivotTableProps> = ({
    width,
    height,
    data,
    groupbyRows,
    groupbyColumns,
    metrics,
    aggregateFunction,
    enableDataBars,
    enableHeatmap,
    enableConditionalFormatting,
    dataBarsColor = '#1f77b4',
    heatmapColorScheme = 'blues',
    conditionalFormattingRules = [],
    statistics,
    onContextMenu,
    setDataMask,
    selectedFilters,
}) => {
    const theme = useTheme();
    const [sortConfig, setSortConfig] = useState<{
        key: string;
        direction: 'asc' | 'desc';
    } | null>(null);

    // 处理数据
    const processedData = useMemo(() => {
        return processData(data, groupbyRows, groupbyColumns, metrics, aggregateFunction);
    }, [data, groupbyRows, groupbyColumns, metrics, aggregateFunction]);

    // 排序处理
    const handleSort = useCallback((key: string) => {
        let direction: 'asc' | 'desc' = 'asc';
        if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    }, [sortConfig]);

    // 渲染单元格
    const renderCell = useCallback((
        value: number,
        metric: string,
        rowKey: string,
        colKey: string,
    ) => {
        const formatter = getNumberFormatter();
        const formattedValue = formatter(value);

        // 数据条渲染
        if (enableDataBars && statistics[metric]) {
            return (
                <DataBarCell
                    value={value}
                    max={statistics[metric].max}
                    color={dataBarsColor}
                >
                    {formattedValue}
                </DataBarCell>
            );
        }

        // 热力图渲染
        if (enableHeatmap && statistics[metric]) {
            const intensity = (value - statistics[metric].min) /
                (statistics[metric].max - statistics[metric].min);
            return (
                <HeatmapCell
                    intensity={intensity}
                    colorScheme={heatmapColorScheme}
                >
                    {formattedValue}
                </HeatmapCell>
            );
        }

        // 条件格式化渲染
        if (enableConditionalFormatting && conditionalFormattingRules.length > 0) {
            const formatting = applyConditionalFormatting(value, metric, conditionalFormattingRules);
            return (
                <ConditionalFormattedCell
                    backgroundColor={formatting.backgroundColor}
                    textColor={formatting.textColor}
                >
                    {formattedValue}
                </ConditionalFormattedCell>
            );
        }

        // 默认渲染
        return <div style={{ padding: '4px 8px' }}>{formattedValue}</div>;
    }, [
        enableDataBars,
        enableHeatmap,
        enableConditionalFormatting,
        dataBarsColor,
        heatmapColorScheme,
        conditionalFormattingRules,
        statistics,
    ]);

    // 获取列键
    const columnKeys = useMemo(() => {
        const keys = new Set<string>();
        Object.values(processedData.pivotData).forEach((row: any) => {
            Object.keys(row).forEach(key => keys.add(key));
        });
        return Array.from(keys);
    }, [processedData.pivotData]);

    return (
        <EnhancedPivotTableContainer width={width} height={height}>
            <PivotTable>
                <thead>
                    <tr>
                        {groupbyRows.map(row => (
                            <th key={row} className="row-header">
                                {row}
                            </th>
                        ))}
                        {columnKeys.map(colKey => (
                            <th
                                key={colKey}
                                onClick={() => handleSort(colKey)}
                                style={{ cursor: 'pointer' }}
                            >
                                {colKey}
                                {sortConfig?.key === colKey && (
                                    <span>{sortConfig.direction === 'asc' ? ' ▲' : ' ▼'}</span>
                                )}
                            </th>
                        ))}
                        <th className="grand-total">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {Object.entries(processedData.pivotData).map(([rowKey, rowData]: [string, any]) => (
                        <tr key={rowKey}>
                            <td className="row-header">{rowKey}</td>
                            {columnKeys.map(colKey => (
                                <td key={colKey}>
                                    {rowData[colKey] && metrics.map(metric => (
                                        <div key={metric}>
                                            {renderCell(
                                                rowData[colKey][metric] || 0,
                                                metric,
                                                rowKey,
                                                colKey,
                                            )}
                                        </div>
                                    ))}
                                </td>
                            ))}
                            <td className="subtotal">
                                {metrics.map(metric => (
                                    <div key={metric}>
                                        {processedData.rowTotals[rowKey]?.[metric] || 0}
                                    </div>
                                ))}
                            </td>
                        </tr>
                    ))}
                    <tr className="grand-total">
                        <td>Total</td>
                        {columnKeys.map(colKey => (
                            <td key={colKey}>
                                {metrics.map(metric => (
                                    <div key={metric}>
                                        {processedData.columnTotals[colKey]?.[metric] || 0}
                                    </div>
                                ))}
                            </td>
                        ))}
                        <td>{processedData.grandTotal}</td>
                    </tr>
                </tbody>
            </PivotTable>
        </EnhancedPivotTableContainer>
    );
};

// ============================================================================
// 5. Transform Props 函数
// ============================================================================

function transformProps(chartProps: ChartProps): EnhancedPivotTableProps {
    const {
        width,
        height,
        queriesData,
        formData,
        hooks: { setDataMask, onContextMenu },
        filterState,
    } = chartProps;

    const { data } = queriesData[0];
    const {
        groupbyRows = [],
        groupbyColumns = [],
        metrics = [],
        aggregateFunction = 'Sum',
        enableDataBars = false,
        enableHeatmap = false,
        enableConditionalFormatting = false,
        dataBarsColor = '#1f77b4',
        heatmapColorScheme = 'blues',
        conditionalFormattingRules = [],
    } = formData as EnhancedPivotTableFormData;

    // 计算统计信息
    const statistics = calculateStatistics(data, metrics);

    return {
        width,
        height,
        data,
        groupbyRows,
        groupbyColumns,
        metrics,
        aggregateFunction,
        enableDataBars,
        enableHeatmap,
        enableConditionalFormatting,
        dataBarsColor,
        heatmapColorScheme,
        conditionalFormattingRules,
        statistics,
        onContextMenu,
        setDataMask,
        selectedFilters: filterState.selectedFilters,
    };
}

// ============================================================================
// 6. 控制面板配置
// ============================================================================

const controlPanel: ControlPanelConfig = {
    controlPanelSections: [
        {
            label: t('Query'),
            expanded: true,
            controlSetRows: [
                [{
                    name: 'groupbyRows',
                    config: {
                        ...sharedControls.groupby,
                        label: t('Rows'),
                        description: t('Columns to group by on the rows'),
                    },
                }],
                [{
                    name: 'groupbyColumns',
                    config: {
                        ...sharedControls.groupby,
                        label: t('Columns'),
                        description: t('Columns to group by on the columns'),
                    },
                }],
                [{
                    name: 'metrics',
                    config: {
                        ...sharedControls.metrics,
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
                    name: 'aggregateFunction',
                    config: {
                        type: 'SelectControl',
                        label: t('Aggregation function'),
                        choices: [
                            ['Sum', t('Sum')],
                            ['Average', t('Average')],
                            ['Count', t('Count')],
                            ['Maximum', t('Maximum')],
                            ['Minimum', t('Minimum')],
                        ],
                        default: 'Sum',
                    },
                }],
            ],
        },
        {
            label: t('Enhanced Features'),
            expanded: false,
            controlSetRows: [
                [{
                    name: 'enableDataBars',
                    config: {
                        type: 'CheckboxControl',
                        label: t('Enable Data Bars'),
                        description: t('Show horizontal data bars in cells'),
                        default: false,
                    },
                }],
                [{
                    name: 'dataBarsColor',
                    config: {
                        type: 'ColorPickerControl',
                        label: t('Data Bars Color'),
                        description: t('Color for data bars'),
                        default: '#1f77b4',
                        visibility: ({ controls }) => controls?.enableDataBars?.value,
                    },
                }],
                [{
                    name: 'enableHeatmap',
                    config: {
                        type: 'CheckboxControl',
                        label: t('Enable Heatmap'),
                        description: t('Color cells based on values'),
                        default: false,
                    },
                }],
                [{
                    name: 'heatmapColorScheme',
                    config: {
                        type: 'SelectControl',
                        label: t('Heatmap Color Scheme'),
                        choices: [
                            ['blues', t('Blues')],
                            ['reds', t('Reds')],
                            ['greens', t('Greens')],
                            ['oranges', t('Oranges')],
                        ],
                        default: 'blues',
                        visibility: ({ controls }) => controls?.enableHeatmap?.value,
                    },
                }],
                [{
                    name: 'enableConditionalFormatting',
                    config: {
                        type: 'CheckboxControl',
                        label: t('Enable Conditional Formatting'),
                        description: t('Apply conditional formatting rules'),
                        default: false,
                    },
                }],
            ],
        },
    ],
};

// ============================================================================
// 7. 插件定义
// ============================================================================

export default class EnhancedPivotTableChartPlugin extends ChartPlugin<
    EnhancedPivotTableFormData,
    ChartProps<EnhancedPivotTableFormData>
> {
    constructor() {
        const metadata = new ChartMetadata({
            behaviors: [
                Behavior.InteractiveChart,
                Behavior.DrillToDetail,
                Behavior.DrillBy,
            ],
            category: t('Table'),
            description: t(
                'Enhanced pivot table with data bars, heatmaps, conditional formatting and advanced features for better data visualization and analysis.',
            ),
            name: t('Enhanced Pivot Table'),
            tags: [
                t('Additive'),
                t('Report'),
                t('Tabular'),
                t('Enhanced'),
                t('Business Intelligence'),
            ],
            thumbnail: '/static/assets/images/viz_types/pivot_table.png',
        });

        super({
            buildQuery: () => ({}), // 使用默认查询构建
            controlPanel,
            loadChart: () => Promise.resolve(EnhancedPivotTableChart),
            metadata,
            transformProps,
        });
    }
}

// ============================================================================
// 8. 导出
// ============================================================================

export { EnhancedPivotTableChart, transformProps, controlPanel }; 