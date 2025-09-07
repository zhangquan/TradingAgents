"""
Database migration script to add the new reports table.
This script creates the reports table and migrates existing report data 
from the analyses.reports JSON field to the new reports table.
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

def create_reports_table(db_path: str = "data/tradingagents.db"):
    """Create the reports table if it doesn't exist."""
    
    # Convert to absolute path
    if not Path(db_path).is_absolute():
        db_path = Path(__file__).parent.parent.parent / db_path
    
    logger.info(f"Creating reports table in database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='reports'
        """)
        
        if cursor.fetchone():
            logger.info("Reports table already exists, skipping creation")
            return True
        
        # Create reports table
        cursor.execute("""
            CREATE TABLE reports (
                id VARCHAR(36) PRIMARY KEY,
                report_id VARCHAR(255) UNIQUE NOT NULL,
                analysis_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(100) NOT NULL,
                ticker VARCHAR(20) NOT NULL,
                report_type VARCHAR(100) NOT NULL,
                title VARCHAR(500),
                content JSON NOT NULL,
                status VARCHAR(50) DEFAULT 'generated',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses (analysis_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create indexes
        indexes = [
            "CREATE INDEX idx_reports_analysis_type ON reports(analysis_id, report_type)",
            "CREATE INDEX idx_reports_user_type ON reports(user_id, report_type)",
            "CREATE INDEX idx_reports_analysis_created ON reports(analysis_id, created_at)",
            "CREATE INDEX idx_reports_ticker_type ON reports(ticker, report_type)",
            "CREATE INDEX idx_reports_user_ticker ON reports(user_id, ticker)",
            "CREATE INDEX idx_reports_ticker_created ON reports(ticker, created_at)",
            "CREATE INDEX idx_reports_report_id ON reports(report_id)",
            "CREATE INDEX idx_reports_user_id ON reports(user_id)",
            "CREATE INDEX idx_reports_ticker ON reports(ticker)",
            "CREATE INDEX idx_reports_status ON reports(status)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
        
        conn.commit()
        logger.info("Reports table created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating reports table: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_existing_reports(db_path: str = "data/tradingagents.db"):
    """Migrate existing report data from analyses.reports JSON field to the new reports table."""
    
    # Convert to absolute path
    if not Path(db_path).is_absolute():
        db_path = Path(__file__).parent.parent.parent / db_path
    
    logger.info(f"Migrating existing reports from analyses table")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all analyses with reports
        cursor.execute("""
            SELECT analysis_id, user_id, ticker, reports, created_at 
            FROM analyses 
            WHERE reports IS NOT NULL AND reports != 'null' AND reports != '{}'
        """)
        
        analyses_with_reports = cursor.fetchall()
        logger.info(f"Found {len(analyses_with_reports)} analyses with reports to migrate")
        
        migrated_count = 0
        
        for analysis_id, user_id, ticker, reports_json, created_at in analyses_with_reports:
            try:
                # Parse the reports JSON
                if isinstance(reports_json, str):
                    reports = json.loads(reports_json)
                else:
                    reports = reports_json
                
                if not isinstance(reports, dict):
                    logger.warning(f"Skipping analysis {analysis_id}: reports is not a dict")
                    continue
                
                # Create individual report records
                for report_type, report_content in reports.items():
                    if not report_content:
                        continue
                    
                    # Generate report ID with ticker
                    report_id = f"report_{ticker}_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                    
                    # Create title from ticker and report type
                    title = f"{ticker.upper()} {report_type.replace('_', ' ').title()} Report"
                    
                    # Insert report record
                    cursor.execute("""
                        INSERT INTO reports (
                            id, report_id, analysis_id, user_id, ticker, report_type, 
                            title, content, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        report_id,
                        analysis_id,
                        user_id,
                        ticker.upper(),
                        report_type,
                        title,
                        json.dumps(report_content),
                        'generated',
                        created_at,
                        created_at
                    ))
                    
                    migrated_count += 1
                    logger.debug(f"Migrated report {report_type} for analysis {analysis_id}")
                
            except Exception as e:
                logger.error(f"Error migrating reports for analysis {analysis_id}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Successfully migrated {migrated_count} reports")
        return migrated_count
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def remove_reports_from_analyses(db_path: str = "data/tradingagents.db"):
    """Remove the reports column from the analyses table after successful migration."""
    
    # Convert to absolute path
    if not Path(db_path).is_absolute():
        db_path = Path(__file__).parent.parent.parent / db_path
    
    logger.info("Removing reports column from analyses table")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support dropping columns directly, so we need to recreate the table
        # First, check if reports column exists
        cursor.execute("PRAGMA table_info(analyses)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'reports' not in columns:
            logger.info("Reports column doesn't exist in analyses table")
            return True
        
        # Create new table without reports column
        cursor.execute("""
            CREATE TABLE analyses_new (
                id VARCHAR(36) PRIMARY KEY,
                analysis_id VARCHAR(255) UNIQUE NOT NULL,
                user_id VARCHAR(100) NOT NULL,
                ticker VARCHAR(20) NOT NULL,
                analysts JSON,
                research_depth INTEGER DEFAULT 1,
                llm_provider VARCHAR(50),
                model_config JSON,
                final_state JSON,
                status VARCHAR(50) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                analysis_date VARCHAR(20),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Copy data from old table (excluding reports column)
        cursor.execute("""
            INSERT INTO analyses_new (
                id, analysis_id, user_id, ticker, analysts, research_depth,
                llm_provider, model_config, final_state, status, 
                created_at, updated_at, analysis_date
            )
            SELECT 
                id, analysis_id, user_id, ticker, analysts, research_depth,
                llm_provider, model_config, final_state, status,
                created_at, updated_at, analysis_date
            FROM analyses
        """)
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE analyses")
        cursor.execute("ALTER TABLE analyses_new RENAME TO analyses")
        
        # Recreate indexes
        indexes = [
            "CREATE INDEX idx_analyses_user_ticker ON analyses(user_id, ticker)",
            "CREATE INDEX idx_analyses_user_date ON analyses(user_id, analysis_date)",
            "CREATE INDEX idx_analyses_ticker_date ON analyses(ticker, analysis_date)",
            "CREATE INDEX idx_analyses_analysis_id ON analyses(analysis_id)",
            "CREATE INDEX idx_analyses_user_id ON analyses(user_id)",
            "CREATE INDEX idx_analyses_status ON analyses(status)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.Error as e:
                logger.warning(f"Error creating index: {e}")
        
        conn.commit()
        logger.info("Successfully removed reports column from analyses table")
        return True
        
    except Exception as e:
        logger.error(f"Error removing reports column: {e}")
        conn.rollback()
        return False
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
        # Check if reports table exists and has data
        cursor.execute("SELECT COUNT(*) FROM reports")
        reports_count = cursor.fetchone()[0]
        
        # Check if analyses table no longer has reports column
        cursor.execute("PRAGMA table_info(analyses)")
        analyses_columns = [row[1] for row in cursor.fetchall()]
        
        # Check if reports table has required columns
        cursor.execute("PRAGMA table_info(reports)")
        reports_columns = [row[1] for row in cursor.fetchall()]
        
        required_reports_columns = [
            'id', 'report_id', 'analysis_id', 'user_id', 'ticker', 'report_type',
            'title', 'content', 'status', 'created_at', 'updated_at'
        ]
        
        missing_columns = [col for col in required_reports_columns if col not in reports_columns]
        
        success = True
        if missing_columns:
            logger.error(f"Missing columns in reports table: {missing_columns}")
            success = False
        
        if 'reports' in analyses_columns:
            logger.warning("Reports column still exists in analyses table")
            # Don't fail verification for this, as it might be intentional
        
        logger.info(f"Migration verification: {reports_count} reports in new table")
        logger.info(f"Reports table columns: {reports_columns}")
        logger.info(f"Analyses table columns: {analyses_columns}")
        
        return success
        
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False
    finally:
        conn.close()

def run_migration(db_path: str = "data/tradingagents.db", remove_old_column: bool = False):
    """Run the complete migration process."""
    
    logger.info("Starting reports table migration")
    
    # Step 1: Create reports table
    if not create_reports_table(db_path):
        logger.error("Failed to create reports table")
        return False
    
    # Step 2: Migrate existing data
    migrated_count = migrate_existing_reports(db_path)
    if migrated_count == 0:
        logger.warning("No reports were migrated (this might be normal if no reports exist)")
    
    # Step 3: Optionally remove reports column from analyses table
    if remove_old_column:
        if not remove_reports_from_analyses(db_path):
            logger.error("Failed to remove reports column from analyses table")
            return False
    else:
        logger.info("Keeping reports column in analyses table (use --remove-old-column to remove)")
    
    # Step 4: Verify migration
    if verify_migration(db_path):
        logger.info("Migration completed successfully")
        return True
    else:
        logger.error("Migration verification failed")
        return False

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Migrate reports to separate table")
    parser.add_argument("--db-path", default="data/tradingagents.db", help="Database path")
    parser.add_argument("--remove-old-column", action="store_true", 
                       help="Remove reports column from analyses table after migration")
    
    args = parser.parse_args()
    
    # Run migration
    success = run_migration(args.db_path, args.remove_old_column)
    exit(0 if success else 1)
