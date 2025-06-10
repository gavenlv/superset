# Superset 学习指南 - Day 2: 实践练习

理论结合实践是最好的学习方式。现在，让我们亲手运行昨天学到的 CLI 命令，来初始化并启动一个功能完备的 Superset 实例。

请打开你的终端，并确保你处于 Superset 项目的根目录下，并且你的虚拟环境已经激活。

## 练习0: 装饰器原理理解 🎯

**目标**：通过实际代码理解装饰器的工作机制

**步骤**：
1. 进入练习目录并运行装饰器演示脚本：
   ```bash
   cd study/day2_cli
   python decorator_practice.py
   ```

2. 仔细观察输出，理解：
   - 装饰器的执行顺序（从下往上）
   - `@transaction()` 如何保证数据一致性
   - `@with_appcontext` 如何管理 Flask 上下文
   - 多个装饰器叠加的效果

3. 动手实验：
   - 尝试修改脚本中装饰器的顺序，观察输出变化
   - 在 `test_order()` 函数上添加/删除装饰器
   - 修改 `dangerous_database_operation()` 让它成功执行

**期望输出示例**：
```
============================================================
🎓 装饰器实践练习 - Day 2 CLI 学习
============================================================

1️⃣ 简单计时装饰器示例:
------------------------------
⏰ 开始执行 slow_function()
执行一些耗时的工作...
✅ slow_function() 执行完毕，耗时 1.00 秒

函数返回值: 工作完成！

2️⃣ 多装饰器叠加示例:
------------------------------
📝 调用函数: calculate_sum
📝 参数: args=(10, 20), kwargs={}
⏰ 开始执行 calculate_sum()
计算 10 + 20
✅ calculate_sum() 执行完毕，耗时 0.00 秒

📝 返回值: 30
最终结果: 30
...
```

**重点理解**：
- 装饰器就像"穿衣服"，给函数添加额外功能
- 执行顺序：最下面的装饰器最先执行
- Superset CLI 中的每个命令都被多个装饰器"包装"，获得了命令行调用、Flask上下文、事务管理等能力

## 练习1: 探索 CLI

首先，运行 `help` 命令，看看你的 Superset 版本都提供了哪些命令。尝试找到我们今天学习过的 `db`, `init`, `run`, `load-examples` 等命令。

```bash
superset --help
```

你也可以查看某个具体命令的帮助信息，比如 `run` 命令有哪些可用的参数：

```bash
superset run --help
```

## 练习2: 初始化 Superset

现在，我们将执行一套标准的初始化流程。**请严格按照以下顺序执行**。

### 步骤 1: 升级数据库

这个命令会根据 `migrations/` 目录下的脚本，在你的元数据数据库中创建或更新所有的表结构。

```bash
superset db upgrade
```

**预期输出**: 你会看到很多 `INFO` 日志，最后一行应该是 `INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.` (或你使用的数据库类型) 和 `OK`。

### 步骤 2: 初始化应用

创建角色、权限等核心元数据。

```bash
superset init
```

**预期输出**: 你会看到很多关于同步权限和角色的日志，最后应该没有报错信息。

## 练习3: 加载示例数据

让我们的 Superset 变得"有血有肉"。这个命令会花费几分钟时间，因为它需要创建数据源、上传数据、创建图表和仪表盘。

```bash
superset load_examples
```

**预期输出**: 你会看到很多 "Loading..." 和 "Creating..." 的日志。请耐心等待它完成。

## 练习4: 启动服务并探索

万事俱备！现在启动开发服务器。

```bash
superset run -p 8088 --with-threads --reload --debugger
```

服务器启动后，打开浏览器访问 `http://localhost:8088`。

你应该可以看到一个登录界面。**因为我们还没有创建管理员用户**，所以现在还无法登录。创建用户是第三天的内容。

不过，今天的目标已经达成：我们成功地使用 CLI 完成了 Superset 的完整初始化流程。

**思考题**:
1. 如果你先运行 `superset init` 再运行 `superset db upgrade` 会发生什么？为什么？
2. `superset load_examples` 加载的数据存储在哪里？是你的元数据数据库，还是一个独立的数据源？
3. **装饰器思考题**：
   - 为什么 `@with_appcontext` 总是在 `@transaction()` 的外层？如果交换顺序会怎样？
   - 如果一个CLI命令没有使用 `@transaction()` 装饰器，在执行过程中出错会发生什么？
   - 能否设计一个装饰器来自动重试失败的数据库操作？

## 深入练习（可选）

如果你想更深入理解装饰器，可以尝试：

1. **修改装饰器练习脚本**：
   - 添加一个 `@retry()` 装饰器，失败时自动重试
   - 创建一个 `@cache()` 装饰器，缓存函数执行结果
   - 实现一个 `@permission_required()` 装饰器，检查用户权限

2. **分析真实的 Superset 代码**：
   ```bash
   # 查找所有使用了 @with_appcontext 的函数
   grep -r "@with_appcontext" superset/cli/
   
   # 查看 transaction 装饰器的实现
   grep -r "def transaction" superset/
   ```

3. **创建自己的 CLI 命令**：
   - 参考 `superset/cli/main.py` 的模式
   - 创建一个简单的命令，使用我们学到的装饰器

干得漂亮！第二天学习结束。现在你不仅知道如何使用 Superset CLI，还深入理解了装饰器这个 Python 的重要特性！ 