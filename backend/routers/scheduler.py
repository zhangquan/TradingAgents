"""
Scheduler Router - API endpoints for observing scheduler tasks and job status
Provides comprehensive observability for the scheduler service including:
- Scheduler status and statistics
- Job execution history
- Real-time job monitoring
- Performance metrics
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from backend.services.scheduler_service import scheduler_service
from backend.services.analysis_services import analysis_service
from backend.repositories.analysis_task_repository import AnalysisTaskRepository

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/scheduler", tags=["scheduler"])

# Initialize repository for direct database access
analysis_task_repo = AnalysisTaskRepository()


# Pydantic models for responses
class SchedulerStatus(BaseModel):
    """Scheduler status response model"""
    is_running: bool
    total_tasks: int
    enabled_tasks: int
    disabled_tasks: int
    jobs_in_scheduler: int
    uptime_seconds: Optional[float] = None
    last_health_check: str

class TaskExecutionInfo(BaseModel):
    """Task execution information model"""
    task_id: str
    ticker: str
    analysts: List[str]
    schedule_type: str
    schedule_time: str
    enabled: bool
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    execution_count: int = 0
    last_error: Optional[str] = None
    avg_execution_time: Optional[float] = None

class JobStatus(BaseModel):
    """Individual job status model"""
    job_id: str
    task_id: str
    ticker: str
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None

class SchedulerMetrics(BaseModel):
    """Scheduler performance metrics model"""
    total_executions_today: int
    successful_executions_today: int
    failed_executions_today: int
    avg_execution_time_today: Optional[float] = None
    tasks_by_status: Dict[str, int]
    executions_by_hour: Dict[str, int]


# API Endpoints

@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status():
    """
    Get current scheduler status and basic statistics
    """
    try:
        # Get basic scheduler status
        basic_status = scheduler_service.get_scheduler_status()
        
        # Calculate additional metrics
        all_tasks = scheduler_service.get_analysis_tasks()
        disabled_tasks = sum(1 for task in all_tasks.values() if not task.get("enabled", True))
        
        return SchedulerStatus(
            is_running=basic_status["running"],
            total_tasks=basic_status["total_tasks"],
            enabled_tasks=basic_status["enabled_tasks"],
            disabled_tasks=disabled_tasks,
            jobs_in_scheduler=basic_status["jobs_in_scheduler"],
            last_health_check=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/job-list", response_model=List[TaskExecutionInfo])
async def get_job_list():
    """
    Get detailed job execution information with improved error handling
    """
    try:
        # Safely get analysis tasks with fallback
        try:
            all_tasks = scheduler_service.get_analysis_tasks()
        except Exception as e:
            logger.warning(f"Error getting tasks from scheduler service: {e}, returning empty list")
            all_tasks = {}
        
        job_executions = []
        
        for task_id, task_data in all_tasks.items():
            try:
                # Safely extract task data with defaults
                job_executions.append(TaskExecutionInfo(
                    task_id=task_id,
                    ticker=task_data.get("ticker", "N/A"),
                    analysts=task_data.get("analysts", []),
                    schedule_type=task_data.get("schedule_type", "unknown"),
                    schedule_time=task_data.get("schedule_time", "00:00"),
                    enabled=task_data.get("enabled", True),
                    last_run=task_data.get("last_run"),
                    next_run=task_data.get("next_run"),
                    execution_count=task_data.get("execution_count", 0),
                    last_error=task_data.get("last_error"),
                    avg_execution_time=task_data.get("avg_execution_time")
                ))
            except Exception as task_error:
                logger.warning(f"Error processing task {task_id}: {task_error}")
                continue
        
        return job_executions
        
    except Exception as e:
        logger.error(f"Error getting job list: {e}")
        # Return empty list instead of raising exception
        return []


@router.get("/statistics")
async def get_scheduler_statistics():
    """
    Get simplified scheduler statistics and performance data
    """
    try:
        # Initialize default statistics
        statistics = {
            "total_jobs": 0,
            "enabled_jobs": 0,
            "disabled_jobs": 0,
            "jobs_with_errors": 0,
            "total_executions": 0,
            "last_updated": datetime.now().isoformat(),
            "scheduler_running": False
        }
        
        try:
            # Get scheduler basic status
            status = scheduler_service.get_scheduler_status()
            statistics["scheduler_running"] = status.get("running", False)
            statistics["total_jobs"] = status.get("total_tasks", 0)
            statistics["enabled_jobs"] = status.get("enabled_tasks", 0)
            
        except Exception as status_error:
            logger.warning(f"Error getting scheduler status: {status_error}")
        
        try:
            # Get tasks for additional metrics
            all_tasks = scheduler_service.get_analysis_tasks()
            
            statistics["disabled_jobs"] = sum(1 for task in all_tasks.values() if not task.get("enabled", True))
            statistics["jobs_with_errors"] = sum(1 for task in all_tasks.values() if task.get("last_error"))
            statistics["total_executions"] = sum(task.get("execution_count", 0) for task in all_tasks.values())
            
        except Exception as tasks_error:
            logger.warning(f"Error getting tasks for statistics: {tasks_error}")
        
        return {
            "status": "success",
            "data": statistics
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler statistics: {e}")
        # Return basic error response instead of raising exception
        return {
            "status": "error",
            "message": str(e),
            "data": {
                "total_jobs": 0,
                "enabled_jobs": 0,
                "disabled_jobs": 0,
                "jobs_with_errors": 0,
                "total_executions": 0,
                "last_updated": datetime.now().isoformat(),
                "scheduler_running": False
            }
        }


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a scheduled task
    """
    try:
        # Delete from scheduler service
        success = scheduler_service.delete_analysis_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found or could not be deleted")
        
        return {
            "message": f"Task {task_id} deleted successfully",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart")
async def restart_scheduler():
    """
    Restart the scheduler service
    """
    try:
        # Stop and start the scheduler
        scheduler_service.stop()
        scheduler_service.start()
        
        return {
            "message": "Scheduler restarted successfully",
            "status": "running" if scheduler_service.is_running() else "stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error restarting scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


