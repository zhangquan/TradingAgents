from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
import uvicorn
import os
from datetime import datetime
from backend.repositories import CacheRepository, SystemRepository
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import routers and services
from backend.routers import analysis, reports, system, notifications, stock_data, conversation, scheduler
from backend.services.scheduler_service import scheduler_service

app = FastAPI(title="TradingAgents API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],  # Allow frontend and development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize repositories
cache_repo = CacheRepository()
system_repo = SystemRepository()

# Initialize and start scheduler service during app startup
@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    # Clear expired cache on startup
    cache_repo.clear_expired_cache()
    
    # Log startup event
    system_repo.log_system_event("server_startup", {
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

    # Start scheduler service
    scheduler_service.start()
    logger.info("Application startup completed")

# Include routers
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(system.router)
app.include_router(notifications.router)
app.include_router(stock_data.router)
app.include_router(conversation.router)  # New conversation memory API
app.include_router(scheduler.router)  # New scheduler observability API

# Mount static files (前端构建文件)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    # 为前端应用提供 SPA 路由支持
    from fastapi import Request
    from fastapi.responses import FileResponse
    
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """为 SPA 应用提供路由支持，所有未匹配的路径都返回 index.html"""
        # 检查是否是 API 路径
        api_prefixes = [
            "api/", "docs", "openapi.json", "health", "stats", "ws",
            "analysis/", "reports/", "system/", "notifications/", "stock_data/", 
            "conversation/", "scheduler/"
        ]
        if any(full_path.startswith(prefix) for prefix in api_prefixes):
            # 这些路径应该由其他路由处理，返回 404
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        
        # 检查是否是静态文件
        static_file_path = os.path.join(static_dir, full_path)
        if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
            return FileResponse(static_file_path)
        
        # 否则返回 index.html（SPA 路由）
        index_file_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file_path):
            return FileResponse(index_file_path)
        
        # 如果没有构建文件，返回提示信息
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Frontend not built. Please run 'npm run build' in the frontend directory.")

# Root endpoint - 如果有静态文件则提供前端应用，否则显示 API 信息
@app.get("/", include_in_schema=False)
async def root():
    """根路径处理 - 优先提供前端应用"""
    index_file_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file_path):
        from fastapi.responses import FileResponse
        return FileResponse(index_file_path)
    else:
        return {"message": "TradingAgents API is running", "docs": "/docs", "health": "/health"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/stats")
async def get_runtime_stats():
    """Get runtime statistics"""
    # Get task statistics from scheduler service
    from backend.services.analysis_services import analysis_service
    active_tasks = analysis_service.list_scheduled_tasks(status="running", limit=1000)
    completed_tasks = analysis_service.list_scheduled_tasks(status="completed", limit=1000)
    
    return {
        "active_tasks": len(active_tasks),
        "completed_tasks": len(completed_tasks),
        "timestamp": datetime.now().isoformat()
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send periodic updates
            updates = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "running"
            }
            
            await websocket.send_text(json.dumps(updates))
            await asyncio.sleep(5)  # Send updates every 5 seconds
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import os
    # 生产环境配置
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    if is_production:
        # 生产环境：不启用热重载，使用环境变量配置
        uvicorn.run(
            'backend.main:app', 
            host=os.getenv("HOST", "0.0.0.0"), 
            port=int(os.getenv("PORT", 8000)),
            reload=False,
            access_log=True,
            log_level=os.getenv("LOG_LEVEL", "info").lower()
        )
    else:
        # 开发环境：启用热重载
        uvicorn.run('backend.main:app', host="0.0.0.0", port=8000, reload=True)