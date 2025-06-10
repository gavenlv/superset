# Superset 学习指南 - Day 2: 实践练习

理论结合实践是最好的学习方式。现在，让我们亲手运行昨天学到的 CLI 命令，来初始化并启动一个功能完备的 Superset 实例。

请打开你的终端，并确保你处于 Superset 项目的根目录下，并且你的虚拟环境已经激活。

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

干得漂亮！第二天学习结束。 