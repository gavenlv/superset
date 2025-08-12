/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { ChartProps, QueryFormData } from '@superset-ui/core';
import { 
  AdvancedPivotTableProps, 
  ViewModeEnum, 
  HierarchyModeEnum,
  MetricsLayoutEnum 
} from '../types';

export default function transformProps(chartProps: ChartProps<QueryFormData>): AdvancedPivotTableProps {
  const {
    width,
    height,
    formData,
    queriesData,
    hooks,
    filterState,
    datasource,
    theme,
    rawFormData,
  } = chartProps;

  const { data = [] } = queriesData[0] || {};
  const { setDataMask } = hooks;
  const { verboseMap = {}, columnFormats = {}, currencyFormats = {} } = datasource || {};

  const {
    groupbyRows = [],
    groupbyColumns = [],
    metrics = [],
    tableRenderer = 'Table',
    colOrder = 'key_a_to_z',
    rowOrder = 'key_a_to_z',
    aggregateFunction = 'Sum',
    transposePivot = false,
    combineMetric = false,
    rowSubtotalPosition = false,
    colSubtotalPosition = false,
    colTotals = false,
    colSubTotals = false,
    rowTotals = false,
    rowSubTotals = false,
    valueFormat = 'SMART_NUMBER',
    currencyFormat = { symbol: '', symbolPosition: 'prefix' },
    metricsLayout = MetricsLayoutEnum.COLUMNS,
    timeGrainSqla,
    
    // Advanced features
    viewMode = ViewModeEnum.TABLE,
    hierarchyMode = HierarchyModeEnum.SINGLE,
    hierarchyGroups = [],
    pinnedColumns = [],
    enableTreeView = false,
    enableDrillDown = false,
    enableGrouping = false,
    maxHierarchyLevels = 5,
    treeIndentSize = 20,
    showHierarchyLines = true,
    allowColumnReordering = true,
    enableVirtualScrolling = false,
    rowHeight = 32,
    enableSearch = true,
    searchColumns = [],
    enableFiltering = true,
    filterableColumns = [],
    enableSorting = true,
    sortableColumns = [],
    enableExport = true,
    exportFormats = ['csv', 'xlsx'],
    enableConditionalFormatting = false,
    conditionalFormattingRules = [],
  } = formData;

  const { selectedFilters } = filterState || {};

  return {
    data,
    width,
    height,
    groupbyRows,
    groupbyColumns,
    metrics,
    tableRenderer,
    colOrder,
    rowOrder,
    aggregateFunction,
    transposePivot,
    combineMetric,
    rowSubtotalPosition,
    colSubtotalPosition,
    colTotals,
    colSubTotals,
    rowTotals,
    rowSubTotals,
    valueFormat,
    currencyFormat,
    setDataMask,
    emitCrossFilters: true,
    selectedFilters,
    verboseMap,
    columnFormats,
    currencyFormats,
    metricsLayout,
    metricColorFormatters: {},
    dateFormatters: {},
    legacy_order_by: null,
    order_desc: false,
    timeGrainSqla,
    time_grain_sqla: timeGrainSqla,
    granularity_sqla: formData.granularity_sqla,

    // Advanced features
    viewMode,
    hierarchyMode,
    hierarchyGroups,
    pinnedColumns,
    enableTreeView,
    enableDrillDown,
    enableGrouping,
    maxHierarchyLevels,
    treeIndentSize,
    showHierarchyLines,
    allowColumnReordering,
    enableVirtualScrolling,
    rowHeight,
    enableSearch,
    searchColumns,
    enableFiltering,
    filterableColumns,
    enableSorting,
    sortableColumns,
    enableExport,
    exportFormats,
    enableConditionalFormatting,
    conditionalFormattingRules,
  };
} 