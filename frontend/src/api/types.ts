// Analysis and Task Types
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

export interface TasksByStockResponse {
  ticker: string
  tasks: UnifiedTaskInfo[]
  total_count: number
}

export interface TaskInfo {
  status: string
  created_at: string
  request: any // Generic request data
  results?: any
  error?: string
}

// Configuration Types
export interface ConfigRequest {
  finnhub_api_key?: string
  openai_api_key?: string
  google_api_key?: string
  aliyun_api_key?: string
  polygon_api_key?: string
  reddit_client_id?: string
  reddit_client_secret?: string
}

// Report Types
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
  execution_started_at?: string
  execution_completed_at?: string
  execution_duration_seconds?: number
  execution_duration_formatted?: string
  execution_type?: string  // manual, scheduled
}

// User Types
export interface UserInfo {
  user_id: string
  username: string
  email?: string
  created_at: string
  status: string
}

// Notification Types
export interface NotificationData {
  notification_id: string
  title: string
  message: string
  type: string
  read: boolean
  created_at: string
  data?: any
}

// News and Data Types
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

// Conversation Memory Types
export interface ConversationSession {
  session_id: string
  user_id: string
  ticker: string
  analysis_date: string
  agent_status: { [key: string]: string }
  is_finalized: boolean
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  message_id: string
  session_id: string
  timestamp: string
  role: 'user' | 'assistant' | 'system' | 'agent'
  content: string
  agent_name?: string
  message_type?: string
  metadata?: any
}

export interface ConversationDetail {
  session_info: {
    session_id: string
    ticker: string
    analysis_date: string
    execution_type: string
    status: string
    created_at: string
    updated_at: string
  }
  analysis_config: {
    analysts: string[]
    research_depth: number
    llm_config: any
  }
  agent_status: { [key: string]: string }
  current_agent?: string
  reports: {
    sections: { [key: string]: string }
    current_report?: string
    final_report?: string
  }
  final_results: {
    final_state?: any
    processed_signal?: any
  }
  chat_history: ChatMessage[]
  statistics: {
    total_messages: number
    total_tool_calls: number
    completed_reports: number
  }
}

export interface ConversationFullDetail {
  session_id: string
  user_id: string
  ticker: string
  analysis_date: string
  task_id?: string
  analysts: string[]
  research_depth: number
  llm_config: any
  agent_status: { [key: string]: string }
  current_agent?: string
  messages: any[]
  tool_calls: any[]
  report_sections: { [key: string]: any }
  current_report?: string
  final_report?: string
  final_state?: any
  processed_signal?: any
  execution_type: string
  last_interaction?: string
  is_finalized: boolean
  created_at: string
  updated_at: string
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
