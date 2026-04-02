#!/bin/bash
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# =============================================================================
# Superset GKE 一键部署脚本
# =============================================================================
# 
# 用途：快速在 GKE 上部署 Superset 生产环境
# 
# 前置要求：
#   - gcloud CLI 已安装并配置
#   - kubectl 已安装
#   - helm 3 已安装
#   - 已创建 GKE 集群
#   - 已创建 Cloud SQL 和 Memorystore
#
# 使用方法：
#   ./scripts/gke-deploy.sh --project YOUR_PROJECT --region asia-east1
# =============================================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认值
PROJECT_ID=""
REGION="asia-east1"
CLUSTER_NAME="superset-cluster"
NAMESPACE="superset"
SUPERSET_DOMAIN="superset.your-domain.com"
DB_HOST=""
REDIS_HOST=""
DB_PASSWORD=""
SECRET_KEY=""

# 帮助信息
usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --project        GCP 项目 ID (必需)"
    echo "  --region         GCP 区域 (默认: asia-east1)"
    echo "  --cluster        GKE 集群名称 (默认: superset-cluster)"
    echo "  --namespace      Kubernetes 命名空间 (默认: superset)"
    echo "  --domain         访问域名 (默认: superset.your-domain.com)"
    echo "  --db-host        Cloud SQL 私有 IP (必需)"
    echo "  --redis-host     Cloud Memorystore 私有 IP (必需)"
    echo "  --db-password    数据库密码 (必需)"
    echo "  --secret-key     Superset 加密密钥 (必需)"
    echo "  --help           显示帮助信息"
    echo ""
    exit 1
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift 2 ;;
        --region) REGION="$2"; shift 2 ;;
        --cluster) CLUSTER_NAME="$2"; shift 2 ;;
        --namespace) NAMESPACE="$2"; shift 2 ;;
        --domain) SUPERSET_DOMAIN="$2"; shift 2 ;;
        --db-host) DB_HOST="$2"; shift 2 ;;
        --redis-host) REDIS_HOST="$2"; shift 2 ;;
        --db-password) DB_PASSWORD="$2"; shift 2 ;;
        --secret-key) SECRET_KEY="$2"; shift 2 ;;
        --help) usage ;;
        *) echo "未知参数: $1"; usage ;;
    esac
done

# 验证必需参数
if [[ -z "$PROJECT_ID" ]] || [[ -z "$DB_HOST" ]] || [[ -z "$REDIS_HOST" ]] || [[ -z "$DB_PASSWORD" ]] || [[ -z "$SECRET_KEY" ]]; then
    echo -e "${RED}错误: 缺少必需参数${NC}"
    usage
fi

# 输出配置信息
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Superset GKE 部署配置${NC}"
echo -e "${GREEN}============================================${NC}"
echo "项目 ID: $PROJECT_ID"
echo "区域: $REGION"
echo "集群名: $CLUSTER_NAME"
echo "命名空间: $NAMESPACE"
echo "域名: $SUPERSET_DOMAIN"
echo "数据库 Host: $DB_HOST"
echo "Redis Host: $REDIS_HOST"
echo -e "${GREEN}============================================${NC}"

# 1. 配置 gcloud
echo -e "${YELLOW}[1/6] 配置 gcloud CLI...${NC}"
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

# 2. 获取集群凭证
echo -e "${YELLOW}[2/6] 获取 GKE 集群凭证...${NC}"
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION

# 3. 创建命名空间
echo -e "${YELLOW}[3/6] 创建 Kubernetes 命名空间...${NC}"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# 4. 创建 Secret
echo -e "${YELLOW}[4/6] 创建 Kubernetes Secret...${NC}"
kubectl create secret generic superset-secrets \
    --namespace $NAMESPACE \
    --from-literal=DB_PASS="$DB_PASSWORD" \
    --from-literal=SUPERSET_SECRET_KEY="$SECRET_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# 5. 生成 values 文件
echo -e "${YELLOW}[5/6] 生成 production values 文件...${NC}"
cat > /tmp/values-gke.yaml << EOF
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0

ingress:
  enabled: true
  ingressClassName: nginx
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
  hosts:
    - $SUPERSET_DOMAIN
  tls:
    - secretName: superset-tls
      hosts:
        - $SUPERSET_DOMAIN

postgresql:
  enabled: false

redis:
  enabled: false

supersetNode:
  replicas:
    enabled: true
    replicaCount: 3
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  env:
    GUNICORN_TIMEOUT: 300
    GUNICORN_WORKERS: 4
    GUNICORN_THREADS: 2
    SERVER_WORKER_AMOUNT: 4
    SERVER_THREADS_AMOUNT: 2
    WORKER_MAX_REQUESTS: 1000
    WORKER_MAX_REQUESTS_JITTER: 200
  connections:
    db_type: postgresql
    db_host: "$DB_HOST"
    db_port: "5432"
    db_user: superset
    db_pass: "$DB_PASSWORD"
    db_name: superset
    redis_host: "$REDIS_HOST"
    redis_port: "6379"
    redis_user: ""
    redis_password: ""
    redis_cache_db: "1"
    redis_celery_db: "0"
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 1000m
      memory: 2Gi
  readinessProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 30
    timeoutSeconds: 5
    failureThreshold: 3
    periodSeconds: 10
  livenessProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 60
    timeoutSeconds: 5
    failureThreshold: 5
    periodSeconds: 30
  startupProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 30
    timeoutSeconds: 5
    failureThreshold: 30
    periodSeconds: 10
  podDisruptionBudget:
    enabled: true
    minAvailable: 2

supersetWorker:
  enabled: true
  replicas:
    enabled: true
    replicaCount: 2
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 8
    targetCPUUtilizationPercentage: 70
  resources:
    limits:
      cpu: 1000m
      memory: 2Gi
    requests:
      cpu: 500m
      memory: 1Gi
  podDisruptionBudget:
    enabled: true
    minAvailable: 1

supersetCeleryBeat:
  enabled: true
  replicaCount: 1

supersetCeleryFlower:
  enabled: true
  replicaCount: 1

init:
  enabled: true
  loadExamples: false
  createAdmin: true
  adminUser:
    username: admin
    firstname: Superset
    lastname: Admin
    email: admin@your-domain.com
    password: admin123

extraSecretEnv:
  DB_PASS: "$DB_PASSWORD"
  SUPERSET_SECRET_KEY: "$SECRET_KEY"

runAsUser: 1000
EOF

# 6. 部署
echo -e "${YELLOW}[6/6] 部署 Superset...${NC}"
helm upgrade --install superset apache-superset/superset \
    --namespace $NAMESPACE \
    --values /tmp/values-gke.yaml \
    --timeout 10m \
    --wait

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "获取 Ingress IP:"
echo "  kubectl get ingress -n $NAMESPACE"
echo ""
echo "查看 Pod 状态:"
echo "  kubectl get pods -n $NAMESPACE"
echo ""
echo "查看日志:"
echo "  kubectl logs -n $NAMESPACE deployment/superset-superset -f"
echo ""
echo "访问 Superset:"
echo "  http://$SUPERSET_DOMAIN"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo -e "${YELLOW}重要: 部署后请立即修改 admin 密码！${NC}"
