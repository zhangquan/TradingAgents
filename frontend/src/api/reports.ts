import { api } from './index'
import { ReportResponse } from './types'

export const reportsApi = {
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
}
