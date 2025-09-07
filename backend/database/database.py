"""
Database configuration and connection management for TradingAgents.
Uses SQLAlchemy 2.0+ with async support.
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/tradingagents.db")

# Create SQLite engine with optimizations
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,  # Allow multiple threads
            "timeout": 30,  # Connection timeout
        },
        echo=False,  # Set to True for SQL debugging
        future=True,  # Use SQLAlchemy 2.0 style
    )
    
    # Enable WAL mode and other optimizations for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Set synchronous mode for better performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Increase cache size (in KB)
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Set busy timeout
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds
        cursor.close()
        
else:
    # Non-SQLite databases (PostgreSQL, MySQL, etc.)
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Create sessionmaker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Create declarative base
Base = declarative_base()

def get_db():
    """
    Dependency for FastAPI to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """
    Initialize database and create all tables.
    """
    try:
        # Ensure data directory exists
        db_path = DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Import all models to ensure they're registered
        from . import models
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def create_tables():
    """
    Create all database tables.
    """
    try:
        from . import models
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

def drop_tables():
    """
    Drop all database tables. Use with caution!
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
        return True
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        return False
