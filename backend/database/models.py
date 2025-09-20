"""
SQLAlchemy ORM models for TradingAgents database.
Defines all database tables and relationships.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid


class User(Base):
    """User model for user management."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255))
    name = Column(String(255))
    status = Column(String(50), default="active")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    reports = relationship("Report", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    user_configs = relationship("UserConfig", back_populates="user", cascade="all, delete-orphan")
    analysis_tasks = relationship("AnalysisTask", back_populates="user", cascade="all, delete-orphan")
    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}')>"


class Report(Base):
    """Report model for storing complete analysis reports with multiple sections."""
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(255), unique=True, nullable=False, index=True)
    # analysis_id = Column(String(255), ForeignKey("analyses.analysis_id"), nullable=False, index=True)  # Removed - Analysis model deprecated
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Stock information for direct querying
    ticker = Column(String(20), nullable=False, index=True)  # Stock ticker symbol
    
    # Report metadata
    title = Column(String(500))
    
    # Complete report content with all sections
    # Expected structure: {
    #   "market_report": "...",
    #   "investment_plan": "...", 
    #   "final_trade_decision": "..."
    # }
    sections = Column(JSON, nullable=False)  # All report sections in one JSON field
    
    # Conversation memory link
    session_id = Column(String(255), nullable=True, index=True)  # Link to conversation session
    
    # Analysis execution metrics
    analysis_started_at = Column(DateTime(timezone=True))
    analysis_completed_at = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(50), default="generated", index=True)  # generated, reviewed, archived
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # analysis = relationship("Analysis", back_populates="reports")  # Removed - Analysis model deprecated
    user = relationship("User", overlaps="reports")
    
    # Indexes for common queries
    __table_args__ = (
        # Index('idx_analysis_id', 'analysis_id'),  # Removed - analysis_id field deprecated
        Index('idx_user_ticker', 'user_id', 'ticker'),
        # Index('idx_analysis_created', 'analysis_id', 'created_at'),  # Removed - analysis_id field deprecated
        Index('idx_ticker_created', 'ticker', 'created_at'),
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_session_id', 'session_id'),
    )
    
    def __repr__(self):
        return f"<Report(report_id='{self.report_id}', ticker='{self.ticker}', sections={len(self.sections) if self.sections else 0})>"


class Notification(Base):
    """Notification model for user notifications."""
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Notification content
    title = Column(String(500), nullable=False)
    message = Column(Text)
    type = Column(String(50), default="info", index=True)  # info, warning, error, success
    data = Column(JSON)  # Additional data
    
    # Status
    read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_read', 'user_id', 'read'),
        Index('idx_user_type', 'user_id', 'type'),
    )
    
    def __repr__(self):
        return f"<Notification(notification_id='{self.notification_id}', title='{self.title}', read={self.read})>"


class SystemConfig(Base):
    """System configuration model."""
    __tablename__ = "system_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_name = Column(String(255), unique=True, nullable=False, index=True)
    config_data = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemConfig(config_name='{self.config_name}')>"


class UserConfig(Base):
    """User-specific configuration model."""
    __tablename__ = "user_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    config_data = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_configs")
    
    def __repr__(self):
        return f"<UserConfig(user_id='{self.user_id}')>"


class CacheEntry(Base):
    """Cache entry model for data caching."""
    __tablename__ = "cache_entries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_key = Column(String(500), unique=True, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    
    # TTL and expiration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    def __repr__(self):
        return f"<CacheEntry(cache_key='{self.cache_key}', expires_at='{self.expires_at}')>"


class SystemLog(Base):
    """System log model for event logging."""
    __tablename__ = "system_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_event_type_timestamp', 'event_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SystemLog(event_type='{self.event_type}', timestamp='{self.timestamp}')>"


