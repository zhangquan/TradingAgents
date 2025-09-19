
import { useEffect, useState } from 'react'
import { notificationsApi } from '@/api/notifications'
import { NotificationData } from '@/api/types'
import { toast } from 'sonner'

export function useNotifications() {
  const [notifications, setNotifications] = useState<NotificationData[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(true)

  const loadNotifications = async () => {
    try {
      const response = await notificationsApi.getNotifications(false, 50)
      setNotifications(response.notifications)
      setUnreadCount(response.notifications.filter(n => !n.read).length)
    } catch (error) {
      console.error('Error loading notifications:', error)
      toast.error('加载通知失败')
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = async (notificationId: string) => {
    try {
      await notificationsApi.markNotificationRead(notificationId)
      setNotifications(prev => 
        prev.map(n => 
          n.notification_id === notificationId 
            ? { ...n, read: true }
            : n
        )
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Error marking notification as read:', error)
      toast.error('标记通知失败')
    }
  }

  const markAllAsRead = async () => {
    try {
      const unreadNotifications = notifications.filter(n => !n.read)
      
      // Mark all unread notifications as read
      await Promise.all(
        unreadNotifications.map(n => 
          notificationsApi.markNotificationRead(n.notification_id)
        )
      )
      
      setNotifications(prev => 
        prev.map(n => ({ ...n, read: true }))
      )
      setUnreadCount(0)
      
      toast.success('所有通知已标记为已读')
    } catch (error) {
      console.error('Error marking all notifications as read:', error)
      toast.error('批量标记失败')
    }
  }

  const addNotification = (notification: NotificationData) => {
    setNotifications(prev => [notification, ...prev])
    if (!notification.read) {
      setUnreadCount(prev => prev + 1)
    }
    
    // Show toast notification for new notifications
    if (notification.type === 'success') {
      toast.success(notification.title, { description: notification.message })
    } else if (notification.type === 'error') {
      toast.error(notification.title, { description: notification.message })
    } else {
      toast.info(notification.title, { description: notification.message })
    }
  }

  useEffect(() => {
    loadNotifications()
  }, [])

  return {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    addNotification,
    refresh: loadNotifications
  }
}
