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

import React, { memo } from 'react';
import { styled } from '@superset-ui/core';
import { ViewModeEnum } from '../types';

const ToolbarContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
`;

const ViewModeSelector = styled.div`
  display: flex;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
`;

const ViewModeButton = styled.button<{ active: boolean }>`
  padding: 6px 12px;
  border: none;
  background: ${({ active }) => active ? '#1890ff' : 'white'};
  color: ${({ active }) => active ? 'white' : '#666'};
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
  
  &:hover {
    background: ${({ active }) => active ? '#40a9ff' : '#f5f5f5'};
  }
  
  &:not(:last-child) {
    border-right: 1px solid #d9d9d9;
  }
`;

const SearchContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const SearchInput = styled.input`
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  width: 200px;
  
  &:focus {
    outline: none;
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }
`;

const ControlGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const IconButton = styled.button`
  padding: 6px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
  transition: all 0.2s ease;
  
  &:hover {
    background: #f5f5f5;
    border-color: #bfbfbf;
  }
  
  &:active {
    background: #e6e6e6;
  }
`;

const Divider = styled.div`
  width: 1px;
  height: 20px;
  background: #d9d9d9;
`;

interface ToolbarControlsProps {
  viewMode: ViewModeEnum;
  onViewModeChange: (mode: ViewModeEnum) => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  enableSearch: boolean;
  enableExport: boolean;
  onExport: (format: string) => void;
  showSidebar: boolean;
  onToggleSidebar: () => void;
}

const ToolbarControls: React.FC<ToolbarControlsProps> = ({
  viewMode,
  onViewModeChange,
  searchTerm,
  onSearchChange,
  enableSearch,
  enableExport,
  onExport,
  showSidebar,
  onToggleSidebar,
}) => {
  return (
    <ToolbarContainer>
      {/* View Mode Selector */}
      <ControlGroup>
        <span style={{ fontSize: '13px', color: '#666', fontWeight: 500 }}>View:</span>
        <ViewModeSelector>
          <ViewModeButton
            active={viewMode === ViewModeEnum.TABLE}
            onClick={() => onViewModeChange(ViewModeEnum.TABLE)}
          >
            📊 Table
          </ViewModeButton>
          <ViewModeButton
            active={viewMode === ViewModeEnum.TREE}
            onClick={() => onViewModeChange(ViewModeEnum.TREE)}
          >
            🌳 Tree
          </ViewModeButton>
          <ViewModeButton
            active={viewMode === ViewModeEnum.HYBRID}
            onClick={() => onViewModeChange(ViewModeEnum.HYBRID)}
          >
            🔀 Hybrid
          </ViewModeButton>
        </ViewModeSelector>
      </ControlGroup>

      <Divider />

      {/* Search */}
      {enableSearch && (
        <SearchContainer>
          <span style={{ fontSize: '13px', color: '#666' }}>🔍</span>
          <SearchInput
            type="text"
            placeholder="Search data..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </SearchContainer>
      )}

      <Divider />

      {/* Controls */}
      <ControlGroup>
        <IconButton onClick={onToggleSidebar}>
          {showSidebar ? '◀️' : '▶️'} {showSidebar ? 'Hide' : 'Show'} Panel
        </IconButton>

        {enableExport && (
          <>
            <IconButton onClick={() => onExport('csv')}>
              📄 CSV
            </IconButton>
            <IconButton onClick={() => onExport('xlsx')}>
              📊 Excel
            </IconButton>
          </>
        )}

        <IconButton onClick={() => window.location.reload()}>
          🔄 Refresh
        </IconButton>
      </ControlGroup>
    </ToolbarContainer>
  );
};

export default memo(ToolbarControls); 