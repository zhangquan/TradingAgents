"""
Database migration script to create the watchlist table and migrate existing
watchlist data from user_configs JSON field to the new dedicated table.
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

def create_watchlist_table(db_path: str = "data/tradingagents.db"):
    """Create the watchlist table if it doesn't exist."""
    
    # Convert to absolute path
    if not Path(db_path).is_absolute():
        db_path = Path(__file__).parent.parent.parent / db_path
    
    logger.info(f"Creating watchlist table in database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='watchlist'
        """)
        
        if cursor.fetchone():
            logger.info("Watchlist table already exists, skipping creation")
            return True
        
        # Create watchlist table
        cursor.execute("""
            CREATE TABLE watchlist (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                ticker VARCHAR(20) NOT NULL,
                added_date VARCHAR(20),
                notes VARCHAR(1000),
                priority INTEGER DEFAULT 1,
                alerts_enabled BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create indexes
        indexes = [
            "CREATE INDEX idx_watchlist_user_id ON watchlist(user_id)",
            "CREATE INDEX idx_watchlist_ticker ON watchlist(ticker)",
            "CREATE INDEX idx_watchlist_user_ticker ON watchlist(user_id, ticker)",
            "CREATE INDEX idx_watchlist_user_priority ON watchlist(user_id, priority)",
            "CREATE INDEX idx_watchlist_ticker_alerts ON watchlist(ticker, alerts_enabled)",
            "CREATE UNIQUE INDEX idx_watchlist_unique_user_ticker ON watchlist(user_id, ticker)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
        
        conn.commit()
        logger.info("Watchlist table created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating watchlist table: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_existing_watchlists(db_path: str = "data/tradingagents.db"):
    """Migrate existing watchlist data from user_configs.config_data to the new watchlist table."""
    
    # Convert to absolute path
    if not Path(db_path).is_absolute():
        db_path = Path(__file__).parent.parent.parent / db_path
    
    logger.info(f"Migrating existing watchlists from user_configs table")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all user configs that contain watchlist data
        cursor.execute("""
            SELECT user_id, config_data 
            FROM user_configs 
            WHERE config_data IS NOT NULL AND config_data != 'null' AND config_data != '{}'
        """)
        
        user_configs = cursor.fetchall()
        logger.info(f"Found {len(user_configs)} user configs to check for watchlists")
        
        migrated_count = 0
        total_stocks = 0
        
        for user_id, config_json in user_configs:
            try:
                # Parse the config JSON
                if isinstance(config_json, str):
                    config_data = json.loads(config_json)
                else:
                    config_data = config_json
                
                if not isinstance(config_data, dict):
                    logger.warning(f"Skipping user {user_id}: config_data is not a dict")
                    continue
                
                # Check if watchlist exists in config
                watchlist = config_data.get("watchlist", [])
                if not watchlist or not isinstance(watchlist, list):
                    logger.debug(f"No watchlist found for user {user_id}")
                    continue
                
                logger.info(f"Migrating watchlist for user {user_id} with {len(watchlist)} stocks")
                
                # Migrate each stock in the watchlist
                for i, ticker in enumerate(watchlist):
                    if not ticker or not isinstance(ticker, str):
                        logger.warning(f"Skipping invalid ticker for user {user_id}: {ticker}")
                        continue
                    
                    ticker = ticker.upper().strip()
                    if not ticker:
                        continue
                    
                    # Check if already exists (avoid duplicates)
                    cursor.execute("""
                        SELECT id FROM watchlist 
                        WHERE user_id = ? AND ticker = ?
                    """, (user_id, ticker))
                    
                    if cursor.fetchone():
                        logger.debug(f"Stock {ticker} already exists for user {user_id}, skipping")
                        continue
                    
                    # Insert watchlist item
                    cursor.execute("""
                        INSERT INTO watchlist (
                            id, user_id, ticker, added_date, notes, priority, 
                            alerts_enabled, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        user_id,
                        ticker,
                        datetime.now().strftime('%Y-%m-%d'),
                        f"Migrated from user config on {datetime.now().strftime('%Y-%m-%d')}",
                        1,  # Default priority
                        True,  # Default alerts enabled
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    
                    total_stocks += 1
                    logger.debug(f"Migrated stock {ticker} for user {user_id}")
                
                migrated_count += 1
                logger.info(f"Successfully migrated watchlist for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error migrating watchlist for user {user_id}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Successfully migrated {total_stocks} stocks for {migrated_count} users")
        return total_stocks
        
    except Exception as e:
        logger.error(f"Error during watchlist migration: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def cleanup_old_watchlist_data(db_path: str = "data/tradingagents.db"):
    """Remove watchlist data from user_configs after successful migration."""
    
    # Convert to absolute path
    if not Path(db_path).is_absolute():
        db_path = Path(__file__).parent.parent.parent / db_path
    
    logger.info("Cleaning up old watchlist data from user_configs")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all user configs
        cursor.execute("SELECT user_id, config_data FROM user_configs")
        user_configs = cursor.fetchall()
        
        updated_count = 0
        
        for user_id, config_json in user_configs:
            try:
                if not config_json or config_json in ('null', '{}'):
                    continue
                
                # Parse the config JSON
                if isinstance(config_json, str):
                    config_data = json.loads(config_json)
                else:
                    config_data = config_json
                
                if not isinstance(config_data, dict):
                    continue
                
                # Remove watchlist if it exists
                if "watchlist" in config_data:
                    del config_data["watchlist"]
                    
                    # Update the user config
                    cursor.execute("""
                        UPDATE user_configs 
                        SET config_data = ? 
                        WHERE user_id = ?
                    """, (json.dumps(config_data), user_id))
                    
                    updated_count += 1
                    logger.debug(f"Removed watchlist from config for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error cleaning up config for user {user_id}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Cleaned up watchlist data from {updated_count} user configs")
        return updated_count
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        conn.rollback()
        return 0
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
        # Check if watchlist table exists and has data
        cursor.execute("SELECT COUNT(*) FROM watchlist")
        watchlist_count = cursor.fetchone()[0]
        
        # Check if watchlist table has required columns
        cursor.execute("PRAGMA table_info(watchlist)")
        watchlist_columns = [row[1] for row in cursor.fetchall()]
        
        required_watchlist_columns = [
            'id', 'user_id', 'ticker', 'added_date', 'notes', 'priority',
            'alerts_enabled', 'created_at', 'updated_at'
        ]
        
        missing_columns = [col for col in required_watchlist_columns if col not in watchlist_columns]
        
        # Check how many users have watchlist items
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM watchlist")
        users_with_watchlist = cursor.fetchone()[0]
        
        success = True
        if missing_columns:
            logger.error(f"Missing columns in watchlist table: {missing_columns}")
            success = False
        
        logger.info(f"Migration verification:")
        logger.info(f"  - Watchlist table exists: Yes")
        logger.info(f"  - Total watchlist items: {watchlist_count}")
        logger.info(f"  - Users with watchlist: {users_with_watchlist}")
        logger.info(f"  - All required columns present: {len(missing_columns) == 0}")
        
        return success
        
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False
    finally:
        conn.close()

def run_migration(db_path: str = "data/tradingagents.db", cleanup_old_data: bool = False):
    """Run the complete watchlist migration process."""
    
    logger.info("Starting watchlist table migration")
    
    # Step 1: Create watchlist table
    if not create_watchlist_table(db_path):
        logger.error("Failed to create watchlist table")
        return False
    
    # Step 2: Migrate existing data
    migrated_count = migrate_existing_watchlists(db_path)
    if migrated_count == 0:
        logger.warning("No watchlist items were migrated (this might be normal if no watchlists exist)")
    
    # Step 3: Optionally clean up old data
    if cleanup_old_data:
        cleaned_count = cleanup_old_watchlist_data(db_path)
        logger.info(f"Cleaned up {cleaned_count} user configs")
    else:
        logger.info("Keeping watchlist data in user_configs (use --cleanup-old-data to remove)")
    
    # Step 4: Verify migration
    if verify_migration(db_path):
        logger.info("Watchlist migration completed successfully")
        return True
    else:
        logger.error("Migration verification failed")
        return False

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Migrate watchlist to separate table")
    parser.add_argument("--db-path", default="data/tradingagents.db", help="Database path")
    parser.add_argument("--cleanup-old-data", action="store_true", 
                       help="Remove watchlist data from user_configs after migration")
    
    args = parser.parse_args()
    
    # Run migration
    success = run_migration(args.db_path, args.cleanup_old_data)
    exit(0 if success else 1)
