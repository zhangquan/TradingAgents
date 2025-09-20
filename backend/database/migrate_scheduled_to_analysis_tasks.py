#!/usr/bin/env python3
"""
Database migration script: Rename scheduled_tasks table to analysis_tasks

This script renames the table from 'scheduled_tasks' to 'analysis_tasks' to better
reflect the purpose of the table and align with the new naming convention.

Run this script to migrate your database:
    python backend/database/migrate_scheduled_to_analysis_tasks.py
"""

import sqlite3
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_path():
    """Get the path to the database file."""
    # Try to find the database in common locations
    possible_paths = [
        "data/tradingagents.db",
        "../data/tradingagents.db",
        "../../data/tradingagents.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If not found, create in data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return "data/tradingagents.db"

def check_table_exists(cursor, table_name):
    """Check if a table exists in the database."""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def migrate_table_name(db_path):
    """Migrate the table name from scheduled_tasks to analysis_tasks."""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if scheduled_tasks table exists
        if not check_table_exists(cursor, 'scheduled_tasks'):
            logger.info("Table 'scheduled_tasks' does not exist. Migration not needed.")
            conn.close()
            return True
        
        # Check if analysis_tasks table already exists
        if check_table_exists(cursor, 'analysis_tasks'):
            logger.warning("Table 'analysis_tasks' already exists. Skipping migration.")
            conn.close()
            return True
        
        logger.info("Starting migration: Renaming 'scheduled_tasks' to 'analysis_tasks'")
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Rename the table
        cursor.execute("ALTER TABLE scheduled_tasks RENAME TO analysis_tasks")
        
        # Update any foreign key references in other tables
        # Check if other tables reference scheduled_tasks
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND sql LIKE '%scheduled_tasks%'
        """)
        
        references = cursor.fetchall()
        if references:
            logger.info("Found tables with foreign key references to scheduled_tasks:")
            for ref in references:
                logger.info(f"  {ref[0]}")
            logger.warning("Manual update may be required for foreign key constraints")
        
        # Update indexes if they exist
        cursor.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='index' AND tbl_name='analysis_tasks'
        """)
        
        indexes = cursor.fetchall()
        for index_name, index_sql in indexes:
            if 'scheduled_tasks' in str(index_sql):
                logger.info(f"Updating index: {index_name}")
                # Drop and recreate index with new table name
                new_sql = str(index_sql).replace('scheduled_tasks', 'analysis_tasks')
                cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                cursor.execute(new_sql)
        
        # Commit transaction
        conn.commit()
        
        # Verify the migration
        if check_table_exists(cursor, 'analysis_tasks'):
            logger.info("✅ Migration successful: 'analysis_tasks' table created")
            
            # Count records to verify data integrity
            cursor.execute("SELECT COUNT(*) FROM analysis_tasks")
            count = cursor.fetchone()[0]
            logger.info(f"✅ Data integrity verified: {count} records in analysis_tasks table")
            
        else:
            logger.error("❌ Migration failed: 'analysis_tasks' table not found")
            conn.rollback()
            conn.close()
            return False
        
        # Close connection
        conn.close()
        
        logger.info("🎉 Migration completed successfully!")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def create_backup(db_path):
    """Create a backup of the database before migration."""
    import shutil
    from datetime import datetime
    
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ Database backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return None

def main():
    """Main migration function."""
    logger.info("🚀 Starting database migration: scheduled_tasks → analysis_tasks")
    
    # Get database path
    db_path = get_database_path()
    logger.info(f"Database path: {db_path}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    # Create backup
    backup_path = create_backup(db_path)
    if not backup_path:
        logger.error("Failed to create backup. Aborting migration.")
        return False
    
    # Perform migration
    success = migrate_table_name(db_path)
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        logger.info(f"Backup available at: {backup_path}")
    else:
        logger.error("❌ Migration failed. Database backup available at: {backup_path}")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
