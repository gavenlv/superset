#!/bin/bash

# Apache Superset 初始化脚本
# 此脚本提供了完整的 Superset 初始化过程，包含错误处理和日志记录

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查函数
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "命令 '$1' 未找到，请先安装"
        exit 1
    fi
}

check_database_connection() {
    log_info "检查数据库连接..."
    if superset version --verbose &> /dev/null; then
        log_success "数据库连接正常"
    else
        log_error "数据库连接失败，请检查配置"
        exit 1
    fi
}

# 环境变量设置（可通过外部配置）
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_FIRSTNAME="${ADMIN_FIRSTNAME:-Superset}"
ADMIN_LASTNAME="${ADMIN_LASTNAME:-Admin}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@superset.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
LOAD_EXAMPLES="${LOAD_EXAMPLES:-false}"
BACKUP_BEFORE_INIT="${BACKUP_BEFORE_INIT:-false}"

# 步骤计数器
STEP_TOTAL=4
if [ "$LOAD_EXAMPLES" = "true" ]; then
    STEP_TOTAL=5
fi

print_step() {
    local step_num=$1
    local step_desc=$2
    echo ""
    echo "======================================="
    echo "步骤 $step_num/$STEP_TOTAL: $step_desc"
    echo "======================================="
}

# 备份函数（针对 PostgreSQL）
backup_database() {
    if [ "$BACKUP_BEFORE_INIT" = "true" ]; then
        log_info "创建数据库备份..."
        local backup_file="superset_backup_$(date +%Y%m%d_%H%M%S).sql"
        
        # 尝试从环境变量获取数据库连接信息
        if [ -n "$DATABASE_URL" ]; then
            pg_dump "$DATABASE_URL" > "$backup_file" 2>/dev/null || {
                log_warning "备份失败，但继续初始化过程"
            }
        else
            log_warning "未找到 DATABASE_URL，跳过备份"
        fi
    fi
}

# 主初始化函数
main() {
    echo "Apache Superset 初始化脚本"
    echo "=========================="
    echo ""
    
    # 环境检查
    log_info "检查环境..."
    check_command "superset"
    check_database_connection
    
    # 显示配置信息
    log_info "初始化配置:"
    echo "  管理员用户名: $ADMIN_USERNAME"
    echo "  管理员邮箱:   $ADMIN_EMAIL"
    echo "  加载示例数据: $LOAD_EXAMPLES"
    echo "  创建备份:     $BACKUP_BEFORE_INIT"
    echo ""
    
    # 确认继续
    if [ "${AUTO_CONFIRM:-false}" != "true" ]; then
        read -p "是否继续初始化? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "初始化已取消"
            exit 0
        fi
    fi
    
    # 备份（如果需要）
    backup_database
    
    # 步骤 1: 数据库升级
    print_step 1 "数据库升级"
    log_info "应用数据库迁移..."
    if superset db upgrade; then
        log_success "数据库升级完成"
    else
        log_error "数据库升级失败"
        exit 1
    fi
    
    # 步骤 2: 创建管理员用户
    print_step 2 "创建管理员用户"
    log_info "创建管理员用户: $ADMIN_USERNAME"
    
    # 检查用户是否已存在
    if superset fab list-users 2>/dev/null | grep -q "$ADMIN_USERNAME"; then
        log_warning "用户 '$ADMIN_USERNAME' 已存在，跳过创建"
    else
        if superset fab create-admin \
            --username "$ADMIN_USERNAME" \
            --firstname "$ADMIN_FIRSTNAME" \
            --lastname "$ADMIN_LASTNAME" \
            --email "$ADMIN_EMAIL" \
            --password "$ADMIN_PASSWORD"; then
            log_success "管理员用户创建完成"
        else
            log_error "管理员用户创建失败"
            exit 1
        fi
    fi
    
    # 步骤 3: 初始化角色和权限
    print_step 3 "初始化角色和权限"
    log_info "同步角色定义和权限..."
    if superset init; then
        log_success "角色和权限初始化完成"
    else
        log_error "角色和权限初始化失败"
        exit 1
    fi
    
    # 步骤 4: 验证初始化
    print_step 4 "验证初始化"
    log_info "验证系统状态..."
    
    # 检查用户是否创建成功
    if superset fab list-users 2>/dev/null | grep -q "$ADMIN_USERNAME"; then
        log_success "✓ 管理员用户验证通过"
    else
        log_error "✗ 管理员用户验证失败"
        exit 1
    fi
    
    # 检查角色是否创建成功
    local expected_roles=("Admin" "Alpha" "Gamma" "sql_lab")
    for role in "${expected_roles[@]}"; do
        if superset fab list-roles 2>/dev/null | grep -q "$role"; then
            log_success "✓ 角色 '$role' 验证通过"
        else
            log_warning "✗ 角色 '$role' 验证失败"
        fi
    done
    
    # 步骤 5: 加载示例数据（可选）
    if [ "$LOAD_EXAMPLES" = "true" ]; then
        print_step 5 "加载示例数据"
        log_info "加载示例数据..."
        if superset load_examples; then
            log_success "示例数据加载完成"
        else
            log_warning "示例数据加载失败，但不影响核心功能"
        fi
    fi
    
    # 完成信息
    echo ""
    echo "======================================="
    log_success "Superset 初始化完成!"
    echo "======================================="
    echo ""
    echo "登录信息:"
    echo "  用户名: $ADMIN_USERNAME"
    echo "  密码:   $ADMIN_PASSWORD"
    echo "  邮箱:   $ADMIN_EMAIL"
    echo ""
    log_info "现在可以启动 Superset 服务器:"
    echo "  superset run -h 0.0.0.0 -p 8088"
    echo ""
}

# 错误处理
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo ""
        log_error "初始化过程中发生错误 (退出码: $exit_code)"
        echo ""
        echo "故障排除建议:"
        echo "1. 检查数据库连接: superset db current"
        echo "2. 查看详细错误: 在命令前添加 SUPERSET_LOG_LEVEL=DEBUG"
        echo "3. 重置数据库: superset db init (谨慎使用，会丢失数据)"
        echo "4. 检查配置文件: 确认 superset_config.py 设置正确"
        echo ""
    fi
}

trap cleanup EXIT

# 执行主函数
main "$@" 