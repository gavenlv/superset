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

import React, { useCallback, useMemo, useState, useRef, useEffect } from 'react';
import { styled, useTheme } from '@superset-ui/core';
import { AdvancedPivotTableProps, ViewModeEnum, HierarchyModeEnum, TreeNodeData } from './types';
import TreeViewRenderer from './components/TreeViewRenderer';
import TableViewRenderer from './components/TableViewRenderer';
import HybridViewRenderer from './components/HybridViewRenderer';
import ToolbarControls from './components/ToolbarControls';
import HierarchyManager from './components/HierarchyManager';
import PinnedColumnsManager from './components/PinnedColumnsManager';

const Styles = styled.div<{ height: number; width: number | string; margin: number }>`
  ${({ height, width, margin }) => `
    margin: ${margin}px;
    height: ${height - margin * 2}px;
    width: ${typeof width === 'string' ? parseInt(width, 10) : width - margin * 2}px;
    display: flex;
    flex-direction: column;
  `}
`;

const ChartContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
`;

const ToolbarContainer = styled.div`
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
`;

const ContentContainer = styled.div`
  flex: 1;
  display: flex;
  overflow: hidden;
`;

const SidebarContainer = styled.div<{ width: number }>`
  width: ${props => props.width}px;
  min-width: ${props => props.width}px;
  border-right: 1px solid #e8e8e8;
  background: #f8f9fa;
  overflow-y: auto;
`;

const MainContent = styled.div`
  flex: 1;
  overflow: hidden;
  position: relative;
`;

export default function AdvancedPivotTableChart(props: AdvancedPivotTableProps) {
  const {
    data,
    height,
    width,
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
    enableFiltering = true,
    enableSorting = true,
    enableExport = true,
    enableConditionalFormatting = false,
    groupbyRows,
    groupbyColumns,
    metrics,
    aggregateFunction,
    valueFormat,
    verboseMap,
    onContextMenu,
    setDataMask,
    selectedFilters,
    ...restProps
  } = props;

  const theme = useTheme();
  const [currentViewMode, setCurrentViewMode] = useState<ViewModeEnum>(viewMode);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [selectedNodes, setSelectedNodes] = useState<Set<string>>(new Set());
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [showSidebar, setShowSidebar] = useState(hierarchyGroups.length > 0 || pinnedColumns.length > 0);
  
  const containerRef = useRef<HTMLDivElement>(null);

  // Transform flat data to tree structure for hierarchy display
  const treeData = useMemo(() => {
    if (!enableTreeView || !groupbyRows.length) return [];
    
    const buildTree = (rows: any[], level = 0, parentPath: string[] = []): TreeNodeData[] => {
      if (level >= groupbyRows.length) return [];
      
      const groupKey = groupbyRows[level];
      const grouped = rows.reduce((acc, row) => {
        const key = row[groupKey] || 'null';
        if (!acc[key]) acc[key] = [];
        acc[key].push(row);
        return acc;
      }, {});

      return Object.entries(grouped).map(([key, groupedRows]: [string, any]) => {
        const nodeId = [...parentPath, key].join('|');
        const hasChildren = level < groupbyRows.length - 1;
        
        return {
          id: nodeId,
          title: verboseMap[key] || key,
          expanded: expandedNodes.has(nodeId),
          level,
          data: groupedRows[0], // Use first row as representative data
          parentPath,
          children: hasChildren ? buildTree(groupedRows, level + 1, [...parentPath, key]) : undefined,
        };
      });
    };

    return buildTree(data);
  }, [data, groupbyRows, verboseMap, expandedNodes, enableTreeView]);

  // Filter data based on search and filters
  const filteredData = useMemo(() => {
    let filtered = [...data];
    
    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }
    
    // Apply column filters
    Object.entries(filters).forEach(([column, filterValue]) => {
      if (filterValue) {
        filtered = filtered.filter(row => {
          const cellValue = row[column];
          if (typeof filterValue === 'string') {
            return String(cellValue).toLowerCase().includes(filterValue.toLowerCase());
          }
          return cellValue === filterValue;
        });
      }
    });
    
    return filtered;
  }, [data, searchTerm, filters]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig) return filteredData;
    
    return [...filteredData].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];
      
      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortConfig]);

  const handleViewModeChange = useCallback((mode: ViewModeEnum) => {
    setCurrentViewMode(mode);
  }, []);

  const handleNodeToggle = useCallback((nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  }, []);

  const handleNodeSelect = useCallback((nodeId: string, isMultiSelect = false) => {
    setSelectedNodes(prev => {
      const newSet = new Set(isMultiSelect ? prev : []);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  }, []);

  const handleSort = useCallback((key: string) => {
    setSortConfig(prev => ({
      key,
      direction: prev?.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const handleFilter = useCallback((column: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [column]: value,
    }));
  }, []);

  const handleExport = useCallback((format: string) => {
    // Export functionality implementation
    console.log('Exporting data in format:', format);
  }, []);

  const renderMainContent = () => {
    const commonProps = {
      data: sortedData,
      treeData,
      groupbyRows,
      groupbyColumns,
      metrics,
      aggregateFunction,
      valueFormat,
      verboseMap,
      expandedNodes,
      selectedNodes,
      onNodeToggle: handleNodeToggle,
      onNodeSelect: handleNodeSelect,
      onSort: handleSort,
      onFilter: handleFilter,
      onContextMenu,
      sortConfig,
      filters,
      enableDrillDown,
      enableGrouping,
      enableVirtualScrolling,
      rowHeight,
      treeIndentSize,
      showHierarchyLines,
      ...restProps,
    };

    switch (currentViewMode) {
      case ViewModeEnum.TREE:
        return <TreeViewRenderer {...commonProps} />;
      case ViewModeEnum.HYBRID:
        return <HybridViewRenderer {...commonProps} />;
      default:
        return <TableViewRenderer {...commonProps} />;
    }
  };

  return (
    <Styles height={height} width={width} margin={theme.gridUnit * 4} ref={containerRef}>
      <ChartContainer>
        <ToolbarContainer>
          <ToolbarControls
            viewMode={currentViewMode}
            onViewModeChange={handleViewModeChange}
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            enableSearch={enableSearch}
            enableExport={enableExport}
            onExport={handleExport}
            showSidebar={showSidebar}
            onToggleSidebar={() => setShowSidebar(!showSidebar)}
          />
        </ToolbarContainer>
        
        <ContentContainer>
          {showSidebar && (
            <SidebarContainer width={sidebarWidth}>
              <HierarchyManager
                hierarchyGroups={hierarchyGroups}
                hierarchyMode={hierarchyMode}
                maxLevels={maxHierarchyLevels}
              />
              <PinnedColumnsManager
                pinnedColumns={pinnedColumns}
                availableColumns={[...groupbyRows, ...groupbyColumns]}
              />
            </SidebarContainer>
          )}
          
          <MainContent>
            {renderMainContent()}
          </MainContent>
        </ContentContainer>
      </ChartContainer>
    </Styles>
  );
} 