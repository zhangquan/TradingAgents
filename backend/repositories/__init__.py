"""
Repository layer for TradingAgents backend.
Provides data access abstractions following the Repository pattern.

Each repository can be imported and used directly by services and routers.
"""

from .base import BaseRepository
from .user_repository import UserRepository, UserConfigRepository

from .report_repository import ReportRepository
from .conversation_repository import ConversationRepository, ChatMessageRepository
from .notification_repository import NotificationRepository
from .config_repository import SystemConfigRepository, ConfigRepository
from .cache_repository import CacheRepository
from .system_repository import SystemRepository
from .watchlist_repository import WatchlistRepository
from .scheduled_task_repository import ScheduledTaskRepository

# Database session factory for repositories
from ..database.database import SessionLocal

__all__ = [
    # Base
    "BaseRepository",
    "SessionLocal",
    
    # Domain repositories
    "UserRepository", 
    "UserConfigRepository",

    "ReportRepository",
    "ConversationRepository",
    "ChatMessageRepository",
    "NotificationRepository",
    "SystemConfigRepository",
    "ConfigRepository",
    "CacheRepository",
    "SystemRepository",
    "WatchlistRepository",
    "ScheduledTaskRepository",
]
