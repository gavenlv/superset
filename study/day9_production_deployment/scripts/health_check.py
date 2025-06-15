#!/usr/bin/env python3
"""
Superset 健康检查脚本
监控 Superset 应用的各个组件状态
"""

import os
import sys
import time
import json
import logging
import argparse
import requests
import psycopg2
import redis
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/superset_health.log')
    ]
)
logger = logging.getLogger(__name__)

class HealthChecker:
    """Superset 健康检查器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results = {}
        
    def check_database(self) -> Tuple[bool, str]:
        """检查数据库连接"""
        try:
            db_config = self.config.get('database', {})
            conn = psycopg2.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 5432),
                database=db_config.get('database', 'superset'),
                user=db_config.get('user', 'superset'),
                password=db_config.get('password', '')
            )
            
            # 执行简单查询
            with conn.cursor() as cursor:
                cursor.execute('SELECT version();')
                version = cursor.fetchone()[0]
                
            conn.close()
            return True, f"数据库连接正常 - PostgreSQL {version.split()[1]}"
            
        except Exception as e:
            return False, f"数据库连接失败: {str(e)}"
    
    def check_redis(self) -> Tuple[bool, str]:
        """检查 Redis 连接"""
        try:
            redis_config = self.config.get('redis', {})
            r = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                password=redis_config.get('password', None),
                decode_responses=True
            )
            
            # 测试连接
            r.ping()
            info = r.info()
            
            return True, f"Redis 连接正常 - 版本 {info['redis_version']}, 内存使用 {info['used_memory_human']}"
            
        except Exception as e:
            return False, f"Redis 连接失败: {str(e)}"
    
    def check_superset_api(self) -> Tuple[bool, str]:
        """检查 Superset API"""
        try:
            api_config = self.config.get('superset', {})
            base_url = api_config.get('url', 'http://localhost:8088')
            timeout = api_config.get('timeout', 30)
            
            # 检查健康端点
            health_url = f"{base_url}/health"
            response = requests.get(health_url, timeout=timeout)
            
            if response.status_code == 200:
                return True, f"Superset API 正常 - 响应时间 {response.elapsed.total_seconds():.2f}s"
            else:
                return False, f"Superset API 响应异常 - 状态码 {response.status_code}"
                
        except Exception as e:
            return False, f"Superset API 检查失败: {str(e)}"
    
    def check_superset_login(self) -> Tuple[bool, str]:
        """检查 Superset 登录功能"""
        try:
            api_config = self.config.get('superset', {})
            base_url = api_config.get('url', 'http://localhost:8088')
            admin_user = api_config.get('admin_user', 'admin')
            admin_password = api_config.get('admin_password', 'admin')
            
            session = requests.Session()
            
            # 获取 CSRF 令牌
            login_page = session.get(f"{base_url}/login/")
            if login_page.status_code != 200:
                return False, f"无法访问登录页面 - 状态码 {login_page.status_code}"
            
            # 提取 CSRF 令牌
            csrf_token = None
            for line in login_page.text.split('\n'):
                if 'csrf_token' in line and 'value=' in line:
                    csrf_token = line.split('value="')[1].split('"')[0]
                    break
            
            if not csrf_token:
                return False, "无法获取 CSRF 令牌"
            
            # 执行登录
            login_data = {
                'username': admin_user,
                'password': admin_password,
                'csrf_token': csrf_token
            }
            
            response = session.post(f"{base_url}/login/", data=login_data)
            
            if response.status_code == 200 and '/superset/welcome' in response.url:
                return True, "Superset 登录功能正常"
            else:
                return False, f"登录失败 - 状态码 {response.status_code}"
                
        except Exception as e:
            return False, f"登录检查失败: {str(e)}"
    
    def check_celery_workers(self) -> Tuple[bool, str]:
        """检查 Celery Worker 状态"""
        try:
            redis_config = self.config.get('redis', {})
            r = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                password=redis_config.get('password', None),
                decode_responses=True
            )
            
            # 检查 Celery 队列
            active_tasks = r.llen('celery')
            worker_stats = r.hgetall('celery@worker.stats')
            
            if worker_stats:
                return True, f"Celery Worker 正常 - 活跃任务: {active_tasks}"
            else:
                return False, "未发现活跃的 Celery Worker"
                
        except Exception as e:
            return False, f"Celery 检查失败: {str(e)}"
    
    def check_system_resources(self) -> Tuple[bool, str]:
        """检查系统资源"""
        try:
            import psutil
            
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 网络连接数
            connections = len(psutil.net_connections())
            
            status_msg = (
                f"系统资源 - CPU: {cpu_percent}%, "
                f"内存: {memory_percent}%, "
                f"磁盘: {disk_percent}%, "
                f"连接数: {connections}"
            )
            
            # 检查是否有资源紧张
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                return False, f"系统资源紧张 - {status_msg}"
            else:
                return True, status_msg
                
        except ImportError:
            return False, "psutil 模块未安装，无法检查系统资源"
        except Exception as e:
            return False, f"系统资源检查失败: {str(e)}"
    
    def check_docker_services(self) -> Tuple[bool, str]:
        """检查 Docker 服务状态"""
        try:
            import docker
            
            client = docker.from_env()
            containers = client.containers.list()
            
            superset_containers = [
                c for c in containers 
                if 'superset' in c.name.lower()
            ]
            
            if not superset_containers:
                return False, "未发现 Superset 相关容器"
            
            running_containers = [
                c for c in superset_containers 
                if c.status == 'running'
            ]
            
            container_info = [
                f"{c.name}({c.status})" 
                for c in superset_containers
            ]
            
            if len(running_containers) == len(superset_containers):
                return True, f"Docker 服务正常 - 容器: {', '.join(container_info)}"
            else:
                return False, f"部分容器异常 - 容器: {', '.join(container_info)}"
                
        except ImportError:
            return False, "docker 模块未安装，无法检查 Docker 服务"
        except Exception as e:
            return False, f"Docker 服务检查失败: {str(e)}"
    
    def run_all_checks(self) -> Dict:
        """运行所有健康检查"""
        checks = [
            ('database', self.check_database),
            ('redis', self.check_redis),
            ('superset_api', self.check_superset_api),
            ('superset_login', self.check_superset_login),
            ('celery_workers', self.check_celery_workers),
            ('system_resources', self.check_system_resources),
            ('docker_services', self.check_docker_services),
        ]
        
        logger.info("开始执行健康检查...")
        
        for check_name, check_func in checks:
            logger.info(f"检查 {check_name}...")
            
            try:
                success, message = check_func()
                self.results[check_name] = {
                    'status': 'healthy' if success else 'unhealthy',
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                if success:
                    logger.info(f"✅ {check_name}: {message}")
                else:
                    logger.error(f"❌ {check_name}: {message}")
                    
            except Exception as e:
                self.results[check_name] = {
                    'status': 'error',
                    'message': f"检查执行失败: {str(e)}",
                    'timestamp': datetime.now().isoformat()
                }
                logger.error(f"💥 {check_name}: 检查执行失败: {str(e)}")
        
        return self.results
    
    def generate_report(self) -> Dict:
        """生成健康检查报告"""
        if not self.results:
            self.run_all_checks()
        
        healthy_count = sum(1 for r in self.results.values() if r['status'] == 'healthy')
        total_count = len(self.results)
        
        overall_status = 'healthy' if healthy_count == total_count else 'unhealthy'
        
        report = {
            'overall_status': overall_status,
            'summary': {
                'total_checks': total_count,
                'healthy_checks': healthy_count,
                'unhealthy_checks': total_count - healthy_count,
                'health_score': round((healthy_count / total_count) * 100, 2)
            },
            'checks': self.results,
            'timestamp': datetime.now().isoformat()
        }
        
        return report

def load_config(config_file: str) -> Dict:
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"配置文件 {config_file} 不存在，使用默认配置")
        return get_default_config()
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
        return get_default_config()

def get_default_config() -> Dict:
    """获取默认配置"""
    return {
        'database': {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'superset'),
            'user': os.getenv('DB_USER', 'superset'),
            'password': os.getenv('DB_PASSWORD', '')
        },
        'redis': {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'password': os.getenv('REDIS_PASSWORD', None)
        },
        'superset': {
            'url': os.getenv('SUPERSET_URL', 'http://localhost:8088'),
            'timeout': int(os.getenv('SUPERSET_TIMEOUT', 30)),
            'admin_user': os.getenv('SUPERSET_ADMIN_USER', 'admin'),
            'admin_password': os.getenv('SUPERSET_ADMIN_PASSWORD', 'admin')
        }
    }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Superset 健康检查工具')
    parser.add_argument('-c', '--config', default='health_config.json',
                       help='配置文件路径')
    parser.add_argument('-o', '--output', default=None,
                       help='输出报告文件路径')
    parser.add_argument('-f', '--format', choices=['json', 'text'], default='text',
                       help='输出格式')
    parser.add_argument('--continuous', action='store_true',
                       help='持续监控模式')
    parser.add_argument('--interval', type=int, default=60,
                       help='持续监控间隔（秒）')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 创建健康检查器
    checker = HealthChecker(config)
    
    if args.continuous:
        logger.info(f"启动持续监控模式，间隔 {args.interval} 秒")
        try:
            while True:
                report = checker.generate_report()
                
                if args.format == 'json':
                    print(json.dumps(report, indent=2, ensure_ascii=False))
                else:
                    print_text_report(report)
                
                if args.output:
                    save_report(report, args.output, args.format)
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            logger.info("监控停止")
    else:
        # 单次检查
        report = checker.generate_report()
        
        if args.format == 'json':
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print_text_report(report)
        
        if args.output:
            save_report(report, args.output, args.format)
        
        # 根据健康状态设置退出码
        sys.exit(0 if report['overall_status'] == 'healthy' else 1)

def print_text_report(report: Dict):
    """打印文本格式报告"""
    print("\n" + "="*60)
    print(" SUPERSET 健康检查报告")
    print("="*60)
    print(f"检查时间: {report['timestamp']}")
    print(f"总体状态: {'🟢 健康' if report['overall_status'] == 'healthy' else '🔴 异常'}")
    print(f"健康分数: {report['summary']['health_score']}%")
    print(f"检查项目: {report['summary']['healthy_checks']}/{report['summary']['total_checks']} 通过")
    print("\n" + "-"*60)
    print(" 详细检查结果")
    print("-"*60)
    
    for check_name, result in report['checks'].items():
        status_icon = {
            'healthy': '🟢',
            'unhealthy': '🔴',
            'error': '💥'
        }.get(result['status'], '❓')
        
        print(f"{status_icon} {check_name.upper().replace('_', ' ')}")
        print(f"   {result['message']}")
        print()

def save_report(report: Dict, output_file: str, format_type: str):
    """保存报告到文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            if format_type == 'json':
                json.dump(report, f, indent=2, ensure_ascii=False)
            else:
                # 简化的文本格式
                f.write(f"健康检查报告 - {report['timestamp']}\n")
                f.write(f"总体状态: {report['overall_status']}\n")
                f.write(f"健康分数: {report['summary']['health_score']}%\n\n")
                
                for check_name, result in report['checks'].items():
                    f.write(f"{check_name}: {result['status']} - {result['message']}\n")
        
        logger.info(f"报告已保存到: {output_file}")
        
    except Exception as e:
        logger.error(f"保存报告失败: {str(e)}")

if __name__ == '__main__':
    main() 