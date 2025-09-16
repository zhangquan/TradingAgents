#!/usr/bin/env python3
"""
Migration script to add session_id field to reports table
to link reports with conversation memory sessions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

def add_session_id_to_reports():
    """Add session_id column to reports table."""
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/tradingagents.db")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔄 Adding session_id column to reports table...")
        
        # Check if column already exists
        result = session.execute(text("PRAGMA table_info(reports)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'session_id' in columns:
            print("✅ session_id column already exists in reports table")
            return
        
        # Add session_id column
        session.execute(text("""
            ALTER TABLE reports 
            ADD COLUMN session_id VARCHAR(255)
        """))
        
        # Create index for session_id for better query performance
        session.execute(text("""
            CREATE INDEX idx_reports_session_id ON reports(session_id)
        """))
        
        session.commit()
        print("✅ Successfully added session_id column to reports table")
        
        # Verify the addition
        result = session.execute(text("PRAGMA table_info(reports)"))
        columns = [row[1] for row in result.fetchall()]
        if 'session_id' in columns:
            print("✅ Verification successful: session_id column added")
        else:
            print("❌ Verification failed: session_id column not found")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding session_id to reports table: {e}")
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    add_session_id_to_reports()
