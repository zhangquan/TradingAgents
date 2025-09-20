import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from tradingagents.default_config import DEFAULT_CONFIG
from backend.repositories import (
    UserConfigRepository, AnalysisTaskRepository,
    SystemRepository
)

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service class for handling trading analysis operations"""
    
    def __init__(self):
        self.user_config_repo = UserConfigRepository()
        self.analysis_task_repo = AnalysisTaskRepository()
        self.system_repo = SystemRepository()
    
    def get_user_config_with_defaults(self, user_id: str) -> Dict[str, Any]:
        """Get user configuration with fallback to system defaults."""
        user_config = self.user_config_repo.get_user_config(user_id)
        
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
    
 

    def create_analysis_task(self, 
                              ticker: str,
                              analysts: List[str],
                              research_depth: int,
                              schedule_type: str,
                              schedule_time: str,
                              schedule_date: Optional[str] = None,
                              cron_expression: Optional[str] = None,
                              enabled: bool = True,
                              user_id: str = "demo_user") -> Dict[str, Any]:
        """
        Create scheduled task.
        This method creates and stores the task data in the unified ScheduledTask model.
        
        Args:
            ticker: Stock ticker symbol
            analysts: List of analyst types
            research_depth: Depth of analysis
            schedule_type: Type of schedule ('once', 'daily', 'weekly', 'monthly', 'cron')
            schedule_time: Time in HH:MM format
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
            "enabled": enabled,
            "status": "created"
        }
        
        # Create task using unified API
        try:
            task_id = self.analysis_task_repo.create_analysis_task(task_data)
            
            # Get the created task data
            created_task = self.analysis_task_repo.get_analysis_task(task_id)
            if not created_task:
                raise Exception(f"Failed to retrieve created task {task_id}")
            
            # Log task creation
            self.system_repo.log_system_event("analysis_task_created", {
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
    
    def update_analysis_task_status(self, task_id: str, status: str, **kwargs) -> None:
        """Update scheduled task status and additional data."""
        try:
            self.analysis_task_repo.update_analysis_task_status(task_id, status, **kwargs)
            logger.info(f"Updated scheduled task {task_id} status to {status}")
        except Exception as e:
            logger.error(f"Error updating scheduled task status: {e}")
            raise e
    def update_analysis_task(self, task_id: str, **kwargs) -> None:
        """Update scheduled task status and additional data."""
        try:
            self.analysis_task_repo.update_analysis_task(task_id, **kwargs)
            logger.info(f"Updated scheduled task {task_id} status to {kwargs['status']}")
        except Exception as e:
            logger.error(f"Error updating scheduled task: {e}")
            raise e
    def toggle_task(self, task_id: str) -> None:
        """Toggle scheduled task status and additional data."""
        try:
            self.analysis_task_repo.toggle_task(task_id)
        
        except Exception as e:
            logger.error(f"Error toggling scheduled task: {e}")
            raise e
    def get_analysis_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get scheduled task by ID."""
        try:
            return self.analysis_task_repo.get_analysis_task(task_id)
        except Exception as e:
            logger.error(f"Error getting scheduled task: {e}")
            return None
    
    def list_analysis_tasks(self, user_id: str = "demo_user", status: str = None, schedule_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List scheduled tasks with optional filters."""
        try:
            return self.analysis_task_repo.list_analysis_tasks(user_id, status, schedule_type, limit)
        except Exception as e:
            logger.error(f"Error listing scheduled tasks: {e}")
            return []
    
    def list_analysis_tasks_by_ticker(self, ticker: str, user_id: str = "demo_user", limit: int = 50) -> List[Dict[str, Any]]:
        """List scheduled tasks filtered by ticker symbol."""
        try:
            logger.info(f"Service: Getting tasks for ticker={ticker.upper()}, user_id={user_id}, limit={limit}")
            result = self.analysis_task_repo.get_tasks_by_ticker(ticker.upper(), user_id, limit)
            logger.info(f"Service: Retrieved {len(result)} tasks")
            return result
        except Exception as e:
            logger.error(f"Error listing scheduled tasks by ticker {ticker}: {e}")
            return []
    
    def delete_analysis_task(self, task_id: str) -> bool:
        """Delete scheduled task."""
        try:
            success = self.analysis_task_repo.delete_analysis_task(task_id)
            if success:
                self.system_repo.log_system_event("analysis_task_deleted", {
                    "task_id": task_id
                })
                logger.info(f"Deleted scheduled task {task_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting scheduled task: {e}")
            return False
    
    async def execute_analysis_task(self, ticker: str, analysts: List[str], 
                                  research_depth: int, task_id: str) -> str:
        """
        Execute an analysis task immediately and return execution ID.
        
        Args:
            ticker: Stock ticker symbol
            analysts: List of analyst types
            research_depth: Depth of research
            task_id: task ID for tracking
            
        Returns:
            str: Execution ID for tracking the analysis
        """
        try:
            # Import here to avoid circular imports
            from backend.agent.agent_runner import agent_runner
            from datetime import datetime
            import uuid
            
            # Generate execution ID
            execution_id = str(uuid.uuid4())
            
            # Execute analysis with memory support
            result = agent_runner.run_sync_analysis_with_memory(
                task_id=execution_id,
                ticker=ticker,
                analysis_date=datetime.now().strftime("%Y-%m-%d"),
                analysts=analysts,
                research_depth=research_depth,
                user_id="demo_user",
                enable_memory=True,
                execution_type="manual"
            )
            
            logger.info(f"Analysis task executed with ID: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Error executing analysis task: {e}")
            raise e


# Global service instance
analysis_service = AnalysisService()
