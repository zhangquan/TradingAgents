"""
Scheduler Service API - Provides high-level interface for scheduling operations
This service wraps the jobs scheduler and provides a clean API for routers to use.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.jobs.scheduler import scheduler_job as jobs_scheduler

logger = logging.getLogger(__name__)


class SchedulerServiceAPI:
    """
    High-level scheduler service API that wraps the jobs scheduler.
    This provides a clean interface for routers and other services.
    """
    
    def __init__(self):
        self.jobs_scheduler = jobs_scheduler
    
    def start(self) -> None:
        """Start the scheduler service."""
        self.jobs_scheduler.start()
    
    def stop(self) -> None:
        """Stop the scheduler service."""
        self.jobs_scheduler.stop()
    
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self.jobs_scheduler.is_running()
    
    def add_task_to_scheduler(self, task_id: str) -> bool:
        """Add task to scheduler by task ID. Fetches task data from repository."""
        try:
            # Import here to avoid circular imports
            from backend.repositories.analysis_task_repository import AnalysisTaskRepository
            
            # Fetch task data from repository
            analysis_task_repo = AnalysisTaskRepository()
            task_data = analysis_task_repo.get_analysis_task(task_id)
            
            if not task_data:
                raise ValueError(f"Task with ID {task_id} not found")
            
            return self.jobs_scheduler.add_task_to_scheduler(task_data)
        except Exception as e:
            logger.error(f"Error adding analysis task via API: {e}")
            raise e
    
    def toggle_task(self, task_id: str) -> Dict[str, Any]:
        """Alias for toggle_analysis_task for backward compatibility."""
        try:
            return self.jobs_scheduler.toggle_task(task_id)
        except Exception as e:
            logger.error(f"Error toggling analysis task via API: {e}")
            raise e
    
    def delete_analysis_task(self, task_id: str) -> bool:
        """
        Delete a scheduled analysis task.
        
        Args:
            task_id: ID of task to delete
            
        Returns:
            bool: True if task was deleted successfully
        """
        try:
            return self.jobs_scheduler.delete_analysis_task(task_id)
        except Exception as e:
            logger.error(f"Error deleting analysis task via API: {e}")
            raise e
    
    def update_analysis_task(self, task_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a scheduled analysis task.
        
        Args:
            task_id: ID of task to update
            update_data: Updated task configuration
            
        Returns:
            dict: Updated task information
        """
        try:
            return self.jobs_scheduler.update_analysis_task(task_id, update_data)
        except Exception as e:
            logger.error(f"Error updating analysis task via API: {e}")
            raise e
    
 
    def get_analysis_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all scheduled analysis tasks."""
        try:
            return self.jobs_scheduler.get_analysis_tasks()
        except Exception as e:
            logger.error(f"Error getting analysis tasks via API: {e}")
            raise e
    
    def get_analysis_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific scheduled analysis task."""
        try:
            return self.jobs_scheduler.get_analysis_task(task_id)
        except Exception as e:
            logger.error(f"Error getting analysis task via API: {e}")
            return None
    
    def refresh_analysis_tasks(self) -> bool:
        """Refresh scheduled tasks from storage."""
        try:
            return self.jobs_scheduler.refresh_analysis_tasks()
        except Exception as e:
            logger.error(f"Error refreshing analysis tasks via API: {e}")
            raise e
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics."""
        try:
            return self.jobs_scheduler.get_scheduler_status()
        except Exception as e:
            logger.error(f"Error getting scheduler status via API: {e}")
            raise e

# Global scheduler service API instance
scheduler_service = SchedulerServiceAPI()