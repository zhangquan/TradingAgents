import { api } from './index'

// Scheduler Types
export interface SchedulerStatus {
  is_running: boolean
  total_tasks: number
  enabled_tasks: number
  disabled_tasks: number
  jobs_in_scheduler: number
  uptime_seconds?: number
  last_health_check: string
}

export interface TaskExecutionInfo {
  task_id: string
  ticker: string
  analysts: string[]
  schedule_type: string
  schedule_time: string
  enabled: boolean
  last_run?: string
  next_run?: string
  execution_count: number
  last_error?: string
  avg_execution_time?: number
}

export interface JobStatus {
  job_id: string
  task_id: string
  ticker: string
  status: string
  started_at?: string
  finished_at?: string
  duration_seconds?: number
  error_message?: string
}

export interface SchedulerStatistics {
  total_jobs: number
  enabled_jobs: number
  disabled_jobs: number
  jobs_with_errors: number
  total_executions: number
  last_updated: string
  scheduler_running: boolean
}

export interface SchedulerStatisticsResponse {
  status: string
  message?: string
  data: SchedulerStatistics
}

export interface SchedulerRestartResponse {
  message: string
  status: string
  timestamp: string
}

export interface TaskDeleteResponse {
  message: string
  task_id: string
  timestamp: string
}

// Scheduler API Functions
export const schedulerApi = {
  // Get current scheduler status
  async getSchedulerStatus(): Promise<SchedulerStatus> {
    const response = await api.get('/scheduler/status')
    return response.data
  },

  // Restart the scheduler service
  async restartScheduler(): Promise<SchedulerRestartResponse> {
    const response = await api.post('/scheduler/restart')
    return response.data
  },

  // Get detailed scheduler statistics
  async getSchedulerStatistics(): Promise<SchedulerStatistics> {
    try {
      const response = await api.get('/scheduler/statistics')
      const responseData: SchedulerStatisticsResponse = response.data
      return responseData.data
    } catch (error) {
      console.error('Error fetching scheduler statistics:', error)
      // Return default statistics structure
      return {
        total_jobs: 0,
        enabled_jobs: 0,
        disabled_jobs: 0,
        jobs_with_errors: 0,
        total_executions: 0,
        last_updated: new Date().toISOString(),
        scheduler_running: false
      }
    }
  },

  // Get job list (renamed from task executions)
  async getJobList(): Promise<TaskExecutionInfo[]> {
    try {
      console.log('SchedulerAPI: Fetching job list from /scheduler/job-list')
      const response = await api.get('/scheduler/job-list')
      console.log('SchedulerAPI: Response status:', response.status)
      console.log('SchedulerAPI: Response data:', response.data)
      const data = response.data
      const result = Array.isArray(data) ? data : []
      console.log('SchedulerAPI: Returning job list:', result)
      return result
    } catch (error) {
      console.error('SchedulerAPI: Error fetching job list:', error)
      return []
    }
  },

  // Backward compatibility method
  async getTaskExecutions(): Promise<TaskExecutionInfo[]> {
    return this.getJobList()
  },

  // Get current job statuses (placeholder for future implementation)
  async getJobStatuses(): Promise<JobStatus[]> {
    // Note: This endpoint might not be implemented yet in the backend
    // For now, return empty array or implement when backend is ready
    return []
  },

  // Delete a scheduled task
  async deleteTask(taskId: string): Promise<TaskDeleteResponse> {
    const response = await api.delete(`/scheduler/tasks/${taskId}`)
    return response.data
  }
}
