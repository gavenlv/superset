#!/usr/bin/env python3
"""
Superset 数据库初始化自动化脚本
自动执行 Superset 数据库初始化的所有步骤
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('superset_init.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SupersetInitializer:
    def __init__(self):
        self.superset_dir = Path("D:/workspace/superset-github/superset")
        self.config_path = self.superset_dir / "superset_config.py"
        self.venv_path = self.superset_dir / ".venv"
        
    def check_environment(self):
        """检查环境配置"""
        logger.info("🔍 检查环境配置...")
        
        # 检查工作目录
        if not self.superset_dir.exists():
            logger.error(f"❌ Superset 目录不存在: {self.superset_dir}")
            return False
            
        # 检查配置文件
        if not self.config_path.exists():
            logger.error(f"❌ 配置文件不存在: {self.config_path}")
            return False
            
        # 检查虚拟环境
        if not self.venv_path.exists():
            logger.error(f"❌ 虚拟环境不存在: {self.venv_path}")
            return False
            
        # 检查环境变量
        config_env = os.environ.get('SUPERSET_CONFIG_PATH')
        if not config_env:
            logger.warning("⚠️ 环境变量 SUPERSET_CONFIG_PATH 未设置")
            os.environ['SUPERSET_CONFIG_PATH'] = str(self.config_path)
            logger.info(f"✅ 已设置 SUPERSET_CONFIG_PATH: {self.config_path}")
            
        logger.info("✅ 环境检查完成")
        return True
        
    def run_command(self, cmd, description):
        """运行命令并记录结果"""
        logger.info(f"🚀 执行: {description}")
        logger.info(f"命令: {cmd}")
        
        try:
            # 在 Windows 上使用 shell=True
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.superset_dir,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description} 成功")
                if result.stdout:
                    logger.info(f"输出: {result.stdout}")
                return True
            else:
                logger.error(f"❌ {description} 失败")
                logger.error(f"错误输出: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {description} 超时")
            return False
        except Exception as e:
            logger.error(f"❌ {description} 异常: {str(e)}")
            return False
            
    def activate_venv_and_run(self, command, description):
        """激活虚拟环境并运行命令"""
        # Windows 虚拟环境激活命令
        activate_cmd = f'"{self.venv_path}\\Scripts\\activate.bat"'
        full_cmd = f'{activate_cmd} && {command}'
        return self.run_command(full_cmd, description)
        
    def initialize_database(self):
        """初始化数据库"""
        logger.info("🔨 开始数据库初始化...")
        
        steps = [
            ("superset db upgrade", "数据库架构升级"),
            ("superset fab create-admin --username admin --firstname Admin --lastname User --email admin@superset.com --password admin123", "创建管理员用户"),
            ("superset init", "初始化 Superset")
        ]
        
        for cmd, desc in steps:
            if not self.activate_venv_and_run(cmd, desc):
                logger.error(f"❌ 初始化失败在步骤: {desc}")
                return False
                
        logger.info("✅ 数据库初始化完成!")
        return True
        
    def load_examples(self):
        """加载示例数据（可选）"""
        logger.info("📊 加载示例数据...")
        
        user_input = input("是否加载示例数据？这将帮助学习但需要更多时间 (y/N): ").strip().lower()
        
        if user_input in ['y', 'yes']:
            return self.activate_venv_and_run("superset load_examples", "加载示例数据")
        else:
            logger.info("⏭️ 跳过示例数据加载")
            return True
            
    def verify_installation(self):
        """验证安装"""
        logger.info("🔍 验证安装...")
        
        # 检查数据库表
        verify_script = """
import os
os.environ['SUPERSET_CONFIG_PATH'] = r'D:\\workspace\\superset-github\\superset\\superset_config.py'

from superset.app import create_app
from superset.extensions import db

app = create_app()
with app.app_context():
    engine = db.get_engine()
    with engine.connect() as conn:
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in result]
        print(f"数据库表数量: {len(tables)}")
        
        # 检查关键表
        key_tables = ['dashboards', 'slices', 'tables', 'datasources', 'ab_user']
        missing_tables = [table for table in key_tables if table not in tables]
        
        if missing_tables:
            print(f"缺少关键表: {missing_tables}")
        else:
            print("✅ 所有关键表都存在")
"""
        
        verify_file = self.superset_dir / "verify_init.py"
        verify_file.write_text(verify_script, encoding='utf-8')
        
        success = self.activate_venv_and_run("python verify_init.py", "验证数据库表")
        
        # 清理临时文件
        verify_file.unlink()
        
        return success
        
    def run_full_initialization(self):
        """运行完整的初始化流程"""
        logger.info("🚀 开始 Superset 完整初始化流程...")
        
        # 步骤1: 检查环境
        if not self.check_environment():
            logger.error("❌ 环境检查失败，无法继续")
            return False
            
        # 步骤2: 初始化数据库
        if not self.initialize_database():
            logger.error("❌ 数据库初始化失败")
            return False
            
        # 步骤3: 加载示例数据（可选）
        if not self.load_examples():
            logger.error("❌ 示例数据加载失败")
            return False
            
        # 步骤4: 验证安装
        if not self.verify_installation():
            logger.error("❌ 安装验证失败")
            return False
            
        logger.info("🎉 Superset 初始化完成!")
        logger.info("📝 下一步:")
        logger.info("1. 在 VS Code 中启动调试 (F5)")
        logger.info("2. 或命令行运行: superset run -p 8088 --with-threads --reload --debugger")
        logger.info("3. 访问 http://localhost:8088")
        logger.info("4. 使用管理员账号登录: admin / admin123")
        
        return True

def main():
    """主函数"""
    print("🚀 Superset 数据库初始化工具")
    print("=" * 50)
    
    initializer = SupersetInitializer()
    
    try:
        success = initializer.run_full_initialization()
        
        if success:
            print("\n✅ 初始化成功完成!")
            print("现在您可以开始调试 Superset 了。")
        else:
            print("\n❌ 初始化失败!")
            print("请检查日志文件 superset_init.log 获取详细信息。")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户取消了初始化过程")
    except Exception as e:
        logger.error(f"❌ 未预期的错误: {str(e)}")
        print(f"\n❌ 发生未预期的错误: {str(e)}")

if __name__ == "__main__":
    main() 