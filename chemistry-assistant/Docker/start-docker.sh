#!/bin/bash
# 化学助手项目 Docker 启动脚本
# 用于快速启动和管理Docker容器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="chemistry-assistant"
DOCKER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$DOCKER_DIR")"

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

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 检查环境变量文件
check_env_file() {
    local env_file="$DOCKER_DIR/.env.docker"
    
    if [ ! -f "$env_file" ]; then
        log_error "环境变量文件不存在: $env_file"
        log_info "请复制 .env.docker.template 并配置相应的API密钥"
        exit 1
    fi
    
    # 检查是否配置了API密钥
    if grep -q "your_.*_here" "$env_file"; then
        log_warning "检测到未配置的API密钥，请确保已正确配置环境变量"
        log_info "编辑文件: $env_file"
        read -p "是否继续启动? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "环境变量文件检查通过"
}

# 创建必要的目录
create_directories() {
    local dirs=("data/vector_store" "data/textbooks" "data/question_bank" "logs")
    
    for dir in "${dirs[@]}"; do
        local full_path="$PROJECT_DIR/$dir"
        if [ ! -d "$full_path" ]; then
            mkdir -p "$full_path"
            log_info "创建目录: $full_path"
        fi
    done
    
    log_success "目录结构检查完成"
}

# 构建Docker镜像
build_image() {
    log_info "开始构建Docker镜像..."
    
    cd "$DOCKER_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose build --no-cache
    else
        docker compose build --no-cache
    fi
    
    log_success "Docker镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动化学助手服务..."
    
    cd "$DOCKER_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    log_success "服务启动完成"
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    check_service_status
}

# 检查服务状态
check_service_status() {
    log_info "检查服务状态..."
    
    cd "$DOCKER_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
    
    # 检查Web服务是否可访问
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:7860/ &> /dev/null; then
            log_success "Web服务已启动，访问地址: http://localhost:7860"
            return 0
        fi
        
        log_info "等待Web服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_warning "Web服务可能未正常启动，请检查日志"
}

# 停止服务
stop_services() {
    log_info "停止化学助手服务..."
    
    cd "$DOCKER_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启化学助手服务..."
    stop_services
    start_services
}

# 查看日志
view_logs() {
    cd "$DOCKER_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose logs -f chemistry-assistant
    else
        docker compose logs -f chemistry-assistant
    fi
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    cd "$DOCKER_DIR"
    
    # 停止并删除容器
    if command -v docker-compose &> /dev/null; then
        docker-compose down -v --rmi all
    else
        docker compose down -v --rmi all
    fi
    
    # 清理未使用的镜像
    docker image prune -f
    
    log_success "清理完成"
}

# 显示帮助信息
show_help() {
    echo "化学助手 Docker 管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动服务 (默认)"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  build     构建镜像"
    echo "  logs      查看日志"
    echo "  status    查看状态"
    echo "  cleanup   清理资源"
    echo "  help      显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动服务"
    echo "  $0 logs     # 查看日志"
    echo "  $0 cleanup  # 清理所有资源"
}

# 主函数
main() {
    local command="${1:-start}"
    
    echo "==========================================="
    echo "化学助手 Docker 管理脚本"
    echo "==========================================="
    
    case "$command" in
        "start")
            check_docker
            check_env_file
            create_directories
            start_services
            ;;
        "stop")
            check_docker
            stop_services
            ;;
        "restart")
            check_docker
            restart_services
            ;;
        "build")
            check_docker
            check_env_file
            create_directories
            build_image
            ;;
        "logs")
            check_docker
            view_logs
            ;;
        "status")
            check_docker
            check_service_status
            ;;
        "cleanup")
            check_docker
            cleanup
            ;;
        "help")
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"