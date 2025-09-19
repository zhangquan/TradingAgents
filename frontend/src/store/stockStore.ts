import { create } from 'zustand'
import { stockApi } from '../api/stock'
import { 
  StockDataResponse, 
  StockSummary, 
  NoDataError, 
  TechnicalIndicatorResponse, 
  MarketOverviewResponse 
} from '../api/types'

interface StockState {
  // State
  availableStocks: string[]
  stockData: Record<string, StockDataResponse>
  stockSummaries: Record<string, StockSummary | NoDataError>
  technicalIndicators: Record<string, TechnicalIndicatorResponse[]>
  marketOverview: MarketOverviewResponse | null
  supportedIndicators: string[]
  isLoading: boolean
  error: string | null
  
  // Actions
  loadAvailableStocks: () => Promise<void>
  getStockData: (symbol: string, currDate: string, lookBackDays?: number) => Promise<void>
  getStockSummary: (symbol: string, currDate: string, lookBackDays?: number) => Promise<void>
  getTechnicalIndicator: (symbol: string, indicator: string, currDate: string, lookBackDays?: number) => Promise<void>
  getMultipleIndicators: (request: {
    symbol: string
    indicators: string[]
    curr_date: string
    look_back_days?: number
  }) => Promise<any>
  loadSupportedIndicators: () => Promise<void>
  getMarketOverview: (symbols?: string[], currDate?: string) => Promise<void>
  getStockHealthCheck: () => Promise<any>
  
  // Utilities
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearStockData: (symbol?: string) => void
}

export const useStockStore = create<StockState>((set, get) => ({
  // Initial state
  availableStocks: [],
  stockData: {},
  stockSummaries: {},
  technicalIndicators: {},
  marketOverview: null,
  supportedIndicators: [],
  isLoading: false,
  error: null,

  // Actions
  loadAvailableStocks: async () => {
    set({ isLoading: true, error: null })
    try {
      const stocks = await stockApi.getAvailableStocks()
      // The API returns "stocks" field, not "symbols"
      set({ availableStocks: stocks.stocks || [], isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load available stocks', isLoading: false })
    }
  },

  getStockData: async (symbol: string, currDate: string, lookBackDays = 30) => {
    set({ isLoading: true, error: null })
    try {
      const data = await stockApi.getStockData(symbol, currDate, lookBackDays)
      set({ 
        stockData: { ...get().stockData, [symbol]: data },
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to get stock data', isLoading: false })
    }
  },

  getStockSummary: async (symbol: string, currDate: string, lookBackDays = 30) => {
    set({ isLoading: true, error: null })
    try {
      const summary = await stockApi.getStockSummary(symbol, currDate, lookBackDays)
      set({ 
        stockSummaries: { ...get().stockSummaries, [symbol]: summary },
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to get stock summary', isLoading: false })
    }
  },

  getTechnicalIndicator: async (symbol: string, indicator: string, currDate: string, lookBackDays = 100) => {
    set({ isLoading: true, error: null })
    try {
      const data = await stockApi.getTechnicalIndicator(symbol, indicator, currDate, lookBackDays)
      const key = `${symbol}_${indicator}`
      const existing = get().technicalIndicators[key] || []
      set({ 
        technicalIndicators: { 
          ...get().technicalIndicators, 
          [key]: [...existing.filter(item => item.indicator !== indicator), data]
        },
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to get technical indicator', isLoading: false })
    }
  },

  getMultipleIndicators: async (request) => {
    set({ isLoading: true, error: null })
    try {
      const data = await stockApi.getMultipleIndicators(request)
      const key = `${request.symbol}_multiple`
      set({ 
        technicalIndicators: { 
          ...get().technicalIndicators, 
          [key]: data.indicators || data
        },
        isLoading: false 
      })
      return data
    } catch (error: any) {
      set({ error: error.message || 'Failed to get multiple indicators', isLoading: false })
      throw error
    }
  },

  loadSupportedIndicators: async () => {
    try {
      const indicators = await stockApi.getSupportedIndicators()
      // Ensure we handle the response structure correctly
      set({ supportedIndicators: indicators.indicators || [] })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load supported indicators' })
    }
  },

  getMarketOverview: async (symbols, currDate) => {
    set({ isLoading: true, error: null })
    try {
      const overview = await stockApi.getMarketOverview(symbols, currDate)
      set({ marketOverview: overview, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to get market overview', isLoading: false })
    }
  },

  getStockHealthCheck: async () => {
    try {
      const health = await stockApi.getStockHealthCheck()
      return health
    } catch (error: any) {
      set({ error: error.message || 'Failed to get stock health check' })
      throw error
    }
  },

  // Utilities
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  clearError: () => set({ error: null }),
  clearStockData: (symbol?: string) => {
    if (symbol) {
      const { stockData, stockSummaries, technicalIndicators } = get()
      const newStockData = { ...stockData }
      const newSummaries = { ...stockSummaries }
      const newIndicators = { ...technicalIndicators }
      
      delete newStockData[symbol]
      delete newSummaries[symbol]
      
      // Remove technical indicators for this symbol
      Object.keys(newIndicators).forEach(key => {
        if (key.startsWith(`${symbol}_`)) {
          delete newIndicators[key]
        }
      })
      
      set({ stockData: newStockData, stockSummaries: newSummaries, technicalIndicators: newIndicators })
    } else {
      set({ stockData: {}, stockSummaries: {}, technicalIndicators: {} })
    }
  },
}))
