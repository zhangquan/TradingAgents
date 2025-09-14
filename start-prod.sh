#!/bin/bash

# TradingAgents 生产环境启动脚本
# Production Environment Startup Script with Optional Nginx Support

set -e  # 遇到错误时退出

# 检查命令行参数
USE_NGINX=false
NGINX_PORT=80

while [[ $# -gt 0 ]]; do
    case $1 in
        --nginx)
            USE_NGINX=true
            shift
            ;;
        --nginx-port)
            NGINX_PORT="$2"
            shift 2
            ;;
        --help|-h)
            echo "TradingAgents 生产环境启动脚本 (集成架构)"
            echo ""
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --nginx          启用 Nginx 反向代理"
            echo "  --nginx-port     设置 Nginx 端口 (默认: 80)"
            echo "  --help, -h       显示此帮助信息"
            echo ""
            echo "架构说明:"
            echo "  前端构建文件已集成到后端静态目录 (backend/static/)"
            echo "  单一后端服务同时提供 API 和静态文件服务"
            echo ""
            echo "示例:"
            echo "  $0                    # 直接启动集成后端服务"
            echo "  $0 --nginx           # 使用 Nginx 代理启动"
            echo "  $0 --nginx --nginx-port 8080  # 使用 Nginx 在端口 8080"
            echo ""
            echo "访问地址:"
            echo "  直接模式: http://localhost:8000"
            echo "  Nginx 模式: http://localhost (或指定端口)"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
BACKEND_HOST=${HOST:-"127.0.0.1"}
BACKEND_PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}
LOG_LEVEL=${LOG_LEVEL:-"info"}

# 显示启动信息
if [ "$USE_NGINX" = true ]; then
    echo "🚀 Starting TradingAgents Production Environment (Nginx + Integrated Backend)"
    echo "============================================================================="
    echo -e "${BLUE}Architecture: Nginx (Port ${NGINX_PORT}) → Backend (Port ${BACKEND_PORT}) with integrated frontend${NC}"
else
    echo "🚀 Starting TradingAgents Production Environment (Integrated Backend)"
    echo "===================================================================="
    echo -e "${BLUE}Architecture: Single Backend Service (Port ${BACKEND_PORT}) with integrated frontend${NC}"
fi
echo ""

# Nginx 相关检查
if [ "$USE_NGINX" = true ]; then
    # 检查 Nginx
    if ! command -v nginx &> /dev/null; then
        echo -e "${RED}❌ Nginx is not installed. Please install Nginx first.${NC}"
        echo "Ubuntu/Debian: sudo apt-get install nginx"
        echo "CentOS/RHEL: sudo yum install nginx"
        echo "macOS: brew install nginx"
        exit 1
    fi

    # 检查 Nginx 端口权限
    if [ "$EUID" -ne 0 ] && [ "$NGINX_PORT" -lt 1024 ]; then
        echo -e "${YELLOW}⚠️  Warning: Running on port $NGINX_PORT usually requires root privileges${NC}"
        echo -e "${YELLOW}   Consider using a higher port (e.g., 8080) or run with sudo${NC}"
    fi

    # 创建 Nginx 日志目录
    mkdir -p nginx/logs
fi

# 创建必要的目录
echo -e "${BLUE}📁 Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data

# 检查 Python 环境
echo -e "${BLUE}🐍 Checking Python environment...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed. Please install uv first.${NC}"
    echo "Install with: pip install uv"
    exit 1
fi

# 检查端口可用性
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use by another service.${NC}"
        echo "Please stop the service using port $port or change the $service port."
        return 1
    fi
    return 0
}

echo -e "${BLUE}🔍 Checking port availability...${NC}"
if ! check_port $BACKEND_PORT "backend"; then
    exit 1
fi

# 前端已集成到后端，无需检查独立前端端口

if [ "$USE_NGINX" = true ]; then
    if ! check_port $NGINX_PORT "nginx"; then
        exit 1
    fi
fi

# 创建生产环境配置文件（如果不存在）
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}⚙️ Creating production environment configuration...${NC}"
    
    # 计算实际的 URL
    if [ "$USE_NGINX" = true ]; then
        API_URL="http://localhost:${NGINX_PORT}"
    else
        API_URL="http://localhost:${BACKEND_PORT}"
    fi
    
    cat > .env.production << EOF
