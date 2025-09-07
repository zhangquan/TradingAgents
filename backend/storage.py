"""
New database-based storage system for TradingAgents backend.
Maintains compatibility with the original LocalStorage API.
"""

import logging
from backend.database.storage_service import DatabaseStorage
from backend.database.database import init_database

logger = logging.getLogger(__name__)


class LocalStorage:
    """
    Database-based storage manager that maintains compatibility with the original file-based LocalStorage.
    This is a drop-in replacement that uses SQLite database instead of files.
    """
    
    def __init__(self, base_dir: str = "data"):
        """
        Initialize storage with database backend.
        base_dir parameter is kept for compatibility but not used.
        """
        self.base_dir = base_dir  # Keep for compatibility
        
        # Initialize database if needed
        try:
            init_database()
            self._storage = DatabaseStorage()
            logger.info("Database storage initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database storage: {e}")
            raise
    
    def ensure_directories(self):
        """Compatibility method - no-op for database storage."""
        pass
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        return self._storage._get_timestamp()
    
    # Delegate all methods to DatabaseStorage
    def create_user(self, user_id: str, user_data: dict) -> bool:
        return self._storage.create_user(user_id, user_data)
    
    def get_user(self, user_id: str):
        return self._storage.get_user(user_id)
    
    def update_user(self, user_id: str, updates: dict) -> bool:
        return self._storage.update_user(user_id, updates)
    
    def list_users(self):
        return self._storage.list_users()
    
    def save_analysis(self, user_id: str, ticker: str, analysis_data: dict) -> str:
        return self._storage.save_analysis(user_id, ticker, analysis_data)
    
    def get_analysis(self, user_id: str, analysis_id: str):
        return self._storage.get_analysis(user_id, analysis_id)
    
    def list_analysis(self, user_id: str, ticker: str = None, limit: int = 50):
        return self._storage.list_analysis(user_id, ticker, limit)
    
    def delete_analysis(self, user_id: str, analysis_id: str) -> bool:
        return self._storage.delete_analysis(user_id, analysis_id)
    
    def save_config(self, config_name: str, config_data: dict):
        return self._storage.save_config(config_name, config_data)
    
    def get_config(self, config_name: str):
        return self._storage.get_config(config_name)
    
    def save_user_config(self, user_id: str, config_data: dict):
        return self._storage.save_user_config(user_id, config_data)
    
    def get_user_config(self, user_id: str):
        return self._storage.get_user_config(user_id)
    
    def save_cache(self, cache_key: str, data, ttl_hours: int = 24):
        return self._storage.save_cache(cache_key, data, ttl_hours)
    
    def get_cache(self, cache_key: str):
        return self._storage.get_cache(cache_key)
    
    def clear_expired_cache(self):
        return self._storage.clear_expired_cache()
    
    def save_notification(self, user_id: str, notification: dict) -> str:
        return self._storage.save_notification(user_id, notification)
    
    def get_notifications(self, user_id: str, unread_only: bool = False, limit: int = 50):
        return self._storage.get_notifications(user_id, unread_only, limit)
    
    def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        return self._storage.mark_notification_read(user_id, notification_id)
    
    def log_system_event(self, event_type: str, event_data: dict):
        return self._storage.log_system_event(event_type, event_data)
    
    def get_system_logs(self, date_str: str = None, event_type: str = None):
        return self._storage.get_system_logs(date_str, event_type)
    
    def get_user_watchlist(self, user_id: str):
        return self._storage.get_user_watchlist(user_id)
    
    def add_to_watchlist(self, user_id: str, symbol: str) -> bool:
        return self._storage.add_to_watchlist(user_id, symbol)
    
    def remove_from_watchlist(self, user_id: str, symbol: str) -> bool:
        return self._storage.remove_from_watchlist(user_id, symbol)
    
    def update_watchlist(self, user_id: str, symbols: list) -> bool:
        return self._storage.update_watchlist(user_id, symbols)
    
    def is_symbol_in_watchlist(self, user_id: str, symbol: str) -> bool:
        return self._storage.is_symbol_in_watchlist(user_id, symbol)
    
    # Scheduled Task Management - Unified API
    def create_scheduled_task(self, task_data: dict) -> str:
        return self._storage.create_scheduled_task(task_data)
    
    def get_scheduled_task(self, task_id: str):
        return self._storage.get_scheduled_task(task_id)
    
    def list_scheduled_tasks(self, user_id: str = None, status: str = None, schedule_type: str = None, limit: int = 50):
        return self._storage.list_scheduled_tasks(user_id, status, schedule_type, limit)
    
    def update_scheduled_task(self, task_id: str, updates: dict) -> bool:
        return self._storage.update_scheduled_task(task_id, updates)
    
    def update_scheduled_task_status(self, task_id: str, status: str, **kwargs) -> bool:
        return self._storage.update_scheduled_task_status(task_id, status, **kwargs)
    
    def delete_scheduled_task(self, task_id: str) -> bool:
        return self._storage.delete_scheduled_task(task_id)
    
    def get_storage_stats(self):
        return self._storage.get_storage_stats()
    
    def create_backup(self, backup_name: str = None) -> str:
        return self._storage.create_backup(backup_name)
