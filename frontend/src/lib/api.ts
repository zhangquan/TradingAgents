import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for auth and language
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // Add browser language preference to headers
  const browserLanguage = navigator.language || navigator.languages?.[0] || 'en-US'
  config.headers['Accept-Language'] = browserLanguage
  
  return config
})

// Types
// AnalysisRequest removed - only scheduled tasks supported

export interface AnalysisConfig {
  llm_provider: string
  backend_url: string
  shallow_thinker: string
  deep_thinker: string
  research_depth: number
  analysts: string[]
}

export interface TaskResponse {
  task_id: string
  status: string
  message: string
}

export interface ScheduledAnalysisRequest {
  ticker: string
  analysts: string[]
  research_depth: number
  schedule_type: string  // 'once', 'daily', 'weekly', 'monthly', 'cron'
  schedule_time: string  // Time for execution (HH:MM format)
  schedule_date?: string  // Date for 'once' type (YYYY-MM-DD)
  cron_expression?: string  // For custom cron schedules
  timezone: string
  enabled: boolean
}

export interface ScheduledTaskResponse {
  task_id: string
  status: string
  message: string
  task_type: string
}

export interface ScheduledTaskInfo {
  task_id: string
  ticker: string
  analysts: string[]
  research_depth: number
  schedule_type: string
  schedule_time: string
  schedule_date?: string
  cron_expression?: string
  timezone: string
  enabled: boolean
  created_at: string
  last_run?: string
  execution_count: number
  last_error?: string
}

export interface UnifiedTaskInfo {
  task_id: string
  task_type: 'manual' | 'scheduled'
  status: string
  ticker?: string
  analysts?: string[]
  research_depth?: number
  created_at: string
  
  // Manual task specific fields
  analysis_date?: string
  request?: any
  completed_at?: string
  error?: string
  results?: any
  
  // Scheduled task specific fields
  schedule_type?: string
  schedule_time?: string
  schedule_date?: string
  cron_expression?: string
  timezone?: string
  enabled?: boolean
  last_run?: string
  execution_count?: number
  last_error?: string
}

export interface ConfigRequest {
  finnhub_api_key?: string
  openai_api_key?: string
  google_api_key?: string
  aliyun_api_key?: string
  polygon_api_key?: string
  reddit_client_id?: string
  reddit_client_secret?: string
}

export interface ReportResponse {
  ticker: string
  date: string
  reports: Record<string, string>
}

export interface AnalysisReportItem {
  report_id?: string
  analysis_id?: string
  ticker: string
  date: string
  report_type?: string
  title?: string
  content?: any
  status?: string
  reports?: string[]  // For backward compatibility
  created_at?: string
  updated_at?: string
  path?: string
  legacy?: boolean
  in_watchlist?: boolean
}

export interface TaskInfo {
  status: string
  created_at: string
  request: any // Generic request data
  results?: any
  error?: string
}

export interface UserInfo {
  user_id: string
  username: string
  email?: string
  created_at: string
  status: string
}


export interface NewsData {
  symbol: string
  timestamp: string
  news: Array<{
    title: string
    url: string
    published_at: string
    summary: string
    source: string
  }>
  count: number
}

export interface NotificationData {
  notification_id: string
  title: string
  message: string
  type: string
  read: boolean
  created_at: string
  data?: any
}

// Stock Data Types
export interface StockDataResponse {
  symbol: string
  period: string
  data: Array<{
    Date: string
    Open: number
    High: number
    Low: number
    Close: number
    Volume: number
  }>
  count: number
  generated_at: string
}

export interface StockSummary {
  symbol: string
  period: string
  data_range: {
    start_date: string
    end_date: string
    total_days: number
  }
  price_info: {
    current_price: number
    open_price: number
    high_price: number
    low_price: number
    price_change: number
    price_change_pct: number
  }
  volume_info: {
    latest_volume: number
    avg_volume: number
    volume_ratio: number
    total_volume: number
  }
  volatility: {
    daily_volatility: number
    annualized_volatility: number
  }
  generated_at: string
}

export interface NoDataError {
  error: string
  error_type: string
  symbol: string
  requested_period: string
  requested_date: string
  suggestions: string[]
  available_symbols: string[]
}

export interface TechnicalIndicatorResponse {
  symbol: string
  indicator: string
  description: string
  period: string
  data: Array<any>
  count: number
  generated_at: string
}

export interface MarketOverviewResponse {
  market_stats: {
    total_stocks: number
    avg_price: number
    avg_change_pct: number
    gainers: number
    losers: number
    total_volume: number
  }
  symbols: string[]
  date: string
  generated_at: string
}