# 生产环境配置
ENVIRONMENT=production
HOST=${BACKEND_HOST}
PORT=${BACKEND_PORT}
NGINX_PORT=${NGINX_PORT}
DATABASE_URL=sqlite:///data/tradingagents.db
API_BASE_URL=${API_URL}
FRONTEND_URL=${API_URL}
LOG_LEVEL=${LOG_LEVEL}
LOG_FILE=logs/production.log
SECRET_KEY=production-secret-key-change-me
CORS_ORIGINS=${API_URL}
WORKERS=${WORKERS}
CACHE_TTL=3600
SCHEDULER_ENABLED=true
SCHEDULER_MAX_WORKERS=5
USE_NGINX=${USE_NGINX}
EOF
    echo -e "${GREEN}✅ Created .env.production file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env.production to add your API keys and customize settings${NC}"
fi

# 设置生产环境标识
export ENVIRONMENT=production

# 加载环境变量
if [ -f ".env.production" ]; then
    echo -e "${BLUE}📄 Loading production environment variables...${NC}"
    # 使用更安全的方式加载环境变量，避免特殊字符问题
    while IFS='=' read -r key value; do
        # 跳过注释行和空行
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue
        # 移除可能的引号
        value=$(echo "$value" | sed 's/^"//g' | sed 's/"$//g')
        export "$key"="$value"
    done < .env.production
fi

# 安装 Python 依赖
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
uv sync

# 初始化数据库
echo -e "${BLUE}🗄️ Initializing database...${NC}"
uv run python -c "
from backend.database.init_db import init_database
init_database()
print('Database initialized successfully')
"

# 构建前端
echo -e "${BLUE}🎨 Building frontend...${NC}"
cd frontend

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed. Please install npm first.${NC}"
    exit 1
fi

# 安装前端依赖
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
    npm install
fi

# 创建前端环境配置（用于构建时的 API 地址）
echo -e "${BLUE}⚙️ Creating frontend build configuration...${NC}"
if [ "$USE_NGINX" = true ]; then
    cat > .env.production << EOF
VITE_API_BASE_URL=http://localhost:${NGINX_PORT}
EOF
else
    cat > .env.production << EOF
VITE_API_BASE_URL=http://localhost:${BACKEND_PORT}
EOF
fi

# 构建前端到后端静态目录
echo -e "${BLUE}🔨 Building frontend for production (output: backend/static/)...${NC}"
npm run build

# 检查构建结果
if [ ! -f "../backend/static/index.html" ]; then
    echo -e "${RED}❌ Frontend build failed - index.html not found in backend/static/${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend build completed successfully${NC}"

# 显示构建统计信息
STATIC_FILES_COUNT=$(find ../backend/static -type f | wc -l | tr -d ' ')
STATIC_DIR_SIZE=$(du -sh ../backend/static | cut -f1)
echo -e "${BLUE}📊 Build stats: ${STATIC_FILES_COUNT} files, ${STATIC_DIR_SIZE} total${NC}"

cd ..

# 配置 Nginx（如果启用）
if [ "$USE_NGINX" = true ]; then
    echo -e "${BLUE}⚙️ Configuring Nginx...${NC}"
    
    # 创建运行时 Nginx 配置
    cat > nginx/nginx-runtime.conf << EOF
# TradingAgents 运行时 Nginx 配置
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志配置
    access_log $(pwd)/nginx/logs/access.log;
    error_log $(pwd)/nginx/logs/error.log;

    # 基本配置
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 100M;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # 上游服务器
    upstream backend {
        server ${BACKEND_HOST}:${BACKEND_PORT};
    }

    server {
        listen ${NGINX_PORT};
        server_name localhost;

        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;

        # 所有请求都转发到后端（包括静态文件和 SPA 路由）
        location / {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_cache_bypass \$http_upgrade;
        }

        # 静态资源缓存（由后端处理）
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # WebSocket 特殊处理（需要长连接支持）
        location /ws {
            proxy_pass http://backend/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 86400;
        }
    }
}
EOF
fi

# 启动后端服务
echo -e "${GREEN}🚀 Starting backend server...${NC}"
echo -e "${BLUE}Host: ${BACKEND_HOST}${NC}"
echo -e "${BLUE}Port: ${BACKEND_PORT}${NC}"
echo -e "${BLUE}Workers: ${WORKERS}${NC}"
echo -e "${BLUE}Log Level: ${LOG_LEVEL}${NC}"

# 使用 uvicorn 启动生产服务器
uv run uvicorn backend.main:app \
    --host ${BACKEND_HOST} \
    --port ${BACKEND_PORT} \
    --workers ${WORKERS} \
    --log-level ${LOG_LEVEL} \
    --access-log &

BACKEND_PID=$!

