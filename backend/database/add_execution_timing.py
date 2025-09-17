"""
Add execution timing fields to Analysis and Report models.
This migration adds fields to track analysis execution duration.
"""

import sqlite3
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

def add_execution_timing_fields():
    """Add execution timing fields to analyses and reports tables."""
    
    # Get database path
    db_path = Path(__file__).parent.parent.parent / "data" / "tradingagents.db"
    
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Starting execution timing fields migration...")
        
        # Add fields to analyses table
        try:
            cursor.execute("ALTER TABLE analyses ADD COLUMN started_at TIMESTAMP")
            logger.info("Added started_at to analyses table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("started_at field already exists in analyses table")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE analyses ADD COLUMN completed_at TIMESTAMP")
            logger.info("Added completed_at to analyses table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("completed_at field already exists in analyses table")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE analyses ADD COLUMN execution_duration_seconds REAL")
            logger.info("Added execution_duration_seconds to analyses table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("execution_duration_seconds field already exists in analyses table")
            else:
                raise
        
        # Add fields to reports table
        try:
            cursor.execute("ALTER TABLE reports ADD COLUMN analysis_started_at TIMESTAMP")
            logger.info("Added analysis_started_at to reports table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("analysis_started_at field already exists in reports table")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE reports ADD COLUMN analysis_completed_at TIMESTAMP")
            logger.info("Added analysis_completed_at to reports table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("analysis_completed_at field already exists in reports table")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE reports ADD COLUMN analysis_duration_seconds REAL")
            logger.info("Added analysis_duration_seconds to reports table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("analysis_duration_seconds field already exists in reports table")
            else:
                raise
        
        # Commit changes
        conn.commit()
        logger.info("Migration completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if conn:
            conn.rollback()
        return False
    
    finally:
        if conn:
            conn.close()

def main():
    """Run the migration."""
    logging.basicConfig(level=logging.INFO)
    
    print("Adding execution timing fields to database...")
    success = add_execution_timing_fields()
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
