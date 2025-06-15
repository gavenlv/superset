#!/bin/bash

# Superset 自动化部署脚本
# 支持 Docker 和 Kubernetes 部署

set -e

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/superset_deploy_$(date +%Y%m%d_%H%M%S).log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# 显示帮助信息
show_help() {
    cat << EOF
Superset 自动化部署脚本

用法:
    $0 [OPTIONS] COMMAND

命令:
    docker          使用 Docker Compose 部署
    kubernetes      使用 Kubernetes 部署
    build           构建 Docker 镜像
    test            运行部署测试
    status          检查部署状态
    logs            查看日志
    stop            停止服务
    clean           清理资源

选项:
    -e, --env ENV           环境 (dev/staging/prod) [默认: prod]
    -v, --version VERSION   版本标签 [默认: latest]
    -n, --namespace NS      Kubernetes 命名空间 [默认: superset]
    -f, --force            强制重新部署
    -h, --help             显示帮助信息

示例:
    $0 docker                           # 使用 Docker 部署到生产环境
    $0 -e staging kubernetes            # 部署到 Kubernetes 暂存环境
    $0 -v v1.5.0 build                 # 构建指定版本镜像
    $0 --force docker                  # 强制重新部署

EOF
}

# 默认配置
ENVIRONMENT="prod"
VERSION="latest"
NAMESPACE="superset"
FORCE_DEPLOY=false
DEPLOYMENT_TYPE=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_DEPLOY=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        docker|kubernetes|build|test|status|logs|stop|clean)
            DEPLOYMENT_TYPE="$1"
            shift
            ;;
        *)
            error "未知参数: $1"
            ;;
    esac
done

# 验证必需参数
if [[ -z "$DEPLOYMENT_TYPE" ]]; then
    error "请指定部署类型: docker, kubernetes, build, test, status, logs, stop, clean"
fi

# 环境配置
case $ENVIRONMENT in
    dev|development)
        ENV_FILE=".env.dev"
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    staging)
        ENV_FILE=".env.staging"
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    prod|production)
        ENV_FILE=".env.prod"
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    *)
        error "不支持的环境: $ENVIRONMENT"
        ;;
esac

log "开始 Superset 部署 - 环境: $ENVIRONMENT, 版本: $VERSION, 类型: $DEPLOYMENT_TYPE"

# 检查系统依赖
check_dependencies() {
    log "检查系统依赖..."
    
    local missing_deps=()
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    # 根据部署类型检查特定依赖
    case $DEPLOYMENT_TYPE in
        docker)
            if ! command -v docker-compose &> /dev/null; then
                missing_deps+=("docker-compose")
            fi
            ;;
        kubernetes)
            if ! command -v kubectl &> /dev/null; then
                missing_deps+=("kubectl")
            fi
            if ! command -v helm &> /dev/null; then
                missing_deps+=("helm")
            fi
            ;;
    esac
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "缺少依赖: ${missing_deps[*]}"
    fi
    
    log "依赖检查通过"
}

# 验证环境配置
validate_environment() {
    log "验证环境配置..."
    
    # 检查环境文件
    if [[ ! -f "$PROJECT_ROOT/$ENV_FILE" ]]; then
        warn "环境文件不存在: $ENV_FILE，使用默认配置"
        # 创建默认环境文件
        create_default_env_file
    fi
    
    # 验证必需的环境变量
    source "$PROJECT_ROOT/$ENV_FILE"
    
    local required_vars=("SUPERSET_SECRET_KEY" "DB_PASSWORD" "REDIS_PASSWORD")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "环境变量 $var 未设置"
        fi
    done
    
    log "环境配置验证通过"
}

# 创建默认环境文件
create_default_env_file() {
    log "创建默认环境文件: $ENV_FILE"
    
    cat > "$PROJECT_ROOT/$ENV_FILE" << EOF
# Superset 配置
SUPERSET_SECRET_KEY=$(openssl rand -base64 42)
SUPERSET_LOAD_EXAMPLES=no

# 数据库配置
DB_HOST=postgres
DB_PORT=5432
DB_USER=superset
DB_PASSWORD=$(openssl rand -base64 16)
DB_NAME=superset

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=$(openssl rand -base64 16)

# 服务端口
HTTP_PORT=80
HTTPS_PORT=443
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_PASSWORD=$(openssl rand -base64 16)

# 版本标签
SUPERSET_VERSION=$VERSION
EOF
    
    log "默认环境文件已创建"
}

# 构建 Docker 镜像
build_image() {
    log "构建 Docker 镜像..."
    
    cd "$PROJECT_ROOT"
    
    # 构建生产镜像
    docker build \
        -t "superset:$VERSION" \
        -t "superset:latest" \
        -f docker/Dockerfile.production \
        .
    
    log "Docker 镜像构建完成: superset:$VERSION"
}

