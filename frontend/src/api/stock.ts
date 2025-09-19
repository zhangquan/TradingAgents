import { api } from './index'
import { 
  StockDataResponse, 
  StockSummary, 
  NoDataError, 
  TechnicalIndicatorResponse, 
  MarketOverviewResponse 
} from './types'

export const stockApi = {
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
