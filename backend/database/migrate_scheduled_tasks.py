"""
Database migration script to add new fields to ScheduledTask table.
This script updates the existing scheduled_tasks table to support both
scheduled and immediate task execution.
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def migrate_scheduled_tasks_table(db_path: str = "data/tradingagents.db"):
    """Migrate the scheduled_tasks table to add new fields for unified task management."""
    
    # Convert to absolute path
    if not Path(db_path).is_absolute():
        db_path = Path(__file__).parent.parent.parent / db_path
    
    logger.info(f"Migrating database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scheduled_tasks'
        """)
        
        if not cursor.fetchone():
            logger.info("scheduled_tasks table does not exist, creating...")
            # If table doesn't exist, it will be created by SQLAlchemy with all fields
            return
        
        # Get current table schema
        cursor.execute("PRAGMA table_info(scheduled_tasks)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        logger.info(f"Current columns: {list(columns.keys())}")
        
        # Define new columns to add
        new_columns = {
            'analysis_date': 'VARCHAR(20)',  # YYYY-MM-DD format
            'status': 'VARCHAR(50) DEFAULT "created"',  # Task status
            'progress': 'INTEGER DEFAULT 0',  # 0-100
            'current_step': 'VARCHAR(100)',  # Current analysis step
            'analysis_id': 'VARCHAR(255)',  # FK to analyses table
            'result_data': 'JSON',  # Task execution results
            'error_message': 'TEXT',  # Error message if failed
            'trace': 'JSON',  # Step execution trace
            'started_at': 'DATETIME',  # When task started
            'completed_at': 'DATETIME'  # When task completed
        }
        
        # Add missing columns
        added_columns = []
        for column_name, column_type in new_columns.items():
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE scheduled_tasks ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    logger.info(f"Added column: {column_name}")
                except sqlite3.Error as e:
                    logger.error(f"Error adding column {column_name}: {e}")
        
        # Update schedule_type column to allow 'immediate' as default
        if 'schedule_type' in columns:
            try:
                # Check if there are any NULL values and update them
                cursor.execute("""
                    UPDATE scheduled_tasks 
                    SET schedule_type = 'immediate' 
                    WHERE schedule_type IS NULL
                """)
                logger.info("Updated NULL schedule_type values to 'immediate'")
            except sqlite3.Error as e:
                logger.error(f"Error updating schedule_type: {e}")
        
        # Update enabled column default if needed
        if 'enabled' in columns:
            try:
                cursor.execute("""
                    UPDATE scheduled_tasks 
                    SET enabled = 1 
                    WHERE enabled IS NULL
                """)
                logger.info("Updated NULL enabled values to 1")
            except sqlite3.Error as e:
                logger.error(f"Error updating enabled values: {e}")
        
        # Make schedule_time and schedule_date optional for immediate tasks
        try:
            cursor.execute("""
                UPDATE scheduled_tasks 
                SET schedule_time = NULL 
                WHERE schedule_type = 'immediate' AND schedule_time = ''
            """)
            logger.info("Updated empty schedule_time for immediate tasks")
        except sqlite3.Error as e:
            logger.error(f"Error updating schedule_time: {e}")
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_user_status ON scheduled_tasks(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_ticker_date ON scheduled_tasks(ticker, analysis_date)",
            "CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_status_type ON scheduled_tasks(status, schedule_type)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except sqlite3.Error as e:
                logger.error(f"Error creating index: {e}")
        
        conn.commit()
        logger.info(f"Migration completed successfully. Added {len(added_columns)} columns.")
        
        if added_columns:
            logger.info(f"New columns added: {', '.join(added_columns)}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def verify_migration(db_path: str = "data/tradingagents.db"):
    """Verify that the migration was successful."""
    
    # Convert to absolute path
    if not Path(db_path).is_absolute():
        db_path = Path(__file__).parent.parent.parent / db_path
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check table schema
        cursor.execute("PRAGMA table_info(scheduled_tasks)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        required_columns = [
            'id', 'task_id', 'user_id', 'ticker', 'analysis_date', 'analysts', 
            'research_depth', 'schedule_type', 'schedule_time', 'schedule_date', 
            'cron_expression', 'timezone', 'status', 'enabled', 'progress', 
            'current_step', 'analysis_id', 'result_data', 'error_message', 
            'trace', 'last_run', 'execution_count', 'last_error', 'created_at', 
            'started_at', 'completed_at', 'updated_at'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            logger.error(f"Migration verification failed. Missing columns: {missing_columns}")
            return False
        else:
            logger.info("Migration verification successful. All required columns present.")
            return True
            
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run migration
    migrate_scheduled_tasks_table()
    
    # Verify migration
    verify_migration()
