# Superset 生产部署详细指南

## 📋 部署前准备

### 系统要求
```bash
# 最小生产环境要求
CPU: 4核
RAM: 8GB
存储: 100GB SSD
网络: 1Gbps

# 推荐生产环境配置
CPU: 8核
RAM: 16GB
存储: 500GB SSD + 备份存储
网络: 10Gbps
```

### 依赖服务
```bash
# 数据库 (选择其一)
PostgreSQL 12+ (推荐)
MySQL 8.0+

# 缓存服务
Redis 6.0+

# 消息队列
Redis (简单部署)
RabbitMQ (企业级)

# Web服务器
Nginx 1.18+
Apache 2.4+

# 容器运行时
Docker 20.10+
Kubernetes 1.20+
```

## 🐳 Docker 生产部署

### 1. 构建生产镜像

```dockerfile
# 多阶段构建 - 优化镜像大小
FROM node:16-alpine AS frontend-builder
WORKDIR /app/superset-frontend
COPY superset-frontend/package*.json ./
RUN npm ci --only=production
COPY superset-frontend ./
RUN npm run build

FROM python:3.9-slim AS backend-builder
WORKDIR /app
COPY requirements/production.txt ./
RUN pip install --no-cache-dir -r production.txt

FROM python:3.9-slim AS production
WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    libpq-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Python依赖
COPY --from=backend-builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# 应用代码
COPY . .
COPY --from=frontend-builder /app/superset-frontend/dist ./superset/static/assets

# 配置
ENV FLASK_APP=superset.app:create_app
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

# 用户权限
RUN groupadd -r superset && useradd -r -g superset superset
RUN chown -R superset:superset /app
USER superset

EXPOSE 8088
CMD ["gunicorn", "--bind", "0.0.0.0:8088", "superset.app:create_app()"]
```

### 2. 生产环境配置

```python
# superset_config.py - 生产环境配置
import os
from datetime import timedelta

# 基础配置
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

# Redis配置
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')

# 缓存配置
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': REDIS_HOST,
    'CACHE_REDIS_PORT': REDIS_PORT,
    'CACHE_REDIS_PASSWORD': REDIS_PASSWORD,
    'CACHE_REDIS_DB': 1,
}

# 结果缓存
RESULTS_BACKEND = {
    'cache_type': 'RedisCache',
    'cache_default_timeout': 86400,
    'cache_key_prefix': 'superset_results_',
    'cache_redis_host': REDIS_HOST,
    'cache_redis_port': REDIS_PORT,
    'cache_redis_password': REDIS_PASSWORD,
    'cache_redis_db': 2,
}

# Celery配置
CELERY_CONFIG = {
    'broker_url': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/3',
    'imports': ['superset.sql_lab'],
    'result_backend': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/4',
    'worker_prefetch_multiplier': 1,
    'task_acks_late': True,
    'task_annotations': {
        'sql_lab.get_sql_results': {
            'rate_limit': '100/s',
        },
    },
}

# 安全配置
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None
PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

# 日志配置
ENABLE_TIME_ROTATE = True
TIME_ROTATE_LOG_LEVEL = 'INFO'
FILENAME = '/app/logs/superset.log'

# 功能开关
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'GLOBAL_ASYNC_QUERIES': True,
    'VERSIONED_EXPORT': True,
}

# 性能配置
SQLLAB_TIMEOUT = 300
SUPERSET_WEBSERVER_TIMEOUT = 300
ROW_LIMIT = 50000
VIZ_ROW_LIMIT = 10000

# 数据库配置
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,
    'max_overflow': 20,
}
```

### 3. Docker Compose 生产配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  redis:
    image: redis:6.2-alpine
    container_name: superset_redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - superset_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:13
    container_name: superset_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - superset_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3

  superset:
    build:
      context: .
      dockerfile: docker/Dockerfile.production
    container_name: superset_app
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
    environment:
      SUPERSET_SECRET_KEY: ${SUPERSET_SECRET_KEY}
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_HOST: redis
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    volumes:
      - ./superset_config.py:/app/superset_config.py
      - superset_logs:/app/logs
    networks:
      - superset_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8088/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.production
    container_name: superset_worker
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
    environment:
      SUPERSET_SECRET_KEY: ${SUPERSET_SECRET_KEY}
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_HOST: redis
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    volumes:
      - ./superset_config.py:/app/superset_config.py
    networks:
      - superset_network
    command: celery worker --app=superset.tasks.celery_app:app --loglevel=info

  celery_beat:
    build:
      context: .
      dockerfile: docker/Dockerfile.production
    container_name: superset_beat
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
    environment:
      SUPERSET_SECRET_KEY: ${SUPERSET_SECRET_KEY}
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_HOST: redis
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    volumes:
      - ./superset_config.py:/app/superset_config.py
    networks:
      - superset_network
    command: celery beat --app=superset.tasks.celery_app:app --loglevel=info

  nginx:
    image: nginx:alpine
    container_name: superset_nginx
    restart: unless-stopped
    depends_on:
      - superset
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - nginx_logs:/var/log/nginx
    networks:
      - superset_network

volumes:
  postgres_data:
  redis_data:
  superset_logs:
  nginx_logs:

networks:
  superset_network:
    driver: bridge
```

## ☸️ Kubernetes 部署

### 1. 命名空间和配置

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: superset
  labels:
    name: superset

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: superset-config
  namespace: superset
data:
  superset_config.py: |
    # 生产配置内容
    import os
    SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY')
    # ... 其他配置

---
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: superset-secrets
  namespace: superset
type: Opaque
data:
  secret-key: <base64-encoded-secret>
  db-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>
```

