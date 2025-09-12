#!/bin/bash
set -e

# TradingAgents 统一部署脚本
# 包含所有部署、构建、管理功能的一体化脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 全局变量
DOCKER_COMPOSE_CMD=""
PROJECT_ENV="production"

# 打印函数
print_header() {
    echo "================================================"
    echo "🚀 TradingAgents 统一部署管理器"
    echo "================================================"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 帮助信息
show_help() {
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${BLUE}Available Commands:${NC}"
    echo ""
    echo "🔍 Environment & Setup:"
    echo "  check       - 检查部署环境和依赖"
    echo "  setup       - 初始化项目环境"
    echo ""
    echo "🚀 Deployment:"
    echo "  deploy      - 一键部署（构建+启动）"
    echo "  quick       - 快速部署（不重新构建）"
    echo ""
    echo "🏗️ Build & Management:"
    echo "  build       - 构建生产环境镜像"
    echo "  start       - 启动服务"
    echo "  stop        - 停止服务"
    echo "  restart     - 重启服务"
    echo ""
    echo "📊 Monitoring:"
    echo "  status      - 查看服务状态"
    echo "  logs        - 查看服务日志"
    echo "  monitor     - 实时监控"
    echo "  health      - 健康检查"
    echo ""
    echo "🧹 Maintenance:"
    echo "  cleanup     - 清理环境"
    echo "  reset       - 重置全部环境"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 check           # 检查环境"
    echo "  $0 deploy          # 一键部署"
    echo "  $0 quick           # 快速启动"
    echo "  $0 monitor         # 监控服务"
    echo ""
}

# Docker 环境检查
check_docker() {
    print_status "检查 Docker 环境..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装。请先安装 Docker。"
        print_status "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker 未运行。请启动 Docker 服务。"
        exit 1
    fi
    
    # 检查 Docker Compose
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose 不可用。请安装 Docker Compose。"
        exit 1
    fi
    
    print_success "Docker 环境正常 (使用: $DOCKER_COMPOSE_CMD)"
}

# 系统环境检查
check_environment() {
    print_status "系统环境检查..."
    
    local check_pass=0
    local check_total=0
    
    # 检查 Docker 版本
    check_total=$((check_total + 1))
    local docker_version=$(docker --version | grep -o '[0-9]\+\.[0-9]\+' | head -1)
    if command -v bc &> /dev/null && [ "$(echo "$docker_version >= 20.10" | bc 2>/dev/null)" = "1" ] 2>/dev/null; then
        print_success "Docker 版本: $docker_version (>= 20.10)"
        check_pass=$((check_pass + 1))
    else
        print_warning "Docker 版本: $docker_version (推荐 >= 20.10)"
    fi
    
    # 检查内存
    check_total=$((check_total + 1))
    if command -v free &> /dev/null; then
        local total_mem=$(free -m 2>/dev/null | awk 'NR==2{printf "%.1f", $2/1024}' || echo "unknown")
        if [ "$total_mem" != "unknown" ] && command -v bc &> /dev/null && (( $(echo "$total_mem >= 2.0" | bc -l) )); then
            print_success "可用内存: ${total_mem}GB"
            check_pass=$((check_pass + 1))
        else
            print_warning "可用内存: ${total_mem}GB (推荐 >= 2GB)"
        fi
    else
        print_warning "无法检查内存 (非 Linux 系统?)"
    fi
    
    # 检查磁盘空间
    check_total=$((check_total + 1))
    local disk_space=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//' 2>/dev/null || echo "unknown")
    if [ "$disk_space" != "unknown" ] && command -v bc &> /dev/null && (( $(echo "$disk_space >= 5" | bc -l 2>/dev/null) )); then
        print_success "可用磁盘: ${disk_space}GB"
        check_pass=$((check_pass + 1))
    else
        print_warning "可用磁盘: ${disk_space}GB (推荐 >= 5GB)"
    fi
    
    # 检查端口
    local ports=(3000 8000 80 443)
    for port in "${ports[@]}"; do
        check_total=$((check_total + 1))
        if command -v netstat &> /dev/null && netstat -tuln 2>/dev/null | grep ":$port " > /dev/null; then
            print_warning "端口 $port 被占用"
        else
            print_success "端口 $port 可用"
            check_pass=$((check_pass + 1))
        fi
    done
    
    # 检查必要文件
    local required_files=("docker-compose.yml" "backend/main.py" "frontend/package.json" "pyproject.toml")
    for file in "${required_files[@]}"; do
        check_total=$((check_total + 1))
        if [ -f "$file" ]; then
            print_success "文件存在: $file"
            check_pass=$((check_pass + 1))
        else
            print_error "文件缺失: $file"
        fi
    done
    
    # 检查网络连接
    check_total=$((check_total + 1))
    if ping -c 1 google.com &> /dev/null; then
        print_success "网络连接正常"
        check_pass=$((check_pass + 1))
    else
        print_warning "网络连接检查失败 (可能影响镜像下载)"
    fi
    
    # 总结
    echo ""
    if [ $check_pass -eq $check_total ]; then
        print_success "所有检查通过！环境已准备就绪。"
    elif [ $check_pass -gt $((check_total * 3 / 4)) ]; then
        print_warning "大部分检查通过，可以继续部署。"
    else
        print_error "多项检查失败，请修复问题后再部署。"
        exit 1
    fi
    
    echo "检查结果: $check_pass/$check_total 通过"
}

# 初始化项目环境
setup_environment() {
    print_status "初始化项目环境..."
    
    # 创建必要目录
    mkdir -p data logs nginx/ssl
    chmod 755 data logs nginx 2>/dev/null || true
    
    # 创建 .env.production 文件
    if [ ! -f ".env.production" ]; then
        cat > .env.production << 'EOF'
# TradingAgents 生产环境配置
ENV=production
DEBUG=false

# 数据库配置
DATABASE_URL=sqlite:///data/tradingagents.db

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=3000

# 安全配置 (生产环境请务必修改)
SECRET_KEY=change-this-in-production-$(date +%s)
JWT_SECRET_KEY=change-this-jwt-secret-in-production-$(date +%s)

# 外部 API (根据需要配置)
# FINNHUB_API_KEY=your_finnhub_api_key
# POLYGON_API_KEY=your_polygon_api_key
# ANTHROPIC_API_KEY=your_anthropic_api_key
# OPENAI_API_KEY=your_openai_api_key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/tradingagents.log

# 性能配置
UVICORN_WORKERS=2
MAX_CONNECTIONS=100
EOF
        print_success "创建了 .env.production 配置文件"
        print_warning "请检查并更新 .env.production 中的配置"
    else
        print_status ".env.production 已存在"
    fi
    
    print_success "环境初始化完成"
}

# 构建镜像
build_images() {
    print_status "构建 Docker 镜像..."
    
    # 清理旧容器和镜像
    print_status "清理旧资源..."
    $DOCKER_COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    
    # 清理 TradingAgents 相关镜像
    if docker images | grep -q tradingagents; then
        print_status "清理旧镜像..."
        docker rmi $(docker images | grep tradingagents | awk '{print $3}') 2>/dev/null || true
    fi
    
    # 构建镜像
    print_status "开始构建新镜像..."
    $DOCKER_COMPOSE_CMD build --no-cache --pull
    
    print_success "镜像构建完成"
}

# 启动服务
start_services() {
    local nginx_mode=${1:-false}
    
    print_status "启动 TradingAgents 服务..."
    
    # 加载环境变量
    if [ -f ".env.production" ]; then
        export $(grep -v '^#' .env.production | xargs) 2>/dev/null || true
    fi
    
    # 停止现有服务
    $DOCKER_COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    
    # 启动服务
    if [ "$nginx_mode" = "true" ]; then
        print_status "启动服务 (包含 Nginx)..."
        $DOCKER_COMPOSE_CMD --profile production up -d
    else
        print_status "启动服务 (直接访问)..."
        $DOCKER_COMPOSE_CMD up -d backend frontend
    fi
    
    print_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    print_status "等待服务就绪..."
    
    # 等待后端
    local backend_ready=false
    for i in {1..30}; do
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            backend_ready=true
            break
        fi
        echo -n "."
        sleep 2
    done
    
    if [ "$backend_ready" = "true" ]; then
        print_success "后端服务就绪"
    else
        print_error "后端服务启动超时"
        show_logs
        return 1
    fi
    
    # 等待前端
    local frontend_ready=false
    for i in {1..30}; do
        if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
            frontend_ready=true
            break
        fi
        echo -n "."
        sleep 2
    done
    
    if [ "$frontend_ready" = "true" ]; then
        print_success "前端服务就绪"
    else
        print_warning "前端服务可能仍在启动中"
    fi
    
    echo ""
}

# 显示服务状态
show_status() {
    print_status "服务状态："
    echo ""
    $DOCKER_COMPOSE_CMD ps 2>/dev/null || print_warning "无法获取服务状态"
    echo ""
    
    print_status "访问地址："
    echo "🔗 前端应用: http://localhost:3000"
    echo "🔗 后端 API: http://localhost:8000"
    echo "🔗 API 文档: http://localhost:8000/docs"
    echo "🔗 健康检查: http://localhost:8000/health"
    
    if docker ps 2>/dev/null | grep -q nginx; then
        echo "🔗 Nginx: http://localhost:80"
    fi
    echo ""
}

# 显示日志
show_logs() {
    local service=${1:-""}
    
    if [ -z "$service" ]; then
        print_status "显示所有服务日志 (最近20行):"
        $DOCKER_COMPOSE_CMD logs --tail=20
    else
        print_status "显示 $service 服务日志:"
        $DOCKER_COMPOSE_CMD logs --tail=50 "$service"
    fi
}

# 实时监控
monitor_services() {
    print_status "开始实时监控 (按 Ctrl+C 退出)..."
    trap 'echo ""; print_status "停止监控"; exit 0' INT
    
    while true; do
        clear
        echo "📊 TradingAgents 实时监控 - $(date)"
        echo "=================================================="
        
        # 显示容器状态
        echo "容器状态:"
        $DOCKER_COMPOSE_CMD ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "无法获取状态"
        echo ""
        
        # 显示资源使用
        echo "资源使用:"
        local containers=$(docker ps --format "{{.Names}}" | grep tradingagents 2>/dev/null | head -5)
        if [ -n "$containers" ]; then
            docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $containers 2>/dev/null || echo "无法获取资源信息"
        else
            echo "没有运行的容器"
        fi
        echo ""
        
        echo "按 Ctrl+C 退出监控"
        sleep 5
    done
}

# 健康检查
health_check() {
    print_status "执行健康检查..."
    
    local all_healthy=true
    
    # 检查后端
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "后端健康检查通过"
    else
        print_error "后端健康检查失败"
        all_healthy=false
    fi
    
    # 检查前端
    if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "前端健康检查通过"
    else
        print_error "前端健康检查失败"
        all_healthy=false
    fi
    
    # 检查容器状态
    local running_containers=$(docker ps --format "{{.Names}}" | grep tradingagents | wc -l)
    if [ "$running_containers" -gt 0 ]; then
        print_success "发现 $running_containers 个运行中的容器"
    else
        print_error "没有发现运行中的容器"
        all_healthy=false
    fi
    
    if [ "$all_healthy" = "true" ]; then
        print_success "所有服务健康检查通过"
    else
        print_error "部分服务健康检查失败"
        print_status "建议运行: $0 logs"
        return 1
    fi
}

# 停止服务
stop_services() {
    print_status "停止所有服务..."
    $DOCKER_COMPOSE_CMD down --remove-orphans
    print_success "所有服务已停止"
}

# 重启服务
restart_services() {
    print_status "重启所有服务..."
    stop_services
    sleep 2
    start_services
    wait_for_services
    show_status
}

# 清理环境
cleanup_environment() {
    print_status "清理环境..."
    
    # 停止并删除容器
    $DOCKER_COMPOSE_CMD down --remove-orphans --volumes
    
    # 清理镜像
    if docker images | grep -q tradingagents; then
        print_status "清理 TradingAgents 镜像..."
        docker rmi $(docker images | grep tradingagents | awk '{print $3}') 2>/dev/null || true
    fi
    
    # 清理无用镜像
    print_status "清理无用资源..."
    docker system prune -f
    
    print_success "环境清理完成"
}

# 重置环境
reset_environment() {
    print_warning "这将删除所有数据和配置！"
    read -p "确认重置环境？(输入 'yes' 确认): " confirm
    
    if [ "$confirm" = "yes" ]; then
        print_status "重置环境..."
        cleanup_environment
        rm -rf data logs .env.production
        print_success "环境已重置"
    else
        print_status "取消重置操作"
    fi
}

# 一键部署
deploy_application() {
    print_status "开始一键部署..."
    
    check_docker
    setup_environment
    build_images
    start_services
    wait_for_services
    show_status
    
    print_success "🎉 部署完成！"
}

# 快速启动
quick_start() {
    print_status "快速启动 TradingAgents..."
    
    check_docker
    setup_environment
    
    # 检查镜像是否存在
    if ! docker images | grep -q tradingagents; then
        print_warning "未找到镜像，需要先构建..."
        build_images
    fi
    
    start_services
    wait_for_services
    show_status
    
    print_success "🎉 快速启动完成！"
}

# 主函数
main() {
    print_header
    
    local command="${1:-help}"
    
    case "$command" in
        "check")
            check_docker
            check_environment
            ;;
        "setup")
            check_docker
            setup_environment
            ;;
        "deploy")
            deploy_application
            ;;
        "quick")
            quick_start
            ;;
        "build")
            check_docker
            setup_environment
            build_images
            ;;
        "start")
            check_docker
            setup_environment
            start_services
            wait_for_services
            show_status
            ;;
        "stop")
            check_docker
            stop_services
            ;;
        "restart")
            check_docker
            restart_services
            ;;
        "status")
            check_docker
            show_status
            ;;
        "logs")
            check_docker
            show_logs "${2:-}"
            ;;
        "monitor")
            check_docker
            monitor_services
            ;;
        "health")
            check_docker
            health_check
            ;;
        "cleanup")
            check_docker
            cleanup_environment
            ;;
        "reset")
            check_docker
            reset_environment
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "未知命令: '$command'"
            show_help
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap 'echo ""; print_warning "操作被中断"; exit 130' INT

# 运行主函数
main "$@"