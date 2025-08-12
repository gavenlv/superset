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

import React, { memo, useCallback } from 'react';
import { styled } from '@superset-ui/core';
import { TreeNodeData } from '../types';

const TreeContainer = styled.div`
  height: 100%;
  overflow: auto;
  padding: 8px;
`;

const TreeNode = styled.div<{ level: number; indentSize: number; isSelected: boolean }>`
  display: flex;
  align-items: center;
  padding: 4px 8px;
  margin-left: ${({ level, indentSize }) => level * indentSize}px;
  cursor: pointer;
  border-radius: 4px;
  background: ${({ isSelected }) => isSelected ? '#e6f7ff' : 'transparent'};
  
  &:hover {
    background: ${({ isSelected }) => isSelected ? '#bae7ff' : '#f5f5f5'};
  }
`;

const ExpandIcon = styled.span<{ expanded: boolean }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-right: 8px;
  cursor: pointer;
  transform: ${({ expanded }) => expanded ? 'rotate(90deg)' : 'rotate(0deg)'};
  transition: transform 0.2s ease;
  
  &::before {
    content: '▶';
    font-size: 10px;
    color: #666;
  }
`;

const NodeIcon = styled.span`
  margin-right: 8px;
  color: #666;
`;

const NodeTitle = styled.span`
  flex: 1;
  font-weight: 500;
`;

const NodeMetrics = styled.div`
  display: flex;
  gap: 12px;
  margin-left: auto;
  font-size: 12px;
  color: #666;
`;

const HierarchyLine = styled.div<{ level: number; indentSize: number }>`
  position: absolute;
  left: ${({ level, indentSize }) => level * indentSize + 8}px;
  top: 0;
  bottom: 0;
  width: 1px;
  background: #e8e8e8;
`;

interface TreeViewRendererProps {
  treeData: TreeNodeData[];
  expandedNodes: Set<string>;
  selectedNodes: Set<string>;
  onNodeToggle: (nodeId: string) => void;
  onNodeSelect: (nodeId: string, isMultiSelect?: boolean) => void;
  onContextMenu?: (event: React.MouseEvent, node: TreeNodeData) => void;
  treeIndentSize: number;
  showHierarchyLines: boolean;
  metrics: any[];
  valueFormat: string;
  verboseMap: Record<string, string>;
}

const TreeViewRenderer: React.FC<TreeViewRendererProps> = ({
  treeData,
  expandedNodes,
  selectedNodes,
  onNodeToggle,
  onNodeSelect,
  onContextMenu,
  treeIndentSize,
  showHierarchyLines,
  metrics,
  valueFormat,
  verboseMap,
}) => {
  const renderNode = useCallback((node: TreeNodeData, index: number) => {
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

    return (
      <div key={node.id}>
        {showHierarchyLines && node.level > 0 && (
          <HierarchyLine level={node.level - 1} indentSize={treeIndentSize} />
        )}
        
        <TreeNode
          level={node.level}
          indentSize={treeIndentSize}
          isSelected={isSelected}
          onClick={handleSelect}
          onContextMenu={handleContextMenu}
        >
          {hasChildren ? (
            <ExpandIcon
              expanded={isExpanded}
              onClick={handleToggle}
            />
          ) : (
            <NodeIcon>•</NodeIcon>
          )}
          
          <NodeTitle>{node.title}</NodeTitle>
          
          <NodeMetrics>
            {metrics.map((metric, idx) => (
              <span key={idx}>
                {verboseMap[metric] || metric}: {node.data[metric] || 0}
              </span>
            ))}
          </NodeMetrics>
        </TreeNode>
        
        {hasChildren && isExpanded && node.children && (
          <div>
            {node.children.map((child, childIndex) => renderNode(child, childIndex))}
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
    showHierarchyLines,
    metrics,
    verboseMap,
  ]);

  return (
    <TreeContainer>
      {treeData.map((node, index) => renderNode(node, index))}
    </TreeContainer>
  );
};

export default memo(TreeViewRenderer); 