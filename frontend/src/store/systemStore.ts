import { create } from 'zustand'
import { systemApi } from '../api/system'
import { ConfigRequest } from '../api/types'

interface SystemState {
  // State
  config: any | null
  runtimeStats: any | null
  systemStats: any | null
  systemLogs: any[]
  analysts: string[]
  models: string[]
  userPreferences: any | null
  isLoading: boolean
  error: string | null
  
  // Actions
  loadConfig: () => Promise<void>
  updateConfig: (config: ConfigRequest) => Promise<void>
  loadRuntimeStats: () => Promise<void>
  loadSystemStats: () => Promise<void>
  loadSystemLogs: (date?: string, eventType?: string) => Promise<void>
  cleanupSystem: () => Promise<any>
  loadAnalysts: () => Promise<void>
  loadModels: () => Promise<void>
  updateUserPreferences: (preferences: {
    llm_provider?: string
    backend_url?: string
    shallow_thinker?: string
    deep_thinker?: string
    default_research_depth?: number
    default_analysts?: string[]
    notification_settings?: any
    default_language?: string
    report_language?: string
  }) => Promise<void>
  
  // Utilities
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  refreshAll: () => Promise<void>
}

export const useSystemStore = create<SystemState>((set, get) => ({
  // Initial state
  config: null,
  runtimeStats: null,
  systemStats: null,
  systemLogs: [],
  analysts: [],
  models: [],
  userPreferences: null,
  isLoading: false,
  error: null,

  // Actions
  loadConfig: async () => {
    set({ isLoading: true, error: null })
    try {
      const config = await systemApi.getConfig()
      set({ config, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load config', isLoading: false })
    }
  },

  updateConfig: async (config: ConfigRequest) => {
    set({ isLoading: true, error: null })
    try {
      const response = await systemApi.updateConfig(config)
      // Reload config to get updated values
      await get().loadConfig()
      set({ isLoading: false })
      return response
    } catch (error: any) {
      set({ error: error.message || 'Failed to update config', isLoading: false })
      throw error
    }
  },

  loadRuntimeStats: async () => {
    set({ isLoading: true, error: null })
    try {
      const stats = await systemApi.getRuntimeStats()
      set({ runtimeStats: stats, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load runtime stats', isLoading: false })
    }
  },

  loadSystemStats: async () => {
    set({ isLoading: true, error: null })
    try {
      const stats = await systemApi.getSystemStats()
      set({ systemStats: stats, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load system stats', isLoading: false })
    }
  },

  loadSystemLogs: async (date?: string, eventType?: string) => {
    set({ isLoading: true, error: null })
    try {
      const logs = await systemApi.getSystemLogs(date, eventType)
      set({ systemLogs: logs.logs || logs, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load system logs', isLoading: false })
    }
  },

  cleanupSystem: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await systemApi.cleanupSystem()
      set({ isLoading: false })
      return response
    } catch (error: any) {
      set({ error: error.message || 'Failed to cleanup system', isLoading: false })
      throw error
    }
  },

  loadAnalysts: async () => {
    try {
      const response = await systemApi.getAnalysts()
      set({ analysts: response.analysts || response })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load analysts' })
    }
  },

  loadModels: async () => {
    try {
      const response = await systemApi.getModels()
      set({ models: response.models || response })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load models' })
    }
  },

  updateUserPreferences: async (preferences) => {
    set({ isLoading: true, error: null })
    try {
      const response = await systemApi.updateUserPreferences(preferences)
      set({ 
        userPreferences: { ...get().userPreferences, ...preferences },
        isLoading: false 
      })
      return response
    } catch (error: any) {
      set({ error: error.message || 'Failed to update user preferences', isLoading: false })
      throw error
    }
  },

  // Utilities
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  clearError: () => set({ error: null }),

  refreshAll: async () => {
    const { loadConfig, loadRuntimeStats, loadSystemStats, loadAnalysts, loadModels } = get()
    
    // Load all system data in parallel
    await Promise.allSettled([
      loadConfig(),
      loadRuntimeStats(),
      loadSystemStats(),
      loadAnalysts(),
      loadModels()
    ])
  },
}))
