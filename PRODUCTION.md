# TradingAgents 生产环境部署指南

本指南介绍如何在生产环境中部署和管理 TradingAgents 应用（不使用 Docker）。

## 前置要求

### 必需软件
- **Python 3.10+**: 应用运行环境
- **Node.js 18+**: 前端构建和运行环境
- **uv**: Python 包管理器
- **npm**: Node.js 包管理器

### 安装 uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 快速启动

### 方式一：一键启动（推荐）
```bash
# 启动所有服务
./start-production.sh
```

### 方式二：服务管理器启动
```bash
# 启动服务
./production-service.sh start

# 查看状态
./production-service.sh status

# 停止服务
./production-service.sh stop

# 重启服务
./production-service.sh restart
```

## 服务管理

### 启动服务
```bash
./production-service.sh start
```

### 停止服务
```bash
./production-service.sh stop
```

### 重启服务
```bash
./production-service.sh restart
```

### 查看状态
```bash
./production-service.sh status
```

### 查看日志
```bash
# 查看后端日志
./production-service.sh logs backend

# 查看前端日志
./production-service.sh logs frontend
```

## 服务信息

### 服务端口
- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 日志文件
- 后端日志: `logs/backend.log`
- 前端日志: `logs/frontend.log`

### 进程文件
- 后端 PID: `pids/backend.pid`
- 前端 PID: `pids/frontend.pid`

## 环境配置

### 环境变量文件
应用启动时会自动创建 `.env` 文件，包含以下配置：

```bash
# 生产环境配置
PYTHON_ENV=production
NODE_ENV=production

# 数据库配置
DATABASE_URL=sqlite:///./data/tradingagents.db

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/tradingagents.log

# 缓存配置
CACHE_TTL=3600

# 安全配置
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000

# 外部 API（根据需要配置）
# POLYGON_API_KEY=your_polygon_api_key
# FINNHUB_API_KEY=your_finnhub_api_key
# REDDIT_CLIENT_ID=your_reddit_client_id
# REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

⚠️ **重要**: 请根据您的实际需求修改环境变量，特别是 API 密钥和安全配置。

### 前端环境配置
前端会自动创建 `.env.production.local` 文件：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NODE_ENV=production
```

## 部署流程

### 1. 准备环境
```bash
# 克隆代码
git clone <repository-url>
cd TradingAgents

# 切换到生产分支
git checkout main  # 或您的生产分支
```

### 2. 配置权限
```bash
# 添加脚本执行权限
chmod +x start-production.sh
chmod +x production-service.sh
```

### 3. 启动服务
```bash
# 使用一键启动脚本
./start-production.sh

# 或使用服务管理器
./production-service.sh start
```

### 4. 验证部署
```bash
# 检查服务状态
./production-service.sh status

# 测试 API
curl http://localhost:8000/health

# 访问前端
open http://localhost:3000
```

## 监控和维护

### 健康检查
```bash
# API 健康检查
curl http://localhost:8000/health

# 系统统计
curl http://localhost:8000/stats
```

### 日志监控
```bash
# 实时查看后端日志
tail -f logs/backend.log

# 实时查看前端日志
tail -f logs/frontend.log

# 查看错误日志
grep ERROR logs/backend.log
```

### 进程监控
```bash
# 查看运行中的服务
ps aux | grep -E "(uvicorn|node)"

# 检查端口使用情况
lsof -i :8000
lsof -i :3000
```

## 故障排除

### 服务无法启动

1. **检查端口占用**
   ```bash
   lsof -i :8000  # 检查后端端口
   lsof -i :3000  # 检查前端端口
   ```

2. **检查依赖安装**
   ```bash
   uv sync  # 重新安装 Python 依赖
   cd frontend && npm install  # 重新安装 Node.js 依赖
   ```

3. **检查日志**
   ```bash
   ./production-service.sh logs backend
   ./production-service.sh logs frontend
   ```

### 服务异常停止

1. **检查进程状态**
   ```bash
   ./production-service.sh status
   ```

2. **重启服务**
   ```bash
   ./production-service.sh restart
   ```

3. **清理并重启**
   ```bash
   ./production-service.sh stop
   rm -f pids/*.pid  # 清理 PID 文件
   ./production-service.sh start
   ```

### 数据库问题

1. **重新初始化数据库**
   ```bash
   uv run python backend/database/init_db.py
   ```

2. **检查数据库文件权限**
   ```bash
   ls -la data/tradingagents.db
   ```

## 性能优化

### 后端优化
- 启动脚本使用 4 个 worker 进程
- 启用了访问日志和 INFO 级别日志
- 配置了缓存 TTL

### 前端优化
- 使用生产构建版本
- 启用了静态文件优化
- 配置了适当的环境变量

## 安全考虑

1. **更改默认密钥**
   - 修改 `.env` 文件中的 `SECRET_KEY`

2. **配置 CORS**
   - 根据实际域名配置 `CORS_ORIGINS`

3. **API 密钥管理**
   - 将敏感的 API 密钥配置在环境变量中
   - 不要将密钥提交到版本控制系统

4. **访问控制**
   - 考虑使用反向代理（如 Nginx）
   - 配置防火墙规则

## 系统服务（可选）

如果需要将应用配置为系统服务，可以创建 systemd 服务文件：

```bash
# /etc/systemd/system/tradingagents.service
[Unit]
Description=TradingAgents Production Service
After=network.target

[Service]
Type=forking
User=your-user
WorkingDirectory=/path/to/TradingAgents
ExecStart=/path/to/TradingAgents/production-service.sh start
ExecStop=/path/to/TradingAgents/production-service.sh stop
Restart=always

[Install]
WantedBy=multi-user.target
```

然后启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tradingagents
sudo systemctl start tradingagents
```

## 更新部署

```bash
# 停止服务
./production-service.sh stop

# 更新代码
git pull origin main

# 更新依赖
uv sync
cd frontend && npm install && npm run build && cd ..

# 重启服务
./production-service.sh start
```
