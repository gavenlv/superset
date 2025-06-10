# 🔧 Superset调试环境搭建指南

## 🚀 快速环境搭建

### 方法1: Docker开发环境 (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/apache/superset.git
cd superset

# 2. 启动开发环境
docker-compose -f docker-compose-non-dev.yml up -d

# 3. 进入容器进行调试
docker-compose exec superset bash

# 4. 在容器内安装调试工具
pip install ipdb pdb-attach
```

### 方法2: 本地开发环境

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -e .
pip install -r requirements/development.txt

# 3. 安装调试工具
pip install ipdb pudb pdb-attach ipython

# 4. 前端依赖
cd superset-frontend
npm install
npm run dev
```

## 🔍 调试工具配置

### VS Code配置
创建 `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Superset Debug",
            "type": "python",
            "request": "launch",
            "module": "superset.cli.main",
            "args": ["run", "-p", "8088", "--with-threads", "--reload", "--debugger"],
            "console": "integratedTerminal",
            "env": {
                "FLASK_ENV": "development",
                "SUPERSET_CONFIG": "debug_config"
            },
            "justMyCode": false
        },
        {
            "name": "Python: Test Single File",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["${file}", "-v", "-s"],
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

### PyCharm配置
1. File → Settings → Project → Python Interpreter
2. 添加项目虚拟环境
3. Run/Debug Configurations → Add New → Python
4. Script path: `superset/cli/main.py`
5. Parameters: `run -p 8088 --with-threads --reload --debugger` 