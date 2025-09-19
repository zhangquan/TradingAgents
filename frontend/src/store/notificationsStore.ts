import { create } from 'zustand'
import { notificationsApi } from '../api/notifications'
import { NotificationData } from '../api/types'

interface NotificationsState {
  // State
  notifications: NotificationData[]
  unreadCount: number
  isLoading: boolean
  error: string | null
  filters: {
    unreadOnly: boolean
    limit: number
  }
  
  // Actions
  loadNotifications: (unreadOnly?: boolean, limit?: number) => Promise<void>
  markAsRead: (notificationId: string) => Promise<void>
  markAllAsRead: () => Promise<void>
  createNotification: (notification: {
    title: string
    message: string
    type?: string
    priority?: string
  }) => Promise<void>
  
  // Real-time updates
  addNotification: (notification: NotificationData) => void
  removeNotification: (notificationId: string) => void
  
  // Utilities
  setFilters: (filters: Partial<NotificationsState['filters']>) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearNotifications: () => void
  getUnreadNotifications: () => NotificationData[]
}

export const useNotificationsStore = create<NotificationsState>((set, get) => ({
  // Initial state
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  error: null,
  filters: {
    unreadOnly: false,
    limit: 50
  },

  // Actions
  loadNotifications: async (unreadOnly = false, limit = 50) => {
    set({ isLoading: true, error: null })
    try {
      const response = await notificationsApi.getNotifications(unreadOnly, limit)
      const notifications = response.notifications || response
      const unreadCount = notifications.filter((n: NotificationData) => !n.read).length
      
      set({ 
        notifications,
        unreadCount,
        isLoading: false,
        filters: { unreadOnly, limit }
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load notifications', isLoading: false })
    }
  },

  markAsRead: async (notificationId: string) => {
    try {
      await notificationsApi.markNotificationRead(notificationId)
      
      // Update local state
      const { notifications } = get()
      const updatedNotifications = notifications.map(notification => 
        notification.notification_id === notificationId 
          ? { ...notification, read: true }
          : notification
      )
      const unreadCount = updatedNotifications.filter(n => !n.read).length
      
      set({ notifications: updatedNotifications, unreadCount })
    } catch (error: any) {
      set({ error: error.message || 'Failed to mark notification as read' })
      throw error
    }
  },

  markAllAsRead: async () => {
    const { notifications } = get()
    const unreadNotifications = notifications.filter(n => !n.read)
    
    try {
      // Mark all unread notifications as read
      await Promise.all(
        unreadNotifications.map(notification => 
          notificationsApi.markNotificationRead(notification.notification_id)
        )
      )
      
      // Update local state
      const updatedNotifications = notifications.map(notification => 
        ({ ...notification, read: true })
      )
      
      set({ notifications: updatedNotifications, unreadCount: 0 })
    } catch (error: any) {
      set({ error: error.message || 'Failed to mark all notifications as read' })
      throw error
    }
  },

  createNotification: async (notification) => {
    set({ isLoading: true, error: null })
    try {
      const response = await notificationsApi.createNotification(notification)
      
      // Add to local state if response includes the created notification
      if (response.notification) {
        const { notifications, unreadCount } = get()
        set({ 
          notifications: [response.notification, ...notifications],
          unreadCount: unreadCount + 1,
          isLoading: false 
        })
      } else {
        // Reload notifications to get the new one
        await get().loadNotifications()
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to create notification', isLoading: false })
      throw error
    }
  },

  // Real-time updates
  addNotification: (notification: NotificationData) => {
    const { notifications, unreadCount } = get()
    set({ 
      notifications: [notification, ...notifications],
      unreadCount: notification.read ? unreadCount : unreadCount + 1
    })
  },

  removeNotification: (notificationId: string) => {
    const { notifications, unreadCount } = get()
    const notification = notifications.find(n => n.notification_id === notificationId)
    const newNotifications = notifications.filter(n => n.notification_id !== notificationId)
    const newUnreadCount = notification && !notification.read ? unreadCount - 1 : unreadCount
    
    set({ 
      notifications: newNotifications,
      unreadCount: Math.max(0, newUnreadCount)
    })
  },

  // Utilities
  setFilters: (filters) => {
    set({ filters: { ...get().filters, ...filters } })
  },

  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  clearError: () => set({ error: null }),
  clearNotifications: () => set({ notifications: [], unreadCount: 0 }),
  
  getUnreadNotifications: () => {
    const { notifications } = get()
    return notifications.filter(n => !n.read)
  },
}))
