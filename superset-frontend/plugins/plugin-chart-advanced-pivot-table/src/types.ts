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
import {
  QueryFormData,
  DataRecord,
  SetDataMaskHook,
  DataRecordValue,
  JsonObject,
  TimeFormatter,
  NumberFormatter,
  QueryFormMetric,
  QueryFormColumn,
  TimeGranularity,
  ContextMenuFilters,
  Currency,
} from '@superset-ui/core';
import { ColorFormatters } from '@superset-ui/chart-controls';

export interface AdvancedPivotTableStylesProps {
  height: number;
  width: number | string;
  margin: number;
}

export enum MetricsLayoutEnum {
  COLUMNS = 'COLUMNS',
  ROWS = 'ROWS',
}

export enum ViewModeEnum {
  TREE = 'TREE',
  TABLE = 'TABLE',
  HYBRID = 'HYBRID',
}

export enum HierarchyModeEnum {
  SINGLE = 'SINGLE',
  MULTIPLE = 'MULTIPLE',
}

export interface HierarchyGroup {
  id: string;
  name: string;
  columns: QueryFormColumn[];
  expanded: boolean;
  pinned: boolean;
  color?: string;
}

export interface PinnedColumn {
  column: QueryFormColumn;
  position: 'left' | 'right';
  width?: number;
}

export interface TreeNodeData {
  id: string;
  title: string;
  children?: TreeNodeData[];
  expanded?: boolean;
  level: number;
  data: DataRecord;
  parentPath: string[];
}

export interface FilterType {
  [key: string]: any;
}

export interface SelectedFiltersType {
  [key: string]: any;
}

export type DateFormatter = TimeFormatter | NumberFormatter | undefined;

interface AdvancedPivotTableCustomizeProps {
  groupbyRows: QueryFormColumn[];
  groupbyColumns: QueryFormColumn[];
  metrics: QueryFormMetric[];
  tableRenderer: string;
  colOrder: string;
  rowOrder: string;
  aggregateFunction: string;
  transposePivot: boolean;
  combineMetric: boolean;
  rowSubtotalPosition: boolean;
  colSubtotalPosition: boolean;
  colTotals: boolean;
  colSubTotals: boolean;
  rowTotals: boolean;
  rowSubTotals: boolean;
  valueFormat: string;
  currencyFormat: Currency;
  setDataMask: SetDataMaskHook;
  emitCrossFilters?: boolean;
  selectedFilters?: SelectedFiltersType;
  verboseMap: JsonObject;
  columnFormats: JsonObject;
  currencyFormats: Record<string, Currency>;
  metricsLayout?: MetricsLayoutEnum;
  metricColorFormatters: ColorFormatters;
  dateFormatters: Record<string, DateFormatter | undefined>;
  legacy_order_by: QueryFormMetric[] | QueryFormMetric | null;
  order_desc: boolean;
  onContextMenu?: (
    clientX: number,
    clientY: number,
    filters?: ContextMenuFilters,
  ) => void;
  timeGrainSqla?: TimeGranularity;
  time_grain_sqla?: TimeGranularity;
  granularity_sqla?: string;
  
  // Advanced features
  viewMode: ViewModeEnum;
  hierarchyMode: HierarchyModeEnum;
  hierarchyGroups: HierarchyGroup[];
  pinnedColumns: PinnedColumn[];
  enableTreeView: boolean;
  enableDrillDown: boolean;
  enableGrouping: boolean;
  maxHierarchyLevels: number;
  treeIndentSize: number;
  showHierarchyLines: boolean;
  allowColumnReordering: boolean;
  enableVirtualScrolling: boolean;
  rowHeight: number;
  enableSearch: boolean;
  searchColumns: QueryFormColumn[];
  enableFiltering: boolean;
  filterableColumns: QueryFormColumn[];
  enableSorting: boolean;
  sortableColumns: QueryFormColumn[];
  enableExport: boolean;
  exportFormats: string[];
  enableConditionalFormatting: boolean;
  conditionalFormattingRules: any[];
}

export interface AdvancedPivotTableProps extends AdvancedPivotTableCustomizeProps {
  data: DataRecord[];
  height: number;
  width: number;
}

export interface AdvancedPivotTableQueryFormData extends QueryFormData {
  groupbyRows: QueryFormColumn[];
  groupbyColumns: QueryFormColumn[];
  metrics: QueryFormMetric[];
  tableRenderer: string;
  colOrder: string;
  rowOrder: string;
  aggregateFunction: string;
  transposePivot: boolean;
  combineMetric: boolean;
  rowSubtotalPosition: boolean;
  colSubtotalPosition: boolean;
  colTotals: boolean;
  colSubTotals: boolean;
  rowTotals: boolean;
  rowSubTotals: boolean;
  valueFormat: string;
  metricsLayout: MetricsLayoutEnum;
  currencyFormat: Currency;
  conditional_formatting: any[];
  
  // Advanced features
  viewMode: ViewModeEnum;
  hierarchyMode: HierarchyModeEnum;
  hierarchyGroups: HierarchyGroup[];
  pinnedColumns: PinnedColumn[];
  enableTreeView: boolean;
  enableDrillDown: boolean;
  enableGrouping: boolean;
  maxHierarchyLevels: number;
  treeIndentSize: number;
  showHierarchyLines: boolean;
  allowColumnReordering: boolean;
  enableVirtualScrolling: boolean;
  rowHeight: number;
  enableSearch: boolean;
  searchColumns: QueryFormColumn[];
  enableFiltering: boolean;
  filterableColumns: QueryFormColumn[];
  enableSorting: boolean;
  sortableColumns: QueryFormColumn[];
  enableExport: boolean;
  exportFormats: string[];
  enableConditionalFormatting: boolean;
  conditionalFormattingRules: any[];
} 