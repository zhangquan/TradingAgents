import { api } from './index'
import { NotificationData } from './types'

export const notificationsApi = {
  // Notifications
  async getNotifications(unreadOnly: boolean = false, limit: number = 50): Promise<{ notifications: NotificationData[] }> {
    const params = new URLSearchParams()
    params.append('unread_only', unreadOnly.toString())
    params.append('limit', limit.toString())
    
    const response = await api.get(`/notifications?${params}`)
    return response.data
  },

  async markNotificationRead(notificationId: string) {
    const response = await api.put(`/notifications/${notificationId}/read`)
    return response.data
  },

  async createNotification(notification: {
    title: string
    message: string
    type?: string
    priority?: string
  }) {
    const response = await api.post('/notifications', notification)
    return response.data
  },
}
