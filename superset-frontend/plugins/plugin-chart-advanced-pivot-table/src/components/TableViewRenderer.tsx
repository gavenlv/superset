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

import React, { memo, useCallback, useMemo, useState } from 'react';
import { styled } from '@superset-ui/core';
import { FixedSizeList as List } from 'react-window';

const TableContainer = styled.div`
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const TableHeader = styled.div`
  display: flex;
  background: #fafafa;
  border-bottom: 2px solid #e8e8e8;
  position: sticky;
  top: 0;
  z-index: 10;
`;

const HeaderCell = styled.div<{ width: number; sortable?: boolean }>`
  flex: 0 0 ${({ width }) => width}px;
  padding: 12px 8px;
  border-right: 1px solid #e8e8e8;
  font-weight: 600;
  cursor: ${({ sortable }) => sortable ? 'pointer' : 'default'};
  user-select: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  
  &:hover {
    background: ${({ sortable }) => sortable ? '#f0f0f0' : 'transparent'};
  }
`;

const SortIcon = styled.span<{ direction?: 'asc' | 'desc' }>`
  margin-left: 4px;
  color: #666;
  font-size: 12px;
  
  &::after {
    content: ${({ direction }) => 
      direction === 'asc' ? "'▲'" : 
      direction === 'desc' ? "'▼'" : "'⇅'"};
  }
`;

const FilterIcon = styled.span`
  margin-left: 4px;
  color: #666;
  cursor: pointer;
  
  &::after {
    content: '🔍';
    font-size: 10px;
  }
`;

const TableBody = styled.div`
  flex: 1;
  overflow: hidden;
`;

const TableRow = styled.div<{ isEven: boolean; isSelected?: boolean }>`
  display: flex;
  background: ${({ isEven, isSelected }) => 
    isSelected ? '#e6f7ff' : 
    isEven ? '#fafafa' : 'white'};
  border-bottom: 1px solid #f0f0f0;
  
  &:hover {
    background: ${({ isSelected }) => isSelected ? '#bae7ff' : '#f5f5f5'};
  }
`;

const TableCell = styled.div<{ width: number; isNumeric?: boolean }>`
  flex: 0 0 ${({ width }) => width}px;
  padding: 8px;
  border-right: 1px solid #f0f0f0;
  text-align: ${({ isNumeric }) => isNumeric ? 'right' : 'left'};
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const PinnedColumnsContainer = styled.div<{ position: 'left' | 'right' }>`
  display: flex;
  flex-direction: column;
  background: white;
  border-right: ${({ position }) => position === 'left' ? '2px solid #1890ff' : 'none'};
  border-left: ${({ position }) => position === 'right' ? '2px solid #1890ff' : 'none'};
  z-index: 5;
`;

const ScrollableContainer = styled.div`
  flex: 1;
  overflow: auto;
`;

interface Column {
  key: string;
  title: string;
  width: number;
  sortable?: boolean;
  filterable?: boolean;
  isNumeric?: boolean;
  pinned?: 'left' | 'right';
  formatter?: (value: any) => string;
}

interface TableViewRendererProps {
  data: any[];
  groupbyRows: any[];
  groupbyColumns: any[];
  metrics: any[];
  pinnedColumns?: any[];
  onSort?: (key: string) => void;
  onFilter?: (column: string, value: any) => void;
  onContextMenu?: (event: React.MouseEvent, rowData: any) => void;
  sortConfig?: { key: string; direction: 'asc' | 'desc' } | null;
  filters?: Record<string, any>;
  enableVirtualScrolling?: boolean;
  rowHeight?: number;
  valueFormat?: string;
  verboseMap?: Record<string, string>;
  selectedNodes?: Set<string>;
  onNodeSelect?: (nodeId: string, isMultiSelect?: boolean) => void;
}

