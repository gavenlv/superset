# Advanced Pivot Table Chart Plugin

A powerful and feature-rich pivot table chart plugin for Apache Superset that extends the standard pivot table with Tableau-like capabilities including multiple hierarchies, tree view, pinned columns, and enhanced grouping features.

## Features

### 🌳 **Multiple View Modes**
- **Table View**: Traditional flat table with enhanced features
- **Tree View**: Hierarchical tree structure for exploring data relationships  
- **Hybrid View**: Combination of tree navigation with detailed table display

### 📊 **Advanced Hierarchy Management**
- **Multiple Hierarchies**: Support for complex multi-level groupings
- **Hierarchy Groups**: Organize columns into logical grouping structures
- **Expandable/Collapsible Nodes**: Interactive exploration of data hierarchies
- **Configurable Hierarchy Levels**: Control the depth of hierarchy display

### 📌 **Pinned Columns**
- **Left/Right Pinning**: Pin important columns to left or right side
- **Customizable Width**: Adjust pinned column widths
- **Drag & Drop Reordering**: Intuitive column management
- **Visual Indicators**: Clear visual distinction for pinned columns

### 🔍 **Enhanced Interactivity**
- **Global Search**: Search across all data with real-time filtering
- **Column-Level Filtering**: Individual column filters
- **Multi-Column Sorting**: Sort by multiple columns simultaneously
- **Drill-Down Capabilities**: Navigate through data hierarchies
- **Context Menus**: Right-click actions for advanced operations

### 📈 **Performance Optimizations**
- **Virtual Scrolling**: Handle large datasets efficiently
- **Lazy Loading**: Load data on-demand for better performance
- **Optimized Rendering**: Smooth interactions even with complex hierarchies

### 📤 **Export Options**
- **CSV Export**: Standard comma-separated values
- **Excel Export**: Rich Excel format with formatting preserved
- **Filtered Data Export**: Export only visible/filtered data

### 🎨 **Visual Enhancements**
- **Conditional Formatting**: Color-code cells based on values
- **Hierarchy Lines**: Visual connection lines in tree view
- **Responsive Design**: Adapts to different screen sizes
- **Customizable Themes**: Match your organization's branding

## Configuration Options

### Basic Pivot Settings
- **Groupby Rows**: Columns to group by on rows
- **Groupby Columns**: Columns to group by on columns  
- **Metrics**: Measures to aggregate and display
- **Aggregation Function**: Sum, Count, Average, etc.
- **Transpose Pivot**: Swap rows and columns

### Advanced View Options
- **View Mode**: Table, Tree, or Hybrid view
- **Enable Tree View**: Toggle hierarchical display
- **Enable Drill Down**: Allow navigation through hierarchies
- **Hierarchy Mode**: Single or multiple hierarchy support
- **Max Hierarchy Levels**: Limit the depth of hierarchy display
- **Tree Indent Size**: Control indentation in tree view
- **Show Hierarchy Lines**: Display connecting lines

### Table Features
- **Virtual Scrolling**: Enable for large datasets
- **Row Height**: Customize row height in pixels
- **Column Reordering**: Allow drag-and-drop column reordering
- **Search**: Global search functionality
- **Column Filtering**: Per-column filtering
- **Sorting**: Multi-column sorting support
- **Export**: CSV and Excel export options

### Formatting Options
- **Value Format**: Number formatting for metrics
- **Currency Format**: Currency symbol and positioning
- **Date Format**: Date/time display format
- **Conditional Formatting**: Color-coding rules

## Usage Examples

### Basic Pivot Table
```javascript
// Simple sales data pivot
{
  groupbyRows: ['region', 'country'],
  groupbyColumns: ['product_category'],
  metrics: ['sum__sales_amount'],
  viewMode: 'TABLE',
  aggregateFunction: 'Sum'
}
```

### Hierarchical Tree View
```javascript
// Multi-level organizational data
{
  groupbyRows: ['department', 'team', 'employee'],
  metrics: ['sum__revenue', 'count__projects'],
  viewMode: 'TREE',
  enableTreeView: true,
  hierarchyMode: 'MULTIPLE',
  maxHierarchyLevels: 3,
  showHierarchyLines: true
}
```

### Hybrid View with Pinned Columns
```javascript
// Financial data with key metrics pinned
{
  groupbyRows: ['account_type', 'account_name'],
  groupbyColumns: ['quarter'],
  metrics: ['sum__amount'],
  viewMode: 'HYBRID',
  pinnedColumns: [
    { column: 'account_name', position: 'left', width: 200 },
    { column: 'total_amount', position: 'right', width: 150 }
  ]
}
```

## Technical Implementation

### Component Architecture
```
AdvancedPivotTableChart (Main Component)
├── ToolbarControls (View controls, search, export)
├── HierarchyManager (Sidebar hierarchy management)
├── PinnedColumnsManager (Sidebar pinned columns)
└── Content Renderers:
    ├── TableViewRenderer (Traditional table)
    ├── TreeViewRenderer (Hierarchical tree)
    └── HybridViewRenderer (Combined view)
```

### Key Technologies
- **React**: Component framework
- **TypeScript**: Type safety and developer experience
- **Styled Components**: CSS-in-JS styling
- **React Window**: Virtual scrolling for performance
- **Superset UI Core**: Integration with Superset framework

### Data Flow
1. **Query Building**: Transform form data into database queries
2. **Data Processing**: Process query results into tree structures
3. **Rendering**: Display data based on selected view mode
4. **Interaction Handling**: Manage user interactions and state updates

## Installation

1. Place the plugin in the Superset plugins directory:
```bash
superset-frontend/plugins/plugin-chart-advanced-pivot-table/
```

2. Register the plugin in your Superset configuration:
```python
# superset_config.py
CUSTOM_VIZ_MANIFEST = {
    'advanced_pivot_table': {
        'module': 'superset-frontend/plugins/plugin-chart-advanced-pivot-table',
        'bundle': True
    }
}
```

3. Build the frontend:
```bash
cd superset-frontend
npm run build
```

## Browser Support

- Chrome 70+
- Firefox 65+
- Safari 12+
- Edge 79+

## Performance Considerations

- **Large Datasets**: Use virtual scrolling for tables with >1000 rows
- **Complex Hierarchies**: Limit hierarchy levels to 5 or fewer for optimal performance
- **Real-time Updates**: Consider data refresh intervals for frequently changing data

## Contributing

Please follow the Superset contribution guidelines when submitting improvements or bug fixes.

## License

Licensed under the Apache License, Version 2.0 