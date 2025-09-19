"""
Notification Repository - 通知相关数据访问
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from .base import BaseRepository
from ..database.models import Notification

logger = logging.getLogger(__name__)


class NotificationRepository(BaseRepository[Notification]):
    """通知数据访问Repository"""
    
    def __init__(self, session_factory=None):
        super().__init__(Notification)
    
    def save_notification(self, user_id: str, notification: Dict[str, Any]) -> str:
        """保存用户通知"""
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
                
                logger.info(f"Saved notification: {notification_id} for user {user_id}")
                return notification_id
        except Exception as e:
            logger.error(f"Error saving notification for user {user_id}: {e}")
            raise
    
    def get_notifications(self, user_id: str, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户通知"""
        try:
            with self._get_session() as db:
                query = db.query(Notification).filter(Notification.user_id == user_id)
                
                if unread_only:
                    query = query.filter(Notification.read == False)
                
                notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()
                
                return [self._to_dict(notif) for notif in notifications]
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            return []
    
    def get_notification(self, user_id: str, notification_id: str) -> Optional[Dict[str, Any]]:
        """获取指定通知"""
        try:
            with self._get_session() as db:
                notification = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user_id,
                        Notification.notification_id == notification_id
                    )
                ).first()
                
                if not notification:
                    return None
                
                return self._to_dict(notification)
        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {e}")
            return None
    
    def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """标记通知为已读"""
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
                
                logger.info(f"Marked notification {notification_id} as read")
                return True
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            return False
    
    def mark_all_notifications_read(self, user_id: str) -> int:
        """标记用户所有通知为已读"""
        try:
            with self._get_session() as db:
                count = db.query(Notification).filter(
                    and_(Notification.user_id == user_id, Notification.read == False)
                ).update({
                    "read": True,
                    "read_at": datetime.now()
                })
                db.commit()
                
                logger.info(f"Marked {count} notifications as read for user {user_id}")
                return count
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {e}")
            return 0
    
    def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """删除通知"""
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
                
                db.delete(notification)
                db.commit()
                
                logger.info(f"Deleted notification {notification_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}")
            return False
    
    def delete_old_notifications(self, user_id: str, days: int = 30) -> int:
        """删除旧通知"""
        try:
            with self._get_session() as db:
                cutoff_date = datetime.now() - timedelta(days=days)
                count = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user_id,
                        Notification.created_at < cutoff_date
                    )
                ).delete()
                db.commit()
                
                logger.info(f"Deleted {count} old notifications for user {user_id}")
                return count
        except Exception as e:
            logger.error(f"Error deleting old notifications for user {user_id}: {e}")
            return 0
    
    def get_unread_count(self, user_id: str) -> int:
        """获取未读通知数量"""
        try:
            with self._get_session() as db:
                count = db.query(Notification).filter(
                    and_(Notification.user_id == user_id, Notification.read == False)
                ).count()
                return count
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {e}")
            return 0
    
    def _to_dict(self, notification: Notification) -> Dict[str, Any]:
        """将Notification模型转换为字典"""
        return {
            "notification_id": notification.notification_id,
            "user_id": notification.user_id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "data": notification.data,
            "read": notification.read,
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "created_at": notification.created_at.isoformat() if notification.created_at else None
        }
