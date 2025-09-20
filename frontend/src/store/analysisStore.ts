import { create } from 'zustand'
import { analysisApi } from '../api/analysis'
import { 
  AnalysisTaskRequest, 
  AnalysisTaskResponse, 
  AnalysisTaskInfo, 
  UnifiedTaskInfo, 
  TaskInfo,
  AnalysisConfig,
  TasksByStockResponse
} from '../api/types'

interface AnalysisState {
  // State
  config: AnalysisConfig | null
  tasks: UnifiedTaskInfo[]
  currentTask: UnifiedTaskInfo | null
  isLoading: boolean
  error: string | null
  
  // Actions
  loadConfig: () => Promise<void>
  loadTasks: () => Promise<void>
  loadTasksByStock: (stockSymbol: string, limit?: number) => Promise<TasksByStockResponse>
  createTask: (request: AnalysisTaskRequest) => Promise<AnalysisTaskResponse>
  getTask: (taskId: string) => Promise<void>
  updateTask: (taskId: string, request: AnalysisTaskRequest) => Promise<void>
  deleteTask: (taskId: string) => Promise<void>
  toggleTask: (taskId: string) => Promise<void>
  runTaskNow: (taskId: string) => Promise<void>
  getTaskProgress: (taskId: string) => Promise<TaskInfo>
  getBatchData: (symbols: string[]) => Promise<any>
  
  // Utilities
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  // Initial state
  config: null,
  tasks: [],
  currentTask: null,
  isLoading: false,
  error: null,

  // Actions
  loadConfig: async () => {
    set({ isLoading: true, error: null })
    try {
      const config = await analysisApi.getAnalysisConfig()
      set({ config, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load analysis config', isLoading: false })
    }
  },

  loadTasks: async () => {
    set({ isLoading: true, error: null })
    try {
      const tasks = await analysisApi.getAllTasks()
      set({ tasks, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load tasks', isLoading: false })
    }
  },

  loadTasksByStock: async (stockSymbol: string, limit: number = 50) => {
    set({ isLoading: true, error: null })
    try {
      const response = await analysisApi.getTasksByStock(stockSymbol, limit)
      set({ isLoading: false })
      return response
    } catch (error: any) {
      set({ error: error.message || 'Failed to load tasks by stock', isLoading: false })
      throw error
    }
  },

  createTask: async (request: AnalysisTaskRequest) => {
    set({ isLoading: true, error: null })
    try {
      const response = await analysisApi.createTask(request)
      // Reload tasks to get updated list
      await get().loadTasks()
      set({ isLoading: false })
      return response
    } catch (error: any) {
      set({ error: error.message || 'Failed to create task', isLoading: false })
      throw error
    }
  },

  getTask: async (taskId: string) => {
    set({ isLoading: true, error: null })
    try {
      const task = await analysisApi.getUnifiedTask(taskId)
      set({ currentTask: task, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to get task', isLoading: false })
    }
  },

  updateTask: async (taskId: string, request: AnalysisTaskRequest) => {
    set({ isLoading: true, error: null })
    try {
      await analysisApi.updateTask(taskId, request)
      // Reload tasks to get updated list
      await get().loadTasks()
      set({ isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to update task', isLoading: false })
      throw error
    }
  },

  deleteTask: async (taskId: string) => {
    set({ isLoading: true, error: null })
    try {
      await analysisApi.deleteUnifiedTask(taskId)
      // Remove from local state
      const { tasks } = get()
      set({ 
        tasks: tasks.filter(task => task.task_id !== taskId),
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to delete task', isLoading: false })
      throw error
    }
  },

  toggleTask: async (taskId: string) => {
    set({ isLoading: true, error: null })
    try {
      await analysisApi.toggleTask(taskId)
      // Reload tasks to get updated status
      await get().loadTasks()
      set({ isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to toggle task', isLoading: false })
      throw error
    }
  },

  runTaskNow: async (taskId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await analysisApi.runTaskNow(taskId)
      set({ isLoading: false })
      return response
    } catch (error: any) {
      set({ error: error.message || 'Failed to run task', isLoading: false })
      throw error
    }
  },

  getTaskProgress: async (taskId: string) => {
    try {
      const progress = await analysisApi.getTaskProgress(taskId)
      return progress
    } catch (error: any) {
      set({ error: error.message || 'Failed to get task progress' })
      throw error
    }
  },

  getBatchData: async (symbols: string[]) => {
    set({ isLoading: true, error: null })
    try {
      const data = await analysisApi.getBatchData(symbols)
      set({ isLoading: false })
      return data
    } catch (error: any) {
      set({ error: error.message || 'Failed to get batch data', isLoading: false })
      throw error
    }
  },

  // Utilities
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  clearError: () => set({ error: null }),
}))