# Docker 部署
deploy_docker() {
    log "开始 Docker Compose 部署..."
    
    cd "$PROJECT_ROOT"
    
    # 检查是否需要强制重建
    if [[ "$FORCE_DEPLOY" == "true" ]]; then
        log "强制重新部署，停止现有服务..."
        docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" down -v
    fi
    
    # 启动服务
    log "启动 Superset 服务..."
    docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # 等待服务启动
    log "等待服务启动..."
    sleep 30
    
    # 初始化数据库
    if [[ "$FORCE_DEPLOY" == "true" ]] || ! docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T superset superset db upgrade &>/dev/null; then
        log "初始化 Superset 数据库..."
        docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T superset superset db upgrade
        docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T superset superset fab create-admin \
            --username admin \
            --firstname Superset \
            --lastname Admin \
            --email admin@superset.com \
            --password admin123
        docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T superset superset init
    fi
    
    log "Docker 部署完成"
}

# Kubernetes 部署
deploy_kubernetes() {
    log "开始 Kubernetes 部署..."
    
    cd "$PROJECT_ROOT"
    
    # 创建命名空间
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # 创建配置文件
    log "创建 Kubernetes 配置..."
    
    # 创建 Secret
    kubectl create secret generic superset-secrets \
        --from-env-file="$ENV_FILE" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # 应用配置文件
    for manifest in kubernetes/*.yaml; do
        if [[ -f "$manifest" ]]; then
            log "应用配置: $(basename "$manifest")"
            envsubst < "$manifest" | kubectl apply -f - -n "$NAMESPACE"
        fi
    done
    
    # 等待部署完成
    log "等待 Pod 就绪..."
    kubectl wait --for=condition=ready pod -l app=superset -n "$NAMESPACE" --timeout=300s
    
    log "Kubernetes 部署完成"
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    case $DEPLOYMENT_TYPE in
        docker)
            # 检查 Docker 服务状态
            if docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" ps | grep -q "Up"; then
                log "Docker 服务运行正常"
            else
                error "Docker 服务未正常运行"
            fi
            
            # 检查应用健康状态
            if curl -f http://localhost/health &>/dev/null; then
                log "应用健康检查通过"
            else
                warn "应用健康检查失败"
            fi
            ;;
        kubernetes)
            # 检查 Pod 状态
            kubectl get pods -n "$NAMESPACE"
            
            # 检查服务状态
            kubectl get services -n "$NAMESPACE"
            
            log "Kubernetes 资源状态检查完成"
            ;;
    esac
}

# 运行测试
run_tests() {
    log "运行部署测试..."
    
    # 基础连接测试
    python3 "$SCRIPT_DIR/health_check.py" || warn "健康检查测试失败"
    
    # 性能测试
    python3 "$SCRIPT_DIR/performance_test.py" || warn "性能测试失败"
    
    log "测试完成"
}

# 查看服务状态
show_status() {
    log "查看服务状态..."
    
    case $DEPLOYMENT_TYPE in
        docker)
            docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" ps
            ;;
        kubernetes)
            kubectl get all -n "$NAMESPACE"
            ;;
    esac
}

# 查看日志
show_logs() {
    log "查看服务日志..."
    
    case $DEPLOYMENT_TYPE in
        docker)
            docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
            ;;
        kubernetes)
            kubectl logs -f deployment/superset -n "$NAMESPACE"
            ;;
    esac
}

# 停止服务
stop_services() {
    log "停止服务..."
    
    case $DEPLOYMENT_TYPE in
        docker)
            docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" down
            ;;
        kubernetes)
            kubectl delete all --all -n "$NAMESPACE"
            ;;
    esac
    
    log "服务已停止"
}

# 清理资源
clean_resources() {
    log "清理资源..."
    
    case $DEPLOYMENT_TYPE in
        docker)
            # 停止并移除容器、网络、卷
            docker-compose -f "docker/$COMPOSE_FILE" --env-file "$ENV_FILE" down -v --remove-orphans
            
            # 清理未使用的镜像
            docker image prune -f
            ;;
        kubernetes)
            # 删除命名空间（会删除所有相关资源）
            kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
            ;;
    esac
    
    log "资源清理完成"
}

# 主执行逻辑
main() {
    # 检查依赖
    check_dependencies
    
    # 验证环境
    validate_environment
    
    # 根据部署类型执行相应操作
    case $DEPLOYMENT_TYPE in
        build)
            build_image
            ;;
        docker)
            build_image
            deploy_docker
            health_check
            ;;
        kubernetes)
            build_image
            deploy_kubernetes
            health_check
            ;;
        test)
            run_tests
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        stop)
            stop_services
            ;;
        clean)
            clean_resources
            ;;
        *)
            error "不支持的部署类型: $DEPLOYMENT_TYPE"
            ;;
    esac
    
    log "部署脚本执行完成"
    info "日志文件: $LOG_FILE"
}

# 信号处理
trap 'error "部署脚本被中断"' INT TERM

# 执行主函数
main "$@" 