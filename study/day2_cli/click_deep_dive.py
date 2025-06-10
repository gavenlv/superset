#!/usr/bin/env python3
"""
Click 装饰器深度演示脚本
Day 2 - CLI 学习辅助工具

这个脚本展示了 Click 装饰器的各种高级用法和内部机制
运行: python click_deep_dive.py --help
"""
import click
import json
import time
from pathlib import Path
import sys


# ========== 基础 Click 装饰器演示 ==========

@click.command()
@click.option('--name', default='World', help='要问候的人')
@click.option('--count', default=1, type=int, help='重复次数')
@click.option('--loud', is_flag=True, help='大声说话')
def basic_hello(name, count, loud):
    """基础 Click 命令示例"""
    greeting = f"Hello, {name}!"
    if loud:
        greeting = greeting.upper()
    
    for i in range(count):
        click.echo(f"{i+1}. {greeting}")


# ========== 高级类型转换演示 ==========

class PortType(click.ParamType):
    """自定义端口类型验证器"""
    name = 'port'
    
    def convert(self, value, param, ctx):
        try:
            port = int(value)
            if not 1 <= port <= 65535:
                self.fail(f'{value} 不是有效的端口号 (1-65535)', param, ctx)
            return port
        except ValueError:
            self.fail(f'{value} 不是有效的整数', param, ctx)


PORT = PortType()

@click.command()
@click.option('--host', default='localhost', 
              help='服务器地址',
              type=click.Choice(['localhost', '127.0.0.1', '0.0.0.0']))
@click.option('--port', default=8088, type=PORT, help='端口号')
@click.option('--ssl/--no-ssl', default=False, help='是否启用 SSL')
def server_config(host, port, ssl):
    """演示高级类型转换和验证"""
    protocol = 'https' if ssl else 'http'
    url = f"{protocol}://{host}:{port}"
    
    click.echo(f"🌐 服务器配置:")
    click.echo(f"   地址: {host}")
    click.echo(f"   端口: {port}")
    click.echo(f"   SSL: {'启用' if ssl else '禁用'}")
    click.echo(f"   完整URL: {url}")


# ========== 参数验证与回调演示 ==========

def validate_config_file(ctx, param, value):
    """配置文件验证回调"""
    if value is None:
        return None
    
    config_path = Path(value)
    if not config_path.exists():
        click.echo(f"⚠️  配置文件不存在: {value}", err=True)
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        click.echo(f"✅ 成功加载配置文件: {value}")
        return config
    except json.JSONDecodeError as e:
        click.echo(f"❌ 配置文件格式错误: {e}", err=True)
        raise click.BadParameter(f"配置文件 {value} 不是有效的 JSON 格式")


@click.command()
@click.option('--config', 
              callback=validate_config_file,
              help='配置文件路径 (JSON格式)')
@click.option('--debug', is_flag=True, help='调试模式')
def load_config(config, debug):
    """演示参数验证和回调处理"""
    if debug:
        click.echo("🐛 调试模式已启用")
    
    if config:
        click.echo("📄 配置内容:")
        for key, value in config.items():
            click.echo(f"   {key}: {value}")
    else:
        click.echo("📄 使用默认配置")


# ========== 命令组和子命令演示 ==========

@click.group()
@click.option('--verbose', is_flag=True, help='详细输出')
@click.pass_context
def cli(ctx, verbose):
    """Click 命令组演示 - 模拟 Superset CLI"""
    # 确保上下文对象存在
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        click.echo("🔍 详细模式已启用")


@cli.command()
@click.option('--force', is_flag=True, help='强制重新初始化')
@click.pass_context
def init(ctx, force):
    """初始化应用 (模拟 superset init)"""
    verbose = ctx.obj.get('verbose', False)
    
    if verbose:
        click.echo("🚀 开始初始化...")
    
    if force:
        click.echo("⚠️  强制模式：将覆盖现有数据")
    
    # 模拟初始化过程
    with click.progressbar(range(5), label='初始化进度') as progress:
        for i in progress:
            time.sleep(0.5)  # 模拟工作
    
    click.echo("✅ 初始化完成!")


