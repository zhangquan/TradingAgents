import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from tradingagents.default_config import DEFAULT_CONFIG
from backend.database.storage_service import DatabaseStorage

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service class for handling trading analysis operations"""
    
    def __init__(self):
        self.storage = DatabaseStorage()
    
    def get_user_config_with_defaults(self, user_id: str) -> Dict[str, Any]:
        """Get user configuration with fallback to system defaults."""
        user_config = self.storage.get_user_config(user_id)
        
        # Use user preferences or fallback to defaults from DEFAULT_CONFIG
        return {
            "llm_provider": user_config.get("llm_provider", DEFAULT_CONFIG["llm_provider"]),
            "backend_url": user_config.get("backend_url", DEFAULT_CONFIG["backend_url"]),
            "deep_think_llm": user_config.get("deep_thinker", DEFAULT_CONFIG["deep_think_llm"]),
            "quick_think_llm": user_config.get("shallow_thinker", DEFAULT_CONFIG["quick_think_llm"]),
            "default_research_depth": user_config.get("default_research_depth", 1),
            "default_analysts": user_config.get("default_analysts", ["market", "news", "fundamentals"])
        }
    
    def get_analysis_config(self, user_id: str = "demo_user") -> Dict[str, Any]:
        """Get analysis configuration for creating new tasks."""
        user_config = self.get_user_config_with_defaults(user_id)
        
        return {
            "default_config": {
                "llm_provider": user_config["llm_provider"],
                "backend_url": user_config["backend_url"],
                "shallow_thinker": user_config["quick_think_llm"],
                "deep_thinker": user_config["deep_think_llm"],
                "research_depth": user_config["default_research_depth"],
                "analysts": user_config["default_analysts"]
            }
        }
    
    def get_analysis_history(self, user_id: str = "demo_user", ticker: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get analysis history for a user."""
        analyses = self.storage.list_analysis(user_id, ticker, limit)
        return {"analyses": analyses}
    
    def get_analysis_by_id(self, analysis_id: str, user_id: str = "demo_user") -> Optional[Dict[str, Any]]:
        """Get specific analysis by ID."""
        return self.storage.get_analysis(user_id, analysis_id)
    
    def create_scheduled_task(self, 
                              ticker: str,
                              analysts: List[str],
                              research_depth: int,
                              schedule_type: str,
                              schedule_time: str,
                              timezone: str = "UTC",
                              schedule_date: Optional[str] = None,
                              cron_expression: Optional[str] = None,
                              enabled: bool = True,
                              user_id: str = "demo_user",
                              language: str = "en-US") -> Dict[str, Any]:
        """
        Create scheduled task.
        This method creates and stores the task data in the unified ScheduledTask model.
        
        Args:
            ticker: Stock ticker symbol
            analysts: List of analyst types
            research_depth: Depth of analysis
            schedule_type: Type of schedule ('once', 'daily', 'weekly', 'monthly', 'cron')
            schedule_time: Time in HH:MM format
            timezone: Timezone for scheduling
            schedule_date: Date for 'once' type (YYYY-MM-DD)
            cron_expression: Cron expression for 'cron' type
            enabled: Whether task is enabled
            user_id: User identifier
            
        Returns:
            dict: Created task data with unique ID
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate analysts
        valid_analysts = ["market", "news", "fundamentals", "social_media"]
        for analyst in analysts:
            if analyst not in valid_analysts:
                raise ValueError(f"Invalid analyst: {analyst}. Must be one of {valid_analysts}")
        
        # Validate schedule parameters
        self._validate_schedule_parameters(schedule_type, schedule_time, schedule_date, cron_expression)
        
        # Create task data for unified ScheduledTask model
        task_data = {
            "user_id": user_id,
            "ticker": ticker.upper(),
            "analysts": analysts,
            "research_depth": research_depth,
            "schedule_type": schedule_type,
            "schedule_time": schedule_time,
            "schedule_date": schedule_date,
            "cron_expression": cron_expression,
            "timezone": timezone,
            "enabled": enabled,
            "status": "created",
            "language": language
        }
        
        # Create task using unified API
        try:
            task_id = self.storage.create_scheduled_task(task_data)
            
            # Get the created task data
            created_task = self.storage.get_scheduled_task(task_id)
            if not created_task:
                raise Exception(f"Failed to retrieve created task {task_id}")
            
            # Log task creation
            self.storage.log_system_event("scheduled_task_created", {
                "task_id": task_id,
                "ticker": ticker,
                "analysts": analysts,
                "schedule_type": schedule_type,
                "user_id": user_id
            })
            
            logger.info(f"Created scheduled task {task_id} for {ticker}")
            return created_task
            
        except Exception as e:
            logger.error(f"Error creating scheduled task data: {e}")
            raise e
    
    def _validate_schedule_parameters(self, 
                                    schedule_type: str, 
                                    schedule_time: str,
                                    schedule_date: Optional[str] = None,
                                    cron_expression: Optional[str] = None) -> None:
        """Validate schedule parameters."""
        if schedule_type not in ["immediate", "once", "daily", "weekly", "monthly", "cron"]:
            raise ValueError("Invalid schedule_type. Must be one of: immediate, once, daily, weekly, monthly, cron")
        
        # Validate time format (skip for immediate tasks)
        if schedule_type != "immediate":
            try:
                hour, minute = map(int, schedule_time.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Invalid time format")
            except (ValueError, IndexError):
                raise ValueError("schedule_time must be in HH:MM format")
        
        # Additional validations
        if schedule_type == "once":
            if not schedule_date:
                raise ValueError("schedule_date is required for 'once' schedule type")
            try:
                schedule_datetime = datetime.strptime(f"{schedule_date} {schedule_time}", "%Y-%m-%d %H:%M")
                if schedule_datetime <= datetime.now():
                    raise ValueError("Scheduled date and time must be in the future")
            except ValueError as e:
                if "time data" in str(e):
                    raise ValueError("schedule_date must be in YYYY-MM-DD format")
                raise e
        
        if schedule_type == "cron" and not cron_expression:
            raise ValueError("cron_expression is required for 'cron' schedule type")
    
    def update_scheduled_task_status(self, task_id: str, status: str, **kwargs) -> None:
        """Update scheduled task status and additional data."""
        try:
            self.storage.update_scheduled_task_status(task_id, status, **kwargs)
            logger.info(f"Updated scheduled task {task_id} status to {status}")
        except Exception as e:
            logger.error(f"Error updating scheduled task status: {e}")
            raise e
    
    def get_scheduled_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get scheduled task by ID."""
        try:
            return self.storage.get_scheduled_task(task_id)
        except Exception as e:
            logger.error(f"Error getting scheduled task: {e}")
            return None
    
    def list_scheduled_tasks(self, user_id: str = "demo_user", status: str = None, schedule_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List scheduled tasks with optional filters."""
        try:
            return self.storage.list_scheduled_tasks(user_id, status, schedule_type, limit)
        except Exception as e:
            logger.error(f"Error listing scheduled tasks: {e}")
            return []
    
    def delete_scheduled_task(self, task_id: str) -> bool:
        """Delete scheduled task."""
        try:
            success = self.storage.delete_scheduled_task(task_id)
            if success:
                self.storage.log_system_event("scheduled_task_deleted", {
                    "task_id": task_id
                })
                logger.info(f"Deleted scheduled task {task_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting scheduled task: {e}")
            return False


# Global service instance
analysis_service = AnalysisService()
