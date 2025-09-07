# TradingAgents 部署指南

本指南帮助您快速部署 TradingAgents 的完整前后端系统。

## 系统要求

### 软件依赖
- **Python 3.10+** - 后端 API 服务
- **Node.js 18+** - 前端应用
- **npm** - 包管理器

### API 密钥（必需）
- **FinnHub API Key** - 金融数据获取
- **OpenAI API Key** - GPT 模型访问

### API 密钥（可选）
- **Google API Key** - Gemini 模型访问
- **Aliyun API Key** - 通义千问模型访问

## 快速启动

### 方法一：使用启动脚本（推荐）

1. **克隆项目并进入目录**
   ```bash
   git clone <repository-url>
   cd TradingAgents
   ```

2. **配置环境变量**
   ```bash
   # 创建 .env 文件
   cat > .env << EOF
   FINNHUB_API_KEY=your_finnhub_api_key
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_API_KEY=your_google_api_key  # 可选
   ALIYUN_API_KEY=your_aliyun_api_key  # 可选
   EOF
   ```

3. **一键启动**
   ```bash
   ./start.sh
   ```

4. **访问应用**
   - 前端界面: http://localhost:3000
   - 后端 API: http://localhost:8000
   - API 文档: http://localhost:8000/docs

5. **停止服务**
   ```bash
   ./stop.sh
   ```

### 方法二：手动启动

#### 启动后端服务

1. **安装后端依赖**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **启动后端 API**
   ```bash
   python main.py
   ```
   后端服务将在 http://localhost:8000 启动

#### 启动前端服务

1. **安装前端依赖**
   ```bash
   cd frontend
   npm install
   ```

2. **配置环境变量**
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

3. **启动前端开发服务器**
   ```bash
   npm run dev
   ```
   前端应用将在 http://localhost:3000 启动

## 配置说明

### 环境变量配置

在项目根目录创建 `.env` 文件：

```bash
# 必需的 API 密钥
FINNHUB_API_KEY=your_finnhub_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 可选的 API 密钥
GOOGLE_API_KEY=your_google_api_key_here
ALIYUN_API_KEY=your_aliyun_api_key_here

# 可选配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### API 密钥获取

1. **FinnHub API Key**
   - 访问 https://finnhub.io/
   - 注册账户并获取免费 API 密钥

2. **OpenAI API Key**
   - 访问 https://platform.openai.com/
   - 创建账户并生成 API 密钥

3. **Google API Key**
   - 访问 https://makersuite.google.com/
   - 创建项目并启用 Generative AI API

4. **Aliyun API Key**
   - 访问阿里云控制台
   - 开通通义千问服务并获取 API 密钥

## 生产环境部署

### 使用 Docker（推荐）

1. **构建 Docker 镜像**
   ```bash
   # 构建后端镜像
   docker build -t tradingagents-backend ./backend
   
   # 构建前端镜像
   docker build -t tradingagents-frontend ./frontend
   ```

2. **使用 Docker Compose**
   ```yaml
   # docker-compose.yml
   version: '3.8'
   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       environment:
         - FINNHUB_API_KEY=${FINNHUB_API_KEY}
         - OPENAI_API_KEY=${OPENAI_API_KEY}
       volumes:
         - ./results:/app/results
     
     frontend:
       build: ./frontend
       ports:
         - "3000:3000"
       environment:
         - NEXT_PUBLIC_API_URL=http://backend:8000
       depends_on:
         - backend
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

### 直接部署到服务器

#### 后端部署

1. **安装系统依赖**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx
   ```

2. **部署应用**
   ```bash
   # 克隆代码
   git clone <repository-url>
   cd TradingAgents/backend
   
   # 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # 安装生产服务器
   pip install gunicorn
   
   # 启动服务
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
   ```

3. **配置 Nginx 反向代理**
   ```nginx
   # /etc/nginx/sites-available/tradingagents-backend
   server {
       listen 80;
       server_name your-backend-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

#### 前端部署

1. **构建生产版本**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **使用 PM2 管理进程**
   ```bash
   npm install -g pm2
   pm2 start npm --name "tradingagents-frontend" -- start
   ```

3. **配置 Nginx**
   ```nginx
   # /etc/nginx/sites-available/tradingagents-frontend
   server {
       listen 80;
       server_name your-frontend-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 监控和维护

### 日志管理

- **后端日志**: `backend/backend.log`
- **前端日志**: 浏览器控制台或 PM2 日志
- **系统日志**: `/var/log/nginx/`

### 健康检查

- **后端健康检查**: `GET http://localhost:8000/health`
- **前端健康检查**: 访问主页 `http://localhost:3000`

### 备份策略

1. **代码备份**: 使用 Git 版本控制
2. **配置备份**: 备份 `.env` 文件（注意安全）
3. **数据备份**: 备份 `results/` 目录中的报告文件

## 故障排除

### 常见问题

1. **端口占用**
   ```bash
   # 检查端口占用
   lsof -i :8000  # 后端端口
   lsof -i :3000  # 前端端口
   
   # 杀死占用进程
   kill -9 <PID>
   ```

2. **API 密钥错误**
   - 检查 `.env` 文件配置
   - 验证 API 密钥有效性
   - 确认 API 额度未用完

3. **内存不足**
   - 监控系统资源使用
   - 适当增加服务器内存
   - 优化模型选择

4. **网络问题**
   - 检查防火墙设置
   - 确认 API 服务可访问
   - 验证 DNS 解析

### 性能优化

1. **后端优化**
   - 增加 worker 进程数
   - 配置缓存机制
   - 使用更快的模型

2. **前端优化**
   - 启用 CDN
   - 配置缓存策略
   - 代码分割优化

3. **系统优化**
   - SSD 存储
   - 足够的内存
   - 多核 CPU

## 安全建议

1. **API 密钥安全**
   - 使用环境变量存储
   - 定期轮换密钥
   - 限制 API 访问权限

2. **网络安全**
   - 使用 HTTPS
   - 配置防火墙
   - 限制访问来源

3. **数据安全**
   - 加密敏感数据
   - 定期备份
   - 访问控制

## 技术支持

如果您在部署过程中遇到问题，可以：

1. 查看项目文档和 README
2. 检查 GitHub Issues
3. 查看后端和前端日志
4. 联系技术支持

---

祝您使用愉快！🚀
