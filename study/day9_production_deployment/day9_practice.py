#!/usr/bin/env python3
"""
Day 9: Superset 生产部署实践
演示生产环境部署、监控、运维的核心功能
"""

import os
import sys
import json
import time
import docker
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class SupersetProductionManager:
    """Superset 生产环境管理器"""
    
    def __init__(self, config_file: str = 'production_config.json'):
        self.config = self.load_config(config_file)
        self.docker_client = None
        self.deployment_log = []
        
    def load_config(self, config_file: str) -> Dict:
        """加载生产配置"""
        default_config = {
            'environment': 'production',
            'superset': {
                'version': 'latest',
                'replicas': 3,
                'resources': {
                    'cpu': '2',
                    'memory': '4Gi'
                }
            },
            'database': {
                'host': 'postgres',
                'port': 5432,
                'name': 'superset',
                'user': 'superset'
            },
            'redis': {
                'host': 'redis',
                'port': 6379
            },
            'monitoring': {
                'enabled': True,
                'prometheus_port': 9090,
                'grafana_port': 3000
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            print(f"配置文件 {config_file} 不存在，使用默认配置")
            
        return default_config
    
    def log_action(self, action: str, status: str = 'INFO', details: str = ''):
        """记录操作日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'status': status,
            'details': details
        }
        self.deployment_log.append(log_entry)
        print(f"[{log_entry['timestamp']}] {status}: {action} - {details}")
    
    def check_docker_environment(self) -> bool:
        """检查Docker环境"""
        try:
            self.docker_client = docker.from_env()
            version = self.docker_client.version()
            self.log_action(
                "检查Docker环境", 
                "SUCCESS", 
                f"Docker版本: {version['Version']}"
            )
            return True
        except Exception as e:
            self.log_action("检查Docker环境", "ERROR", str(e))
            return False
    
    def build_production_image(self) -> bool:
        """构建生产镜像"""
        try:
            self.log_action("开始构建生产镜像", "INFO")
            
            # 构建参数
            build_args = {
                'SUPERSET_VERSION': self.config['superset']['version']
            }
            
            # 执行构建
            image, build_logs = self.docker_client.images.build(
                path='.',
                dockerfile='docker/Dockerfile.production',
                tag=f"superset:{self.config['superset']['version']}",
                buildargs=build_args,
                rm=True
            )
            
            self.log_action(
                "镜像构建完成", 
                "SUCCESS", 
                f"镜像ID: {image.short_id}"
            )
            return True
            
        except Exception as e:
            self.log_action("镜像构建失败", "ERROR", str(e))
            return False
    
    def deploy_infrastructure(self) -> bool:
        """部署基础设施（数据库、Redis等）"""
        try:
            self.log_action("部署基础设施", "INFO")
            
            # 创建网络
            try:
                network = self.docker_client.networks.create(
                    "superset_network",
                    driver="bridge"
                )
                self.log_action("创建网络", "SUCCESS", "superset_network")
            except docker.errors.APIError as e:
                if "already exists" in str(e):
                    self.log_action("网络已存在", "INFO", "superset_network")
                else:
                    raise e
            
            # 部署PostgreSQL
            self.deploy_postgres()
            
            # 部署Redis
            self.deploy_redis()
            
            # 等待服务启动
            time.sleep(10)
            
            return True
            
        except Exception as e:
            self.log_action("基础设施部署失败", "ERROR", str(e))
            return False
    
    def deploy_postgres(self):
        """部署PostgreSQL数据库"""
        try:
            container = self.docker_client.containers.run(
                "postgres:13",
                name="superset_postgres",
                environment={
                    'POSTGRES_DB': self.config['database']['name'],
                    'POSTGRES_USER': self.config['database']['user'],
                    'POSTGRES_PASSWORD': os.getenv('DB_PASSWORD', 'superset123')
                },
                networks=['superset_network'],
                volumes={
                    'postgres_data': {'bind': '/var/lib/postgresql/data', 'mode': 'rw'}
                },
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            self.log_action("PostgreSQL部署", "SUCCESS", f"容器ID: {container.short_id}")
            
        except docker.errors.APIError as e:
            if "already in use" in str(e):
                self.log_action("PostgreSQL已存在", "INFO")
            else:
                raise e
    
    def deploy_redis(self):
        """部署Redis缓存"""
        try:
            container = self.docker_client.containers.run(
                "redis:6.2-alpine",
                name="superset_redis",
                command=f"redis-server --requirepass {os.getenv('REDIS_PASSWORD', 'superset123')}",
                networks=['superset_network'],
                volumes={
                    'redis_data': {'bind': '/data', 'mode': 'rw'}
                },
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            self.log_action("Redis部署", "SUCCESS", f"容器ID: {container.short_id}")
            
        except docker.errors.APIError as e:
            if "already in use" in str(e):
                self.log_action("Redis已存在", "INFO")
            else:
                raise e
    
    def deploy_superset_app(self) -> bool:
        """部署Superset应用"""
        try:
            self.log_action("部署Superset应用", "INFO")
            
            # 应用配置
            environment = {
                'SUPERSET_SECRET_KEY': os.getenv('SUPERSET_SECRET_KEY', 'your-secret-key'),
                'DATABASE_URL': f"postgresql://{self.config['database']['user']}:{os.getenv('DB_PASSWORD', 'superset123')}@postgres:5432/{self.config['database']['name']}",
                'REDIS_HOST': self.config['redis']['host'],
                'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD', 'superset123'),
                'FLASK_ENV': 'production'
            }
            
            # 启动应用容器
            container = self.docker_client.containers.run(
                f"superset:{self.config['superset']['version']}",
                name="superset_app",
                environment=environment,
                networks=['superset_network'],
                ports={'8088/tcp': 8088},
                volumes={
                    'superset_home': {'bind': '/app/superset_home', 'mode': 'rw'},
                    'superset_logs': {'bind': '/app/logs', 'mode': 'rw'}
                },
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            self.log_action(
                "Superset应用部署", 
                "SUCCESS", 
                f"容器ID: {container.short_id}"
            )
            
            # 等待应用启动
            self.wait_for_service('http://localhost:8088/health', timeout=120)
            
            return True
            
        except Exception as e:
            self.log_action("Superset应用部署失败", "ERROR", str(e))
            return False
    
    def deploy_celery_workers(self) -> bool:
        """部署Celery Worker"""
        try:
            self.log_action("部署Celery Workers", "INFO")
            
            environment = {
                'SUPERSET_SECRET_KEY': os.getenv('SUPERSET_SECRET_KEY', 'your-secret-key'),
                'DATABASE_URL': f"postgresql://{self.config['database']['user']}:{os.getenv('DB_PASSWORD', 'superset123')}@postgres:5432/{self.config['database']['name']}",
                'REDIS_HOST': self.config['redis']['host'],
                'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD', 'superset123')
            }
            
            # Worker容器
            worker_container = self.docker_client.containers.run(
                f"superset:{self.config['superset']['version']}",
                name="superset_worker",
                environment=environment,
                networks=['superset_network'],
                command="celery worker --app=superset.tasks.celery_app:app --loglevel=info",
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            # Beat容器
            beat_container = self.docker_client.containers.run(
                f"superset:{self.config['superset']['version']}",
                name="superset_beat",
                environment=environment,
                networks=['superset_network'],
                command="celery beat --app=superset.tasks.celery_app:app --loglevel=info",
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            self.log_action(
                "Celery部署", 
                "SUCCESS", 
                f"Worker: {worker_container.short_id}, Beat: {beat_container.short_id}"
            )
            
            return True
            
        except Exception as e:
            self.log_action("Celery部署失败", "ERROR", str(e))
            return False
    
    def deploy_monitoring(self) -> bool:
        """部署监控系统"""
        if not self.config['monitoring']['enabled']:
            self.log_action("监控未启用", "INFO")
            return True
            
        try:
            self.log_action("部署监控系统", "INFO")
            
            # 部署Prometheus
            prometheus_container = self.docker_client.containers.run(
                "prom/prometheus:latest",
                name="superset_prometheus",
                networks=['superset_network'],
                ports={f"{self.config['monitoring']['prometheus_port']}/tcp": self.config['monitoring']['prometheus_port']},
                volumes={
                    './monitoring/prometheus.yml': {'bind': '/etc/prometheus/prometheus.yml', 'mode': 'ro'},
                    'prometheus_data': {'bind': '/prometheus', 'mode': 'rw'}
                },
                command=[
                    '--config.file=/etc/prometheus/prometheus.yml',
                    '--storage.tsdb.path=/prometheus',
                    '--web.console.libraries=/etc/prometheus/console_libraries',
                    '--web.console.templates=/etc/prometheus/consoles',
                    '--web.enable-lifecycle'
                ],
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            # 部署Grafana
            grafana_container = self.docker_client.containers.run(
                "grafana/grafana:latest",
                name="superset_grafana",
                environment={
                    'GF_SECURITY_ADMIN_PASSWORD': os.getenv('GRAFANA_PASSWORD', 'admin123')
                },
                networks=['superset_network'],
                ports={f"{self.config['monitoring']['grafana_port']}/tcp": self.config['monitoring']['grafana_port']},
                volumes={
                    'grafana_data': {'bind': '/var/lib/grafana', 'mode': 'rw'}
                },
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            self.log_action(
                "监控系统部署", 
                "SUCCESS", 
                f"Prometheus: {prometheus_container.short_id}, Grafana: {grafana_container.short_id}"
            )
            
            return True
            
        except Exception as e:
            self.log_action("监控系统部署失败", "ERROR", str(e))
            return False
    
    def wait_for_service(self, url: str, timeout: int = 60) -> bool:
        """等待服务启动"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.log_action("服务就绪", "SUCCESS", url)
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(5)
        
        self.log_action("服务启动超时", "ERROR", url)
        return False
    
    def initialize_superset(self) -> bool:
        """初始化Superset"""
        try:
            self.log_action("初始化Superset数据库", "INFO")
            
            # 获取应用容器
            app_container = self.docker_client.containers.get("superset_app")
            
            # 数据库升级
            result = app_container.exec_run("superset db upgrade")
            if result.exit_code != 0:
                raise Exception(f"数据库升级失败: {result.output.decode()}")
            
            # 创建管理员用户
            admin_cmd = [
                "superset", "fab", "create-admin",
                "--username", "admin",
                "--firstname", "Superset",
                "--lastname", "Admin",
                "--email", "admin@superset.com",
                "--password", "admin123"
            ]
            
            result = app_container.exec_run(admin_cmd)
            if result.exit_code != 0 and "already exists" not in result.output.decode():
                raise Exception(f"创建管理员失败: {result.output.decode()}")
            
            # 初始化角色和权限
            result = app_container.exec_run("superset init")
            if result.exit_code != 0:
                raise Exception(f"初始化失败: {result.output.decode()}")
            
            self.log_action("Superset初始化", "SUCCESS", "数据库和用户创建完成")
            return True
            
        except Exception as e:
            self.log_action("Superset初始化失败", "ERROR", str(e))
            return False
    
    def run_health_checks(self) -> Dict:
        """运行健康检查"""
        self.log_action("执行健康检查", "INFO")
        
        checks = {}
        
        # 检查容器状态
        containers = ['superset_postgres', 'superset_redis', 'superset_app', 'superset_worker']
        for container_name in containers:
            try:
                container = self.docker_client.containers.get(container_name)
                checks[container_name] = {
                    'status': container.status,
                    'healthy': container.status == 'running'
                }
            except docker.errors.NotFound:
                checks[container_name] = {
                    'status': 'not_found',
                    'healthy': False
                }
        
        # 检查API健康状态
        try:
            response = requests.get('http://localhost:8088/health', timeout=10)
            checks['superset_api'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'healthy': response.status_code == 200
            }
        except Exception as e:
            checks['superset_api'] = {
                'status': 'error',
                'error': str(e),
                'healthy': False
            }
        
        # 统计健康状态
        healthy_count = sum(1 for check in checks.values() if check.get('healthy', False))
        total_count = len(checks)
        
        health_summary = {
            'overall_healthy': healthy_count == total_count,
            'healthy_services': healthy_count,
            'total_services': total_count,
            'health_score': (healthy_count / total_count) * 100,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
        
        self.log_action(
            "健康检查完成", 
            "SUCCESS" if health_summary['overall_healthy'] else "WARNING",
            f"健康分数: {health_summary['health_score']:.1f}%"
        )
        
        return health_summary
    
    def full_deployment(self) -> bool:
        """完整部署流程"""
        self.log_action("开始完整部署", "INFO", "生产环境部署")
        
        steps = [
            ("检查Docker环境", self.check_docker_environment),
            ("构建生产镜像", self.build_production_image),
            ("部署基础设施", self.deploy_infrastructure),
            ("部署Superset应用", self.deploy_superset_app),
            ("部署Celery Workers", self.deploy_celery_workers),
            ("初始化Superset", self.initialize_superset),
            ("部署监控系统", self.deploy_monitoring),
        ]
        
        for step_name, step_func in steps:
            self.log_action(f"执行步骤: {step_name}", "INFO")
            if not step_func():
                self.log_action("部署失败", "ERROR", f"步骤失败: {step_name}")
                return False
        
        # 最终健康检查
        health_result = self.run_health_checks()
        
        self.log_action(
            "完整部署完成", 
            "SUCCESS" if health_result['overall_healthy'] else "WARNING",
            f"健康分数: {health_result['health_score']:.1f}%"
        )
        
        return health_result['overall_healthy']
    
    def generate_deployment_report(self) -> str:
        """生成部署报告"""
        report = {
            'deployment_timestamp': datetime.now().isoformat(),
            'environment': self.config['environment'],
            'configuration': self.config,
            'deployment_log': self.deployment_log,
            'health_status': self.run_health_checks()
        }
        
        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log_action("部署报告生成", "SUCCESS", report_file)
        return report_file

def demonstrate_production_deployment():
    """演示生产部署流程"""
    print("=== Day 9: Superset 生产部署实践 ===\n")
    
    # 创建部署管理器
    manager = SupersetProductionManager()
    
    print("1. 检查系统环境...")
    if not manager.check_docker_environment():
        print("❌ Docker环境检查失败，请确保Docker已安装并运行")
        return
    
    print("\n2. 创建生产配置...")
    config_file = 'production_config.json'
    if not os.path.exists(config_file):
        with open(config_file, 'w') as f:
            json.dump(manager.config, f, indent=2)
        print(f"✅ 已创建配置文件: {config_file}")
    
    print("\n3. 执行完整部署...")
    success = manager.full_deployment()
    
    print(f"\n4. 部署结果: {'✅ 成功' if success else '❌ 失败'}")
    
    print("\n5. 生成部署报告...")
    report_file = manager.generate_deployment_report()
    print(f"📊 部署报告: {report_file}")
    
    if success:
        print("\n🎉 生产部署完成！")
        print("📖 访问地址:")
        print("   - Superset: http://localhost:8088")
        print("   - Prometheus: http://localhost:9090")
        print("   - Grafana: http://localhost:3000")
        print("\n🔐 默认登录:")
        print("   - Superset: admin / admin123")
        print("   - Grafana: admin / admin123")
    else:
        print("\n❌ 部署过程中遇到问题，请检查日志")

def demonstrate_monitoring_setup():
    """演示监控配置"""
    print("\n=== 监控系统配置演示 ===")
    
    # 监控配置示例
    monitoring_config = {
        'prometheus': {
            'scrape_interval': '15s',
            'targets': [
                'superset:8088',
                'postgres-exporter:9187',
                'redis-exporter:9121'
            ]
        },
        'grafana': {
            'dashboards': [
                'Superset Overview',
                'System Resources',
                'Database Performance'
            ]
        },
        'alerts': [
            {
                'name': 'HighErrorRate',
                'condition': 'error_rate > 0.05',
                'duration': '5m'
            },
            {
                'name': 'HighMemoryUsage',
                'condition': 'memory_usage > 90',
                'duration': '10m'
            }
        ]
    }
    
    print("📊 监控配置:")
    print(json.dumps(monitoring_config, indent=2, ensure_ascii=False))

def demonstrate_backup_strategy():
    """演示备份策略"""
    print("\n=== 备份策略演示 ===")
    
    backup_strategy = {
        'database_backup': {
            'frequency': 'daily',
            'retention': '30 days',
            'method': 'pg_dump',
            'storage': 'local + cloud'
        },
        'config_backup': {
            'frequency': 'on_change',
            'retention': '90 days',
            'method': 'git_commit'
        },
        'monitoring_data': {
            'frequency': 'continuous',
            'retention': '90 days',
            'method': 'prometheus_remote_write'
        }
    }
    
    print("💾 备份策略:")
    print(json.dumps(backup_strategy, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    # 设置环境变量（生产环境应该从安全的地方获取）
    os.environ.setdefault('SUPERSET_SECRET_KEY', 'your-secret-key-here')
    os.environ.setdefault('DB_PASSWORD', 'superset123')
    os.environ.setdefault('REDIS_PASSWORD', 'superset123')
    os.environ.setdefault('GRAFANA_PASSWORD', 'admin123')
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'deploy':
            demonstrate_production_deployment()
        elif sys.argv[1] == 'monitoring':
            demonstrate_monitoring_setup()
        elif sys.argv[1] == 'backup':
            demonstrate_backup_strategy()
        else:
            print("用法: python day9_practice.py [deploy|monitoring|backup]")
    else:
        # 运行所有演示
        demonstrate_production_deployment()
        demonstrate_monitoring_setup()
        demonstrate_backup_strategy() 