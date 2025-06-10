# 🔧 VS Code + Superset 调试完整设置指南

## 📋 前置准备

### 1. 确保项目结构正确
```
superset/                     # 项目根目录
├── .vscode/                 # ✅ 这里放VS Code配置
│   ├── launch.json         # ✅ 调试配置
│   └── settings.json       # ✅ 项目设置
├── debug_config.py         # ✅ 调试专用配置
├── superset/               # Python源代码
├── superset-frontend/      # 前端源代码
└── venv/                   # Python虚拟环境
```

### 2. 安装必要的VS Code扩展
```bash
# 必需扩展
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Debugger for Chrome (msjsdiag.debugger-for-chrome)

# 推荐扩展
- Python Docstring Generator
- autoDocstring
- GitLens
- Thunder Client (API测试)
```

### 3. 配置Python环境
```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

# 3. 安装依赖
pip install -e .
pip install -r requirements/development.txt

# 4. 初始化数据库
export SUPERSET_CONFIG_PATH=debug_config
superset db upgrade
superset fab create-admin
superset init
```

## 🚀 启动调试的详细步骤

### 步骤1: 选择Python解释器
1. 按 `Ctrl+Shift+P` 打开命令面板
2. 输入 `Python: Select Interpreter`
3. 选择项目中的虚拟环境: `./venv/bin/python`

### 步骤2: 设置断点
```python
# 在你想调试的代码行左侧点击，设置断点
# 例如在 superset/models/core.py 中
def get_df(self, sql, schema=None):
    # 这里设置断点 🔴
    logger.debug(f"Executing SQL: {sql}")
    ...
```

### 步骤3: 启动调试
1. 按 `Ctrl+Shift+D` 打开调试面板
2. 在下拉菜单中选择 `🚀 Superset: Debug Server`
3. 按 `F5` 或点击绿色播放按钮

### 步骤4: 验证调试启动成功
```bash
# 终端应该显示类似输出:
🔧 调试配置已加载
📊 数据库: sqlite:///superset_debug.db
🔍 调试模式: True
📝 SQL日志: True

 * Environment: development
 * Debug mode: on
 * Running on http://127.0.0.1:8088/
```

## 🎯 不同调试场景的启动方法

### 1. 调试Web服务器
```json
配置: "🚀 Superset: Debug Server"
用途: 调试Web请求、API端点、页面渲染
启动: F5 → 浏览器访问 http://localhost:8088
```

### 2. 调试测试用例
```json
配置: "🧪 Superset: Debug Tests"  
用途: 调试单元测试、集成测试
启动: 
1. 打开测试文件 (如 tests/charts/test_api.py)
2. F5 → 会调试当前打开的测试文件
```

### 3. 调试当前文件
```json
配置: "🔍 Superset: Debug Current File"
用途: 调试独立的Python脚本
启动:
1. 打开要调试的.py文件
2. F5 → 会执行并调试当前文件
```

### 4. 调试CLI命令
```json
配置: "⚙️ Superset: Debug CLI Command"
用途: 调试superset命令行工具
启动: F5 → 会执行 superset db upgrade 命令
```

### 5. 全栈调试
```json
配置: "🔥 Full Stack Debug"
用途: 同时调试后端和前端
启动: 
1. 确保前端开发服务器已启动 (npm run dev)
2. F5 → 同时启动后端调试和前端调试
```

## 🔍 调试技巧

### 1. 断点调试
```python
# 在代码中设置断点，程序会在断点处暂停
# 你可以:
# - 查看变量值
# - 单步执行 (F10)
# - 进入函数 (F11)  
# - 继续执行 (F5)
# - 查看调用堆栈
```

### 2. 条件断点
```python
# 右键断点 → "编辑断点" → 添加条件
# 例如: user_id == 123
# 只有当条件为True时才会暂停
```

### 3. 日志断点
```python
# 右键断点 → "编辑断点" → 选择"日志消息"
# 输入: "User {user_id} is accessing dashboard {dashboard_id}"
# 不会暂停程序，但会输出日志
```

### 4. 异常断点
```python
# 调试面板 → 断点 → 勾选"未捕获的异常"
# 程序遇到未处理异常时会自动暂停
```

## 🐛 常见问题解决

### 问题1: "No module named 'superset'"
```bash
解决方案:
1. 确保激活了正确的虚拟环境
2. 检查launch.json中的PYTHONPATH设置
3. 在项目根目录运行: pip install -e .
```

### 问题2: 调试器无法连接到Chrome
```bash
解决方案:
1. 确保Chrome已启动前端开发服务器
2. 启动Chrome时添加调试参数:
   chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
3. 确保前端开发服务器运行在端口9000
```

### 问题3: 断点不生效
```bash
解决方案:
1. 确保设置了justMyCode: false
2. 检查源码映射是否正确
3. 重新启动调试会话
4. 清理Python缓存: find . -name "*.pyc" -delete
```

### 问题4: 数据库连接失败
```bash
解决方案:
1. 检查debug_config.py中的数据库配置
2. 确保SQLite文件权限正确
3. 运行数据库初始化: superset db upgrade
```

## 📊 调试性能优化

### 1. 加快启动速度
```python
# 在debug_config.py中:
SQLALCHEMY_ECHO = False  # 调试SQL时才开启
CACHE_CONFIG = {'CACHE_TYPE': 'SimpleCache'}  # 使用简单缓存
```

### 2. 减少内存占用
```bash
# 限制VS Code扩展
# 只启用必要的Python和调试扩展
# 关闭不需要的功能: Pylint、Type Checking等
```

### 3. 热重载配置
```json
// 在launch.json中确保有--reload参数
"args": ["run", "-p", "8088", "--reload", "--debugger"]
```

## 🎯 调试最佳实践

1. **分层调试**: 先调试模型层，再调试视图层，最后调试前端
2. **小步调试**: 每次只专注一个小功能的调试
3. **日志先行**: 结合日志和断点，快速定位问题
4. **保存配置**: 为不同的调试场景保存不同的launch配置
5. **版本控制**: 将.vscode/launch.json加入git版本控制，团队共享配置 