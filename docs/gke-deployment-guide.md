# Apache Superset 生产级 GKE 部署指南

## 目录
- [架构概览](#架构概览)
- [容量规划](#容量规划)
- [前置要求](#前置要求)
- [GKE 集群创建](#gke-集群创建)
- [依赖服务配置](#依赖服务配置)
- [部署 Superset](#部署-superset)
- [验证部署](#验证部署)
- [监控与告警](#监控与告警)
- [监控配置清单](#监控配置清单)

---

## 架构概览

```
                              ┌─────────────────────────────────────┐
                              │           GKE Cluster               │
                              │                                     │
┌──────────────┐              │  ┌─────────────────────────────┐   │
│   Internet   │ ──────────► │  │   Nginx/GCE Ingress          │   │
└──────────────┘              │  └──────────────┬──────────────┘   │
                              │                 │                   │
                              │  ┌──────────────▼──────────────┐   │
                              │  │   Superset Web (3-10 pods)  │   │
                              │  │   Gunicorn: 4 workers/pod   │   │
                              │  └──────────────┬──────────────┘   │
                              │                 │                   │
                              │  ┌──────────────▼──────────────┐   │
                              │  │   Superset Worker (2-8 pods)│   │
                              │  │   Celery + Redis Queue      │   │
                              │  └──────────────┬──────────────┘   │
                              │                 │                   │
                              │  ┌──────────────▼──────────────┐   │
                              │  │   Celery Beat (1 pod)       │   │
                              │  │   Scheduled Tasks           │   │
                              │  └─────────────────────────────┘   │
                              └─────────────────────────────────────┘
                                         │           │
                     ┌───────────────────┘           └───────────────────┐
                     │                                                   │
              ┌──────▼──────┐                                    ┌──────▼──────┐
              │ Cloud SQL   │                                    │Cloud Memory │
              │ PostgreSQL  │                                    │   Store     │
              │  (HA Setup) │                                    │   Redis     │
              └─────────────┘                                    └─────────────┘
```

### 核心组件说明

| 组件 | 副本数 | CPU | 内存 | 说明 |
|------|--------|-----|------|------|
| Superset Web | 3-10 (HPA) | 2核 × 3 = 6核 | 4Gi × 3 = 12Gi | HTTP服务，处理用户请求 |
| Superset Worker | 2-8 (HPA) | 1核 × 2 = 2核 | 2Gi × 2 = 4Gi | 异步任务处理 |
| Celery Beat | 1 | 0.5核 | 1Gi | 定时任务调度 |
| Celery Flower | 1 | 0.5核 | 1Gi | 任务监控UI |

### Ingress vs Gunicorn 分工

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户请求                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Nginx/GCE Ingress                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  职责：                                                  │   │
│  │  1. 流量入口 - 唯一对外暴露点                           │   │
│  │  2. TLS 终止 - HTTPS 解密                               │   │
│  │  3. 负载均衡 - 分发到多个 Pod                          │   │
│  │  4. 静态资源 - CSS/JS/图片等                            │   │
│  │  5. 限流/防护 - 防止 DDoS                               │   │
│  │  6. 路径路由 - /api/* → web, /ws/* → websocket        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │  HTTP (内部集群)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Gunicorn                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  职责：                                                  │   │
│  │  1. WSGI 应用服务器 - 运行 Flask/Superset              │   │
│  │  2. Python 请求处理 - 执行 Python 代码                 │   │
│  │  3. 动态内容生成 - 图表数据、API 响应                   │   │
│  │  4. Worker 管理 - 进程/线程池管理                       │   │
│  │  5. 超时控制 - 单请求超时设置                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

| 维度 | Ingress (Nginx/GCE) | Gunicorn |
|------|---------------------|----------|
| **层级** | L7 负载均衡器 | 应用服务器 |
| **协议** | HTTP/HTTPS | WSGI |
| **处理内容** | 流量路由、静态资源 | Python/Flask 动态请求 |
| **部署位置** | K8s Ingress Controller | Pod 内 |
| **并行处理** | 跨所有 Pod | 单 Pod 内多 Worker |
| **超时** | 全局连接超时 | 单请求超时 |

**分工原因**：

| 组件 | 回答的问题 | 类比 |
|------|-----------|------|
| **Ingress** | "请求去哪台机器？" | 酒店礼宾员，引导客人到楼层 |
| **Gunicorn** | "谁来处理这个请求？" | 客房服务生，执行具体服务 |

两者配合：**Ingress 决定哪个 Pod 处理请求，Gunicorn 决定哪个 Worker 执行代码**。

---

## 容量规划

### 200并发需求分析

```
┌─────────────────────────────────────────────────────────────┐
│                    容量计算公式                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  总并发需求 = 200 请求/秒                                   │
│                                                             │
│  Gunicorn Worker 并发 = 4 workers/pod × 50 pods = 200      │
│                                                             │
│  每 Worker 处理 ≈ 25-50 并发（取决于查询复杂度）            │
│                                                             │
│  实际推荐配置：                                             │
│  - 初始副本: 3（正常负载）                                   │
│  - HPA 最大: 10（峰值负载）                                 │
│  - 每 Pod Worker: 4                                        │
│  - 总 Worker 容量: 3×4 = 12 ... 10×4 = 40                  │
│                                                             │
│  结论: 3-10 副本可支持 200 并发                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 为什么这样配置？

1. **Gunicorn Workers = 4**
   - 每个 worker 是独立进程，受 GIL 限制
   - 2 核 CPU / 4 workers = 每个 worker 0.5 核
   - 过少 workers：并发处理能力不足
   - 过多 workers：内存消耗大，上下文切换开销高

2. **HPA minReplicas = 3**
   - 保证基础可用性
   - 允许滚动更新时不中断服务
   - 正常负载下成本可控

3. **HPA maxReplicas = 10**
   - 10 × 4 = 40 workers
   - 40 × 50 = 2000 请求/秒理论上限
    - 实际考虑查询复杂度，留有余量

4. **targetCPUUtilizationPercentage = 70%**
   - 70% 时触发扩容，平衡响应时间和资源利用率
   - 太低：频繁扩容，资源浪费
   - 太高：响应时间增加，用户体验下降

---

## 前置要求

### 工具安装

```bash
# 安装 gcloud CLI
curl https://sdk.cloud.google.com | bash
gcloud init

# 安装 kubectl
gcloud components install kubectl

# 安装 helm 3
curl -fsSL https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar -xz
sudo mv linux-amd64/helm /usr/local/bin/helm

# 安装 nginx-ingress（可选）
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
```

### GCP 项目配置

```bash
# 设置项目
export PROJECT_ID="your-project-id"
export REGION="asia-east1"
export ZONE="asia-east1-a"

gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

# 启用必要 API
gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

---

## GKE 集群创建

### 方案一：私有集群（推荐生产环境）

```bash
# 创建私有集群
gcloud container clusters create superset-cluster \
  --region $REGION \
  --enable-private-nodes \
  --master-ipv4-cidr 172.16.0.0/28 \
  --enable-ip-alias \
  --num-nodes 6 \
  --machine-type e2-standard-4 \
  --disk-type pd-ssd \
  --disk-size 100GB \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10 \
  --node-pool-name superset-pool \
  --service-account your-sa@$PROJECT_ID.iam.gserviceaccount.com

# 获取集群凭证
gcloud container clusters get-credentials superset-cluster --region $REGION
```

### 方案二：标准集群（开发/测试）

```bash
gcloud container clusters create superset-cluster \
  --region $REGION \
  --num-nodes 4 \
  --machine-type e2-standard-4 \
  --disk-type pd-ssd \
  --disk-size 50GB
```

### 节点池配置

```bash
# 创建专用节点池
gcloud container node-pools create superset-pool \
  --cluster superset-cluster \
  --region $REGION \
  --num-nodes 3 \
  --machine-type e2-standard-4 \
  --disk-type pd-ssd \
  --disk-size 100GB \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 8

# 为节点池添加标签
gcloud container node-pools update superset-pool \
  --cluster superset-cluster \
  --region $REGION \
  --update-labels=dedicated=superset
```

---

## 依赖服务配置

### 1. Cloud SQL for PostgreSQL

```bash
# 创建 PostgreSQL 实例（HA 配置）
gcloud sql instances create superset-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=$REGION \
  --availability-type=REGIONAL \
  --storage-type=SSD \
  --storage-size=50GB \
  --storage-auto-increase \
  --backup-start-time=02:00 \
  --enable-bin-log \
  --network=your-vpc-network

# 创建数据库和用户
gcloud sql databases create superset --instance=superset-db
gcloud sql users create superset \
  --instance=superset-db \
  --password='SECURE_PASSWORD'

# 获取连接 IP
gcloud sql instances describe superset-db --format="value(ipAddresses.ipAddress)"
```

### 2. Cloud Memorystore for Redis

```bash
# 创建 Redis 实例
gcloud redis instances create superset-redis \
  --size=2 \
  --region=$REGION \
  --redis-version=redis_7_0 \
  --network=your-vpc-network \
  --tier=STANDARD_HA

# 获取连接 IP
gcloud redis instances describe superset-redis --region=$REGION --format="value(host)"
```

### 3. Secret 管理

```bash
# 创建 Kubernetes Secret
kubectl create secret generic superset-secrets \
  --from-literal=DB_PASS="YOUR_DB_PASSWORD" \
  --from-literal=REDIS_PASSWORD="YOUR_REDIS_PASSWORD" \
  --from-literal=SUPERSET_SECRET_KEY="$(openssl rand -base64 42)"

# 或使用 GCP Secret Manager
# 安装 External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace
```

### 4. VPC Native 配置（可选）

如果使用 VPC Native 集群访问 Cloud SQL：

```bash
# 创建私有 Service Access
gcloud compute addresses create google-managed-services \
  --global \
  --purpose=VPC_PEERING \
  --prefix-length=16 \
  --network=your-vpc-network

# 创建私有连接
gcloud services vpc-peerings connect \
  --service=servicenetworking.googleapis.com \
  --ranges=google-managed-services \
  --network=your-vpc-network
```

---

## 部署 Superset

### 1. 添加 Helm 仓库

```bash
# 如果使用官方 Chart
helm repo add apache-superset https://apache.github.io/superset-helm-chart
helm repo update

# 或使用本地 Chart
cd superset/helm/superset
```

### 2. 配置 values-production.yaml

修改以下配置为你的实际值：

```yaml
# 域名
ingress:
  hosts:
    - superset.your-domain.com

# Cloud SQL IP
supersetNode:
  connections:
    db_host: "10.0.0.10"  # Cloud SQL 私有 IP

# Cloud Memorystore IP
    redis_host: "10.0.0.20"  # Memorystore 私有 IP

# Secret
extraSecretEnv:
  DB_PASS: "YOUR_ACTUAL_DB_PASSWORD"
  SUPERSET_SECRET_KEY: "YOUR_ACTUAL_SECRET_KEY_MIN_32_CHARS"

# Service Account
serviceAccount:
  annotations:
    iam.gke.io/gcp-service-account: superset@your-project.iam.gserviceaccount.com
```

### 3. 部署

```bash
# 创建命名空间
kubectl create namespace superset

# 部署
helm install superset apache-superset/superset \
  --namespace superset \
  --values values-production.yaml \
  --timeout 10m

# 或使用本地 Chart
helm install superset . \
  --namespace superset \
  --values values-production.yaml \
  --timeout 10m
```

### 4. 验证部署

```bash
# 查看 Pod 状态
kubectl get pods -n superset

# 查看资源使用
kubectl top pods -n superset

# 查看日志
kubectl logs -n superset deployment/superset-superset -f

# 查看 Service
kubectl get svc -n superset
```

---

## 验证部署

### 1. 访问 Superset

```bash
# 获取 Ingress IP
kubectl get ingress -n superset

# 测试健康端点
curl http://<INGRESS_IP>/health
```

### 2. HPA 验证

```bash
# 查看 HPA 状态
kubectl get hpa -n superset

# 模拟负载测试
kubectl run load-generator \
  --image=busybox \
  -- /bin/sh -c "while true; do wget -q -O- http://superset-superset/health; done"

# 观察扩容
watch kubectl get pods -n superset
```

### 3. 性能基准测试

```bash
# 使用 Apache Bench 测试
ab -n 1000 -c 200 http://superset.your-domain.com/health

# 或使用 k6
cat > load-test.js << EOF
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 },
  ],
};

export default function() {
  const res = http.get('http://superset.your-domain.com/health');
  check(res, { 'status was 200': r => r.status === 200 });
  sleep(1);
}
EOF
k6 run load-test.js
```

---

## 监控与告警

### 监控架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Prometheus + Grafana                        │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   Prometheus    │◄───│  node-exporter  │ (每个 Node)       │
│  │   (抓取指标)     │    └─────────────────┘                    │
│  └────────┬────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │     Grafana     │                                            │
│  │   (可视化)       │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │    Cloud Monitoring     │
              │     (GCP 原生)          │
              └─────────────────────────┘
```

### 1. Node-Exporter 部署

Node-Exporter 用于暴露 **宿主机级别指标**（CPU、内存、磁盘、网络）。

```bash
# 添加 Prometheus 社区仓库
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 创建监控命名空间
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# 安装 node-exporter（daemonset，每个节点一个实例）
helm install node-exporter prometheus-community/prometheus-node-exporter \
  --namespace monitoring \
  --values - << 'EOF'
# prometheus-community/prometheus-node-exporter
# 官方 values.yaml 参考: https://github.com/prometheus-community/helm-charts/blob/main/charts/prometheus-node-exporter/values.yaml

service:
  type: ClusterIP
  port: 9100
  targetPort: 9100

# 配置 ServiceMonitor 让 Prometheus 自动发现
serviceMonitor:
  enabled: true
  interval: 15s
  namespace: monitoring

# 添加 PodMonitor（Kubernetes 1.20+）
podMonitor:
  enabled: true
  interval: 15s
  namespace: monitoring

# 资源配置
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

# 容忍所有污点，确保能在所有节点运行
tolerations:
  - operator: Exists
EOF

# 验证部署
kubectl get pods -n monitoring -l app=prometheus-node-exporter
```

### 2. Prometheus + Grafana 部署

```bash
# 安装 kube-prometheus-stack（包含 Prometheus + Grafana + AlertManager）
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values - << 'EOF'
# kube-prometheus-stack 配置

# Prometheus 配置
prometheus:
  prometheusSpec:
    # 保留数据 15 天
    retention: 15d
    # 副本数（生产环境建议 2）
    replicaCount: 1
    # 资源限制
    resources:
      limits:
        cpu: 1000m
        memory: 2Gi
      requests:
        cpu: 500m
        memory: 1Gi
    # 启用 ServiceMonitor 自动发现
    serviceMonitorSelector:
      matchLabels:
        release: kube-prometheus
    # 抓取间隔
    scrapeInterval: 15s
    # 评估间隔
    evaluationInterval: 15s

  # Prometheus Service
  service:
    type: ClusterIP

# AlertManager 配置
alertmanager:
  enabled: true
  alertmanagerSpec:
    replicas: 1
    resources:
      limits:
        cpu: 200m
        memory: 256Mi
      requests:
        cpu: 100m
        memory: 128Mi

# Grafana 配置
grafana:
  enabled: true
  adminPassword: "CHANGE_IN_PRODUCTION"
  grafana.ini:
    server:
      domain: grafana.your-domain.com
      root_url: https://grafana.your-domain.com
  # 持久化
  persistence:
    enabled: true
    size: 10Gi
  resources:
    limits:
      cpu: 500m
      memory: 1Gi
    requests:
      cpu: 100m
      memory: 256Mi

# Ingress 配置
ingress:
  enabled: true
  ingressClassName: nginx
  annotations:
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
  hosts:
    - prometheus.your-domain.com
    - grafana.your-domain.com
  tls:
    - secretName: monitoring-tls
      hosts:
        - prometheus.your-domain.com
        - grafana.your-domain.com

# 全局配置
defaultRules:
  enabled: true
  create: true
  rules:
    # 启用常用告警规则
    alertmanager: true
    etcd: true
    k8sCriticalEquipment: true
    k8sDailyBudget: true
    k8sResourceAvailability: true
    k8sSystemLeft: true
    kubernetesAbsence: true
    kubernetesApps: true
    kubernetesResources: true
    kubernetesStorage: true
    kubernetesSystem: true
    node: true           # Node 级别告警
    prometheus: true
EOF
```

### 3. Superset 指标暴露

Superset 3.x 内置了 Prometheus 指标端点，需要启用：

```yaml
# values-production.yaml 中添加
supersetNode:
  env:
    # 启用 Prometheus 指标
    PROMETHEUS_METRICS: "true"
    # ... 其他配置

# 创建 ServiceMonitor 让 Prometheus 抓取 Superset 指标
kubectl apply -n superset -f - << 'EOF'
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: superset-monitor
  labels:
    release: kube-prometheus  # 必须与 Prometheus 的 serviceMonitorSelector 匹配
spec:
  selector:
    matchLabels:
      app: superset
  endpoints:
    - port: http
      path: /health
      interval: 15s
      scheme: http
EOF
```

### 4. 核心监控指标

#### Node-Exporter 指标（宿主机级别）

| 指标名称 | 说明 | 用途 |
|---------|------|------|
| `node_cpu_seconds_total` | CPU 使用时间 | CPU 负载分析 |
| `node_memory_MemTotal_bytes` | 总内存 | 内存使用率计算 |
| `node_memory_MemAvailable_bytes` | 可用内存 | 内存压力检测 |
| `node_filesystem_size_bytes` | 文件系统大小 | 磁盘空间监控 |
| `node_filesystem_free_bytes` | 文件系统可用 | 磁盘空间预警 |
| `node_network_receive_bytes_total` | 网络接收字节 | 网络流量监控 |
| `node_network_transmit_bytes_total` | 网络发送字节 | 网络流量监控 |
| `node_disk_read_bytes_total` | 磁盘读取字节 | I/O 性能分析 |
| `node_disk_written_bytes_total` | 磁盘写入字节 | I/O 性能分析 |

#### GKE 特有指标

```bash
# 安装 GKE 指标插件（可选，用于 HPA 基于自定义指标）
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/k8s-stackdriver/master/kubemonitor-demo/kubemonitor-crds.yaml

# 或使用 Google Cloud Managed Service for Prometheus
# GKE 集群启用方式：
# gcloud container clusters update CLUSTER_NAME --enable-managed-prometheus --region=REGION
```

#### Superset 业务指标

| 指标名称 | 说明 |
|---------|------|
| `superset_sql Lab_queries` | SQL 查询数量 |
| `superset_dashboard_load_time` | 仪表板加载时间 |
| `superset_chart_render_time` | 图表渲染时间 |
| `superset_cache_hit_total` | 缓存命中数 |

### 5. 告警配置建议

| 指标 | 阈值 | 动作 |
|------|------|------|
| CPU 使用率 | > 80% 持续 5 分钟 | 扩容 |
| Pod 重启次数 | > 3 次/小时 | 告警 |
| 请求延迟 P99 | > 5 秒 | 告警 |
| HPA 最大副本 | >= 8 | 扩容 + 告警 |
| 错误率 | > 1% | 告警 |

### 3. 日志管理

```bash
# 配置 Cloud Logging
kubectl apply -f - << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: log-collector
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: log-collector
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: log-collector
subjects:
- kind: ServiceAccount
  name: log-collector
  namespace: kube-system
EOF

# 使用 GKE 的 Cloud Logging（默认启用）
```

---

## 故障排查

### 常见问题

1. **Pod 无法启动**
   ```bash
   kubectl describe pod <pod-name> -n superset
   kubectl logs <pod-name> -n superset
   ```

2. **无法连接数据库**
   - 检查 `db_host` 配置
   - 验证 VPC 网络连通性
   - 确认防火墙规则

3. **HPA 不工作**
   ```bash
   kubectl describe hpa superset-superset -n superset
   kubectl top pods -n superset
   ```

4. **内存泄漏**
   - Worker 的 `WORKER_MAX_REQUESTS` 设置较小值
   - 定期重启 Pod

---

## 安全加固

### 1. Network Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: superset-network-policy
  namespace: superset
spec:
  podSelector:
    matchLabels:
      app: superset
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8088
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgresql
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
```

### 2. Pod Security Policy

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: superset-psp
spec:
  privileged: false
  runAsUser:
    rule: MustRunAsNonRoot
  seLinux:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
```

---

## 成本优化

### 建议

| 优化项 | 说明 |
|--------|------|
| 使用 E2 机器类型 | 比 N1 便宜 20-30% |
| 启用 HPA | 只在需要时扩展 |
| 使用 Spot 实例 | 可用于非关键 Worker |
| 合理设置 limits | 避免资源浪费 |
| 监控成本 | 使用 GKE 成本视图 |

### Spot 实例配置（Worker）

```yaml
supersetWorker:
  tolerations:
    - key: cloud.google.com/gke-spot
      operator: Equal
      value: "true"
      effect: NoSchedule
  nodeSelector:
    cloud.google.com/gke-spot: "true"
```

---

## 监控配置清单

### 快速部署命令

```bash
# 1. 创建监控命名空间
kubectl create namespace monitoring

# 2. 安装 Node-Exporter（宿主机指标）
helm install node-exporter prometheus-community/prometheus-node-exporter \
  --namespace monitoring \
  --values helm/superset/monitoring-node-exporter.yaml

# 3. 安装 Prometheus + Grafana
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values helm/superset/monitoring-prometheus.yaml

# 4. 部署 Superset ServiceMonitor
kubectl apply -f helm/superset/superset-servicemonitor.yaml -n superset

# 5. 启用 Superset Prometheus 指标（修改 values-production.yaml）
# 添加: PROMETHEUS_METRICS: "true"
```

### 监控配置文件清单

| 文件 | 说明 |
|------|------|
| `helm/superset/monitoring-node-exporter.yaml` | Node-Exporter DaemonSet 配置 |
| `helm/superset/monitoring-prometheus.yaml` | Prometheus + Grafana + AlertManager 配置 |
| `helm/superset/superset-servicemonitor.yaml` | Superset 指标抓取配置 |

### 监控指标分类

#### 基础设施层（Node-Exporter）

| 指标类型 | 示例 | 用途 |
|---------|------|------|
| CPU | `node_cpu_seconds_total` | CPU 使用率、负载 |
| 内存 | `node_memory_MemAvailable_bytes` | 内存压力检测 |
| 磁盘 | `node_filesystem_free_bytes` | 磁盘空间预警 |
| 网络 | `node_network_receive_bytes_total` | 网络流量监控 |
| I/O | `node_disk_read_bytes_total` | 磁盘读写性能 |

#### Kubernetes 层（kube-prometheus-stack）

| 指标类型 | 示例 | 用途 |
|---------|------|------|
| Pod 状态 | `kube_pod_status_phase` | Pod 运行状态 |
| 资源使用 | `kube_pod_container_resource_limits` | 资源限制追踪 |
| HPA | `kube_horizontalpodautoscaler_status_current_replicas` | 扩缩容状态 |

#### 应用层（Superset）

| 指标类型 | 示例 | 用途 |
|---------|------|------|
| 请求量 | `/prometheus_metrics` | QPS、并发数 |
| 延迟 | `/health` 响应时间 | 性能分析 |
| 缓存 | Redis 命中率 | 缓存效率 |

### 验证监控部署

```bash
# 1. 检查 Node-Exporter Pods
kubectl get pods -n monitoring -l app=prometheus-node-exporter

# 2. 检查 Prometheus targets
kubectl port-forward -n monitoring svc/kube-prom-prometheus 9090:9090
# 访问 http://localhost:9090/targets 查看抓取目标

# 3. 检查 Grafana
kubectl port-forward -n monitoring svc/kube-prom-grafana 3000:80
# 访问 http://localhost:3000 查看 Dashboard

# 4. 验证 Superset 指标
curl http://superset-superset:8088/health
curl http://superset-superset:8088/prometheus_metrics
```

### 推荐 Grafana Dashboard

| Dashboard ID | 名称 | 数据源 |
|-------------|------|--------|
| 1860 | Node Exporter Full | Prometheus |
| 6417 | Kubernetes Cluster | Prometheus |
| 12486 | Superset Dashboard | Prometheus |

导入方式：Grafana → Dashboards → Import → 输入 Dashboard ID

---

## 参考文档

- [GKE 文档](https://cloud.google.com/kubernetes-engine/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Cloud Memorystore](https://cloud.google.com/memorystore/docs/redis)
- [Superset Helm Chart](https://github.com/apache/superset-helm-chart)