@cli.command()
@click.option('--sample-data', is_flag=True, help='包含示例数据')
@click.option('--batch-size', default=1000, type=int, help='批处理大小')
@click.pass_context
def load_examples(ctx, sample_data, batch_size):
    """加载示例数据 (模拟 superset load_examples)"""
    verbose = ctx.obj.get('verbose', False)
    
    if verbose:
        click.echo(f"📊 批处理大小: {batch_size}")
    
    if sample_data:
        click.echo("🎲 包含示例数据")
    
    # 模拟数据加载
    datasets = ['销售数据', '用户统计', '产品分析', '财务报表']
    
    with click.progressbar(datasets, label='加载数据集') as progress:
        for dataset in progress:
            if verbose:
                click.echo(f"\n   正在加载: {dataset}")
            time.sleep(0.3)
    
    click.echo("\n📈 示例数据加载完成!")


@cli.command()
@click.option('-h', '--host', default='localhost', help='主机地址')
@click.option('-p', '--port', default=8088, type=PORT, help='端口号')
@click.option('--debug', is_flag=True, help='调试模式')
@click.option('--reload', is_flag=True, help='自动重载')
def run(host, port, debug, reload):
    """启动开发服务器 (模拟 superset run)"""
    click.echo("🚀 启动 Superset 开发服务器...")
    click.echo(f"   地址: {host}:{port}")
    click.echo(f"   调试模式: {'开启' if debug else '关闭'}")
    click.echo(f"   自动重载: {'开启' if reload else '关闭'}")
    
    if debug:
        click.echo("⚠️  调试模式不应在生产环境中使用!")
    
    click.echo("\n按 Ctrl+C 停止服务器")
    click.echo("(这只是演示，不会真正启动服务器)")


# ========== 动态装饰器演示 ==========

def add_database_options(func):
    """动态添加数据库相关选项"""
    func = click.option('--database-url', 
                       envvar='DATABASE_URL',
                       help='数据库连接URL')(func)
    func = click.option('--pool-size', 
                       default=5, 
                       type=int,
                       help='连接池大小')(func)
    return func


@cli.command()
@add_database_options
@click.option('--timeout', default=30, type=int, help='超时时间(秒)')
def db_test(database_url, pool_size, timeout):
    """数据库连接测试 (演示动态装饰器)"""
    click.echo("🔌 测试数据库连接...")
    click.echo(f"   URL: {database_url or '使用默认配置'}")
    click.echo(f"   连接池大小: {pool_size}")
    click.echo(f"   超时时间: {timeout}秒")
    
    # 模拟连接测试
    with click.progressbar(range(3), label='连接测试') as progress:
        for i in progress:
            time.sleep(0.5)
    
    click.echo("✅ 数据库连接正常!")


# ========== 错误处理演示 ==========

@cli.command()
@click.option('--fail-mode', 
              type=click.Choice(['none', 'early', 'late']),
              default='none',
              help='失败模式')
def error_demo(fail_mode):
    """错误处理演示"""
    click.echo(f"🎭 错误演示模式: {fail_mode}")
    
    try:
        if fail_mode == 'early':
            raise click.BadParameter("这是一个参数错误示例")
        elif fail_mode == 'late':
            click.echo("开始处理...")
            time.sleep(1)
            raise click.ClickException("这是一个运行时错误示例")
        else:
            click.echo("✅ 正常执行完成")
            
    except click.ClickException as e:
        click.echo(f"❌ 捕获到 Click 异常: {e}", err=True)
        raise  # 重新抛出让 Click 处理
    except Exception as e:
        click.echo(f"💥 未预期的错误: {e}", err=True)
        raise click.Abort()


# ========== 主入口 ==========

if __name__ == '__main__':
    # 添加帮助信息
    cli.help = """
    🎓 Click 装饰器深度演示工具
    
    这个工具演示了 Click 装饰器的各种用法：
    
    基础命令:
      basic-hello    - 基础装饰器使用
      server-config  - 高级类型转换
      load-config    - 参数验证回调
    
    命令组演示:
      init           - 应用初始化
      load-examples  - 加载示例数据  
      run            - 启动服务器
      db-test        - 数据库测试
      error-demo     - 错误处理
    
    试试这些命令:
      python click_deep_dive.py --help
      python click_deep_dive.py basic-hello --name "张三" --count 3 --loud
      python click_deep_dive.py server-config --host localhost --port 8080 --ssl
      python click_deep_dive.py --verbose init --force
      python click_deep_dive.py run --debug --reload
    """
    
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n👋 用户中断，再见!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"\n💥 未处理的异常: {e}", err=True)
        sys.exit(1) 