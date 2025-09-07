"""
Database-based storage service for TradingAgents backend.
Replaces the file-based LocalStorage with SQLAlchemy ORM operations.
Maintains the same API interface for backward compatibility.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.exc import IntegrityError

from .database import SessionLocal
from .models import (
    User, Analysis, Report, Notification, SystemConfig,
    UserConfig, CacheEntry, SystemLog, ScheduledTask, Watchlist
)

logger = logging.getLogger(__name__)


class DatabaseStorage:
    """Database-based storage manager using SQLAlchemy ORM."""
    
    def __init__(self):
        """Initialize storage service."""
        self.session_factory = SessionLocal
    
    def _get_session(self) -> Session:
        """Get database session."""
        return self.session_factory()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        return datetime.now().isoformat()
    
    def _format_datetime(self, dt) -> str:
        """Format datetime object to ISO string with timezone info."""
        if dt is None:
            return None
        # Ensure we add timezone info if not present
        return dt.isoformat() + ('Z' if dt.tzinfo is None else '')
    
    # User Management
    def create_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Create a new user."""
        try:
            with self._get_session() as db:
                # Check if user already exists
                existing_user = db.query(User).filter(User.user_id == user_id).first()
                if existing_user:
                    return False
                
                # Create new user
                user = User(
                    user_id=user_id,
                    email=user_data.get("email"),
                    name=user_data.get("name"),
                    status=user_data.get("status", "active")
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                logger.info(f"Created user: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data."""
        try:
            with self._get_session() as db:
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return None
                
                return {
                    "user_id": user.user_id,
                    "email": user.email,
                    "name": user.name,
                    "status": user.status,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                }
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data."""
        try:
            with self._get_session() as db:
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return False
                
                # Update fields
                for key, value in updates.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users."""
        try:
            with self._get_session() as db:
                users = db.query(User).order_by(User.created_at).all()
                return [
                    {
                        "user_id": user.user_id,
                        "email": user.email,
                        "name": user.name,
                        "status": user.status,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": user.updated_at.isoformat() if user.updated_at else None
                    }
                    for user in users
                ]
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    # Analysis Management
    def save_analysis(self, user_id: str, ticker: str, analysis_data: Dict[str, Any]) -> str:
        """Save analysis results."""
        try:
            with self._get_session() as db:
                # Generate analysis ID
                analysis_id = f"analysis_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Create analysis record
                analysis = Analysis(
                    analysis_id=analysis_id,
                    user_id=user_id,
                    ticker=ticker,
                    analysts=analysis_data.get("analysts", []),
                    research_depth=analysis_data.get("research_depth", 1),
                    llm_provider=analysis_data.get("llm_provider"),
                    model_config=analysis_data.get("model_config"),
                    final_state=analysis_data.get("final_state", {}),
                    status=analysis_data.get("status", "completed"),
                    analysis_date=analysis_data.get("analysis_date")
                )
                
                db.add(analysis)
                db.commit()
                db.refresh(analysis)
                
                logger.info(f"Saved analysis: {analysis_id}")
                return analysis_id
                
        except Exception as e:
            logger.error(f"Error saving analysis for {ticker}: {e}")
            raise
    
    def get_analysis(self, user_id: str, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get specific analysis by ID."""
        try:
            with self._get_session() as db:
                analysis = db.query(Analysis).filter(
                    and_(Analysis.user_id == user_id, Analysis.analysis_id == analysis_id)
                ).first()
                
                if not analysis:
                    return None
                
                return {
                    "analysis_id": analysis.analysis_id,
                    "user_id": analysis.user_id,
                    "ticker": analysis.ticker,
                    "analysts": analysis.analysts,
                    "research_depth": analysis.research_depth,
                    "llm_provider": analysis.llm_provider,
                    "model_config": analysis.model_config,
                    "final_state": analysis.final_state,
                    "status": analysis.status,
                    "analysis_date": analysis.analysis_date,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                    "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None
                }
        except Exception as e:
            logger.error(f"Error getting analysis {analysis_id}: {e}")
            return None
    
    def list_analysis(self, user_id: str, ticker: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List user's analysis results."""
        try:
            with self._get_session() as db:
                query = db.query(Analysis).filter(Analysis.user_id == user_id)
                
                if ticker:
                    query = query.filter(Analysis.ticker == ticker)
                
                analyses = query.order_by(desc(Analysis.created_at)).limit(limit).all()
                
                return [
                    {
                        "analysis_id": analysis.analysis_id,
                        "user_id": analysis.user_id,
                        "ticker": analysis.ticker,
                        "analysts": analysis.analysts,
                        "research_depth": analysis.research_depth,
                        "llm_provider": analysis.llm_provider,
                        "model_config": analysis.model_config,
                        "final_state": analysis.final_state,
                        "status": analysis.status,
                        "analysis_date": analysis.analysis_date,
                        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                        "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None
                    }
                    for analysis in analyses
                ]
        except Exception as e:
            logger.error(f"Error listing analyses: {e}")
            return []
    
    def delete_analysis(self, user_id: str, analysis_id: str) -> bool:
        """Delete specific analysis by ID."""
        try:
            with self._get_session() as db:
                analysis = db.query(Analysis).filter(
                    and_(Analysis.user_id == user_id, Analysis.analysis_id == analysis_id)
                ).first()
                
                if not analysis:
                    return False
                
                db.delete(analysis)
                db.commit()
                
                logger.info(f"Deleted analysis {analysis_id} for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            return False
    
    # Report Management
    def save_unified_report(self, analysis_id: str, user_id: str, ticker: str, sections: Dict[str, str], title: str = None) -> str:
        """Save a unified report with multiple sections for an analysis."""
        try:
            with self._get_session() as db:
                # Check if report already exists for this analysis
                existing_report = db.query(Report).filter(
                    and_(Report.analysis_id == analysis_id, Report.user_id == user_id)
                ).first()
                
                if existing_report:
                    # Update existing report
                    existing_report.sections = sections
                    existing_report.title = title or existing_report.title
                    existing_report.updated_at = datetime.now()
                    db.commit()
                    logger.info(f"Updated unified report: {existing_report.report_id} for analysis {analysis_id}")
                    return existing_report.report_id
                else:
                    # Generate report ID
                    report_id = f"report_{ticker}_{analysis_id.split('_')[-1]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    # Create new unified report record
                    report = Report(
                        report_id=report_id,
                        analysis_id=analysis_id,
                        user_id=user_id,
                        ticker=ticker.upper(),
                        title=title or f"{ticker.upper()} Complete Analysis Report",
                        sections=sections,
                        status="generated"
                    )
                    
                    db.add(report)
                    db.commit()
                    db.refresh(report)
                    
                    logger.info(f"Saved unified report: {report_id} for analysis {analysis_id}")
                    return report_id
                
        except Exception as e:
            logger.error(f"Error saving unified report for analysis {analysis_id}: {e}")
            raise
    
 
    def get_report(self, user_id: str, report_id: str) -> Optional[Dict[str, Any]]:
        """Get specific unified report by ID."""
        try:
            with self._get_session() as db:
                # Join with Analysis to get the analysis_date
                report = db.query(Report).filter(
                    and_(Report.user_id == user_id, Report.report_id == report_id)
                ).first()
                
                if not report:
                    return None
                
              
                
                return {
                    "report_id": report.report_id,
                    "analysis_id": report.analysis_id,
                    "user_id": report.user_id,
                    "ticker": report.ticker,
                    "date": report.created_at.isoformat() if report.created_at else None,  # Get date from related Analysis
                    "title": report.title,
                    "sections": report.sections,  # Contains all report sections
                    "status": report.status,
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                    "updated_at": report.updated_at.isoformat() if report.updated_at else None
                }
        except Exception as e:
            logger.error(f"Error getting report {report_id}: {e}")
            return None
    
    def list_reports(self, user_id: str, ticker: str = None, analysis_id: str = None,  limit: int = 50) -> List[Dict[str, Any]]:
        """List unified reports with optional filters."""
        try:
            with self._get_session() as db:
                query = db.query(Report).filter(Report.user_id == user_id)
                
                if ticker:
                    query = query.filter(Report.ticker == ticker.upper())
                if analysis_id:
                    query = query.filter(Report.analysis_id == analysis_id)

                reports = query.order_by(desc(Report.created_at)).limit(limit).all()
                
                return [
                    {
                        "report_id": report.report_id,
                        "analysis_id": report.analysis_id,
                        "user_id": report.user_id,
                        "ticker": report.ticker,
                        "title": report.title,
                        "sections": report.sections,
                        "status": report.status,
                        "created_at": report.created_at.isoformat() + 'Z' if report.created_at else None,
                        "updated_at": report.updated_at.isoformat() + 'Z' if report.updated_at else None,
                        # For backward compatibility, add derived fields
                        "report_type": "unified_analysis",  # Indicate this is a unified report
                        "content": report.sections  # Map sections to content for legacy compatibility
                    }
                    for report in reports
                ]
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            return []
    
    def delete_report(self, user_id: str, report_id: str) -> bool:
        """Delete specific report by ID."""
        try:
            with self._get_session() as db:
                report = db.query(Report).filter(
                    and_(Report.user_id == user_id, Report.report_id == report_id)
                ).first()
                
                if not report:
                    return False
                
                db.delete(report)
                db.commit()
                
                logger.info(f"Deleted report {report_id} for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting report {report_id}: {e}")
            return False
    
  
    def list_reports_by_ticker(self, user_id: str, ticker: str, report_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all reports for a specific ticker symbol."""
        try:
            with self._get_session() as db:
                query = db.query(Report).filter(
                    and_(Report.user_id == user_id, Report.ticker == ticker.upper())
                )
                
                if report_type:
                    query = query.filter(Report.report_type == report_type)
                
                reports = query.order_by(desc(Report.created_at)).limit(limit).all()
                
                return [
                    {
                        "report_id": report.report_id,
                        "analysis_id": report.analysis_id,
                        "user_id": report.user_id,
                        "ticker": report.ticker,
                        "report_type": report.report_type,
                        "title": report.title,
                        "content": report.content,
                        "status": report.status,
                        "created_at": report.created_at.isoformat() if report.created_at else None,
                        "updated_at": report.updated_at.isoformat() if report.updated_at else None
                    }
                    for report in reports
                ]
        except Exception as e:
            logger.error(f"Error listing reports for ticker {ticker}: {e}")
            return []
    
    # Configuration Management
    def save_config(self, config_name: str, config_data: Dict[str, Any]):
        """Save system configuration."""
        try:
            with self._get_session() as db:
                config = db.query(SystemConfig).filter(SystemConfig.config_name == config_name).first()
                
                if config:
                    # Update existing config
                    config.config_data = config_data
                else:
                    # Create new config
                    config = SystemConfig(
                        config_name=config_name,
                        config_data=config_data
                    )
                    db.add(config)
                
                db.commit()
        except Exception as e:
            logger.error(f"Error saving config {config_name}: {e}")
            raise
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """Get system configuration."""
        try:
            with self._get_session() as db:
                config = db.query(SystemConfig).filter(SystemConfig.config_name == config_name).first()
                
                if config:
                    return config.config_data
                return {}
        except Exception as e:
            logger.error(f"Error getting config {config_name}: {e}")
            return {}
    
    def save_user_config(self, user_id: str, config_data: Dict[str, Any]):
        """Save user-specific configuration."""
        try:
            with self._get_session() as db:
                user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
                
                if user_config:
                    # Update existing config
                    user_config.config_data = config_data
                else:
                    # Create new config
                    user_config = UserConfig(
                        user_id=user_id,
                        config_data=config_data
                    )
                    db.add(user_config)
                
                db.commit()
        except Exception as e:
            logger.error(f"Error saving user config for {user_id}: {e}")
            raise
    
    def get_user_config(self, user_id: str) -> Dict[str, Any]:
        """Get user-specific configuration."""
        try:
            with self._get_session() as db:
                user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
                
                if user_config:
                    return user_config.config_data
                return {}
        except Exception as e:
            logger.error(f"Error getting user config for {user_id}: {e}")
            return {}
    
    # Cache Management
    def save_cache(self, cache_key: str, data: Any, ttl_hours: int = 24):
        """Save data to cache with TTL."""
        try:
            with self._get_session() as db:
                expires_at = datetime.now() + timedelta(hours=ttl_hours)
                
                cache_entry = db.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()
                
                if cache_entry:
                    # Update existing cache
                    cache_entry.data = data
                    cache_entry.expires_at = expires_at
                else:
                    # Create new cache entry
                    cache_entry = CacheEntry(
                        cache_key=cache_key,
                        data=data,
                        expires_at=expires_at
                    )
                    db.add(cache_entry)
                
                db.commit()
        except Exception as e:
            logger.error(f"Error saving cache {cache_key}: {e}")
    
    def get_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        try:
            with self._get_session() as db:
                cache_entry = db.query(CacheEntry).filter(
                    and_(
                        CacheEntry.cache_key == cache_key,
                        CacheEntry.expires_at > datetime.now()
                    )
                ).first()
                
                if cache_entry:
                    return cache_entry.data
                return None
        except Exception as e:
            logger.error(f"Error getting cache {cache_key}: {e}")
            return None
    
    def clear_expired_cache(self):
        """Clear all expired cache entries."""
        try:
            with self._get_session() as db:
                expired_entries = db.query(CacheEntry).filter(
                    CacheEntry.expires_at <= datetime.now()
                ).all()
                
                for entry in expired_entries:
                    db.delete(entry)
                
                db.commit()
                logger.info(f"Cleared {len(expired_entries)} expired cache entries")
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
    
    # Notification Management
    def save_notification(self, user_id: str, notification: Dict[str, Any]) -> str:
        """Save user notification."""
        try:
            with self._get_session() as db:
                notification_id = f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                
                notif = Notification(
                    notification_id=notification_id,
                    user_id=user_id,
                    title=notification.get("title", ""),
                    message=notification.get("message", ""),
                    type=notification.get("type", "info"),
                    data=notification.get("data", {}),
                    read=notification.get("read", False)
                )
                
                db.add(notif)
                db.commit()
                db.refresh(notif)
                
                return notification_id
        except Exception as e:
            logger.error(f"Error saving notification for user {user_id}: {e}")
            raise
    
    def get_notifications(self, user_id: str, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user notifications."""
        try:
            with self._get_session() as db:
                query = db.query(Notification).filter(Notification.user_id == user_id)
                
                if unread_only:
                    query = query.filter(Notification.read == False)
                
                notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()
                
                return [
                    {
                        "notification_id": notif.notification_id,
                        "user_id": notif.user_id,
                        "title": notif.title,
                        "message": notif.message,
                        "type": notif.type,
                        "data": notif.data,
                        "read": notif.read,
                        "read_at": notif.read_at.isoformat() if notif.read_at else None,
                        "created_at": notif.created_at.isoformat() if notif.created_at else None
                    }
                    for notif in notifications
                ]
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            return []
    
    def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read."""
        try:
            with self._get_session() as db:
                notification = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user_id,
                        Notification.notification_id == notification_id
                    )
                ).first()
                
                if not notification:
                    return False
                
                notification.read = True
                notification.read_at = datetime.now()
                db.commit()
                
                return True
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            return False
    
    # Logging and Monitoring
    def log_system_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log system events."""
        try:
            with self._get_session() as db:
                log_entry = SystemLog(
                    event_type=event_type,
                    event_data=event_data
                )
                
                db.add(log_entry)
                db.commit()
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
    
    def get_system_logs(self, date_str: str = None, event_type: str = None) -> List[Dict[str, Any]]:
        """Get system logs for a specific date."""
        try:
            with self._get_session() as db:
                query = db.query(SystemLog)
                
                if date_str:
                    # Filter by date
                    date_obj = datetime.strptime(date_str, "%Y%m%d").date()
                    start_of_day = datetime.combine(date_obj, datetime.min.time())
                    end_of_day = datetime.combine(date_obj, datetime.max.time())
                    query = query.filter(
                        and_(
                            SystemLog.timestamp >= start_of_day,
                            SystemLog.timestamp <= end_of_day
                        )
                    )
                
                if event_type:
                    query = query.filter(SystemLog.event_type == event_type)
                
                logs = query.order_by(desc(SystemLog.timestamp)).all()
                
                return [
                    {
                        "event_type": log.event_type,
                        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                        "data": log.event_data
                    }
                    for log in logs
                ]
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return []
    
    # Watchlist Management - Using dedicated Watchlist table
    def get_user_watchlist(self, user_id: str) -> List[str]:
        """Get user's watchlist ticker symbols."""
        try:
            with self._get_session() as db:
                watchlist_items = db.query(Watchlist).filter(
                    Watchlist.user_id == user_id
                ).order_by(Watchlist.priority, Watchlist.ticker).all()
                
                return [item.ticker for item in watchlist_items]
        except Exception as e:
            logger.error(f"Error getting watchlist for user {user_id}: {e}")
            return []
    
    def get_user_watchlist_detailed(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's watchlist with detailed information."""
        try:
            with self._get_session() as db:
                watchlist_items = db.query(Watchlist).filter(
                    Watchlist.user_id == user_id
                ).order_by(Watchlist.priority, Watchlist.ticker).all()
                
                return [
                    {
                        "id": item.id,
                        "ticker": item.ticker,
                        "added_date": item.added_date,
                        "notes": item.notes,
                        "priority": item.priority,
                        "alerts_enabled": item.alerts_enabled,
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                        "updated_at": item.updated_at.isoformat() if item.updated_at else None
                    }
                    for item in watchlist_items
                ]
        except Exception as e:
            logger.error(f"Error getting detailed watchlist for user {user_id}: {e}")
            return []
    
    def add_to_watchlist(self, user_id: str, symbol: str, notes: str = None, priority: int = 1, alerts_enabled: bool = True) -> bool:
        """Add symbol to user's watchlist."""
        try:
            with self._get_session() as db:
                symbol = symbol.upper()
                
                # Check if already exists
                existing = db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user_id, Watchlist.ticker == symbol)
                ).first()
                
                if existing:
                    return False  # Already in watchlist
                
                # Create new watchlist item
                watchlist_item = Watchlist(
                    user_id=user_id,
                    ticker=symbol,
                    added_date=datetime.now().strftime('%Y-%m-%d'),
                    notes=notes,
                    priority=priority,
                    alerts_enabled=alerts_enabled
                )
                
                db.add(watchlist_item)
                db.commit()
                
                # Get updated count
                count = db.query(Watchlist).filter(Watchlist.user_id == user_id).count()
                
                self.log_system_event("watchlist_add", {
                    "user_id": user_id,
                    "symbol": symbol,
                    "watchlist_size": count,
                    "priority": priority
                })
                
                logger.info(f"Added {symbol} to watchlist for user {user_id}")
                return True
                
        except IntegrityError:
            logger.warning(f"Symbol {symbol} already in watchlist for user {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error adding {symbol} to watchlist for user {user_id}: {e}")
            return False
    
    def remove_from_watchlist(self, user_id: str, symbol: str) -> bool:
        """Remove symbol from user's watchlist."""
        try:
            with self._get_session() as db:
                symbol = symbol.upper()
                
                watchlist_item = db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user_id, Watchlist.ticker == symbol)
                ).first()
                
                if not watchlist_item:
                    return False  # Not in watchlist
                
                db.delete(watchlist_item)
                db.commit()
                
                # Get updated count
                count = db.query(Watchlist).filter(Watchlist.user_id == user_id).count()
                
                self.log_system_event("watchlist_remove", {
                    "user_id": user_id,
                    "symbol": symbol,
                    "watchlist_size": count
                })
                
                logger.info(f"Removed {symbol} from watchlist for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing {symbol} from watchlist for user {user_id}: {e}")
            return False
    
    def update_watchlist(self, user_id: str, symbols: List[str]) -> bool:
        """Update user's entire watchlist."""
        try:
            with self._get_session() as db:
                # Remove all existing items
                db.query(Watchlist).filter(Watchlist.user_id == user_id).delete()
                
                # Add new items
                symbols = list(set([symbol.upper() for symbol in symbols]))
                for i, symbol in enumerate(sorted(symbols)):
                    watchlist_item = Watchlist(
                        user_id=user_id,
                        ticker=symbol,
                        added_date=datetime.now().strftime('%Y-%m-%d'),
                        priority=1,  # Default priority
                        alerts_enabled=True
                    )
                    db.add(watchlist_item)
                
                db.commit()
                
                self.log_system_event("watchlist_update", {
                    "user_id": user_id,
                    "symbols": symbols,
                    "watchlist_size": len(symbols)
                })
                
                logger.info(f"Updated watchlist for user {user_id} with {len(symbols)} symbols")
                return True
                
        except Exception as e:
            logger.error(f"Error updating watchlist for user {user_id}: {e}")
            return False
    
    def update_watchlist_item(self, user_id: str, symbol: str, updates: Dict[str, Any]) -> bool:
        """Update specific watchlist item properties."""
        try:
            with self._get_session() as db:
                symbol = symbol.upper()
                
                watchlist_item = db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user_id, Watchlist.ticker == symbol)
                ).first()
                
                if not watchlist_item:
                    return False
                
                # Update allowed fields
                allowed_fields = ['notes', 'priority', 'alerts_enabled']
                for key, value in updates.items():
                    if key in allowed_fields and hasattr(watchlist_item, key):
                        setattr(watchlist_item, key, value)
                
                db.commit()
                
                self.log_system_event("watchlist_item_update", {
                    "user_id": user_id,
                    "symbol": symbol,
                    "updates": list(updates.keys())
                })
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating watchlist item {symbol} for user {user_id}: {e}")
            return False
    
    def is_symbol_in_watchlist(self, user_id: str, symbol: str) -> bool:
        """Check if symbol is in user's watchlist."""
        try:
            with self._get_session() as db:
                symbol = symbol.upper()
                
                exists = db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user_id, Watchlist.ticker == symbol)
                ).first() is not None
                
                return exists
                
        except Exception as e:
            logger.error(f"Error checking if {symbol} in watchlist for user {user_id}: {e}")
            return False
    
    # Scheduled Task Management - Unified API for all tasks
    def create_scheduled_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new scheduled task (immediate or scheduled execution)."""
        try:
            with self._get_session() as db:
                task_id = task_data.get("task_id") or f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                
                task = ScheduledTask(
                    task_id=task_id,
                    user_id=task_data.get("user_id", "demo_user"),
                    ticker=task_data["ticker"],
                    analysis_date=task_data.get("analysis_date"),
                    analysts=task_data.get("analysts", []),
                    research_depth=task_data.get("research_depth", 1),
                    schedule_type=task_data.get("schedule_type", "immediate"),
                    schedule_time=task_data.get("schedule_time"),
                    schedule_date=task_data.get("schedule_date"),
                    cron_expression=task_data.get("cron_expression"),
                    timezone=task_data.get("timezone", "UTC"),
                    status=task_data.get("status", "created"),
                    enabled=task_data.get("enabled", True),
                    progress=task_data.get("progress", 0),
                    current_step=task_data.get("current_step"),
                    result_data=task_data.get("result_data", {}),
                    trace=task_data.get("trace", [])
                )
                
                db.add(task)
                db.commit()
                db.refresh(task)
                
                logger.info(f"Created scheduled task: {task_id}")
                return task_id
                
        except Exception as e:
            logger.error(f"Error creating scheduled task: {e}")
            raise
    
    def get_scheduled_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get scheduled task by ID."""
        try:
            with self._get_session() as db:
                task = db.query(ScheduledTask).filter(ScheduledTask.task_id == task_id).first()
                
                if not task:
                    return None
                
                return {
                    "task_id": task.task_id,
                    "user_id": task.user_id,
                    "ticker": task.ticker,
                    "analysis_date": task.analysis_date,
                    "analysts": task.analysts,
                    "research_depth": task.research_depth,
                    "schedule_type": task.schedule_type,
                    "schedule_time": task.schedule_time,
                    "schedule_date": task.schedule_date,
                    "cron_expression": task.cron_expression,
                    "timezone": task.timezone,
                    "status": task.status,
                    "enabled": task.enabled,
                    "progress": task.progress,
                    "current_step": task.current_step,
                    "analysis_id": task.analysis_id,
                    "result_data": task.result_data,
                    "error_message": task.error_message,
                    "trace": task.trace,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "execution_count": task.execution_count,
                    "last_error": task.last_error,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                }
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    def list_scheduled_tasks(self, user_id: str = None, status: str = None, schedule_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List scheduled tasks with optional filters."""
        try:
            with self._get_session() as db:
                query = db.query(ScheduledTask)
                
                if user_id:
                    query = query.filter(ScheduledTask.user_id == user_id)
                if status:
                    query = query.filter(ScheduledTask.status == status)
                if schedule_type:
                    query = query.filter(ScheduledTask.schedule_type == schedule_type)
                
                tasks = query.order_by(desc(ScheduledTask.created_at)).limit(limit).all()
                
                return [
                    {
                        "task_id": task.task_id,
                        "user_id": task.user_id,
                        "ticker": task.ticker,
                        "analysis_date": task.analysis_date,
                        "analysts": task.analysts,
                        "research_depth": task.research_depth,
                        "schedule_type": task.schedule_type,
                        "schedule_time": task.schedule_time,
                        "schedule_date": task.schedule_date,
                        "cron_expression": task.cron_expression,
                        "timezone": task.timezone,
                        "status": task.status,
                        "enabled": task.enabled,
                        "progress": task.progress,
                        "current_step": task.current_step,
                        "analysis_id": task.analysis_id,
                        "result_data": task.result_data,
                        "error_message": task.error_message,
                        "trace": task.trace,
                        "last_run": task.last_run.isoformat() if task.last_run else None,
                        "execution_count": task.execution_count,
                        "last_error": task.last_error,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "updated_at": task.updated_at.isoformat() if task.updated_at else None
                    }
                    for task in tasks
                ]
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return []
    
    def update_scheduled_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update scheduled task."""
        try:
            with self._get_session() as db:
                task = db.query(ScheduledTask).filter(ScheduledTask.task_id == task_id).first()
                
                if task:
                    for key, value in updates.items():
                        if hasattr(task, key):
                            if key == "last_run" and isinstance(value, str):
                                setattr(task, key, datetime.fromisoformat(value))
                            elif key in ["started_at", "completed_at"] and isinstance(value, str):
                                setattr(task, key, datetime.fromisoformat(value))
                            else:
                                setattr(task, key, value)
                    
                    db.commit()
                    
                    self.log_system_event("scheduled_task_updated", {
                        "task_id": task_id,
                        "updates": list(updates.keys()),
                        "timestamp": self._get_timestamp()
                    })
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating scheduled task {task_id}: {e}")
            return False
    
    def update_scheduled_task_status(self, task_id: str, status: str, **kwargs) -> bool:
        """Update scheduled task status and additional data."""
        try:
            updates = {"status": status}
            
            # Handle timestamp updates
            if status == "running" and "started_at" not in kwargs:
                updates["started_at"] = datetime.now()
            elif status in ["completed", "failed", "error"] and "completed_at" not in kwargs:
                updates["completed_at"] = datetime.now()
            
            # Add any additional kwargs
            updates.update(kwargs)
            
            return self.update_scheduled_task(task_id, updates)
        except Exception as e:
            logger.error(f"Error updating scheduled task status {task_id}: {e}")
            return False
    
    def delete_scheduled_task(self, task_id: str) -> bool:
        """Delete scheduled task."""
        try:
            with self._get_session() as db:
                task = db.query(ScheduledTask).filter(ScheduledTask.task_id == task_id).first()
                
                if task:
                    db.delete(task)
                    db.commit()
                    
                    self.log_system_event("scheduled_task_deleted", {
                        "task_id": task_id,
                        "timestamp": self._get_timestamp()
                    })
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting scheduled task {task_id}: {e}")
            return False
    
    # Storage Statistics
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            with self._get_session() as db:
                stats = {
                    "storage_type": "database",
                    "last_updated": self._get_timestamp(),
                    "tables": {}
                }
                
                # Count records in each table
                tables = {
                    "users": User,
                    "analyses": Analysis,
                    "reports": Report,
                    "notifications": Notification,
                    "system_configs": SystemConfig,
                    "user_configs": UserConfig,
                    "cache_entries": CacheEntry,
                    "system_logs": SystemLog,
                    "scheduled_tasks": ScheduledTask,
                    "watchlist": Watchlist
                }
                
                for table_name, model in tables.items():
                    count = db.query(model).count()
                    stats["tables"][table_name] = {"record_count": count}
                
                return stats
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {"error": str(e)}
    
    # Backup functionality (placeholder)
    def create_backup(self, backup_name: str = None) -> str:
        """Create a backup (placeholder for database backup)."""
        backup_name = backup_name or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.warning("Database backup not implemented - use database-specific backup tools")
        return backup_name