# 等待后端启动
echo -e "${YELLOW}⏳ Waiting for backend to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:${BACKEND_PORT}/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend started successfully${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend failed to start after 30 seconds${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# 前端已构建并集成到后端静态目录
echo -e "${GREEN}✅ Frontend built and integrated into backend static files${NC}"

# 启动 Nginx（如果启用）
if [ "$USE_NGINX" = true ]; then
    echo -e "${GREEN}🌐 Starting Nginx...${NC}"
    nginx -c $(pwd)/nginx/nginx-runtime.conf -p $(pwd)/nginx/ &
    NGINX_PID=$!

    # 等待 Nginx 启动
    echo -e "${YELLOW}⏳ Waiting for Nginx to start...${NC}"
    sleep 3

    # 检查 Nginx 状态
    if ! curl -s http://localhost:${NGINX_PORT}/health >/dev/null 2>&1; then
        echo -e "${RED}❌ Nginx failed to start or proxy is not working${NC}"
        kill $BACKEND_PID $NGINX_PID 2>/dev/null || true
        exit 1
    fi
    echo -e "${GREEN}✅ Nginx started successfully${NC}"
fi

echo ""
if [ "$USE_NGINX" = true ]; then
    echo -e "${GREEN}🎉 TradingAgents Production Environment (Nginx + Integrated Backend) Started!${NC}"
    echo "=============================================================================="
    echo -e "${GREEN}🌐 Main Application: http://localhost:${NGINX_PORT}${NC}"
    echo -e "${GREEN}📚 API Documentation: http://localhost:${NGINX_PORT}/docs${NC}"
    echo -e "${GREEN}📊 Health Check: http://localhost:${NGINX_PORT}/health${NC}"
    echo ""
    echo -e "${BLUE}Architecture: Nginx → Backend (with integrated frontend static files)${NC}"
    echo -e "${BLUE}Direct Backend Access (for debugging):${NC}"
    echo -e "${BLUE}   Backend API: http://localhost:${BACKEND_PORT}${NC}"
    echo -e "${BLUE}   Backend Docs: http://localhost:${BACKEND_PORT}/docs${NC}"
    echo ""
    echo -e "${YELLOW}📝 Logs:${NC}"
    echo -e "${YELLOW}   Nginx Access: nginx/logs/access.log${NC}"
    echo -e "${YELLOW}   Nginx Error: nginx/logs/error.log${NC}"
    echo -e "${YELLOW}   Backend: logs/production.log${NC}"
else
    echo -e "${GREEN}🎉 TradingAgents Production Environment (Integrated Backend) Started!${NC}"
    echo "======================================================================="
    echo -e "${GREEN}🌐 Main Application: http://localhost:${BACKEND_PORT}${NC}"
    echo -e "${GREEN}📚 API Documentation: http://localhost:${BACKEND_PORT}/docs${NC}"
    echo -e "${GREEN}📊 Health Check: http://localhost:${BACKEND_PORT}/health${NC}"
    echo ""
    echo -e "${BLUE}Architecture: Single Backend Service (with integrated frontend static files)${NC}"
    echo -e "${BLUE}Static Files: Served directly from backend/static/${NC}"
    echo ""
    echo -e "${YELLOW}📝 Logs:${NC}"
    echo -e "${YELLOW}   Backend: logs/production.log${NC}"
    echo -e "${YELLOW}   Access: uvicorn access logs${NC}"
fi
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    
    if [ "$USE_NGINX" = true ] && [ ! -z "$NGINX_PID" ]; then
        kill $NGINX_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Nginx stopped${NC}"
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi
    
    # 清理可能的子进程
    pkill -f "nginx.*nginx-runtime.conf" 2>/dev/null || true
    pkill -f "uvicorn backend.main:app" 2>/dev/null || true
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# 捕获中断信号
trap cleanup INT TERM

# 监控服务状态
monitor_services() {
    while true; do
        sleep 30
        
        if [ "$USE_NGINX" = true ]; then
            # 使用 Nginx 时检查主入口
            if ! curl -s http://localhost:${NGINX_PORT}/health >/dev/null 2>&1; then
                echo -e "${RED}⚠️  Nginx or backend health check failed${NC}"
            fi
        else
            # 直接访问时检查后端（包含前端静态文件）
            if ! curl -s http://localhost:${BACKEND_PORT}/health >/dev/null 2>&1; then
                echo -e "${RED}⚠️  Backend health check failed${NC}"
            fi
        fi
    done
}

# 在后台运行监控
monitor_services &
MONITOR_PID=$!

# 等待用户中断
if [ "$USE_NGINX" = true ]; then
    wait $BACKEND_PID $NGINX_PID
else
    wait $BACKEND_PID
fi
