import { api } from './index'
import { 
  ScheduledAnalysisRequest, 
  ScheduledTaskResponse, 
  ScheduledTaskInfo, 
  UnifiedTaskInfo, 
  TaskInfo,
  TasksByStockResponse
} from './types'

export const analysisApi = {
  // Analysis config
  async getAnalysisConfig() {
    const response = await api.get('/analysis/config')
    return response.data
  },

  // Get all tasks (only scheduled now)
  async getAllTasks() {
    const response = await api.get('/analysis/tasks')
    return response.data
  },

  // Get tasks by stock symbol
  async getTasksByStock(stockSymbol: string, limit: number = 50): Promise<TasksByStockResponse> {
    const response = await api.get(`/analysis/tasks/by-stock/${stockSymbol}?limit=${limit}`)
    return response.data
  },

  async getUnifiedTask(taskId: string): Promise<UnifiedTaskInfo> {
    const response = await api.get(`/analysis/tasks/${taskId}`)
    return response.data
  },

  async deleteUnifiedTask(taskId: string) {
    const response = await api.delete(`/analysis/tasks/${taskId}`)
    return response.data
  },

  async getTaskStatus(taskId: string): Promise<TaskInfo> {
    const response = await api.get(`/analysis/tasks/${taskId}`)
    return response.data
  },

  async deleteTask(taskId: string) {
    const response = await api.delete(`/analysis/tasks/${taskId}`)
    return response.data
  },

  // Task API (only scheduled tasks now)
  async createTask(request: ScheduledAnalysisRequest): Promise<ScheduledTaskResponse> {
    const response = await api.post('/analysis/tasks', request)
    return response.data
  },

  async getTasks() {
    const response = await api.get('/analysis/tasks')
    return response.data
  },

  async getTask(taskId: string): Promise<ScheduledTaskInfo> {
    const response = await api.get(`/analysis/tasks/${taskId}`)
    return response.data
  },

  async toggleTask(taskId: string) {
    const response = await api.put(`/analysis/tasks/${taskId}/toggle`)
    return response.data
  },

  async deleteScheduledTask(taskId: string) {
    const response = await api.delete(`/analysis/tasks/${taskId}`)
    return response.data
  },

  async updateTask(taskId: string, request: ScheduledAnalysisRequest) {
    const response = await api.put(`/analysis/tasks/${taskId}`, request)
    return response.data
  },

  async runTaskNow(taskId: string) {
    const response = await api.post(`/analysis/tasks/${taskId}/run-now`)
    return response.data
  },

  // Task monitoring with enhanced real-time features
  async getTaskProgress(taskId: string) {
    const response = await api.get(`/analysis/tasks/${taskId}`)
    return response.data
  },

  async getBatchData(symbols: string[]) {
    const response = await api.post('/data/batch', symbols)
    return response.data
  },
}
