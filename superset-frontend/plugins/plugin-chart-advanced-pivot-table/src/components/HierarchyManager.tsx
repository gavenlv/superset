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

import React, { memo, useState } from 'react';
import { styled } from '@superset-ui/core';
import { HierarchyGroup, HierarchyModeEnum } from '../types';

const ManagerContainer = styled.div`
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
`;

const ManagerHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
`;

const ManagerTitle = styled.h4`
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
`;

const AddButton = styled.button`
  padding: 4px 8px;
  border: 1px solid #1890ff;
  border-radius: 4px;
  background: white;
  color: #1890ff;
  cursor: pointer;
  font-size: 12px;
  
  &:hover {
    background: #f0f8ff;
  }
`;

const HierarchyItem = styled.div<{ expanded: boolean; pinned: boolean }>`
  border: 1px solid ${({ pinned }) => pinned ? '#1890ff' : '#e8e8e8'};
  border-radius: 6px;
  margin-bottom: 8px;
  background: ${({ pinned }) => pinned ? '#f0f8ff' : 'white'};
  box-shadow: ${({ pinned }) => pinned ? '0 2px 4px rgba(24, 144, 255, 0.1)' : 'none'};
`;

const HierarchyHeader = styled.div`
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 6px 6px 0 0;
`;

const HierarchyName = styled.span`
  font-weight: 500;
  font-size: 13px;
  flex: 1;
`;

const HierarchyControls = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ControlButton = styled.button<{ active?: boolean }>`
  padding: 2px 6px;
  border: 1px solid ${({ active }) => active ? '#1890ff' : '#d9d9d9'};
  border-radius: 3px;
  background: ${({ active }) => active ? '#1890ff' : 'white'};
  color: ${({ active }) => active ? 'white' : '#666'};
  cursor: pointer;
  font-size: 11px;
  
  &:hover {
    background: ${({ active }) => active ? '#40a9ff' : '#f5f5f5'};
  }
`;

const ExpandIcon = styled.span<{ expanded: boolean }>`
  transform: ${({ expanded }) => expanded ? 'rotate(90deg)' : 'rotate(0deg)'};
  transition: transform 0.2s ease;
  font-size: 12px;
  
  &::before {
    content: '▶';
  }
`;

const HierarchyContent = styled.div<{ expanded: boolean }>`
  display: ${({ expanded }) => expanded ? 'block' : 'none'};
  padding: 12px;
  border-top: 1px solid #f0f0f0;
`;

const ColumnList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`;

const ColumnItem = styled.div`
  padding: 6px 8px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const ModeSelector = styled.div`
  margin-bottom: 16px;
`;

const ModeButton = styled.button<{ active: boolean }>`
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  background: ${({ active }) => active ? '#1890ff' : 'white'};
  color: ${({ active }) => active ? 'white' : '#666'};
  cursor: pointer;
  font-size: 11px;
  
  &:first-child {
    border-radius: 4px 0 0 4px;
  }
  
  &:last-child {
    border-radius: 0 4px 4px 0;
    border-left: none;
  }
  
  &:hover {
    background: ${({ active }) => active ? '#40a9ff' : '#f5f5f5'};
  }
`;

interface HierarchyManagerProps {
  hierarchyGroups: HierarchyGroup[];
  hierarchyMode: HierarchyModeEnum;
  maxLevels: number;
  onAddGroup?: () => void;
  onRemoveGroup?: (groupId: string) => void;
  onToggleGroup?: (groupId: string) => void;
  onTogglePin?: (groupId: string) => void;
  onModeChange?: (mode: HierarchyModeEnum) => void;
}

const HierarchyManager: React.FC<HierarchyManagerProps> = ({
  hierarchyGroups,
  hierarchyMode,
  maxLevels,
  onAddGroup,
  onRemoveGroup,
  onToggleGroup,
  onTogglePin,
  onModeChange,
}) => {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const handleToggleExpand = (groupId: string) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(groupId)) {
        newSet.delete(groupId);
      } else {
        newSet.add(groupId);
      }
      return newSet;
    });
  };

  if (hierarchyGroups.length === 0) {
    return (
      <ManagerContainer>
        <ManagerHeader>
          <ManagerTitle>Hierarchy Groups</ManagerTitle>
        </ManagerHeader>
        <div style={{ textAlign: 'center', color: '#999', fontSize: '12px', padding: '20px 0' }}>
          No hierarchy groups configured
        </div>
      </ManagerContainer>
    );
  }

  return (
    <ManagerContainer>
      <ManagerHeader>
        <ManagerTitle>Hierarchy Groups</ManagerTitle>
        {onAddGroup && (
          <AddButton onClick={onAddGroup}>
            + Add Group
          </AddButton>
        )}
      </ManagerHeader>

      <ModeSelector>
        <ModeButton
          active={hierarchyMode === HierarchyModeEnum.SINGLE}
          onClick={() => onModeChange?.(HierarchyModeEnum.SINGLE)}
        >
          Single
        </ModeButton>
        <ModeButton
          active={hierarchyMode === HierarchyModeEnum.MULTIPLE}
          onClick={() => onModeChange?.(HierarchyModeEnum.MULTIPLE)}
        >
          Multiple
        </ModeButton>
      </ModeSelector>

      {hierarchyGroups.map(group => {
        const isExpanded = expandedGroups.has(group.id);
        
        return (
          <HierarchyItem key={group.id} expanded={isExpanded} pinned={group.pinned}>
            <HierarchyHeader onClick={() => handleToggleExpand(group.id)}>
              <ExpandIcon expanded={isExpanded} />
              <HierarchyName>{group.name}</HierarchyName>
              <HierarchyControls>
                <ControlButton
                  active={group.pinned}
                  onClick={(e) => {
                    e.stopPropagation();
                    onTogglePin?.(group.id);
                  }}
                >
                  📌
                </ControlButton>
                <ControlButton
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveGroup?.(group.id);
                  }}
                >
                  ❌
                </ControlButton>
              </HierarchyControls>
            </HierarchyHeader>
            
            <HierarchyContent expanded={isExpanded}>
              <div style={{ marginBottom: '8px', fontSize: '11px', color: '#666' }}>
                Columns ({group.columns.length}):
              </div>
              <ColumnList>
                {group.columns.map((column, index) => (
                  <ColumnItem key={index}>
                    <span>{String(column)}</span>
                    <span style={{ color: '#999' }}>Level {index + 1}</span>
                  </ColumnItem>
                ))}
              </ColumnList>
            </HierarchyContent>
          </HierarchyItem>
        );
      })}
      
      <div style={{ fontSize: '11px', color: '#999', marginTop: '12px' }}>
        Max hierarchy levels: {maxLevels}
      </div>
    </ManagerContainer>
  );
};

export default memo(HierarchyManager); 