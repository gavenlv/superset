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
  ensureIsArray,
  isAdhocColumn,
  isPhysicalColumn,
  QueryFormMetric,
  SMART_DATE_ID,
  t,
  validateNonEmpty,
} from '@superset-ui/core';
import {
  ControlPanelConfig,
  D3_TIME_FORMAT_OPTIONS,
  sharedControls,
  Dataset,
  getStandardizedControls,
} from '@superset-ui/chart-controls';
import { MetricsLayoutEnum, ViewModeEnum, HierarchyModeEnum } from '../types';

const config: ControlPanelConfig = {
  controlPanelSections: [
    {
      label: t('Query'),
      expanded: true,
      controlSetRows: [
        [
          {
            name: 'groupbyColumns',
            config: {
              ...sharedControls.groupby,
              label: t('Columns'),
              description: t('Columns to group by on the columns'),
            },
          },
        ],
        [
          {
            name: 'groupbyRows',
            config: {
              ...sharedControls.groupby,
              label: t('Rows'),
              description: t('Columns to group by on the rows'),
            },
          },
        ],
        [
          {
            name: 'metrics',
            config: {
              ...sharedControls.metrics,
              validators: [validateNonEmpty],
              rerender: ['conditional_formatting'],
            },
          },
        ],
        ['adhoc_filters'],
        ['series_limit'],
        [
          {
            name: 'row_limit',
            config: {
              ...sharedControls.row_limit,
              label: t('Cell limit'),
              description: t('Limits the number of cells that get retrieved.'),
            },
          },
        ],
      ],
    },
    {
      label: t('Advanced View Options'),
      expanded: true,
      controlSetRows: [
        [
          {
            name: 'viewMode',
            config: {
              type: 'RadioButtonControl',
              renderTrigger: true,
              label: t('View Mode'),
              default: ViewModeEnum.TABLE,
              options: [
                [ViewModeEnum.TABLE, t('Table View')],
                [ViewModeEnum.TREE, t('Tree View')],
                [ViewModeEnum.HYBRID, t('Hybrid View')],
              ],
              description: t('Choose how to display the data: traditional table, hierarchical tree, or hybrid view'),
            },
          },
        ],
        [
          {
            name: 'enableTreeView',
            config: {
              type: 'CheckboxControl',
              label: t('Enable Tree View'),
              default: true,
              description: t('Enable hierarchical tree view for grouped data'),
              renderTrigger: true,
            },
          },
          {
            name: 'enableDrillDown',
            config: {
              type: 'CheckboxControl',
              label: t('Enable Drill Down'),
              default: true,
              description: t('Allow users to drill down into data hierarchies'),
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'hierarchyMode',
            config: {
              type: 'RadioButtonControl',
              renderTrigger: true,
              label: t('Hierarchy Mode'),
              default: HierarchyModeEnum.SINGLE,
              options: [
                [HierarchyModeEnum.SINGLE, t('Single Hierarchy')],
                [HierarchyModeEnum.MULTIPLE, t('Multiple Hierarchies')],
              ],
              description: t('Single hierarchy shows one grouping at a time, multiple allows complex multi-level groupings'),
            },
          },
        ],
        [
          {
            name: 'maxHierarchyLevels',
            config: {
              type: 'TextControl',
              label: t('Max Hierarchy Levels'),
              default: 5,
              isInt: true,
              description: t('Maximum number of hierarchy levels to display'),
              renderTrigger: true,
            },
          },
          {
            name: 'treeIndentSize',
            config: {
              type: 'TextControl',
              label: t('Tree Indent Size'),
              default: 20,
              isInt: true,
              description: t('Pixel size for each level of tree indentation'),
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'showHierarchyLines',
            config: {
              type: 'CheckboxControl',
              label: t('Show Hierarchy Lines'),
              default: true,
              description: t('Display connecting lines in tree view'),
              renderTrigger: true,
            },
          },
        ],
      ],
    },
    {
      label: t('Table Features'),
      expanded: true,
      controlSetRows: [
        [
          {
            name: 'enableVirtualScrolling',
            config: {
              type: 'CheckboxControl',
              label: t('Virtual Scrolling'),
              default: false,
              description: t('Enable virtual scrolling for large datasets'),
              renderTrigger: true,
            },
          },
          {
            name: 'rowHeight',
            config: {
              type: 'TextControl',
              label: t('Row Height'),
              default: 32,
              isInt: true,
              description: t('Height of each table row in pixels'),
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'allowColumnReordering',
            config: {
              type: 'CheckboxControl',
              label: t('Allow Column Reordering'),
              default: true,
              description: t('Allow users to drag and reorder columns'),
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'enableSearch',
            config: {
              type: 'CheckboxControl',
              label: t('Enable Search'),
              default: true,
              description: t('Show search box for filtering data'),
              renderTrigger: true,
            },
          },
          {
            name: 'enableFiltering',
            config: {
              type: 'CheckboxControl',
              label: t('Enable Column Filtering'),
              default: true,
              description: t('Allow filtering on individual columns'),
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'enableSorting',
            config: {
              type: 'CheckboxControl',
              label: t('Enable Sorting'),
              default: true,
              description: t('Allow sorting by clicking column headers'),
              renderTrigger: true,
            },
          },
          {
            name: 'enableExport',
            config: {
              type: 'CheckboxControl',
              label: t('Enable Export'),
              default: true,
              description: t('Show export buttons for CSV and Excel'),
              renderTrigger: true,
            },
          },
        ],
      ],
    },
    {
      label: t('Pivot Options'),
      expanded: true,
      controlSetRows: [
        [
          {
            name: 'aggregateFunction',
            config: {
              type: 'SelectControl',
              label: t('Aggregation function'),
              clearable: false,
              choices: [
                ['Count', t('Count')],
                ['Count Unique Values', t('Count Unique Values')],
                ['List Unique Values', t('List Unique Values')],
                ['Sum', t('Sum')],
                ['Average', t('Average')],
                ['Median', t('Median')],
                ['Sample Variance', t('Sample Variance')],
                ['Sample Standard Deviation', t('Sample Standard Deviation')],
                ['Minimum', t('Minimum')],
                ['Maximum', t('Maximum')],
                ['First', t('First')],
                ['Last', t('Last')],
                ['Sum as Fraction of Total', t('Sum as Fraction of Total')],
                ['Sum as Fraction of Rows', t('Sum as Fraction of Rows')],
                ['Sum as Fraction of Columns', t('Sum as Fraction of Columns')],
                ['Count as Fraction of Total', t('Count as Fraction of Total')],
                ['Count as Fraction of Rows', t('Count as Fraction of Rows')],
                ['Count as Fraction of Columns', t('Count as Fraction of Columns')],
              ],
              default: 'Sum',
              description: t('Aggregate function to apply when pivoting and computing the total rows and columns'),
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'metricsLayout',
            config: {
              type: 'RadioButtonControl',
              renderTrigger: true,
              label: t('Apply metrics on'),
              default: MetricsLayoutEnum.COLUMNS,
              options: [
                [MetricsLayoutEnum.COLUMNS, t('Columns')],
                [MetricsLayoutEnum.ROWS, t('Rows')],
              ],
              description: t('Use metrics as a top level group for columns or for rows'),
            },
          },
        ],
        [
          {
            name: 'transposePivot',
            config: {
              type: 'CheckboxControl',
              label: t('Transpose pivot'),
              default: false,
              description: t('Swap rows and columns in the pivot table'),
              renderTrigger: true,
            },
          },
          {
            name: 'combineMetric',
            config: {
              type: 'CheckboxControl',
              label: t('Combine metrics'),
              default: false,
              description: t('Display metrics side by side within each column'),
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'rowTotals',
            config: {
              type: 'CheckboxControl',
              label: t('Show totals'),
              default: false,
              description: t('Display row-wise totals'),
              renderTrigger: true,
            },
          },
          {
            name: 'colTotals',
            config: {
              type: 'CheckboxControl',
              label: t('Show totals'),
              default: false,
              description: t('Display column-wise totals'),
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'rowSubTotals',
            config: {
              type: 'CheckboxControl',
              label: t('Show subtotals'),
              default: false,
              description: t('Display row-wise subtotals'),
              renderTrigger: true,
            },
          },
          {
            name: 'colSubTotals',
            config: {
              type: 'CheckboxControl',
              label: t('Show subtotals'),
              default: false,
              description: t('Display column-wise subtotals'),
              renderTrigger: true,
            },
          },
        ],
      ],
    },
    {
      label: t('Formatting'),
      expanded: true,
      controlSetRows: [
        [
          {
            name: 'valueFormat',
            config: {
              ...sharedControls.y_axis_format,
              label: t('Value format'),
            },
          },
        ],
        [
          {
            name: 'currencyFormat',
            config: {
              ...sharedControls.currency_format,
            },
          },
        ],
        [
          {
            name: 'dateFormat',
            config: {
              type: 'SelectControl',
              freeForm: true,
              label: t('Date format'),
              default: SMART_DATE_ID,
              choices: D3_TIME_FORMAT_OPTIONS,
              description: t('D3 time format for datetime columns'),
            },
          },
        ],
        [
          {
            name: 'conditional_formatting',
            config: {
              type: 'ConditionalFormattingControl',
              renderTrigger: true,
              label: t('Conditional formatting'),
              description: t('Apply conditional formatting to cells'),
            },
          },
        ],
      ],
    },
  ],
  controlOverrides: {
    groupbyColumns: {
      initialValue: [],
    },
    groupbyRows: {
      initialValue: [],
    },
    series_limit: {
      hidden: true,
    },
    series_limit_metric: {
      hidden: true,
    },
  },
};

export default config; 