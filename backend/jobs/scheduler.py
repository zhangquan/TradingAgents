"""
Scheduler Service - Manages background task scheduling using APScheduler
"""

import logging
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

from backend.repositories import AnalysisTaskRepository
from backend.agent.agent_runner import agent_runner

logger = logging.getLogger(__name__)


class SchedulerJob:
    """
    Service for managing scheduled tasks using APScheduler.
    Provides task persistence, lifecycle management, and monitoring.
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.analysis_task_repo = AnalysisTaskRepository()
        self.analysis_tasks: Dict[str, Dict[str, Any]] = {}
        self._started = False
        # Initialize analysis runner service for analysis execution
        self.agent_runner = agent_runner
    
    def start(self) -> None:
        """Start the scheduler service."""
        if not self._started:
            self.scheduler.start()
            self._started = True
            self.load_analysis_tasks_on_startup()
            logger.info("Scheduler service started")
    
    def stop(self) -> None:
        """Stop the scheduler service."""
        if self._started:
            self.scheduler.shutdown()
            self._started = False
            logger.info("Scheduler service stopped")
    
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._started and self.scheduler.running
    
    def load_analysis_tasks_on_startup(self) -> None:
        """Load scheduled tasks from persistent storage and register with scheduler."""
        try:
            # Load from storage using unified API
            loaded_tasks = self.analysis_task_repo.list_analysis_tasks(limit=1000)
            
            # Convert to dict format for compatibility
            task_dict = {}
            for task in loaded_tasks:
                if task["schedule_type"] != "immediate":  # Only schedule non-immediate tasks
                    task_dict[task["task_id"]] = task
            
            self.analysis_tasks.update(task_dict)
            
            # Re-register enabled tasks with scheduler
            for task_id, task_info in task_dict.items():
                if task_info.get("enabled", True):
                    self._register_task_with_scheduler(task_id, task_info)
            
            logger.info(f"Loaded and registered {len(task_dict)} scheduled tasks")
            
        except Exception as e:
            logger.error(f"Error loading scheduled tasks on startup: {e}")
    
    def _register_task_with_scheduler(self, task_id: str, task_info: Dict[str, Any]) -> bool:
        """Register a task with the APScheduler."""
        try:
            # Set default timezone if not present (backward compatibility)
            if "timezone" not in task_info:
                task_info["timezone"] = "UTC"
                
            # Parse schedule time
            hour, minute = map(int, task_info["schedule_time"].split(':'))
            
            # Create scheduler trigger based on schedule type
            trigger = None
            if task_info["schedule_type"] == "once":
                if task_info.get("schedule_date"):
                    run_date = datetime.strptime(
                        f"{task_info['schedule_date']} {task_info['schedule_time']}", 
                        "%Y-%m-%d %H:%M"
                    )
                    if run_date > datetime.now():  # Only schedule if in future
                        analysis_config = {
                            "ticker": task_info["ticker"],
                            "analysts": task_info["analysts"],
                            "research_depth": task_info["research_depth"]
                        }
                        self.scheduler.add_job(
                            self._get_execution_function(),
                            trigger="date",
                            run_date=run_date,
                            args=[analysis_config, task_id],
                            id=task_id
                        )
                        return True
                    else:
                        logger.warning(f"Task {task_id} scheduled for past date, skipping")
                        return False
                
            elif task_info["schedule_type"] == "daily":
                trigger = CronTrigger(hour=hour, minute=minute, timezone=task_info["timezone"])
                
            elif task_info["schedule_type"] == "weekly":
                trigger = CronTrigger(day_of_week=0, hour=hour, minute=minute, timezone=task_info["timezone"])
                
            elif task_info["schedule_type"] == "monthly":
                trigger = CronTrigger(day=1, hour=hour, minute=minute, timezone=task_info["timezone"])
                
            elif task_info["schedule_type"] == "cron":
                if task_info.get("cron_expression"):
                    trigger = CronTrigger.from_crontab(task_info["cron_expression"], timezone=task_info["timezone"])
            
            if trigger and task_info["schedule_type"] != "once":
                analysis_config = {
                    "ticker": task_info["ticker"],
                    "analysts": task_info["analysts"],
                    "research_depth": task_info["research_depth"]
                }
                self.scheduler.add_job(
                    self._get_execution_function(),
                    trigger=trigger,
                    args=[analysis_config, task_id],
                    id=task_id
                )
                return True
                
        except Exception as e:
            logger.error(f"Error re-registering scheduled task {task_id}: {e}")
            # Mark task as disabled if it can't be registered
            self.analysis_tasks[task_id]["enabled"] = False
            self.analysis_task_repo.update_analysis_task(task_id, {"enabled": False, "last_error": str(e)})
            return False
        
        return False
    
    def add_task_to_scheduler(self, task_data: Dict[str, Any]) -> bool:
        """
        Add an existing task to the APScheduler.
        This method receives task data that was already created and validated by analysis_service.
        
        Args:
            task_data: Task data dictionary containing all necessary scheduling information
            
        Returns:
            bool: True if task was successfully added to scheduler
            
        Raises:
            ValueError: If task data is invalid
            Exception: If scheduler addition fails
        """
        try:
            schedule_id = task_data["task_id"]
            
            # Validate required fields
            required_fields = ["task_id", "ticker", "analysts", "research_depth", 
                             "schedule_type", "schedule_time", "enabled"]
            for field in required_fields:
                if field not in task_data:
                    raise ValueError(f"Missing required field: {field}")
            
       
            # Parse schedule time
            hour, minute = map(int, task_data["schedule_time"].split(':'))
            
            # Add to internal tracking
            self.analysis_tasks[schedule_id] = task_data.copy()
            
            # Add job to scheduler if enabled
            if task_data["enabled"]:
                self._add_job_to_scheduler(schedule_id, task_data, hour, minute)
            
            logger.info(f"Added scheduled task {schedule_id} to scheduler for {task_data['ticker']}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding task to scheduler: {e}")
            # Clean up if we added to internal tracking but failed to schedule
            if 'schedule_id' in locals() and schedule_id in self.analysis_tasks:
                del self.analysis_tasks[schedule_id]
            raise e
    

    
    def _add_job_to_scheduler(self, schedule_id: str, task_data: Dict[str, Any], hour: int, minute: int) -> None:
        """Add a job to the APScheduler."""
        # Set default timezone if not present (backward compatibility)
        if "timezone" not in task_data:
            task_data["timezone"] = "UTC"
            
        if task_data["schedule_type"] == "once":
            run_date = datetime.strptime(
                f"{task_data['schedule_date']} {task_data['schedule_time']}", 
                "%Y-%m-%d %H:%M"
            )
            analysis_config = {
                "ticker": task_data["ticker"],
                "analysts": task_data["analysts"],
                "research_depth": task_data["research_depth"]
            }
            self.scheduler.add_job(
                self._get_execution_function(),
                trigger="date",
                run_date=run_date,
                args=[analysis_config, schedule_id],
                id=schedule_id
            )
        else:
            # Create trigger based on schedule type
            if task_data["schedule_type"] == "daily":
                trigger = CronTrigger(hour=hour, minute=minute, timezone=task_data["timezone"])
            elif task_data["schedule_type"] == "weekly":
                trigger = CronTrigger(day_of_week=0, hour=hour, minute=minute, timezone=task_data["timezone"])
            elif task_data["schedule_type"] == "monthly":
                trigger = CronTrigger(day=1, hour=hour, minute=minute, timezone=task_data["timezone"])
            elif task_data["schedule_type"] == "cron":
                trigger = CronTrigger.from_crontab(task_data["cron_expression"], timezone=task_data["timezone"])
            
            analysis_config = {
                "ticker": task_data["ticker"],
                "analysts": task_data["analysts"],
                "research_depth": task_data["research_depth"]
            }
            self.scheduler.add_job(
                self._get_execution_function(),
                trigger=trigger,
                args=[analysis_config, schedule_id],
                id=schedule_id
            )
    
    def delete_analysis_task(self, task_id: str) -> bool:
        """
        Delete a scheduled task.
        
        Args:
            task_id: ID of task to delete
            
        Returns:
            bool: True if task was deleted successfully
            
        Raises:
            ValueError: If task not found
        """
        # Check if task exists
        if task_id not in self.analysis_tasks:
            # Double-check by loading from storage directly
            task = self.analysis_task_repo.get_analysis_task(task_id)
            if not task:
                raise ValueError(f"No job by the id of {task_id} was found")
            else:
                # Task exists in storage but not in memory, sync and try again
                self.analysis_tasks[task_id] = task
        
        try:
            # Remove from scheduler (ignore if job doesn't exist in scheduler)
            try:
                self.scheduler.remove_job(task_id)
            except JobLookupError:
                logger.warning(f"Job {task_id} not found in scheduler")
            
            # Remove from both memory and persistent storage
            if task_id in self.analysis_tasks:
                del self.analysis_tasks[task_id]
            
            success = self.analysis_task_repo.delete_analysis_task(task_id)
            if not success:
                raise Exception("Failed to delete task from storage")
            
            logger.info(f"Deleted scheduled task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting scheduled task {task_id}: {e}")
            raise e
    
    def update_analysis_task(self, task_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a scheduled task configuration.
        
        Args:
            task_id: ID of task to update
            update_data: Dictionary containing updated task configuration
            
        Returns:
            dict: Updated task information
            
        Raises:
            ValueError: If task not found or invalid data
        """
        if task_id not in self.analysis_tasks:
            raise ValueError("Scheduled task not found")
        
        try:
            task_info = self.analysis_tasks[task_id]
            
            # Remove from scheduler if it exists
            try:
                self.scheduler.remove_job(task_id)
            except JobLookupError:
                logger.warning(f"Job {task_id} not found in scheduler when trying to remove for update")
            
            # Update task info with new data
            task_info.update(update_data)
            
            # Re-register with scheduler if enabled
            if task_info.get("enabled", True):
                self._register_task_with_scheduler(task_id, task_info)
            
   
            
            logger.info(f"Updated scheduled task {task_id}")
            return {"message": "Task updated successfully", "task": task_info}
            
        except Exception as e:
            logger.error(f"Error updating scheduled task {task_id}: {e}")
            raise e

    def toggle_task(self, task_id: str) -> Dict[str, Any]:
        """
        Enable or disable a scheduled task.
        
        Args:
            task_id: ID of task to toggle
            
        Returns:
            dict: Status information
            
        Raises:
            ValueError: If task not found
        """
        if task_id not in self.analysis_tasks:
            raise ValueError("Scheduled task not found")
        
        try:
            task_info = self.analysis_tasks[task_id]
            
            if task_info["enabled"]:
                # Disable the task
                try:
                    self.scheduler.pause_job(task_id)
                except JobLookupError:
                    logger.warning(f"Job {task_id} not found in scheduler when trying to pause")
                task_info["enabled"] = False
                message = "Scheduled task disabled"
            else:
                # Enable the task
                try:
                    self.scheduler.resume_job(task_id)
                except JobLookupError:
                    # Job doesn't exist in scheduler, need to re-register
                    self._register_task_with_scheduler(task_id, task_info)
                task_info["enabled"] = True
                message = "Scheduled task enabled"
            
            # Save to persistent storage
            self.analysis_task_repo.update_analysis_task(task_id, {"enabled": task_info["enabled"]})
            
            return {"message": message, "enabled": task_info["enabled"]}
            
        except Exception as e:
            logger.error(f"Error toggling scheduled task {task_id}: {e}")
            raise e
    
    def get_analysis_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all scheduled tasks."""
        self.refresh_analysis_tasks()
        return self.analysis_tasks.copy()
    
    def get_analysis_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a single analysis task by ID."""
        return self.analysis_task_repo.get_analysis_task(task_id)
    
  
    
    def refresh_analysis_tasks(self) -> bool:
        """Refresh scheduled tasks from storage to sync with persistent data."""
        try:
            loaded_tasks = self.analysis_task_repo.list_analysis_tasks(limit=1000)
            
            # Convert to dict format for compatibility
            task_dict = {}
            for task in loaded_tasks:
                if task["schedule_type"] != "immediate":  # Only include scheduled tasks
                    task_dict[task["task_id"]] = task
            
            self.analysis_tasks.clear()
            self.analysis_tasks.update(task_dict)
            logger.debug(f"Refreshed {len(task_dict)} scheduled tasks from storage")
            return True
        except Exception as e:
            logger.error(f"Error refreshing scheduled tasks: {e}")
            return False
    
    def update_task_execution(self, task_id: str, execution_data: Dict[str, Any]) -> None:
        """Update task execution information."""
        if task_id in self.analysis_tasks:
            self.analysis_tasks[task_id].update(execution_data)
            self.analysis_task_repo.update_analysis_task(task_id, execution_data)
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics."""
        return {
            "running": self.is_running(),
            "total_tasks": len(self.analysis_tasks),
            "enabled_tasks": sum(1 for task in self.analysis_tasks.values() if task.get("enabled", True)),
            "jobs_in_scheduler": len(self.scheduler.get_jobs()) if self._started else 0
        }
    
    def execute_analysis(self, analysis_config: Dict[str, Any], schedule_id: str) -> None:
        """
        APScheduler调用的入口，直接启动背景任务执行.
        
        Args:
            analysis_config: 分析配置字典
            schedule_id: 调度任务ID
        """
        try:
            # 提取配置参数
            ticker = analysis_config["ticker"]
            analysts = analysis_config["analysts"]
            research_depth = analysis_config["research_depth"]
            analysis_date = analysis_config.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))
            
            # 生成执行ID
            execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ticker}_{str(uuid.uuid4())[:8]}"
            
            # 直接启动背景任务，避免不必要的中间层
            asyncio.create_task(self._execute_analysis_background(
                execution_id=execution_id,
                ticker=ticker,
                analysis_date=analysis_date,
                analysts=analysts,
                research_depth=research_depth,
                schedule_id=schedule_id,
                execution_type="scheduled"  # 标记为自动执行
            ))
            
            logger.info(f"Triggered scheduled analysis {execution_id} for schedule {schedule_id}")
                
        except Exception as e:
            logger.error(f"Error starting scheduled analysis {schedule_id}: {e}")
            raise e
    
    async def _execute_analysis_background(self, execution_id: str, ticker: str, 
                                         analysis_date: str, analysts: List[str], 
                                         research_depth: int, schedule_id: str,
                                         execution_type: str = "scheduled") -> None:
        """统一的背景任务执行器，处理所有类型的分析任务."""
        try:
            logger.info(f"Starting analysis execution {execution_id} for schedule {schedule_id}")
            
            # 在线程池中执行同步分析，避免阻塞事件循环
            result = await asyncio.to_thread(
                self.agent_runner.run_analysis_with_memory,
                task_id=execution_id,
                ticker=ticker,
                analysis_date=analysis_date,
                analysts=analysts,
                research_depth=research_depth,
                user_id="demo_user",
                enable_memory=True,
                execution_type=execution_type
            )
            
            # 更新调度任务的执行状态
            if schedule_id:  # 只有调度任务才更新schedule状态
                self.update_task_execution(schedule_id, {
                    "last_run": datetime.now().isoformat(),
                    "execution_count": self.get_analysis_task(schedule_id).get("execution_count", 0) + 1
                })
            
            logger.info(f"Completed analysis execution {execution_id}")
            return result
                
        except Exception as e:
            logger.error(f"Error in analysis execution {execution_id}: {e}")
            
            # 更新任务错误状态
            self.analysis_task_repo.update_analysis_task_status(execution_id, "error", error_message=str(e))
            
            # 如果是调度任务，也更新调度状态
            if schedule_id:
                self.update_task_execution(schedule_id, {
                    "last_error": str(e),
                    "last_run": datetime.now().isoformat()
                })
            
            # Note: System event logging would need to be implemented in analysis_task_repo
            # or through a separate logging service
            logger.error(f"Analysis error for task {execution_id}, schedule {schedule_id}, ticker {ticker}: {e}")
            
            raise e

    def _get_execution_function(self) -> Callable:
        """Get the execution function for scheduled tasks."""
        return self.execute_analysis



# Global scheduler service instance
scheduler_job = SchedulerJob()
