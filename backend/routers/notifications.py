from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from backend.storage import LocalStorage

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: str = "info"
    metadata: Optional[Dict[str, Any]] = None

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    read: bool
    created_at: str
    metadata: Optional[Dict[str, Any]] = None

# Initialize storage
storage = LocalStorage()

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    user_id: str = Query("demo_user", description="User ID to get notifications for"),
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, description="Maximum number of notifications to return")
):
    """Get user notifications"""
    try:
        notifications = storage.get_notifications(user_id, unread_only, limit)
        return notifications
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")

@router.post("/", response_model=Dict[str, str])
async def create_notification(notification: NotificationCreate):
    """Create a new notification"""
    try:
        notification_id = storage.save_notification(
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.type,
            metadata=notification.metadata or {}
        )
        return {"id": notification_id, "message": "Notification created successfully"}
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification")

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Query("demo_user", description="User ID who owns the notification")
):
    """Mark a notification as read"""
    try:
        success = storage.mark_notification_read(user_id, notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@router.get("/stats")
async def get_notification_stats(
    user_id: str = Query("demo_user", description="User ID to get stats for")
):
    """Get notification statistics for a user"""
    try:
        all_notifications = storage.get_notifications(user_id, unread_only=False, limit=1000)
        unread_notifications = storage.get_notifications(user_id, unread_only=True, limit=1000)
        
        return {
            "total": len(all_notifications),
            "unread": len(unread_notifications),
            "read": len(all_notifications) - len(unread_notifications),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification stats")
