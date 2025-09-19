import { api } from './index'

export const watchlistApi = {
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
}
