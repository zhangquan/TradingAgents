from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from backend.services.analysis_services import analysis_service
from backend.services.scheduler_service import scheduler_service
from backend.database.storage_service import DatabaseStorage

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize storage
storage = DatabaseStorage()



# Pydantic models
# AnalysisRequest removed - only scheduled tasks supported now

class ScheduledAnalysisRequest(BaseModel):
    ticker: str
    analysts: List[str]
    research_depth: int = 1
    schedule_type: str  # 'once', 'daily', 'weekly', 'monthly', 'cron'
    schedule_time: str  # Time for execution (HH:MM format)
    schedule_date: Optional[str] = None  # Date for 'once' type (YYYY-MM-DD)
    cron_expression: Optional[str] = None  # For custom cron schedules
    timezone: str = "UTC"
    enabled: bool = True

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    task_type: str = "scheduled"
    schedule_id: Optional[str] = None

class AnalysisResponse(BaseModel):
    analysis_id: str
    ticker: str
    status: str
    results: Optional[Dict[str, Any]] = None
    created_at: str

# Helper functions - now delegated to services



# API Endpoints - Scheduled tasks and analysis data

@router.get("/tasks")
async def list_tasks():
    """Get list of all scheduled tasks (unified model)"""
    try:
        # Get all tasks from database storage
        all_tasks = storage.list_scheduled_tasks(limit=100)
        
        # Separate tasks by type and status
        scheduled_tasks = {}
        active_tasks = {}
        completed_tasks = {}
        
        for task in all_tasks:
            task_id = task["task_id"]
            
            if task["schedule_type"] in ["once", "daily", "weekly", "monthly", "cron"]:
                # These are scheduled tasks
                scheduled_tasks[task_id] = {
                    "task_id": task_id,
                    "task_type": "scheduled",
                    "status": "enabled" if task["enabled"] else "disabled",
                    "ticker": task["ticker"],
                    "analysts": task["analysts"],
                    "research_depth": task["research_depth"],
                    "schedule_type": task["schedule_type"],
                    "schedule_time": task["schedule_time"],
                    "schedule_date": task.get("schedule_date"),
                    "cron_expression": task.get("cron_expression"),
                    "timezone": task["timezone"],
                    "enabled": task["enabled"],
                    "created_at": task["created_at"],
                    "last_run": task.get("last_run"),
                    "execution_count": task.get("execution_count", 0),
                    "last_error": task.get("last_error")
                }
            else:
                # These are immediate execution tasks
                if task["status"] in ["created", "starting", "running"]:
                    active_tasks[task_id] = task
                elif task["status"] in ["completed", "failed", "error"]:
                    completed_tasks[task_id] = task
        
        return {
            "scheduled_tasks": scheduled_tasks,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks
        }
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    """Get details of a specific scheduled task"""
    try:
        # Get task from database storage
        task = storage.get_scheduled_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Format the task based on its type
        if task["schedule_type"] in ["once", "daily", "weekly", "monthly", "cron"]:
            # Scheduled task format
            return {
                "task_id": task_id,
                "task_type": "scheduled",
                "status": "enabled" if task["enabled"] else "disabled",
                "ticker": task["ticker"],
                "analysts": task["analysts"],
                "research_depth": task["research_depth"],
                "schedule_type": task["schedule_type"],
                "schedule_time": task["schedule_time"],
                "schedule_date": task.get("schedule_date"),
                "cron_expression": task.get("cron_expression"),
                "timezone": task["timezone"],
                "enabled": task["enabled"],
                "created_at": task["created_at"],
                "last_run": task.get("last_run"),
                "execution_count": task.get("execution_count", 0),
                "last_error": task.get("last_error")
            }
        else:
            # Immediate execution task format
            return task
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task details for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a scheduled task"""
    try:
        # Step 1: Remove from scheduler service
        scheduler_service.delete_scheduled_task(task_id)
        
        # Step 2: Remove task data from analysis service
        analysis_service.delete_scheduled_task(task_id)
        
        return {"message": "Scheduled task deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting scheduled task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_analysis_config():
    """Get analysis configuration for creating new tasks"""
    try:
        user_id = "demo_user"  # Simplified without user management
        return analysis_service.get_analysis_config(user_id)
    except Exception as e:
        logger.error(f"Error getting analysis config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_analysis_history(ticker: str = None, limit: int = 50):
    """Get analysis history"""
    try:
        user_id = "demo_user"  # Simplified without user management
        return analysis_service.get_analysis_history(user_id, ticker, limit)
    except Exception as e:
        logger.error(f"Error getting analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str):
    """Get specific analysis"""
    try:
        user_id = "demo_user"  # Simplified without user management
        analysis = analysis_service.get_analysis_by_id(analysis_id, user_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return AnalysisResponse(
            analysis_id=analysis["analysis_id"],
            ticker=analysis["ticker"],
            status=analysis["status"],
            results=analysis.get("reports"),
            created_at=analysis["created_at"]
        )
    except Exception as e:
        logger.error(f"Error getting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Scheduled Tasks API Endpoints

@router.post("/tasks", response_model=TaskResponse)
async def create_scheduled_analysis(request: ScheduledAnalysisRequest, http_request: Request):
    """Create a scheduled analysis task"""
    try:
        # Extract language preference from headers using enhanced language detection
        from tradingagents.agents.utils.language_utils import detect_language_from_accept_header
        accept_language_header = http_request.headers.get("Accept-Language", "en-US")
        accept_language = detect_language_from_accept_header(accept_language_header)
        
        # Step 1: Create task data in analysis service first
        task_data = analysis_service.create_scheduled_task(
            ticker=request.ticker,
            analysts=request.analysts,
            research_depth=request.research_depth,
            schedule_type=request.schedule_type,
            schedule_time=request.schedule_time,
            timezone=request.timezone,
            schedule_date=request.schedule_date,
            cron_expression=request.cron_expression,
            enabled=request.enabled,
            user_id="demo_user",
            language=accept_language
        )
        
        schedule_id = task_data["task_id"]
        
        # Step 2: Add the task to scheduler service
        try:
            scheduler_success = scheduler_service.add_task_to_scheduler(task_data)
            if scheduler_success:
                # Update task status to scheduled
                analysis_service.update_scheduled_task_status(schedule_id, "scheduled")
            else:
                # If scheduler failed, update status to error
                analysis_service.update_scheduled_task_status(schedule_id, "error", 
                                                            error="Failed to add to scheduler")
                raise Exception("Failed to add task to scheduler")
                
        except Exception as scheduler_error:
            # If scheduler fails, we still have the task data but it won't be executed
            logger.error(f"Failed to add task to scheduler: {scheduler_error}")
            analysis_service.update_scheduled_task_status(schedule_id, "error", 
                                                        error=str(scheduler_error))
            raise HTTPException(status_code=500, 
                              detail=f"Task created but scheduling failed: {str(scheduler_error)}")
        
        return TaskResponse(
            task_id=schedule_id,
            status="scheduled",
            message="Scheduled analysis task created and scheduled successfully",
            task_type="scheduled",
            schedule_id=schedule_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error creating scheduled analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))





@router.put("/tasks/{task_id}/toggle")
async def toggle_task(task_id: str):
    """Enable or disable a scheduled task"""
    try:
        # Step 1: Toggle in scheduler service
        result = scheduler_service.toggle_task(task_id)
        
        # Step 2: Update status in analysis service  
        new_status = "scheduled" if result["enabled"] else "disabled"
        analysis_service.update_scheduled_task_status(task_id, new_status, enabled=result["enabled"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error toggling scheduled task: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.put("/tasks/{task_id}")
async def update_task(task_id: str, request: ScheduledAnalysisRequest):
    """Update a scheduled task"""
    try:
        # Get existing task to validate it exists
        existing_task = storage.get_scheduled_task(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Validate that it's a scheduled task (not immediate)
        if existing_task.get("schedule_type") == "immediate":
            raise HTTPException(status_code=400, detail="Cannot edit immediate execution tasks")
        
        # Prepare update data
        update_data = {
            "ticker": request.ticker,
            "analysts": request.analysts,
            "research_depth": request.research_depth,
            "schedule_type": request.schedule_type,
            "schedule_time": request.schedule_time,
            "schedule_date": request.schedule_date,
            "cron_expression": request.cron_expression,
            "timezone": request.timezone,
            "enabled": request.enabled
        }
        
        # Update in scheduler service (this will handle re-registering the job)
        scheduler_service.update_scheduled_task(task_id, update_data)
        
        # Update in analysis service 
        analysis_service.update_scheduled_task_status(task_id, "scheduled", **update_data)
        
        return {
            "message": "Task updated successfully",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating scheduled task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/run-now")
async def run_task_now(task_id: str):
    """Execute a scheduled task immediately"""
    task_info = scheduler_service.get_scheduled_task(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    
    try:
        # Execute immediately using scheduler service
        analysis_config = {
            "ticker": task_info["ticker"],
            "analysts": task_info["analysts"],
            "research_depth": task_info["research_depth"]
        }
        
        # Execute the analysis using unified task executor
        execution_id = await scheduler_service.execute_analysis_task(
            ticker=analysis_config["ticker"],
            analysts=analysis_config["analysts"],
            research_depth=analysis_config["research_depth"],
            schedule_id=task_id
        )
        
        return {
            "message": f"Scheduled task '{task_id}' started successfully",
            "task_id": task_id,
            "ticker": task_info["ticker"],
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Error running scheduled task now: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler service status and statistics"""
    try:
        return scheduler_service.get_scheduler_status()
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