const TableViewRenderer: React.FC<TableViewRendererProps> = ({
  data,
  groupbyRows,
  groupbyColumns,
  metrics,
  pinnedColumns = [],
  onSort,
  onFilter,
  onContextMenu,
  sortConfig,
  filters,
  enableVirtualScrolling = false,
  rowHeight = 32,
  valueFormat,
  verboseMap = {},
  selectedNodes = new Set(),
  onNodeSelect,
}) => {
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});

  // Generate columns configuration
  const columns = useMemo(() => {
    const allColumns: Column[] = [];
    
    // Add row groupby columns
    groupbyRows.forEach((col: any) => {
      allColumns.push({
        key: col,
        title: verboseMap[col] || col,
        width: columnWidths[col] || 150,
        sortable: true,
        filterable: true,
        pinned: pinnedColumns.find(p => p.column === col)?.position,
      });
    });
    
    // Add column groupby columns
    groupbyColumns.forEach((col: any) => {
      allColumns.push({
        key: col,
        title: verboseMap[col] || col,
        width: columnWidths[col] || 150,
        sortable: true,
        filterable: true,
        pinned: pinnedColumns.find(p => p.column === col)?.position,
      });
    });
    
    // Add metric columns
    metrics.forEach((metric: any) => {
      allColumns.push({
        key: metric,
        title: verboseMap[metric] || metric,
        width: columnWidths[metric] || 120,
        sortable: true,
        filterable: true,
        isNumeric: true,
        pinned: pinnedColumns.find(p => p.column === metric)?.position,
      });
    });
    
    return allColumns;
  }, [groupbyRows, groupbyColumns, metrics, verboseMap, columnWidths, pinnedColumns]);

  // Separate pinned and regular columns
  const { leftPinnedColumns, rightPinnedColumns, regularColumns } = useMemo(() => {
    const left: Column[] = [];
    const right: Column[] = [];
    const regular: Column[] = [];
    
    columns.forEach(col => {
      if (col.pinned === 'left') {
        left.push(col);
      } else if (col.pinned === 'right') {
        right.push(col);
      } else {
        regular.push(col);
      }
    });
    
    return {
      leftPinnedColumns: left,
      rightPinnedColumns: right,
      regularColumns: regular,
    };
  }, [columns]);

  const handleSort = useCallback((columnKey: string) => {
    onSort?.(columnKey);
  }, [onSort]);

  const handleCellClick = useCallback((rowData: any, rowIndex: number, event: React.MouseEvent) => {
    const rowId = `row-${rowIndex}`;
    onNodeSelect?.(rowId, event.ctrlKey || event.metaKey);
  }, [onNodeSelect]);

  const renderHeaderCell = useCallback((column: Column) => {
    const sortDirection = sortConfig?.key === column.key ? sortConfig.direction : undefined;
    
    return (
      <HeaderCell
        key={column.key}
        width={column.width}
        sortable={column.sortable}
        onClick={() => column.sortable && handleSort(column.key)}
      >
        <span>{column.title}</span>
        <div>
          {column.sortable && <SortIcon direction={sortDirection} />}
          {column.filterable && <FilterIcon />}
        </div>
      </HeaderCell>
    );
  }, [sortConfig, handleSort]);

  const renderCell = useCallback((column: Column, rowData: any, rowIndex: number) => {
    const value = rowData[column.key];
    const formattedValue = column.formatter ? column.formatter(value) : String(value || '');
    
    return (
      <TableCell
        key={`${rowIndex}-${column.key}`}
        width={column.width}
        isNumeric={column.isNumeric}
        title={formattedValue}
      >
        {formattedValue}
      </TableCell>
    );
  }, []);

  const renderRow = useCallback(({ index, style }: { index: number; style: any }) => {
    const rowData = data[index];
    const isEven = index % 2 === 0;
    const rowId = `row-${index}`;
    const isSelected = selectedNodes.has(rowId);
    
    return (
      <div style={style}>
        <TableRow
          isEven={isEven}
          isSelected={isSelected}
          onClick={(e) => handleCellClick(rowData, index, e)}
          onContextMenu={(e) => onContextMenu?.(e, rowData)}
        >
          {/* Left pinned columns */}
          {leftPinnedColumns.map(column => renderCell(column, rowData, index))}
          {/* Regular columns */}
          {regularColumns.map(column => renderCell(column, rowData, index))}
          {/* Right pinned columns */}
          {rightPinnedColumns.map(column => renderCell(column, rowData, index))}
        </TableRow>
      </div>
    );
  }, [data, leftPinnedColumns, regularColumns, rightPinnedColumns, selectedNodes, handleCellClick, onContextMenu, renderCell]);

  const renderStaticRow = useCallback((rowData: any, index: number) => {
    const isEven = index % 2 === 0;
    const rowId = `row-${index}`;
    const isSelected = selectedNodes.has(rowId);
    
    return (
      <TableRow
        key={index}
        isEven={isEven}
        isSelected={isSelected}
        onClick={(e) => handleCellClick(rowData, index, e)}
        onContextMenu={(e) => onContextMenu?.(e, rowData)}
      >
        {/* Left pinned columns */}
        {leftPinnedColumns.map(column => renderCell(column, rowData, index))}
        {/* Regular columns */}
        {regularColumns.map(column => renderCell(column, rowData, index))}
        {/* Right pinned columns */}
        {rightPinnedColumns.map(column => renderCell(column, rowData, index))}
      </TableRow>
    );
  }, [leftPinnedColumns, regularColumns, rightPinnedColumns, selectedNodes, handleCellClick, onContextMenu, renderCell]);

  return (
    <TableContainer>
      {/* Header */}
      <TableHeader>
        {leftPinnedColumns.map(renderHeaderCell)}
        {regularColumns.map(renderHeaderCell)}
        {rightPinnedColumns.map(renderHeaderCell)}
      </TableHeader>
      
      {/* Body */}
      <TableBody>
        {enableVirtualScrolling ? (
          <List
            height={400} // This should be calculated based on container height
            itemCount={data.length}
            itemSize={rowHeight}
            itemData={data}
          >
            {renderRow}
          </List>
        ) : (
          <div>
            {data.map(renderStaticRow)}
          </div>
        )}
      </TableBody>
    </TableContainer>
  );
};

export default memo(TableViewRenderer); 