#!/usr/bin/env python3
"""
Day 7 - Web服务架构演示脚本
展示Superset风格的Web服务架构和微服务通信模式
"""

import json
import time
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from queue import Queue
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 服务发现与注册
@dataclass
class ServiceInstance:
    """服务实例"""
    service_name: str
    instance_id: str
    host: str
    port: int
    health_check_url: str
    metadata: Dict[str, Any]
    status: str = "UP"
    last_heartbeat: datetime = None
    
    def __post_init__(self):
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now()

class ServiceRegistry:
    """服务注册中心"""
    
    def __init__(self):
        self.services: Dict[str, List[ServiceInstance]] = {}
        self.health_check_interval = 30  # 秒
        self._running = False
        self._health_check_thread = None
    
    def register_service(self, instance: ServiceInstance):
        """注册服务"""
        if instance.service_name not in self.services:
            self.services[instance.service_name] = []
        
        # 检查是否已存在
        existing = next(
            (s for s in self.services[instance.service_name] 
             if s.instance_id == instance.instance_id), None
        )
        
        if existing:
            # 更新现有实例
            existing.status = instance.status
            existing.last_heartbeat = datetime.now()
        else:
            # 添加新实例
            self.services[instance.service_name].append(instance)
        
        print(f"✓ 服务注册: {instance.service_name}#{instance.instance_id} @ {instance.host}:{instance.port}")
    
    def deregister_service(self, service_name: str, instance_id: str):
        """注销服务"""
        if service_name in self.services:
            self.services[service_name] = [
                s for s in self.services[service_name] 
                if s.instance_id != instance_id
            ]
            print(f"✓ 服务注销: {service_name}#{instance_id}")
    
    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """获取健康的服务实例"""
        if service_name not in self.services:
            return []
        
        return [
            instance for instance in self.services[service_name]
            if instance.status == "UP" and 
            (datetime.now() - instance.last_heartbeat).seconds < self.health_check_interval * 2
        ]
    
    def heartbeat(self, service_name: str, instance_id: str):
        """服务心跳"""
        if service_name in self.services:
            for instance in self.services[service_name]:
                if instance.instance_id == instance_id:
                    instance.last_heartbeat = datetime.now()
                    instance.status = "UP"
                    return True
        return False
    
    def start_health_check(self):
        """启动健康检查"""
        self._running = True
        self._health_check_thread = threading.Thread(target=self._health_check_loop)
        self._health_check_thread.start()
        print("🏥 健康检查服务已启动")
    
    def stop_health_check(self):
        """停止健康检查"""
        self._running = False
        if self._health_check_thread:
            self._health_check_thread.join()
        print("🏥 健康检查服务已停止")
    
    def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            current_time = datetime.now()
            
            for service_name, instances in self.services.items():
                for instance in instances:
                    time_since_heartbeat = (current_time - instance.last_heartbeat).seconds
                    
                    if time_since_heartbeat > self.health_check_interval * 2:
                        instance.status = "DOWN"
                        print(f"⚠️  实例不健康: {service_name}#{instance.instance_id}")
            
            time.sleep(self.health_check_interval)
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        status = {}
        
        for service_name, instances in self.services.items():
            healthy_count = len([i for i in instances if i.status == "UP"])
            total_count = len(instances)
            
            status[service_name] = {
                "total_instances": total_count,
                "healthy_instances": healthy_count,
                "health_rate": healthy_count / total_count if total_count > 0 else 0,
                "instances": [
                    {
                        "instance_id": i.instance_id,
                        "host": i.host,
                        "port": i.port,
                        "status": i.status,
                        "last_heartbeat": i.last_heartbeat.isoformat()
                    }
                    for i in instances
                ]
            }
        
        return status

