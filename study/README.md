# Superset 源码学习资料

本目录包含了 Apache Superset 源码学习的所有相关资料，按天、主题和文件类型进行了清晰的组织。

## 📁 目录结构

```
study/
├── README.md              # 本说明文件
├── study_guide.md         # 总体学习指南和规划
│
├── day1_flask_architecture/   # 第一天：Flask 应用架构
│   ├── day1_learning_notes.md        # 学习笔记
│   ├── day1_practice.py              # 实践脚本
│   ├── simple_debug_start.py         # 应用启动调试脚本
│   ├── debug_config.py               # 配置调试脚本
│   └── test_db_connection.py         # 数据库连接测试
│
├── day2_cli/                  # 第二天：命令行接口 (CLI)
│   ├── day2_learning_notes.md        # 深度源码分析笔记（含装饰器专题）
│   ├── day2_practice.md              # 实践指南
│   ├── decorator_practice.py         # 装饰器原理演示脚本
│   ├── debug_diagnostic.py          # CLI 环境诊断工具
│   └── debug_manual_start.py        # 手动启动脚本
│
└── debug/                 # 调试工具和指南
    ├── guides/            # 调试指南文档
    │   ├── debug_setup_guide.md      # 调试环境设置
    │   ├── debug_troubleshooting.md  # 故障排除指南
    │   ├── frontend_debug_guide.md   # 前端调试指南
    │   └── database_debug_guide.md   # 数据库调试指南
    └── scripts/           # 调试脚本工具
        ├── debug_config.py           # 调试配置
        ├── debug_diagnostic.py      # 环境诊断工具
        ├── debug_manual_start.py     # 手动启动脚本
        ├── debug_test.py             # 调试测试脚本
        ├── python_debug_examples.py  # Python 调试示例
        ├── simple_debug_start.py     # 简化启动脚本
        └── test_db_connection.py     # 数据库连接测试
```

## 🚀 快速开始

### 新手入门
1. 先阅读 [`study_guide.md`](study_guide.md) 了解整体学习计划
2. 按天数顺序学习：
   - **Day 1**: [`day1_flask_architecture/day1_learning_notes.md`](day1_flask_architecture/day1_learning_notes.md) + [`day1_flask_architecture/day1_practice.py`](day1_flask_architecture/day1_practice.py)
   - **Day 2**: [`day2_cli/day2_learning_notes.md`](day2_cli/day2_learning_notes.md) + [`day2_cli/day2_practice.md`](day2_cli/day2_practice.md)
     - 💡 **特别推荐**: 运行 `day2_cli/decorator_practice.py` 来深入理解装饰器原理

### 遇到调试问题
1. 查看 [`debug/guides/debug_setup_guide.md`](debug/guides/debug_setup_guide.md) 设置调试环境
2. 运行 [`debug/scripts/debug_diagnostic.py`](debug/scripts/debug_diagnostic.py) 诊断问题
3. 参考对应的调试指南解决具体问题

### 快速启动 Superset
使用简化脚本快速启动：
```bash
cd study/debug/scripts
python simple_debug_start.py
```

## 📚 学习建议

- **循序渐进**: 严格按照天数顺序学习，不要跳跃
- **理论结合实践**: 每天的学习都包含理论笔记和实践环节
- **善用调试工具**: 遇到问题时，优先使用 `debug/` 目录下的工具
- **做好笔记**: 在学习过程中记录自己的思考和发现

## 🔧 维护说明

这个目录结构的设计原则：
- **按天组织**: 每天的学习内容独立成目录，文件直接放在对应天数目录下
- **简化层级**: 避免过多的子目录层级，方便快速定位文件
- **按主题归档**: 调试相关的所有资料集中在 debug 目录
- **便于扩展**: 后续可以轻松添加 day3、day4 等新内容

---

Happy Learning! 🎯 