### 2. 部署配置

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: superset
  namespace: superset
  labels:
    app: superset
spec:
  replicas: 3
  selector:
    matchLabels:
      app: superset
  template:
    metadata:
      labels:
        app: superset
    spec:
      containers:
      - name: superset
        image: superset:production
        ports:
        - containerPort: 8088
        env:
        - name: SUPERSET_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: superset-secrets
              key: secret-key
        - name: DATABASE_URL
          value: "postgresql://user:$(DB_PASSWORD)@postgres:5432/superset"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: superset-secrets
              key: db-password
        volumeMounts:
        - name: config
          mountPath: /app/superset_config.py
          subPath: superset_config.py
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8088
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8088
          initialDelaySeconds: 15
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: superset-config

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: superset-service
  namespace: superset
spec:
  selector:
    app: superset
  ports:
  - port: 80
    targetPort: 8088
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: superset-ingress
  namespace: superset
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - superset.yourdomain.com
    secretName: superset-tls
  rules:
  - host: superset.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: superset-service
            port:
              number: 80
```

### 3. 水平自动扩展

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: superset-hpa
  namespace: superset
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: superset
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🚀 部署脚本

### 1. 自动化部署脚本

```bash
#!/bin/bash
# deploy.sh - 自动化部署脚本

set -e

# 配置变量
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}
NAMESPACE="superset"

echo "🚀 开始部署 Superset $VERSION 到 $ENVIRONMENT 环境"

# 检查依赖
check_dependencies() {
    echo "检查部署依赖..."
    
    if ! command -v kubectl &> /dev/null; then
        echo "❌ kubectl 未安装"
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        echo "❌ helm 未安装"
        exit 1
    fi
    
    echo "✅ 依赖检查通过"
}

# 构建镜像
build_image() {
    echo "构建生产镜像..."
    docker build -t superset:${VERSION} -f docker/Dockerfile.production .
    docker tag superset:${VERSION} superset:latest
    echo "✅ 镜像构建完成"
}

# 部署到 Kubernetes
deploy_kubernetes() {
    echo "部署到 Kubernetes..."
    
    # 创建命名空间
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # 应用配置
    kubectl apply -f kubernetes/configmap.yaml
    kubectl apply -f kubernetes/secrets.yaml
    kubectl apply -f kubernetes/deployment.yaml
    kubectl apply -f kubernetes/service.yaml
    kubectl apply -f kubernetes/ingress.yaml
    kubectl apply -f kubernetes/hpa.yaml
    
    echo "✅ Kubernetes 部署完成"
}

# 健康检查
health_check() {
    echo "执行健康检查..."
    
    # 等待 Pod 就绪
    kubectl wait --for=condition=ready pod -l app=superset -n ${NAMESPACE} --timeout=300s
    
    # 检查服务状态
    kubectl get pods -n ${NAMESPACE}
    kubectl get services -n ${NAMESPACE}
    
    echo "✅ 健康检查通过"
}

# 执行部署流程
main() {
    check_dependencies
    build_image
    deploy_kubernetes
    health_check
    
    echo "🎉 部署完成！"
    echo "访问地址: https://superset.yourdomain.com"
}

main "$@"
```

### 2. 备份脚本

```bash
#!/bin/bash
# backup.sh - 数据备份脚本

set -e

BACKUP_DIR="/backup/superset"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

echo "🔄 开始数据备份 - $DATE"

# 创建备份目录
mkdir -p ${BACKUP_DIR}

# 数据库备份
backup_database() {
    echo "备份数据库..."
    
    kubectl exec -n superset deployment/postgres -- pg_dump \
        -U ${DB_USER} \
        -d ${DB_NAME} \
        --clean --if-exists \
        > ${BACKUP_DIR}/superset_db_${DATE}.sql
    
    echo "✅ 数据库备份完成"
}

# 配置备份
backup_configs() {
    echo "备份配置文件..."
    
    kubectl get configmap superset-config -n superset -o yaml \
        > ${BACKUP_DIR}/configmap_${DATE}.yaml
    
    kubectl get secret superset-secrets -n superset -o yaml \
        > ${BACKUP_DIR}/secrets_${DATE}.yaml
    
    echo "✅ 配置备份完成"
}

# 压缩备份
compress_backup() {
    echo "压缩备份文件..."
    
    cd ${BACKUP_DIR}
    tar -czf superset_backup_${DATE}.tar.gz \
        superset_db_${DATE}.sql \
        configmap_${DATE}.yaml \
        secrets_${DATE}.yaml
    
    rm superset_db_${DATE}.sql configmap_${DATE}.yaml secrets_${DATE}.yaml
    
    echo "✅ 备份压缩完成"
}

# 清理旧备份
cleanup_old_backups() {
    echo "清理过期备份..."
    
    find ${BACKUP_DIR} -name "superset_backup_*.tar.gz" \
        -mtime +${RETENTION_DAYS} -delete
    
    echo "✅ 过期备份清理完成"
}

# 执行备份
main() {
    backup_database
    backup_configs
    compress_backup
    cleanup_old_backups
    
    echo "🎉 备份完成: ${BACKUP_DIR}/superset_backup_${DATE}.tar.gz"
}

main "$@"
```

## 📊 监控配置

通过本指南，您可以实现Superset的企业级生产部署，包括容器化、高可用、监控告警等完整体系。接下来我们将深入学习监控和性能优化配置。 