# 负载均衡器
class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.algorithms = {
            'round_robin': self._round_robin,
            'random': self._random,
            'least_connections': self._least_connections,
            'weighted_round_robin': self._weighted_round_robin
        }
        self.current_index = {}
        self.connection_counts = {}
    
    def select_instance(self, service_name: str, algorithm: str = 'round_robin') -> Optional[ServiceInstance]:
        """选择服务实例"""
        healthy_instances = self.service_registry.get_healthy_instances(service_name)
        
        if not healthy_instances:
            return None
        
        if algorithm in self.algorithms:
            return self.algorithms[algorithm](service_name, healthy_instances)
        else:
            return self._round_robin(service_name, healthy_instances)
    
    def _round_robin(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """轮询算法"""
        if service_name not in self.current_index:
            self.current_index[service_name] = 0
        
        instance = instances[self.current_index[service_name]]
        self.current_index[service_name] = (self.current_index[service_name] + 1) % len(instances)
        
        return instance
    
    def _random(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """随机算法"""
        import random
        return random.choice(instances)
    
    def _least_connections(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """最少连接算法"""
        # 找出连接数最少的实例
        min_connections = float('inf')
        selected_instance = instances[0]
        
        for instance in instances:
            key = f"{instance.service_name}#{instance.instance_id}"
            connections = self.connection_counts.get(key, 0)
            
            if connections < min_connections:
                min_connections = connections
                selected_instance = instance
        
        return selected_instance
    
    def _weighted_round_robin(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """加权轮询算法"""
        # 基于元数据中的权重进行选择
        weighted_instances = []
        
        for instance in instances:
            weight = instance.metadata.get('weight', 1)
            weighted_instances.extend([instance] * weight)
        
        return self._round_robin(f"{service_name}_weighted", weighted_instances)
    
    def record_connection(self, instance: ServiceInstance):
        """记录连接"""
        key = f"{instance.service_name}#{instance.instance_id}"
        self.connection_counts[key] = self.connection_counts.get(key, 0) + 1
    
    def release_connection(self, instance: ServiceInstance):
        """释放连接"""
        key = f"{instance.service_name}#{instance.instance_id}"
        if key in self.connection_counts:
            self.connection_counts[key] = max(0, self.connection_counts[key] - 1)

# API网关
class ApiGateway:
    """API网关"""
    
    def __init__(self, service_registry: ServiceRegistry, load_balancer: LoadBalancer):
        self.service_registry = service_registry
        self.load_balancer = load_balancer
        self.routes = {}
        self.middlewares = []
        self.cache = {}
        self.rate_limits = {}
    
    def register_route(self, path: str, service_name: str, target_path: str = None):
        """注册路由"""
        self.routes[path] = {
            'service_name': service_name,
            'target_path': target_path or path
        }
        print(f"🛣️  路由注册: {path} -> {service_name}")
    
    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self.middlewares.append(middleware)
    
    def route_request(self, path: str, method: str = 'GET', headers: Dict = None, body: Any = None) -> Dict:
        """路由请求"""
        headers = headers or {}
        
        # 查找匹配的路由
        route_config = None
        for route_path, config in self.routes.items():
            if path.startswith(route_path):
                route_config = config
                break
        
        if not route_config:
            return {
                'status': 404,
                'error': 'Route not found',
                'path': path
            }
        
        # 选择服务实例
        service_name = route_config['service_name']
        instance = self.load_balancer.select_instance(service_name)
        
        if not instance:
            return {
                'status': 503,
                'error': 'Service unavailable',
                'service': service_name
            }
        
        # 执行中间件
        request_context = {
            'path': path,
            'method': method,
            'headers': headers,
            'body': body,
            'service_name': service_name,
            'instance': instance
        }
        
        for middleware in self.middlewares:
            result = middleware(request_context)
            if result and result.get('status') != 200:
                return result
        
        # 转发请求
        target_path = route_config['target_path']
        response = self._forward_request(instance, target_path, method, headers, body)
        
        return response
    
    def _forward_request(self, instance: ServiceInstance, path: str, method: str, 
                        headers: Dict, body: Any) -> Dict:
        """转发请求到目标服务"""
        # 模拟HTTP请求转发
        self.load_balancer.record_connection(instance)
        
        try:
            # 模拟网络延迟
            time.sleep(0.01)
            
            # 模拟服务响应
            response = {
                'status': 200,
                'data': {
                    'message': f'Response from {instance.service_name}#{instance.instance_id}',
                    'path': path,
                    'method': method,
                    'timestamp': datetime.now().isoformat()
                },
                'headers': {
                    'X-Service-Instance': instance.instance_id,
                    'X-Response-Time': '10ms'
                }
            }
            
            return response
            
        except Exception as e:
            return {
                'status': 500,
                'error': f'Service error: {str(e)}',
                'service': instance.service_name
            }
        
        finally:
            self.load_balancer.release_connection(instance)

# 中间件
class AuthenticationMiddleware:
    """认证中间件"""
    
    def __init__(self):
        self.excluded_paths = ['/api/v1/auth/login', '/health', '/metrics']
    
    def __call__(self, request_context: Dict) -> Optional[Dict]:
        """处理认证"""
        path = request_context['path']
        
        # 跳过不需要认证的路径
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return None
        
        headers = request_context['headers']
        auth_header = headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return {
                'status': 401,
                'error': 'Missing or invalid authorization header'
            }
        
        token = auth_header[7:]  # 移除 'Bearer ' 前缀
        
        # 简单的token验证
        if not self._validate_token(token):
            return {
                'status': 401,
                'error': 'Invalid token'
            }
        
        # 将用户信息添加到上下文
        request_context['user'] = self._get_user_from_token(token)
        return None
    
    def _validate_token(self, token: str) -> bool:
        """验证token"""
        # 简化的token验证逻辑
        return len(token) > 10 and token.startswith('eyJ')
    
    def _get_user_from_token(self, token: str) -> Dict:
        """从token获取用户信息"""
        return {
            'user_id': 'user_123',
            'username': 'demo_user',
            'roles': ['user']
        }

class RateLimitMiddleware:
    """限流中间件"""
    
    def __init__(self):
        self.limits = {}  # {ip: [(timestamp, count), ...]}
        self.default_limit = 100  # 每分钟100次请求
    
    def __call__(self, request_context: Dict) -> Optional[Dict]:
        """处理限流"""
        # 从header获取客户端IP（简化处理）
        client_ip = request_context['headers'].get('X-Real-IP', '127.0.0.1')
        
        current_time = time.time()
        
        # 清理过期记录
        if client_ip in self.limits:
            self.limits[client_ip] = [
                (ts, count) for ts, count in self.limits[client_ip]
                if current_time - ts < 60  # 保留最近1分钟的记录
            ]
        
        # 计算当前请求数
        current_requests = sum(count for _, count in self.limits.get(client_ip, []))
        
        if current_requests >= self.default_limit:
            return {
                'status': 429,
                'error': 'Rate limit exceeded',
                'limit': self.default_limit,
                'reset_time': int(current_time + 60)
            }
        
        # 记录当前请求
        if client_ip not in self.limits:
            self.limits[client_ip] = []
        self.limits[client_ip].append((current_time, 1))
        
        return None

class LoggingMiddleware:
    """日志中间件"""
    
    def __call__(self, request_context: Dict) -> Optional[Dict]:
        """记录请求日志"""
        path = request_context['path']
        method = request_context['method']
        service_name = request_context['service_name']
        instance = request_context['instance']
        
        print(f"📝 [API Gateway] {method} {path} -> {service_name}#{instance.instance_id}")
        
        return None

# 断路器
class CircuitBreaker:
    """断路器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """执行函数调用"""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        if self.last_failure_time is None:
            return False
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """成功处理"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """失败处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
    
    def get_state(self) -> Dict[str, Any]:
        """获取断路器状态"""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure_time': self.last_failure_time
        }

# 服务监控
class ServiceMonitor:
    """服务监控"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
    
    def record_request(self, service_name: str, method: str, path: str, 
                      status_code: int, response_time: float):
        """记录请求指标"""
        key = f"{service_name}:{method}:{path}"
        
        if key not in self.metrics:
            self.metrics[key] = {
                'total_requests': 0,
                'success_requests': 0,
                'error_requests': 0,
                'response_times': [],
                'status_codes': {}
            }
        
        metric = self.metrics[key]
        metric['total_requests'] += 1
        
        if 200 <= status_code < 400:
            metric['success_requests'] += 1
        else:
            metric['error_requests'] += 1
        
        metric['response_times'].append(response_time)
        metric['status_codes'][status_code] = metric['status_codes'].get(status_code, 0) + 1
        
        # 检查是否需要告警
        self._check_alerts(service_name, metric)
    
    def _check_alerts(self, service_name: str, metric: Dict):
        """检查告警条件"""
        total_requests = metric['total_requests']
        error_rate = metric['error_requests'] / total_requests if total_requests > 0 else 0
        
        # 错误率告警
        if error_rate > 0.1 and total_requests >= 10:  # 错误率超过10%
            alert = {
                'type': 'HIGH_ERROR_RATE',
                'service': service_name,
                'error_rate': error_rate,
                'timestamp': datetime.now().isoformat(),
                'message': f'{service_name} 错误率过高: {error_rate:.2%}'
            }
            self.alerts.append(alert)
        
        # 响应时间告警
        if metric['response_times']:
            avg_response_time = sum(metric['response_times']) / len(metric['response_times'])
            if avg_response_time > 1.0:  # 平均响应时间超过1秒
                alert = {
                    'type': 'HIGH_RESPONSE_TIME',
                    'service': service_name,
                    'avg_response_time': avg_response_time,
                    'timestamp': datetime.now().isoformat(),
                    'message': f'{service_name} 响应时间过长: {avg_response_time:.2f}s'
                }
                self.alerts.append(alert)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}
        
        for key, metric in self.metrics.items():
            service_name, method, path = key.split(':', 2)
            
            if service_name not in summary:
                summary[service_name] = {
                    'total_requests': 0,
                    'success_requests': 0,
                    'error_requests': 0,
                    'avg_response_time': 0,
                    'endpoints': {}
                }
            
            service_summary = summary[service_name]
            service_summary['total_requests'] += metric['total_requests']
            service_summary['success_requests'] += metric['success_requests']
            service_summary['error_requests'] += metric['error_requests']
            
            # 计算平均响应时间
            if metric['response_times']:
                avg_time = sum(metric['response_times']) / len(metric['response_times'])
                service_summary['avg_response_time'] = avg_time
            
            # 端点详情
            endpoint_key = f"{method} {path}"
            service_summary['endpoints'][endpoint_key] = {
                'requests': metric['total_requests'],
                'success_rate': metric['success_requests'] / metric['total_requests'] if metric['total_requests'] > 0 else 0,
                'avg_response_time': sum(metric['response_times']) / len(metric['response_times']) if metric['response_times'] else 0
            }
        
        return summary
    
    def get_alerts(self, limit: int = 10) -> List[Dict]:
        """获取最近的告警"""
        return self.alerts[-limit:]

# 演示函数
def demo_web_services():
    """演示Web服务架构"""
    print("🌐 Day 7 Web服务架构演示")
    print("=" * 60)
    
    # 初始化组件
    service_registry = ServiceRegistry()
    load_balancer = LoadBalancer(service_registry)
    api_gateway = ApiGateway(service_registry, load_balancer)
    service_monitor = ServiceMonitor()
    
    # 添加中间件
    api_gateway.add_middleware(AuthenticationMiddleware())
    api_gateway.add_middleware(RateLimitMiddleware())
    api_gateway.add_middleware(LoggingMiddleware())
    
    print("\n" + "=" * 60)
    print("🏗️ 服务注册与发现")
    print("=" * 60)
    
    # 注册服务实例
    services_to_register = [
        # 用户服务
        ServiceInstance("user-service", "user-1", "192.168.1.10", 8001, "/health", {"weight": 2}),
        ServiceInstance("user-service", "user-2", "192.168.1.11", 8001, "/health", {"weight": 1}),
        
        # 仪表板服务
        ServiceInstance("dashboard-service", "dashboard-1", "192.168.1.20", 8002, "/health", {"weight": 3}),
        ServiceInstance("dashboard-service", "dashboard-2", "192.168.1.21", 8002, "/health", {"weight": 2}),
        
        # 数据服务
        ServiceInstance("data-service", "data-1", "192.168.1.30", 8003, "/health", {"weight": 1}),
    ]
    
    print("📋 注册服务实例:")
    for service in services_to_register:
        service_registry.register_service(service)
    
    # 启动健康检查
    service_registry.start_health_check()
    
    # 注册路由
    print("\n🛣️  注册API路由:")
    routes = [
        ("/api/v1/users", "user-service"),
        ("/api/v1/dashboards", "dashboard-service"),
        ("/api/v1/data", "data-service"),
    ]
    
    for path, service_name in routes:
        api_gateway.register_route(path, service_name)
    
    print("\n" + "=" * 60)
    print("⚖️ 负载均衡演示")
    print("=" * 60)
    
    # 测试不同负载均衡算法
    algorithms = ['round_robin', 'random', 'least_connections', 'weighted_round_robin']
    
    for algorithm in algorithms:
        print(f"\n🔄 {algorithm} 算法测试:")
        
        # 发送5个请求
        for i in range(5):
            instance = load_balancer.select_instance("user-service", algorithm)
            if instance:
                print(f"  请求 {i+1} -> {instance.instance_id} ({instance.host}:{instance.port})")
    
    print("\n" + "=" * 60)
    print("🚪 API网关演示")
    print("=" * 60)
    
    # 模拟API请求
    test_requests = [
        {
            "path": "/api/v1/users",
            "method": "GET",
            "headers": {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}
        },
        {
            "path": "/api/v1/dashboards",
            "method": "POST",
            "headers": {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"},
            "body": {"title": "新仪表板"}
        },
        {
            "path": "/api/v1/data/query",
            "method": "GET",
            "headers": {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}
        },
        {
            "path": "/api/v1/users",
            "method": "GET",
            "headers": {}  # 无认证header
        }
    ]
    
    print("📨 发送API请求:")
    for i, req in enumerate(test_requests, 1):
        print(f"\n🔄 请求 {i}: {req['method']} {req['path']}")
        
        start_time = time.time()
        response = api_gateway.route_request(
            req['path'], 
            req['method'], 
            req['headers'], 
            req.get('body')
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        print(f"  ✓ 状态码: {response['status']}")
        if response['status'] == 200:
            print(f"  ✓ 服务实例: {response.get('headers', {}).get('X-Service-Instance', 'N/A')}")
        else:
            print(f"  ✗ 错误: {response.get('error', 'Unknown error')}")
        
        # 记录监控指标
        service_name = req['path'].split('/')[3] + "-service"
        service_monitor.record_request(
            service_name, req['method'], req['path'], 
            response['status'], response_time
        )
    
    print("\n" + "=" * 60)
    print("🔧 断路器演示")
    print("=" * 60)
    
    # 创建断路器
    circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
    
    def unstable_service():
        """不稳定的服务"""
        import random
        if random.random() < 0.7:  # 70%的失败率
            raise Exception("Service error")
        return "Success"
    
    print("🔌 测试断路器:")
    
    # 发送多个请求触发断路器
    for i in range(8):
        try:
            result = circuit_breaker.call(unstable_service)
            print(f"  请求 {i+1}: ✓ 成功 - {result}")
        except Exception as e:
            print(f"  请求 {i+1}: ✗ 失败 - {str(e)}")
        
        # 显示断路器状态
        state = circuit_breaker.get_state()
        print(f"    断路器状态: {state['state']} (失败次数: {state['failure_count']})")
        
        if i == 4:  # 在第5次请求后暂停一下
            print("    ⏸️  暂停5秒等待恢复...")
            time.sleep(5)
    
    print("\n" + "=" * 60)
    print("📊 服务监控统计")
    print("=" * 60)
    
    # 获取监控数据
    metrics_summary = service_monitor.get_metrics_summary()
    
    print("📈 服务指标摘要:")
    for service_name, metrics in metrics_summary.items():
        print(f"\n🔸 {service_name}:")
        print(f"  总请求数: {metrics['total_requests']}")
        print(f"  成功请求: {metrics['success_requests']}")
        print(f"  失败请求: {metrics['error_requests']}")
        print(f"  成功率: {metrics['success_requests']/metrics['total_requests']*100:.1f}%")
        print(f"  平均响应时间: {metrics['avg_response_time']*1000:.1f}ms")
        
        print(f"  📍 端点详情:")
        for endpoint, stats in metrics['endpoints'].items():
            print(f"    {endpoint}: {stats['requests']}次请求, "
                  f"成功率{stats['success_rate']*100:.1f}%, "
                  f"响应时间{stats['avg_response_time']*1000:.1f}ms")
    
    # 显示告警
    alerts = service_monitor.get_alerts()
    if alerts:
        print(f"\n🚨 最近告警:")
        for alert in alerts:
            print(f"  [{alert['type']}] {alert['message']}")
    else:
        print(f"\n✅ 无告警")
    
    print("\n" + "=" * 60)
    print("🏥 服务健康状态")
    print("=" * 60)
    
    # 获取服务状态
    service_status = service_registry.get_service_status()
    
    print("💊 服务健康报告:")
    for service_name, status in service_status.items():
        health_rate = status['health_rate']
        health_icon = "✅" if health_rate == 1.0 else "⚠️" if health_rate > 0.5 else "❌"
        
        print(f"{health_icon} {service_name}:")
        print(f"  健康实例: {status['healthy_instances']}/{status['total_instances']}")
        print(f"  健康率: {health_rate*100:.1f}%")
        
        for instance in status['instances']:
            status_icon = "🟢" if instance['status'] == "UP" else "🔴"
            print(f"    {status_icon} {instance['instance_id']} @ {instance['host']}:{instance['port']}")
    
    print("\n" + "=" * 60)
    print("🔄 服务间通信演示")
    print("=" * 60)
    
    # 模拟服务间调用链
    print("📞 模拟服务调用链:")
    print("  客户端 -> API网关 -> 仪表板服务 -> 数据服务 -> 用户服务")
    
    call_chain = [
        ("客户端", "API网关", "GET /api/v1/dashboards"),
        ("API网关", "仪表板服务", "获取仪表板列表"),
        ("仪表板服务", "数据服务", "查询仪表板数据"),
        ("数据服务", "用户服务", "验证用户权限"),
    ]
    
    for i, (from_service, to_service, operation) in enumerate(call_chain, 1):
        print(f"  {i}. {from_service} -> {to_service}: {operation}")
        time.sleep(0.1)  # 模拟网络延迟
        print(f"     ✓ 响应时间: {10 + i*5}ms")
    
    print("\n" + "=" * 60)
    print("⚡ 性能优化建议")
    print("=" * 60)
    
    # 生成性能优化建议
    suggestions = [
        "🚀 使用连接池减少连接开销",
        "📦 实现响应缓存减少重复计算",
        "🔄 启用异步处理提高并发能力",
        "📊 使用数据库读写分离优化查询性能",
        "🗜️ 实现响应压缩减少网络传输",
        "🎯 使用CDN加速静态资源访问",
        "🔍 实现智能预加载提升用户体验",
        "📈 使用自动扩缩容应对流量变化"
    ]
    
    print("💡 性能优化建议:")
    for suggestion in suggestions:
        print(f"  {suggestion}")
    
    # 停止健康检查
    service_registry.stop_health_check()
    
    print("\n" + "=" * 60)
    print("✅ Web服务架构演示完成！")
    print("=" * 60)
    
    print(f"\n📚 核心架构组件总结:")
    print(f"- 服务注册与发现：动态服务管理和健康检查")
    print(f"- 负载均衡器：多种算法智能分发请求")
    print(f"- API网关：统一入口和中间件处理")
    print(f"- 断路器：防止级联故障的保护机制")
    print(f"- 服务监控：实时指标收集和告警")
    print(f"- 微服务通信：服务间调用链管理")

if __name__ == "__main__":
    demo_web_services() 