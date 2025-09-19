import { create } from 'zustand'
import { watchlistApi } from '../api/watchlist'

interface WatchlistState {
  // State
  symbols: string[]
  symbolStatus: Record<string, boolean>
  isLoading: boolean
  error: string | null
  userId: string
  
  // Actions
  loadWatchlist: (userId?: string) => Promise<void>
  addToWatchlist: (symbol: string, userId?: string) => Promise<void>
  removeFromWatchlist: (symbol: string, userId?: string) => Promise<void>
  updateWatchlist: (symbols: string[], userId?: string) => Promise<void>
  checkSymbolStatus: (symbol: string, userId?: string) => Promise<boolean>
  toggleSymbol: (symbol: string, userId?: string) => Promise<void>
  
  // Utilities
  setUserId: (userId: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  isInWatchlist: (symbol: string) => boolean
}

export const useWatchlistStore = create<WatchlistState>((set, get) => ({
  // Initial state
  symbols: [],
  symbolStatus: {},
  isLoading: false,
  error: null,
  userId: 'demo_user',

  // Actions
  loadWatchlist: async (userId = 'demo_user') => {
    set({ isLoading: true, error: null, userId })
    try {
      const response = await watchlistApi.getWatchlist(userId)
      // The API returns "watchlist" field, not "symbols"
      const symbols = response.watchlist || []
      
      // Update symbol status
      const symbolStatus: Record<string, boolean> = {}
      symbols.forEach((symbol: string) => {
        symbolStatus[symbol] = true
      })
      
      set({ symbols, symbolStatus, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load watchlist', isLoading: false })
    }
  },

  addToWatchlist: async (symbol: string, userId) => {
    const currentUserId = userId || get().userId
    set({ isLoading: true, error: null })
    try {
      await watchlistApi.addToWatchlist(symbol, currentUserId)
      
      // Update local state
      const { symbols, symbolStatus } = get()
      if (!symbols.includes(symbol)) {
        set({ 
          symbols: [...symbols, symbol],
          symbolStatus: { ...symbolStatus, [symbol]: true },
          isLoading: false 
        })
      } else {
        set({ isLoading: false })
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to add to watchlist', isLoading: false })
      throw error
    }
  },

  removeFromWatchlist: async (symbol: string, userId) => {
    const currentUserId = userId || get().userId
    set({ isLoading: true, error: null })
    try {
      await watchlistApi.removeFromWatchlist(symbol, currentUserId)
      
      // Update local state
      const { symbols, symbolStatus } = get()
      set({ 
        symbols: symbols.filter(s => s !== symbol),
        symbolStatus: { ...symbolStatus, [symbol]: false },
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to remove from watchlist', isLoading: false })
      throw error
    }
  },

  updateWatchlist: async (symbols: string[], userId) => {
    const currentUserId = userId || get().userId
    set({ isLoading: true, error: null })
    try {
      await watchlistApi.updateWatchlist(symbols, currentUserId)
      
      // Update local state
      const symbolStatus: Record<string, boolean> = {}
      symbols.forEach(symbol => {
        symbolStatus[symbol] = true
      })
      
      set({ symbols, symbolStatus, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to update watchlist', isLoading: false })
      throw error
    }
  },

  checkSymbolStatus: async (symbol: string, userId) => {
    const currentUserId = userId || get().userId
    try {
      const response = await watchlistApi.checkWatchlistStatus(symbol, currentUserId)
      const isInWatchlist = response.in_watchlist || false
      
      // Update local status
      const { symbolStatus } = get()
      set({ 
        symbolStatus: { ...symbolStatus, [symbol]: isInWatchlist }
      })
      
      return isInWatchlist
    } catch (error: any) {
      set({ error: error.message || 'Failed to check symbol status' })
      return false
    }
  },

  toggleSymbol: async (symbol: string, userId) => {
    const { symbols } = get()
    const isCurrentlyInWatchlist = symbols.includes(symbol)
    
    if (isCurrentlyInWatchlist) {
      await get().removeFromWatchlist(symbol, userId)
    } else {
      await get().addToWatchlist(symbol, userId)
    }
  },

  // Utilities
  setUserId: (userId: string) => set({ userId }),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  clearError: () => set({ error: null }),
  isInWatchlist: (symbol: string) => {
    const { symbols } = get()
    return symbols.includes(symbol)
  },
}))
