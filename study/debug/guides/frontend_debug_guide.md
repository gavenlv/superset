# 🎨 Superset前端调试指南

## 🚀 前端开发环境启动

```bash
# 1. 进入前端目录
cd superset-frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器 (带热重载)
npm run dev

# 4. 开启源码调试模式
npm run dev-server -- --devtool source-map
```

## 🔧 Chrome DevTools调试

### 1. React开发者工具
```bash
# 安装React DevTools扩展
# Chrome扩展商店搜索: "React Developer Tools"
```

**使用技巧:**
- 🔍 **组件树检查**: 查看组件层次结构
- 📊 **Props/State查看**: 实时查看组件状态
- ⚡ **Profiler**: 性能分析工具
- 🎯 **Hook调试**: 查看useState、useEffect等Hook状态

### 2. Redux DevTools
```bash
# 安装Redux DevTools扩展
# Chrome扩展商店搜索: "Redux DevTools"
```

**调试功能:**
- 📈 **Action追踪**: 查看所有dispatch的action
- 🕒 **时间旅行**: 回退到任意状态
- 🎛️ **状态检查**: 实时查看store状态
- 📝 **Action重放**: 重新执行特定action

## 💻 代码调试技巧

### 1. Console调试
```javascript
// 在React组件中添加调试代码
export const DashboardComponent = ({ dashboard }) => {
  // 基础调试
  console.log('Dashboard data:', dashboard);
  
  // 表格形式显示对象
  console.table(dashboard.slices);
  
  // 分组日志
  console.group('Dashboard Debug Info');
  console.log('Title:', dashboard.dashboard_title);
  console.log('Slices count:', dashboard.slices?.length);
  console.groupEnd();
  
  // 条件调试
  if (dashboard.slices?.length > 10) {
    console.warn('Large dashboard detected:', dashboard.slices.length);
  }
  
  return <div>...</div>;
};
```

### 2. Debugger断点
```javascript
// 在代码中设置断点
export const ChartContainer = ({ chartId, formData }) => {
  // 浏览器会在这里暂停
  debugger;
  
  // 或者条件断点
  if (chartId === 123) {
    debugger;
  }
  
  const handleDataLoad = (data) => {
    debugger; // 数据加载时断点
    setChartData(data);
  };
  
  return <Chart onDataLoad={handleDataLoad} />;
};
```

### 3. 网络请求调试
```javascript
// 拦截和调试API请求
import { SupersetClient } from '@superset-ui/core';

// 添加请求拦截器
SupersetClient.configure({
  debug: true,
  requestInterceptor: (request) => {
    console.log('API Request:', request);
    return request;
  },
  responseInterceptor: (response) => {
    console.log('API Response:', response);
    return response;
  }
});
```

## 🎛️ 开发工具配置

### VS Code调试配置
创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Chrome",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:9000",
      "webRoot": "${workspaceFolder}/superset-frontend/src",
      "sourceMapPathOverrides": {
        "webpack:///./src/*": "${webRoot}/*"
      }
    },
    {
      "name": "Attach to Chrome",
      "type": "chrome",
      "request": "attach",
      "port": 9222,
      "webRoot": "${workspaceFolder}/superset-frontend/src"
    }
  ]
}
```

### Webpack配置优化
```javascript
// webpack.config.js 调试配置
module.exports = {
  mode: 'development',
  devtool: 'eval-source-map', // 最佳调试体验
  
  // 开发服务器配置
  devServer: {
    hot: true,
    liveReload: true,
    open: true,
  },
  
  // 源码映射配置
  optimization: {
    minimize: false, // 开发环境不压缩代码
  }
};
```

## 🐛 常见问题调试

### 1. 组件状态问题
```javascript
// 使用useEffect调试状态变化
import { useEffect } from 'react';

export const MyComponent = ({ data }) => {
  const [state, setState] = useState(null);
  
  // 调试状态变化
  useEffect(() => {
    console.log('State changed:', state);
  }, [state]);
  
  // 调试props变化
  useEffect(() => {
    console.log('Data prop changed:', data);
  }, [data]);
  
  return <div>...</div>;
};
```

### 2. 异步操作调试
```javascript
// 调试async/await操作
const loadDashboardData = async (dashboardId) => {
  try {
    console.log('Loading dashboard:', dashboardId);
    
    const response = await SupersetClient.get({
      endpoint: `/api/v1/dashboard/${dashboardId}`
    });
    
    console.log('Dashboard loaded:', response.json);
    return response.json;
    
  } catch (error) {
    console.error('Dashboard load failed:', error);
    debugger; // 在错误时断点
    throw error;
  }
};
```

### 3. Redux状态调试
```javascript
// 在reducer中添加调试
const dashboardReducer = (state = initialState, action) => {
  console.log('Reducer action:', action.type, action.payload);
  
  switch (action.type) {
    case 'SET_DASHBOARD_DATA':
      const newState = {
        ...state,
        data: action.payload
      };
      console.log('State transition:', state, '->', newState);
      return newState;
      
    default:
      return state;
  }
};
```

## 📊 性能调试

### 1. React Profiler
```javascript
import { Profiler } from 'react';

const onRenderCallback = (id, phase, actualDuration) => {
  console.log('Component render:', {
    id,
    phase,
    duration: actualDuration
  });
};

export const App = () => (
  <Profiler id="Dashboard" onRender={onRenderCallback}>
    <Dashboard />
  </Profiler>
);
```

### 2. 内存泄漏检测
```javascript
// 检测组件卸载
export const MyComponent = () => {
  useEffect(() => {
    console.log('Component mounted');
    
    return () => {
      console.log('Component unmounted');
    };
  }, []);
  
  return <div>...</div>;
};
```

## 🔍 调试最佳实践

### 1. 分层调试策略
```
🎯 前端调试层次:
├── 🌐 网络层 (API请求/响应)
├── 🔄 状态层 (Redux store)
├── 🧩 组件层 (Props/State)
├── 🎨 渲染层 (DOM更新)
└── 👆 交互层 (用户事件)
```

### 2. 调试工具优先级
1. **React DevTools** - 组件状态检查
2. **Redux DevTools** - 应用状态管理
3. **Chrome DevTools** - 网络和性能
4. **Console.log** - 快速值检查
5. **Debugger** - 复杂逻辑断点

### 3. 生产环境调试
```javascript
// 只在开发环境启用调试代码
if (process.env.NODE_ENV === 'development') {
  console.log('Debug info:', data);
}

// 使用debug库进行条件调试
import debug from 'debug';
const log = debug('superset:dashboard');
log('Dashboard data loaded:', data);
``` 