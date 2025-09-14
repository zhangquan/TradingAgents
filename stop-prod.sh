#!/bin/bash

# TradingAgents 生产环境停止脚本
# Production Environment Stop Script (支持 Nginx)

echo "🛑 Stopping TradingAgents Production Environment"
echo "================================================"

# 检查是否有 Nginx 进程运行
NGINX_RUNNING=$(pgrep -f "nginx.*nginx-runtime.conf" 2>/dev/null | wc -l)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 停止 Nginx（如果运行中）
if [ $NGINX_RUNNING -gt 0 ]; then
    echo -e "${YELLOW}🌐 Stopping Nginx...${NC}"
    pkill -f "nginx.*nginx-runtime.conf" 2>/dev/null || true
fi

# 停止后端服务
echo -e "${YELLOW}🔧 Stopping backend services...${NC}"
pkill -f "uvicorn backend.main:app" 2>/dev/null || true
pkill -f "python.*backend.main" 2>/dev/null || true

# 前端已集成到后端，无需单独停止前端服务

# 等待进程完全停止
sleep 3

# 检查是否还有残留进程
NGINX_STILL_RUNNING=$(pgrep -f "nginx.*nginx-runtime.conf" 2>/dev/null | wc -l)
BACKEND_RUNNING=$(pgrep -f "uvicorn backend.main:app" 2>/dev/null | wc -l)

if [ $NGINX_RUNNING -gt 0 ]; then
    if [ $NGINX_STILL_RUNNING -eq 0 ]; then
        echo -e "${GREEN}✅ Nginx stopped successfully${NC}"
    else
        echo -e "${RED}⚠️  Some Nginx processes may still be running${NC}"
    fi
fi

if [ $BACKEND_RUNNING -eq 0 ]; then
    echo -e "${GREEN}✅ Backend (with integrated frontend) stopped successfully${NC}"
else
    echo -e "${RED}⚠️  Some backend processes may still be running${NC}"
fi

# 清理运行时文件（可选）
if [ -f "nginx/nginx-runtime.conf" ]; then
    echo -e "${YELLOW}🧹 Cleaning up runtime files...${NC}"
    # rm -f nginx/nginx-runtime.conf  # 取消注释以删除运行时配置
fi

echo -e "${GREEN}🎉 Production environment stopped${NC}"
