from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import uvicorn
from datetime import datetime
from backend.database.storage_service import DatabaseStorage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import routers and services
from backend.routers import analysis, reports,system, notifications, stock_data
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

# Initialize storage
storage = DatabaseStorage()

# Initialize and start scheduler service during app startup
@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    # Clear expired cache on startup
    storage.clear_expired_cache()
    
    # Log startup event
    storage.log_system_event("server_startup", {
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

# Root endpoints
@app.get("/")
async def root():
    return {"message": "TradingAgents API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/stats")
async def get_runtime_stats():
    """Get runtime statistics"""
    # Get task statistics from database
    active_tasks = storage.list_tasks(status="running", limit=1000)
    completed_tasks = storage.list_tasks(status="completed", limit=1000)
    
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
    uvicorn.run('backend.main:app', host="0.0.0.0", port=8000, reload=True)