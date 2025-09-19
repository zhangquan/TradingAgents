"""
Database initialization script for TradingAgents.
Creates tables and sets up initial data.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.database import init_database, engine
from backend.database.models import User, UserConfig
from backend.repositories import UserRepository, UserConfigRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_default_user():
    """Create default demo_user if it doesn't exist."""
    try:
        user_repo = UserRepository()
        user_config_repo = UserConfigRepository()
        
        # Check if demo_user exists
        user = user_repo.get_user_by_user_id("demo_user")
        if user:
            logger.info("Demo user already exists")
            return True
        
        # Create demo user
        user_data = {
            "email": "demo@tradingagents.com",
            "name": "Demo User",
            "status": "active"
        }
        
        success = user_repo.create_user("demo_user", user_data)
        if success:
            logger.info("Created demo user")
            
            # Create default user config
            default_config = {
                "llm_provider": "aliyun",
                "backend_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "shallow_thinker": "qwen-plus",
                "deep_thinker": "qwen-plus",
                "default_research_depth": 1,
                "default_analysts": ["market"],
                "watchlist": ["AAPL", "TSLA"],
                "user_id": "demo_user"
            }
            
            user_config_repo.save_user_config("demo_user", default_config)
            logger.info("Created default user config")
            
            return True
        else:
            logger.error("Failed to create demo user")
            return False
            
    except Exception as e:
        logger.error(f"Error creating default user: {e}")
        return False


def migrate_existing_data():
    """Migrate existing file-based data to database (optional)."""
    try:
        # Migration is no longer needed as we use Repository pattern
        logger.info("Migration from LocalStorage to Repository pattern is complete - skipping.")
        return
        
        logger.info("Starting data migration from files to database...")
        
        # Migrate user configs
        user_config = old_storage.get_user_config("demo_user")
        if user_config:
            new_storage.save_user_config("demo_user", user_config)
            logger.info("Migrated user config")
        
        # Migrate analyses
        analyses = old_storage.list_analysis("demo_user", limit=1000)
        migrated_count = 0
        for analysis in analyses:
            try:
                new_storage.save_analysis(
                    user_id=analysis["user_id"],
                    ticker=analysis["ticker"],
                    analysis_data=analysis
                )
                migrated_count += 1
            except Exception as e:
                logger.warning(f"Failed to migrate analysis {analysis.get('analysis_id')}: {e}")
        
        logger.info(f"Migrated {migrated_count} analyses")
        
        # Migrate notifications
        notifications = old_storage.get_notifications("demo_user", limit=1000)
        migrated_notif_count = 0
        for notif in notifications:
            try:
                new_storage.save_notification("demo_user", notif)
                migrated_notif_count += 1
            except Exception as e:
                logger.warning(f"Failed to migrate notification {notif.get('notification_id')}: {e}")
        
        logger.info(f"Migrated {migrated_notif_count} notifications")
        
        # Migrate scheduled tasks
        scheduled_tasks = old_storage.load_scheduled_tasks()
        for task_id, task_data in scheduled_tasks.items():
            try:
                # Add user_id if not present
                if "user_id" not in task_data:
                    task_data["user_id"] = "demo_user"
                new_storage.save_single_scheduled_task(task_id, task_data)
            except Exception as e:
                logger.warning(f"Failed to migrate scheduled task {task_id}: {e}")
        
        logger.info(f"Migrated {len(scheduled_tasks)} scheduled tasks")
        
        logger.info("Data migration completed")
        return True
        
    except Exception as e:
        logger.error(f"Error during data migration: {e}")
        return False


def main():
    """Main initialization function."""
    try:
        logger.info("Initializing TradingAgents database...")
        
        # Initialize database and create tables
        success = init_database()
        if not success:
            logger.error("Failed to initialize database")
            return False
        
        logger.info("Database initialized successfully")
        
        # Create default user
        create_default_user()
        
        # Optionally migrate existing data
        data_dir = Path("data")
        if data_dir.exists() and any(data_dir.iterdir()):
            response = input("Existing data directory found. Migrate data to database? (y/n): ")
            if response.lower() == 'y':
                migrate_existing_data()
        
        logger.info("Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
