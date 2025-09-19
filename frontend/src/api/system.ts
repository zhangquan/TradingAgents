import { api } from './index'
import { ConfigRequest } from './types'

export const systemApi = {
  // Configuration
  async getConfig() {
    const response = await api.get('/system/config')
    return response.data
  },

  async updateConfig(config: ConfigRequest) {
    const response = await api.post('/system/config', config)
    return response.data
  },

  // Runtime stats
  async getRuntimeStats() {
    const response = await api.get('/stats')
    return response.data
  },

  // System management
  async getSystemStats() {
    const response = await api.get('/system/stats')
    return response.data
  },

  async getSystemLogs(date?: string, eventType?: string) {
    const params = new URLSearchParams()
    if (date) params.append('date', date)
    if (eventType) params.append('event_type', eventType)
    
    const response = await api.get(`/system/logs?${params}`)
    return response.data
  },

  async cleanupSystem() {
    const response = await api.post('/system/cleanup')
    return response.data
  },

  // Available options
  async getAnalysts() {
    const response = await api.get('/system/analysts')
    return response.data
  },

  async getModels() {
    const response = await api.get('/system/models')
    return response.data
  },

  async updateUserPreferences(preferences: {
    llm_provider?: string
    backend_url?: string
    shallow_thinker?: string
    deep_thinker?: string
    default_research_depth?: number
    default_analysts?: string[]
    notification_settings?: any
    default_language?: string
    report_language?: string
  }) {
    const response = await api.post('/system/preferences', preferences)
    return response.data
  },
}
