"""
System Repository - 系统日志和监控相关数据访问
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from .base import BaseRepository
from ..database.models import SystemLog

logger = logging.getLogger(__name__)


class SystemRepository(BaseRepository[SystemLog]):
    """系统日志数据访问Repository"""
    
    def __init__(self, session_factory=None):
        super().__init__(SystemLog)
    
    def log_system_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """记录系统事件"""
        try:
            with self._get_session() as db:
                log_entry = SystemLog(
                    event_type=event_type,
                    event_data=event_data
                )
                
                db.add(log_entry)
                db.commit()
                logger.debug(f"Logged system event: {event_type}")
                return True
        except Exception as e:
            logger.error(f"Error logging system event {event_type}: {e}")
            return False
    
    def get_system_logs(self, date_str: str = None, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取系统日志"""
        try:
            with self._get_session() as db:
                query = db.query(SystemLog)
                
                if date_str:
                    # 按日期过滤
                    try:
                        date_obj = datetime.strptime(date_str, "%Y%m%d").date()
                        start_of_day = datetime.combine(date_obj, datetime.min.time())
                        end_of_day = datetime.combine(date_obj, datetime.max.time())
                        query = query.filter(
                            and_(
                                SystemLog.timestamp >= start_of_day,
                                SystemLog.timestamp <= end_of_day
                            )
                        )
                    except ValueError:
                        logger.warning(f"Invalid date format: {date_str}")
                
                if event_type:
                    query = query.filter(SystemLog.event_type == event_type)
                
                logs = query.order_by(desc(SystemLog.timestamp)).limit(limit).all()
                
                return [self._to_dict(log) for log in logs]
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return []
    
    def get_logs_by_date_range(self, start_date: datetime, end_date: datetime, 
                              event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """按日期范围获取日志"""
        try:
            with self._get_session() as db:
                query = db.query(SystemLog).filter(
                    and_(
                        SystemLog.timestamp >= start_date,
                        SystemLog.timestamp <= end_date
                    )
                )
                
                if event_type:
                    query = query.filter(SystemLog.event_type == event_type)
                
                logs = query.order_by(desc(SystemLog.timestamp)).limit(limit).all()
                return [self._to_dict(log) for log in logs]
        except Exception as e:
            logger.error(f"Error getting logs by date range: {e}")
            return []
    
    def get_event_types(self) -> List[str]:
        """获取所有事件类型"""
        try:
            with self._get_session() as db:
                event_types = db.query(SystemLog.event_type).distinct().all()
                return [event_type[0] for event_type in event_types]
        except Exception as e:
            logger.error(f"Error getting event types: {e}")
            return []
    
    def get_event_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取事件统计信息"""
        try:
            with self._get_session() as db:
                start_date = datetime.now() - timedelta(days=days)
                
                # 总事件数
                total_events = db.query(SystemLog).filter(
                    SystemLog.timestamp >= start_date
                ).count()
                
                # 按类型统计
                from sqlalchemy import func
                event_type_stats = db.query(
                    SystemLog.event_type,
                    func.count(SystemLog.id).label('count')
                ).filter(
                    SystemLog.timestamp >= start_date
                ).group_by(SystemLog.event_type).all()
                
                return {
                    "total_events": total_events,
                    "period_days": days,
                    "event_types": {
                        event_type: count for event_type, count in event_type_stats
                    }
                }
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return {}
    
    def cleanup_old_logs(self, days: int = 90) -> int:
        """清理旧日志"""
        try:
            with self._get_session() as db:
                cutoff_date = datetime.now() - timedelta(days=days)
                old_logs = db.query(SystemLog).filter(
                    SystemLog.timestamp < cutoff_date
                ).all()
                
                count = len(old_logs)
                for log in old_logs:
                    db.delete(log)
                
                db.commit()
                logger.info(f"Cleaned up {count} old log entries (older than {days} days)")
                return count
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0
    
    def _to_dict(self, log: SystemLog) -> Dict[str, Any]:
        """将SystemLog模型转换为字典"""
        return {
            "event_type": log.event_type,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "data": log.event_data
        }

