# TradingAgents 使用指南

## 快速开始

### 开发环境

```bash
# 启动开发环境
./start-dev.sh
```

### 生产环境

#### 方式一：直接启动（简单部署）
```bash
# 直接启动后端（包含集成的前端）
./start-prod.sh

# 访问应用
open http://localhost:8000  # 统一入口（前端+后端）
open http://localhost:8000/docs  # API 文档
```

#### 方式二：Nginx 代理（推荐生产环境）
```bash
# 使用 Nginx 反向代理启动
./start-prod.sh --nginx

# 访问应用
open http://localhost  # 统一入口
```

#### 方式三：自定义端口
```bash
# 使用自定义 Nginx 端口
./start-prod.sh --nginx --nginx-port 8080

# 访问应用
open http://localhost:8080
```

### 停止服务

```bash
# 停止所有服务（自动检测并停止 Nginx、后端、前端）
./stop-prod.sh
```

## 命令参数

### start-prod.sh 参数说明

```bash
./start-prod.sh [选项]

选项:
  --nginx          启用 Nginx 反向代理
  --nginx-port     设置 Nginx 端口 (默认: 80)
  --help, -h       显示帮助信息

示例:
  ./start-prod.sh                    # 直接启动后端和前端
  ./start-prod.sh --nginx           # 使用 Nginx 代理启动
  ./start-prod.sh --nginx --nginx-port 8080  # 使用 Nginx 在端口 8080
```

## 部署模式对比

| 特性 | 直接启动 | Nginx 代理 |
|------|----------|------------|
| 复杂度 | 简单 | 中等 |
| 架构 | 单服务 | 代理+后端 |
| 性能 | 基础 | 优化 |
| 缓存 | FastAPI 缓存 | Nginx 缓存优化 |
| 压缩 | FastAPI 压缩 | Gzip 压缩 |
| 负载均衡 | 无 | 支持 |
| SSL/HTTPS | 需手动配置 | 易于配置 |
| 生产推荐 | 小规模 | 大规模 |

## 端口说明

### 直接启动模式
- **后端（包含前端）**: 8000

### Nginx 代理模式
- **Nginx**: 80 (或自定义端口)
- **后端（包含前端）**: 8000 (内部)

## 访问地址

### 直接启动模式
- 主应用: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### Nginx 代理模式
- 主应用: http://localhost (或自定义端口)
- API 接口: http://localhost/api/
- API 文档: http://localhost/docs
- 健康检查: http://localhost/health
- WebSocket: ws://localhost/ws

## 日志文件

### 应用日志
- **后端日志**: `logs/production.log`
- **系统日志**: `data/logs/system_*.json`

### Nginx 日志（仅 Nginx 模式）
- **访问日志**: `nginx/logs/access.log`
- **错误日志**: `nginx/logs/error.log`

## 常见问题

### 1. 端口被占用
```bash
# 检查端口占用
lsof -i :80    # Nginx 端口
lsof -i :8000  # 后端端口（包含前端）

# 停止占用进程
kill -9 <PID>
```

### 2. 权限问题（端口 80）
```bash
# 方式一：使用 sudo 运行
sudo ./start-prod.sh --nginx

# 方式二：使用高端口
./start-prod.sh --nginx --nginx-port 8080
```

### 3. Nginx 未安装
```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx

# macOS
brew install nginx
```

### 4. 服务无法启动
```bash
# 检查依赖
which uv      # Python 包管理器
which node    # Node.js
which npm     # npm 包管理器
which nginx   # Nginx (仅 Nginx 模式需要)

# 查看详细日志
tail -f logs/production.log
```

### 5. 前端构建失败
```bash
# 清理并重新安装依赖
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
cd ..
```

## 高级配置

### 环境变量配置
编辑 `.env.production` 文件：

```bash
# 基础配置
HOST=127.0.0.1
PORT=8000
NGINX_PORT=80

# API 密钥
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# 性能配置
WORKERS=2
LOG_LEVEL=INFO
```

### 系统服务配置
参考 `PRODUCTION_DEPLOYMENT.md` 中的 systemd 配置部分。

## 监控和维护

### 健康检查
```bash
# 检查服务状态
curl http://localhost/health      # Nginx 模式
curl http://localhost:8000/health # 直接模式
```

### 查看日志
```bash
# 实时查看后端日志
tail -f logs/production.log

# 查看 Nginx 日志（仅 Nginx 模式）
tail -f nginx/logs/access.log
tail -f nginx/logs/error.log
```

### 重启服务
```bash
# 停止服务
./stop-prod.sh

# 重新启动
./start-prod.sh --nginx  # 或其他参数
```

## 技术支持

如需更详细的部署和配置信息，请参考：
- `PRODUCTION_DEPLOYMENT.md` - 完整生产环境部署指南
- `NGINX_DEPLOYMENT.md` - Nginx 详细配置指南
- `README.md` - 项目概述和基础信息
