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
import { PinnedColumn } from '../types';

const ManagerContainer = styled.div`
  padding: 16px;
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

const PinnedSection = styled.div`
  margin-bottom: 16px;
`;

const SectionTitle = styled.h5`
  margin: 0 0 8px 0;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ColumnItem = styled.div<{ position: 'left' | 'right' }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  margin-bottom: 6px;
  background: ${({ position }) => position === 'left' ? '#e6f7ff' : '#fff2e6'};
  border: 1px solid ${({ position }) => position === 'left' ? '#91d5ff' : '#ffcc99'};
  border-radius: 4px;
  font-size: 12px;
`;

const ColumnInfo = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
`;

const ColumnName = styled.span`
  font-weight: 500;
  color: #333;
`;

const ColumnMeta = styled.span`
  font-size: 10px;
  color: #666;
`;

const ColumnControls = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
`;

const ControlButton = styled.button`
  padding: 2px 4px;
  border: 1px solid #d9d9d9;
  border-radius: 3px;
  background: white;
  color: #666;
  cursor: pointer;
  font-size: 10px;
  
  &:hover {
    background: #f5f5f5;
  }
`;

const WidthInput = styled.input`
  width: 50px;
  padding: 2px 4px;
  border: 1px solid #d9d9d9;
  border-radius: 3px;
  font-size: 10px;
  text-align: center;
`;

const DragHandle = styled.div`
  padding: 2px;
  cursor: grab;
  color: #999;
  
  &:active {
    cursor: grabbing;
  }
  
  &::before {
    content: '⋮⋮';
    font-size: 8px;
    line-height: 1;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 20px 0;
  color: #999;
  font-size: 11px;
`;

const AvailableColumns = styled.div`
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background: #fafafa;
`;

const AvailableColumn = styled.div`
  padding: 6px 8px;
  border-bottom: 1px solid #e8e8e8;
  cursor: pointer;
  font-size: 11px;
  
  &:hover {
    background: #f0f0f0;
  }
  
  &:last-child {
    border-bottom: none;
  }
`;

interface PinnedColumnsManagerProps {
  pinnedColumns: PinnedColumn[];
  availableColumns: any[];
  onAddColumn?: (column: any, position: 'left' | 'right') => void;
  onRemoveColumn?: (column: any) => void;
  onUpdateWidth?: (column: any, width: number) => void;
  onMoveColumn?: (column: any, fromPosition: 'left' | 'right', toPosition: 'left' | 'right') => void;
  onReorderColumns?: (columns: PinnedColumn[]) => void;
}

const PinnedColumnsManager: React.FC<PinnedColumnsManagerProps> = ({
  pinnedColumns,
  availableColumns,
  onAddColumn,
  onRemoveColumn,
  onUpdateWidth,
  onMoveColumn,
  onReorderColumns,
}) => {
  const [showAvailable, setShowAvailable] = useState(false);
  
  const leftPinnedColumns = pinnedColumns.filter(col => col.position === 'left');
  const rightPinnedColumns = pinnedColumns.filter(col => col.position === 'right');
  
  const availableForPinning = availableColumns.filter(col => 
    !pinnedColumns.some(pinned => pinned.column === col)
  );

  const handleWidthChange = (column: any, width: string) => {
    const numericWidth = parseInt(width, 10);
    if (!isNaN(numericWidth) && numericWidth > 0) {
      onUpdateWidth?.(column, numericWidth);
    }
  };

  const renderColumnItem = (pinnedCol: PinnedColumn, index: number) => (
    <ColumnItem key={index} position={pinnedCol.position}>
      <DragHandle />
      <ColumnInfo>
        <ColumnName>{String(pinnedCol.column)}</ColumnName>
        <ColumnMeta>
          Width: <WidthInput
            type="number"
            value={pinnedCol.width || 150}
            onChange={(e) => handleWidthChange(pinnedCol.column, e.target.value)}
            min="50"
            max="500"
          />px
        </ColumnMeta>
      </ColumnInfo>
      <ColumnControls>
        <ControlButton
          onClick={() => onMoveColumn?.(
            pinnedCol.column,
            pinnedCol.position,
            pinnedCol.position === 'left' ? 'right' : 'left'
          )}
        >
          {pinnedCol.position === 'left' ? '→' : '←'}
        </ControlButton>
        <ControlButton onClick={() => onRemoveColumn?.(pinnedCol.column)}>
          ❌
        </ControlButton>
      </ColumnControls>
    </ColumnItem>
  );

  return (
    <ManagerContainer>
      <ManagerHeader>
        <ManagerTitle>Pinned Columns</ManagerTitle>
        <AddButton onClick={() => setShowAvailable(!showAvailable)}>
          {showAvailable ? 'Hide' : 'Add'}
        </AddButton>
      </ManagerHeader>

      {showAvailable && (
        <div style={{ marginBottom: '16px' }}>
          <SectionTitle>Available Columns</SectionTitle>
          <AvailableColumns>
            {availableForPinning.length === 0 ? (
              <EmptyState>All columns are already pinned</EmptyState>
            ) : (
              availableForPinning.map((col, index) => (
                <AvailableColumn
                  key={index}
                  onClick={() => onAddColumn?.(col, 'left')}
                >
                  {String(col)} 
                  <span style={{ float: 'right', color: '#999' }}>+ Pin Left</span>
                </AvailableColumn>
              ))
            )}
          </AvailableColumns>
        </div>
      )}

      <PinnedSection>
        <SectionTitle>📌 Left Pinned ({leftPinnedColumns.length})</SectionTitle>
        {leftPinnedColumns.length === 0 ? (
          <EmptyState>No left pinned columns</EmptyState>
        ) : (
          leftPinnedColumns.map(renderColumnItem)
        )}
      </PinnedSection>

      <PinnedSection>
        <SectionTitle>📌 Right Pinned ({rightPinnedColumns.length})</SectionTitle>
        {rightPinnedColumns.length === 0 ? (
          <EmptyState>No right pinned columns</EmptyState>
        ) : (
          rightPinnedColumns.map(renderColumnItem)
        )}
      </PinnedSection>

      <div style={{ fontSize: '10px', color: '#999', marginTop: '12px' }}>
        💡 Tip: Drag columns to reorder them within their pinned section
      </div>
    </ManagerContainer>
  );
};

export default memo(PinnedColumnsManager); 