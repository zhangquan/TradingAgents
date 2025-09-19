import { create } from 'zustand'
import { reportsApi } from '../api/reports'
import { ReportResponse, AnalysisReportItem } from '../api/types'

interface ReportsState {
  // State
  reports: AnalysisReportItem[]
  currentReport: ReportResponse | null
  reportsByTicker: Record<string, AnalysisReportItem[]>
  isLoading: boolean
  error: string | null
  filters: {
    watchlistOnly: boolean
    ticker?: string
    reportType?: string
    userId: string
  }
  
  // Actions
  loadReports: (watchlistOnly?: boolean, ticker?: string, reportType?: string, userId?: string) => Promise<void>
  getReport: (ticker: string, date: string) => Promise<void>
  getReportById: (reportId: string, userId?: string) => Promise<AnalysisReportItem>
  getReportsByTicker: (ticker: string, reportType?: string, limit?: number, userId?: string) => Promise<void>
  deleteReport: (reportId: string, userId?: string) => Promise<void>
  deleteAnalysisReport: (analysisId: string, userId?: string) => Promise<void>
  deleteMultipleReports: (reportIds: string[], userId?: string) => Promise<void>
  deleteMultipleAnalyses: (analysisIds: string[], userId?: string) => Promise<void>
  
  // Filters and utilities
  setFilters: (filters: Partial<ReportsState['filters']>) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearReports: () => void
}

export const useReportsStore = create<ReportsState>((set, get) => ({
  // Initial state
  reports: [],
  currentReport: null,
  reportsByTicker: {},
  isLoading: false,
  error: null,
  filters: {
    watchlistOnly: false,
    userId: 'demo_user'
  },

  // Actions
  loadReports: async (watchlistOnly = false, ticker, reportType, userId = 'demo_user') => {
    set({ isLoading: true, error: null })
    try {
      const reports = await reportsApi.getReports(watchlistOnly, ticker, reportType, userId)
      set({ 
        reports: reports.reports || reports, 
        isLoading: false,
        filters: { ...get().filters, watchlistOnly, ticker, reportType, userId }
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load reports', isLoading: false })
    }
  },

  getReport: async (ticker: string, date: string) => {
    set({ isLoading: true, error: null })
    try {
      const report = await reportsApi.getReport(ticker, date)
      set({ currentReport: report, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to get report', isLoading: false })
    }
  },

  getReportById: async (reportId: string, userId = 'demo_user') => {
    set({ isLoading: true, error: null })
    try {
      const report = await reportsApi.getReportById(reportId, userId)
      set({ isLoading: false })
      return report
    } catch (error: any) {
      set({ error: error.message || 'Failed to get report by ID', isLoading: false })
      throw error
    }
  },

  getReportsByTicker: async (ticker: string, reportType, limit = 50, userId = 'demo_user') => {
    set({ isLoading: true, error: null })
    try {
      const reports = await reportsApi.getReportsByTicker(ticker, reportType, limit, userId)
      set({ 
        reportsByTicker: { 
          ...get().reportsByTicker, 
          [ticker]: reports.reports || reports 
        },
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to get reports by ticker', isLoading: false })
    }
  },

  deleteReport: async (reportId: string, userId = 'demo_user') => {
    set({ isLoading: true, error: null })
    try {
      await reportsApi.deleteReport(reportId, userId)
      // Remove from local state
      const { reports } = get()
      set({ 
        reports: reports.filter(report => report.report_id !== reportId),
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to delete report', isLoading: false })
      throw error
    }
  },

  deleteAnalysisReport: async (analysisId: string, userId = 'demo_user') => {
    set({ isLoading: true, error: null })
    try {
      await reportsApi.deleteAnalysisReport(analysisId, userId)
      // Remove from local state
      const { reports } = get()
      set({ 
        reports: reports.filter(report => report.analysis_id !== analysisId),
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to delete analysis report', isLoading: false })
      throw error
    }
  },

  deleteMultipleReports: async (reportIds: string[], userId = 'demo_user') => {
    set({ isLoading: true, error: null })
    try {
      await reportsApi.deleteMultipleReports(reportIds, userId)
      // Remove from local state
      const { reports } = get()
      set({ 
        reports: reports.filter(report => !reportIds.includes(report.report_id || '')),
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to delete multiple reports', isLoading: false })
      throw error
    }
  },

  deleteMultipleAnalyses: async (analysisIds: string[], userId = 'demo_user') => {
    set({ isLoading: true, error: null })
    try {
      await reportsApi.deleteMultipleAnalyses(analysisIds, userId)
      // Remove from local state
      const { reports } = get()
      set({ 
        reports: reports.filter(report => !analysisIds.includes(report.analysis_id || '')),
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to delete multiple analyses', isLoading: false })
      throw error
    }
  },

  // Filters and utilities
  setFilters: (filters) => {
    set({ filters: { ...get().filters, ...filters } })
  },

  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  clearError: () => set({ error: null }),
  clearReports: () => set({ reports: [], currentReport: null, reportsByTicker: {} }),
}))