// API functions
export const apiService = {
  // Health check
  async health() {
    const response = await api.get('/health')
    return response.data
  },

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

  async getAnalysisHistory(ticker?: string, limit: number = 50) {
    const params = new URLSearchParams()
    if (ticker) params.append('ticker', ticker)
    params.append('limit', limit.toString())
    
    const response = await api.get(`/analysis/history?${params}`)
    return response.data
  },

  async getAnalysis(analysisId: string) {
    const response = await api.get(`/analysis/${analysisId}`)
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

  // Reports
  async getReports(watchlistOnly: boolean = false, ticker?: string, reportType?: string, userId: string = 'demo_user') {
    const params = new URLSearchParams()
    params.append('watchlist_only', watchlistOnly.toString())
    params.append('user_id', userId)
    if (ticker) params.append('ticker', ticker)
    if (reportType) params.append('report_type', reportType)
    
    const response = await api.get(`/reports?${params}`)
    return response.data
  },

  async getReport(ticker: string, date: string): Promise<ReportResponse> {
    const response = await api.get(`/reports/${ticker}/${date}`)
    return response.data
  },

  async getReportById(reportId: string, userId: string = 'demo_user') {
    const response = await api.get(`/reports/report/${reportId}?user_id=${userId}`)
    return response.data
  },

  async getReportsByTicker(ticker: string, reportType?: string, limit: number = 50, userId: string = 'demo_user') {
    const params = new URLSearchParams()
    params.append('user_id', userId)
    if (reportType) params.append('report_type', reportType)
    params.append('limit', limit.toString())
    
    const response = await api.get(`/reports/ticker/${ticker}?${params}`)
    return response.data
  },

  async deleteReport(reportId: string, userId: string = 'demo_user') {
    const response = await api.delete(`/reports/${reportId}?user_id=${userId}`)
    return response.data
  },

  async deleteAnalysisReport(analysisId: string, userId: string = 'demo_user') {
    const response = await api.delete(`/reports/${analysisId}?user_id=${userId}`)
    return response.data
  },

  async deleteMultipleReports(reportIds: string[], userId: string = 'demo_user') {
    const response = await api.delete('/reports/batch/reports', {
      data: { report_ids: reportIds },
      params: { user_id: userId }
    })
    return response.data
  },

  async deleteMultipleAnalyses(analysisIds: string[], userId: string = 'demo_user') {
    const response = await api.delete('/reports/batch/analyses', {
      data: { analysis_ids: analysisIds },
      params: { user_id: userId }
    })
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



  // WebSocket connection for system updates (optional)
  createWebSocket(): WebSocket {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + `/ws`
    return new WebSocket(wsUrl)
  },

  // Stock Data API (new endpoints)
  async getAvailableStocks() {
    const response = await api.get('/api/stock/available-stocks')
    return response.data
  },

  async getStockData(symbol: string, currDate: string, lookBackDays: number = 30): Promise<StockDataResponse> {
    const response = await api.get(`/api/stock/data/${symbol}?curr_date=${currDate}&look_back_days=${lookBackDays}`)
    return response.data
  },

  async getStockSummary(symbol: string, currDate: string, lookBackDays: number = 30): Promise<StockSummary | NoDataError> {
    try {
      const response = await api.get(`/api/stock/summary/${symbol}?curr_date=${currDate}&look_back_days=${lookBackDays}`)
      return response.data
    } catch (error: any) {
      if (error.response?.status === 404 && error.response?.data) {
        // Return the enhanced error information
        return error.response.data as NoDataError
      }
      throw error
    }
  },

  async getTechnicalIndicator(symbol: string, indicator: string, currDate: string, lookBackDays: number = 100): Promise<TechnicalIndicatorResponse> {
    const response = await api.get(`/api/stock/indicator/${symbol}?indicator=${indicator}&curr_date=${currDate}&look_back_days=${lookBackDays}`)
    return response.data
  },

  async getMultipleIndicators(request: {
    symbol: string
    indicators: string[]
    curr_date: string
    look_back_days?: number
  }) {
    const response = await api.post('/api/stock/indicators/multiple', request)
    return response.data
  },

 



  async getStockHealthCheck() {
    const response = await api.get('/api/stock/health')
    return response.data
  },

  async getSupportedIndicators() {
    const response = await api.get('/api/stock/supported-indicators')
    return response.data
  },

  // Watchlist API
  async getWatchlist(userId: string = 'demo_user') {
    const response = await api.get(`/api/stock/watchlist?user_id=${userId}`)
    return response.data
  },

  async addToWatchlist(symbol: string, userId: string = 'demo_user') {
    const response = await api.post(`/api/stock/watchlist/add?user_id=${userId}`, {
      symbol: symbol
    })
    return response.data
  },

  async removeFromWatchlist(symbol: string, userId: string = 'demo_user') {
    const response = await api.delete(`/api/stock/watchlist/remove?symbol=${symbol}&user_id=${userId}`)
    return response.data
  },

  async updateWatchlist(symbols: string[], userId: string = 'demo_user') {
    const response = await api.put(`/api/stock/watchlist?user_id=${userId}`, {
      symbols: symbols
    })
    return response.data
  },

  async checkWatchlistStatus(symbol: string, userId: string = 'demo_user') {
    const response = await api.get(`/api/stock/watchlist/check/${symbol}?user_id=${userId}`)
    return response.data
  },

  // Market Overview API
  async getMarketOverview(symbols?: string[], currDate?: string): Promise<MarketOverviewResponse> {
    if (symbols && symbols.length > 0) {
      const response = await api.post('/api/stock/market-overview', {
        symbols: symbols,
        curr_date: currDate
      })
      return response.data
    } else {
      const params = new URLSearchParams()
      if (currDate) params.append('curr_date', currDate)
      
      const response = await api.get(`/api/stock/market-overview?${params}`)
      return response.data
    }
  },

  // Alias for backward compatibility
  async getMarketOverviewNew(symbols?: string[], currDate?: string): Promise<MarketOverviewResponse> {
    return this.getMarketOverview(symbols, currDate)
  },
}