class AnalysisTask(Base):
    """Task model for all analysis tasks - supports both scheduled execution and immediate execution."""
    __tablename__ = "analysis_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Task configuration
    ticker = Column(String(20), nullable=False, index=True)
    analysis_date = Column(String(20))  # YYYY-MM-DD format - for analysis execution
    analysts = Column(JSON)  # List of analysts
    research_depth = Column(Integer, default=1)
    
  
    schedule_type = Column(String(50), default="daily")  # once,  daily, weekly, monthly, cron
    schedule_time = Column(String(10))  # HH:MM format (optional for immediate tasks)
    schedule_date = Column(String(20))  # For 'once' type: YYYY-MM-DD (optional for immediate tasks)
    cron_expression = Column(String(100))  # For 'cron' type
    # timezone = Column(String(50), default="UTC")  # Removed - use UTC universally, convert in UI
    
    # Task execution status and lifecycle
    status = Column(String(50), default="created", index=True)  # created, running, completed, failed
    enabled = Column(Boolean, default=True, index=True)
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100))  # Current analysis step
    
    # Results and data
    # analysis_id = Column(String(255), ForeignKey("analyses.analysis_id"), index=True)  # Removed - Analysis model deprecated
    result_data = Column(JSON)  # Task execution results
    error_message = Column(Text)
    trace = Column(JSON)  # Step execution trace
    
    # Execution tracking
    last_run = Column(DateTime(timezone=True))
    execution_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analysis_tasks")
    # analysis = relationship("Analysis")  # Removed - Analysis model deprecated
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_enabled', 'user_id', 'enabled'),
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_schedule_type', 'schedule_type'),
        Index('idx_ticker_date', 'ticker', 'analysis_date'),
        Index('idx_status_type', 'status', 'schedule_type'),
    )
    
    def __repr__(self):
        return f"<AnalysisTask(task_id='{self.task_id}', ticker='{self.ticker}', status='{self.status}', type='{self.schedule_type}')>"


class Watchlist(Base):
    """Watchlist model for storing user's watched stocks."""
    __tablename__ = "watchlist"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    
    # Additional metadata
    added_date = Column(String(20))  # YYYY-MM-DD format when stock was added
    notes = Column(String(1000))  # Optional user notes about the stock
    priority = Column(Integer, default=1)  # Priority level (1=highest, 5=lowest)
    alerts_enabled = Column(Boolean, default=True)  # Whether to send alerts for this stock
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="watchlist_items")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_ticker', 'user_id', 'ticker'),
        Index('idx_user_priority', 'user_id', 'priority'),
        Index('idx_ticker_alerts', 'ticker', 'alerts_enabled'),
        # Unique constraint: one ticker per user
        Index('idx_unique_user_ticker', 'user_id', 'ticker', unique=True),
    )
    
    def __repr__(self):
        return f"<Watchlist(user_id='{self.user_id}', ticker='{self.ticker}', priority={self.priority})>"


class ConversationState(Base):
    """Conversation state model for storing chat sessions and analysis contexts."""
    __tablename__ = "conversation_states"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Analysis context
    ticker = Column(String(20), nullable=False, index=True)
    analysis_date = Column(String(20))  # YYYY-MM-DD format
    task_id = Column(String(255), index=True)  # Link to scheduled task
    # analysis_id = Column(String(255), ForeignKey("analyses.analysis_id"), index=True)  # Removed - Analysis model deprecated
    
    # Analysis configuration
    analysts = Column(JSON)  # List of analysts used
    research_depth = Column(Integer, default=1)
    llm_config = Column(JSON)
    
    # Agent state tracking
    agent_status = Column(JSON)  # Dict of agent -> status
    current_agent = Column(String(100))
    
    # Message and tool call history
    messages = Column(JSON)  # List of (timestamp, type, content) tuples
    tool_calls = Column(JSON)  # List of (timestamp, tool_name, args) tuples
    
    # Report sections
    report_sections = Column(JSON)  # Dict of section -> content
    current_report = Column(Text)
    final_report = Column(Text)
    
    # Complete trading graph state
    final_state = Column(JSON)  # Decision, confidence, reasoning
    processed_signal = Column(JSON)  # Any processed signal data
    
    # Session metadata
    execution_type = Column(String(20), default="manual", index=True)  # manual, scheduled
    last_interaction = Column(DateTime(timezone=True))
    is_finalized = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    # analysis = relationship("Analysis")  # Removed - Analysis model deprecated
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_ticker', 'user_id', 'ticker'),
        Index('idx_session_finalized', 'session_id', 'is_finalized'),
        Index('idx_user_date', 'user_id', 'analysis_date'),
        Index('idx_task_id', 'task_id'),
        Index('idx_last_interaction', 'last_interaction'),
    )
    
    def __repr__(self):
        return f"<ConversationState(session_id='{self.session_id}', ticker='{self.ticker}', finalized={self.is_finalized})>"


class ChatMessage(Base):
    """Chat message model for storing individual chat messages."""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    
    # Message metadata
    message_type = Column(String(50), default="text")  # text, tool_call, tool_response, system
    message_metadata = Column(JSON)  # Additional message metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_session_created', 'session_id', 'created_at'),
        Index('idx_user_session', 'user_id', 'session_id'),
        Index('idx_role_type', 'role', 'message_type'),
    )
    
    def __repr__(self):
        return f"<ChatMessage(message_id='{self.message_id}', role='{self.role}', type='{self.message_type}')>"
