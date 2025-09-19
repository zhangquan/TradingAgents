"""
Add execution_type field to analyses and scheduled_tasks tables
"""

import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_execution_type_fields():
    """Add execution_type field to conversation_states table."""
    
    # Database path
    db_path = Path(__file__).parent.parent.parent / "data" / "tradingagents.db"
    
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Add execution_type to conversation_states table
        try:
            cursor.execute("""
                ALTER TABLE conversation_states 
                ADD COLUMN execution_type VARCHAR(20) DEFAULT 'manual'
            """)
            logger.info("Added execution_type column to conversation_states table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("execution_type column already exists in conversation_states table")
            else:
                raise e
        
        # Create index for the new column
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_states_execution_type 
                ON conversation_states(execution_type)
            """)
            logger.info("Created index for conversation_states.execution_type")
        except sqlite3.OperationalError as e:
            logger.warning(f"Could not create index for conversation_states.execution_type: {e}")
        
        # Update existing records
        # Set all existing conversation states to 'manual' by default
        cursor.execute("""
            UPDATE conversation_states 
            SET execution_type = 'manual' 
            WHERE execution_type IS NULL OR execution_type = ''
        """)
        
        # Set scheduled conversation states to 'scheduled' if they have a corresponding task_id
        cursor.execute("""
            UPDATE conversation_states 
            SET execution_type = 'scheduled' 
            WHERE task_id IS NOT NULL AND task_id != ''
        """)
        
        conn.commit()
        logger.info("Successfully added execution_type field and updated existing records")
        return True
        
    except Exception as e:
        logger.error(f"Error adding execution_type field: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = add_execution_type_fields()
    if success:
        print("Migration completed successfully")
    else:
        print("Migration failed")
