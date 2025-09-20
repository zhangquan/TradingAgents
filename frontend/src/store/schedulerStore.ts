import { create } from 'zustand'
import { schedulerApi, SchedulerStatus, TaskExecutionInfo, JobStatus, SchedulerStatistics, TaskDeleteResponse } from '../api/scheduler'

interface SchedulerState {
  // State
  status: SchedulerStatus | null
  statistics: SchedulerStatistics | null
  taskExecutions: TaskExecutionInfo[]
  jobStatuses: JobStatus[]
  isLoading: boolean
  error: string | null
  lastUpdated: string | null
  
  // Actions
  loadSchedulerStatus: () => Promise<void>
  loadSchedulerStatistics: () => Promise<void>
  loadTaskExecutions: () => Promise<void>
  loadJobStatuses: () => Promise<void>
  restartScheduler: () => Promise<void>
  refreshAll: () => Promise<void>
  deleteTask: (taskId: string) => Promise<void>
  
  // Utilities
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  
  // Backward compatibility (deprecated)
  metrics: SchedulerStatistics | null
  loadSchedulerMetrics: () => Promise<void>
}

export const useSchedulerStore = create<SchedulerState>((set, get) => ({
  // Initial state
  status: null,
  statistics: null,
  taskExecutions: [],
  jobStatuses: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  
  // Backward compatibility
  metrics: null,

  // Actions
  loadSchedulerStatus: async () => {
    set({ isLoading: true, error: null })
    try {
      const status = await schedulerApi.getSchedulerStatus()
      set({ 
        status, 
        isLoading: false,
        lastUpdated: new Date().toISOString()
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load scheduler status'
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      console.error('Error loading scheduler status:', error)
    }
  },

  loadSchedulerStatistics: async () => {
    try {
      const statistics = await schedulerApi.getSchedulerStatistics()
      set({ statistics, metrics: statistics }) // Set both for backward compatibility
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load scheduler statistics'
      set({ error: errorMessage })
      console.error('Error loading scheduler statistics:', error)
    }
  },

  // Backward compatibility method
  loadSchedulerMetrics: async () => {
    return get().loadSchedulerStatistics()
  },

  loadTaskExecutions: async () => {
    try {
      console.log('SchedulerStore: Loading task executions...')
      const taskExecutions = await schedulerApi.getTaskExecutions()
      console.log('SchedulerStore: Raw task executions response:', taskExecutions)
      const processedTasks = Array.isArray(taskExecutions) ? taskExecutions : []
      console.log('SchedulerStore: Processed task executions:', processedTasks)
      set({ taskExecutions: processedTasks })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load task executions'
      console.error('SchedulerStore: Error loading task executions:', error)
      set({ error: errorMessage, taskExecutions: [] })
    }
  },

  loadJobStatuses: async () => {
    try {
      const jobStatuses = await schedulerApi.getJobStatuses()
      set({ jobStatuses })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load job statuses'
      set({ error: errorMessage })
      console.error('Error loading job statuses:', error)
    }
  },

  restartScheduler: async () => {
    set({ isLoading: true, error: null })
    try {
      await schedulerApi.restartScheduler()
      
      // Reload status after restart
      await get().loadSchedulerStatus()
      
      set({ isLoading: false })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to restart scheduler'
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      console.error('Error restarting scheduler:', error)
      throw error
    }
  },

  refreshAll: async () => {
    set({ isLoading: true, error: null })
    try {
      await Promise.allSettled([
        get().loadSchedulerStatus(),
        get().loadSchedulerStatistics(),
        get().loadTaskExecutions(),
        get().loadJobStatuses()
      ])
      set({ 
        isLoading: false,
        lastUpdated: new Date().toISOString()
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to refresh scheduler data'
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      console.error('Error refreshing scheduler data:', error)
    }
  },

  deleteTask: async (taskId: string) => {
    set({ isLoading: true, error: null })
    try {
      await schedulerApi.deleteTask(taskId)
      
      // Remove task from local state
      set(state => ({
        taskExecutions: state.taskExecutions.filter(task => task.task_id !== taskId),
        isLoading: false
      }))
      
      // Refresh status to get updated counts
      await get().loadSchedulerStatus()
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete task'
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      console.error('Error deleting task:', error)
      throw error
    }
  },

  // Utilities
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  
  setError: (error: string | null) => set({ error }),
  
  clearError: () => set({ error: null })
}))
