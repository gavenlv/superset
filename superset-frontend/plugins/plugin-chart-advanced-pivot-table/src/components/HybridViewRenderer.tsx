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

import React, { memo, useCallback, useMemo } from 'react';
import { styled } from '@superset-ui/core';
import { TreeNodeData } from '../types';

const HybridContainer = styled.div`
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const TreeSection = styled.div`
  flex: 0 0 300px;
  border-bottom: 2px solid #e8e8e8;
  overflow: auto;
  background: #f8f9fa;
`;

const TableSection = styled.div`
  flex: 1;
  overflow: hidden;
  background: white;
`;

const HybridRow = styled.div<{ level: number; indentSize: number; isSelected: boolean; isExpanded?: boolean }>`
  display: flex;
  align-items: center;
  padding: 6px 8px;
  margin-left: ${({ level, indentSize }) => level * indentSize}px;
  cursor: pointer;
  border-radius: 3px;
  background: ${({ isSelected }) => isSelected ? '#e6f7ff' : 'transparent'};
  border-left: ${({ isExpanded }) => isExpanded ? '3px solid #1890ff' : '3px solid transparent'};
  
  &:hover {
    background: ${({ isSelected }) => isSelected ? '#bae7ff' : '#f0f0f0'};
  }
`;

const ExpandIcon = styled.span<{ expanded: boolean; hasChildren: boolean }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-right: 8px;
  cursor: pointer;
  transform: ${({ expanded }) => expanded ? 'rotate(90deg)' : 'rotate(0deg)'};
  transition: transform 0.2s ease;
  opacity: ${({ hasChildren }) => hasChildren ? 1 : 0.3};
  
  &::before {
    content: '▶';
    font-size: 10px;
    color: #666;
  }
`;

const NodeContent = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const NodeTitle = styled.span`
  font-weight: 500;
  color: #333;
`;

const NodeSummary = styled.div`
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
`;

const DetailTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
`;

const DetailHeader = styled.th`
  background: #fafafa;
  padding: 8px 12px;
  text-align: left;
  border: 1px solid #e8e8e8;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 1;
`;

const DetailCell = styled.td<{ isNumeric?: boolean }>`
  padding: 6px 12px;
  border: 1px solid #f0f0f0;
  text-align: ${({ isNumeric }) => isNumeric ? 'right' : 'left'};
  
  &:nth-child(even) {
    background: #fafafa;
  }
`;

const DetailRow = styled.tr`
  &:hover {
    background: #f5f5f5;
  }
`;

interface HybridViewRendererProps {
  treeData: TreeNodeData[];
  data: any[];
  expandedNodes: Set<string>;
  selectedNodes: Set<string>;
  onNodeToggle: (nodeId: string) => void;
  onNodeSelect: (nodeId: string, isMultiSelect?: boolean) => void;
  onContextMenu?: (event: React.MouseEvent, node: TreeNodeData) => void;
  treeIndentSize: number;
  metrics: any[];
  groupbyRows: any[];
  groupbyColumns: any[];
  valueFormat: string;
  verboseMap: Record<string, string>;
}

const HybridViewRenderer: React.FC<HybridViewRendererProps> = ({
  treeData,
  data,
  expandedNodes,
  selectedNodes,
  onNodeToggle,
  onNodeSelect,
  onContextMenu,
  treeIndentSize,
  metrics,
  groupbyRows,
  groupbyColumns,
  valueFormat,
  verboseMap,
}) => {
  // Get detailed data for selected nodes
  const selectedNodeData = useMemo(() => {
    if (selectedNodes.size === 0) return [];
    
    return data.filter((row, index) => {
      const rowId = `row-${index}`;
      return selectedNodes.has(rowId) || 
             Array.from(selectedNodes).some(nodeId => {
               // Check if this row belongs to any selected tree node
               const nodePath = nodeId.split('|');
               return nodePath.every((pathSegment, pathIndex) => {
                 const columnKey = groupbyRows[pathIndex];
                 return row[columnKey] === pathSegment;
               });
             });
    });
  }, [selectedNodes, data, groupbyRows]);

  const renderTreeNode = useCallback((node: TreeNodeData, index: number) => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expandedNodes.has(node.id);
    const isSelected = selectedNodes.has(node.id);

    const handleToggle = (e: React.MouseEvent) => {
      e.stopPropagation();
      if (hasChildren) {
        onNodeToggle(node.id);
      }
    };

    const handleSelect = (e: React.MouseEvent) => {
      e.stopPropagation();
      onNodeSelect(node.id, e.ctrlKey || e.metaKey);
    };

    const handleContextMenu = (e: React.MouseEvent) => {
      e.preventDefault();
      onContextMenu?.(e, node);
    };

    // Calculate summary metrics for this node
    const nodeSummary = metrics.reduce((acc, metric) => {
      acc[metric] = node.data[metric] || 0;
      return acc;
    }, {} as Record<string, any>);

    return (
      <div key={node.id}>
        <HybridRow
          level={node.level}
          indentSize={treeIndentSize}
          isSelected={isSelected}
          isExpanded={isExpanded}
          onClick={handleSelect}
          onContextMenu={handleContextMenu}
        >
          <ExpandIcon
            expanded={isExpanded}
            hasChildren={hasChildren}
            onClick={handleToggle}
          />
          
          <NodeContent>
            <NodeTitle>{node.title}</NodeTitle>
            <NodeSummary>
              {Object.entries(nodeSummary).map(([metric, value]) => (
                <span key={metric}>
                  {verboseMap[metric] || metric}: {value}
                </span>
              ))}
            </NodeSummary>
          </NodeContent>
        </HybridRow>
        
        {hasChildren && isExpanded && node.children && (
          <div>
            {node.children.map((child, childIndex) => renderTreeNode(child, childIndex))}
          </div>
        )}
      </div>
    );
  }, [
    expandedNodes,
    selectedNodes,
    onNodeToggle,
    onNodeSelect,
    onContextMenu,
    treeIndentSize,
    metrics,
    verboseMap,
  ]);

  const renderDetailTable = useCallback(() => {
    if (selectedNodeData.length === 0) {
      return (
        <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
          Select a node from the tree above to view detailed data
        </div>
      );
    }

    const allColumns = [...groupbyRows, ...groupbyColumns, ...metrics];

    return (
      <DetailTable>
        <thead>
          <tr>
            {allColumns.map(column => (
              <DetailHeader key={column}>
                {verboseMap[column] || column}
              </DetailHeader>
            ))}
          </tr>
        </thead>
        <tbody>
          {selectedNodeData.map((row, index) => (
            <DetailRow key={index}>
              {allColumns.map(column => {
                const isNumeric = metrics.includes(column);
                return (
                  <DetailCell key={column} isNumeric={isNumeric}>
                    {row[column] || ''}
                  </DetailCell>
                );
              })}
            </DetailRow>
          ))}
        </tbody>
      </DetailTable>
    );
  }, [selectedNodeData, groupbyRows, groupbyColumns, metrics, verboseMap]);

  return (
    <HybridContainer>
      <TreeSection>
        {treeData.map((node, index) => renderTreeNode(node, index))}
      </TreeSection>
      
      <TableSection>
        {renderDetailTable()}
      </TableSection>
    </HybridContainer>
  );
};

export default memo(HybridViewRenderer); 