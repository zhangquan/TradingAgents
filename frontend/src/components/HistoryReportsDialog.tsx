

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  History, 
  FileText, 
  Calendar, 
  Filter, 
  Star, 
  Eye,
  AlertCircle,
  CheckCircle2,
  Clock,
  FolderOpen,
  Search,
  X,
  ArrowLeft
} from 'lucide-react'
import { apiService, AnalysisReportItem } from '@/lib/api'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { ReportDisplay } from './ReportDisplay'

interface HistoryReportsDialogProps {
  trigger?: React.ReactNode
  initialTicker?: string
  onReportSelect?: (report: AnalysisReportItem) => void
}

export function HistoryReportsDialog({ 
  trigger, 
  initialTicker = '',
  onReportSelect
}: HistoryReportsDialogProps) {
  const [open, setOpen] = useState(false)
  const [reports, setReports] = useState<AnalysisReportItem[]>([])
  const [selectedReport, setSelectedReport] = useState<AnalysisReportItem | null>(null)
  const [selectedReportData, setSelectedReportData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [loadingReport, setLoadingReport] = useState(false)
  const [showWatchlistOnly, setShowWatchlistOnly] = useState(false)
  const [tickerFilter, setTickerFilter] = useState<string>(initialTicker)
  const [reportTypeFilter, setReportTypeFilter] = useState<string>('')

  const loadReports = async () => {
    try {
      setLoading(true)
      const data = await apiService.getReports(
        showWatchlistOnly, 
        tickerFilter || undefined, 
        reportTypeFilter && reportTypeFilter !== 'all' ? reportTypeFilter : undefined
      )
      
      // Sort reports by creation time (newest first)
      data.sort((a: AnalysisReportItem, b: AnalysisReportItem) => (b.created_at || '').localeCompare(a.created_at || ''))
      setReports(data)
    } catch (error) {
      console.error('Failed to load reports:', error)
      toast.error("加载历史报告失败")
    } finally {
      setLoading(false)
    }
  }

  const loadReportData = async (report: AnalysisReportItem) => {
    try {
      setLoadingReport(true)
      
      let reportData
      if (report.report_id) {
        reportData = await apiService.getReportById(report.report_id)
      } else {
        // Fallback to legacy format
        reportData = await apiService.getReport(report.ticker, report.date)
      }
      
      // Transform legacy format to new format if needed
      if (reportData.reports && typeof reportData.reports === 'object') {
        reportData.sections = reportData.reports
      }
      
      setSelectedReportData(reportData)
      onReportSelect?.(report)
    } catch (error) {
      console.error('Failed to load report data:', error)
      toast.error("加载报告详情失败")
    } finally {
      setLoadingReport(false)
    }
  }

  useEffect(() => {
    if (open) {
      loadReports()
    }
  }, [open, showWatchlistOnly, tickerFilter, reportTypeFilter])

  const formatDate = (dateStr: string) => {
    try {
      // 将UTC时间字符串转换为本地时间
      let date = new Date(dateStr)
      
      // 如果时间字符串没有时区信息，假设它是UTC时间
      if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
        date = new Date(dateStr + 'Z')
      }
      
      return formatDistanceToNow(date, { addSuffix: true, locale: zhCN })
    } catch {
      return dateStr
    }
  }

  const formatFullDate = (dateStr: string) => {
    try {
      // 将UTC时间字符串转换为本地时间
      let date = new Date(dateStr)
      
      // 如果时间字符串没有时区信息，假设它是UTC时间
      if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
        date = new Date(dateStr + 'Z')
      }
      
      // 转换为本地时间并格式化
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
      })
    } catch {
      return dateStr
    }
  }

  const getTotalReports = () => reports.length
  const getWatchlistCount = () => reports.filter(r => r.in_watchlist).length

  const handleReportSelect = (report: AnalysisReportItem) => {
    if (onReportSelect) {
      // If callback is provided, use it and close dialog
      onReportSelect(report)
      setOpen(false)
    } else {
      // Otherwise, show report in dialog
      setSelectedReport(report)
      loadReportData(report)
    }
  }

  const handleBackToList = () => {
    setSelectedReport(null)
    setSelectedReportData(null)
  }

  const defaultTrigger = (
    <Button variant="outline" className="flex items-center gap-2">
      <History className="h-4 w-4" />
      历史报告
    </Button>
  )

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || defaultTrigger}
      </DialogTrigger>
      <DialogContent className="w-[80vw] sm:max-w-none max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-2">
            {selectedReport && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBackToList}
                className="mr-2"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            )}
            <History className="h-5 w-5" />
            {selectedReport ? `${selectedReport.ticker} - 报告详情` : '历史报告'}
          </DialogTitle>
          <DialogDescription>
            {selectedReport ? '查看完整的分析报告内容' : '浏览和查看您的历史分析报告'}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          {selectedReport && selectedReportData ? (
            // Show selected report content
            <div className="h-full overflow-y-auto">
              <div className="pr-4">
                {loadingReport ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="text-gray-500">加载报告中...</div>
                  </div>
                ) : (
                  <ReportDisplay 
                    reportData={selectedReportData}
                    showHeader={true}
                    compact={false}
                  />
                )}
              </div>
            </div>
          ) : (
            // Show reports list
            <div className="space-y-4 h-full flex flex-col">
              {/* 筛选和操作区域 */}
              <div className="flex-shrink-0 space-y-4 border-b pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Button
                      variant={showWatchlistOnly ? "default" : "outline"}
                      size="sm"
                      onClick={() => setShowWatchlistOnly(!showWatchlistOnly)}
                      className="flex items-center gap-2"
                    >
                      <Filter className="h-4 w-4" />
                      {showWatchlistOnly ? "显示全部" : "仅关注股票"}
                    </Button>
                  </div>
                  
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <div className="flex items-center gap-1">
                      <FileText className="h-4 w-4" />
                      报告: {getTotalReports()}
                    </div>
                    <div className="flex items-center gap-1">
                      <Star className="h-4 w-4" />
                      关注: {getWatchlistCount()}
                    </div>
                  </div>
                </div>
                
                {/* 高级筛选 */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Search className="h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="按股票代码筛选..."
                      value={tickerFilter}
                      onChange={(e) => setTickerFilter(e.target.value)}
                      className="w-48"
                    />
                    {tickerFilter && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setTickerFilter('')}
                        className="p-1 h-auto"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                  
                  <Select value={reportTypeFilter} onValueChange={setReportTypeFilter}>
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="报告类型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">所有类型</SelectItem>
                      <SelectItem value="market_report">市场报告</SelectItem>
                      <SelectItem value="investment_plan">投资计划</SelectItem>
                      <SelectItem value="final_trade_decision">交易决策</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  {(tickerFilter || (reportTypeFilter && reportTypeFilter !== 'all')) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setTickerFilter('')
                        setReportTypeFilter('')
                      }}
                      className="flex items-center gap-2"
                    >
                      <X className="h-4 w-4" />
                      清除筛选
                    </Button>
                  )}
                </div>
              </div>

              {/* 报告列表 */}
              <div className="flex-1 overflow-hidden">
                <div className="h-full overflow-y-auto">
                  <div className="pr-4">
                    {loading ? (
                      <div className="flex items-center justify-center h-32">
                        <div className="text-gray-500">加载中...</div>
                      </div>
                    ) : reports.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <FolderOpen className="h-12 w-12 mx-auto mb-3 opacity-50" />
                        <p>暂无历史报告</p>
                        <p className="text-sm">
                          {showWatchlistOnly ? "您关注的股票还没有分析报告" : "还没有任何分析报告"}
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {reports.map((report) => (
                          <Card 
                            key={report.report_id || report.analysis_id || `${report.ticker}-${report.date}`}
                            className="cursor-pointer hover:bg-gray-50 transition-colors"
                            onClick={() => handleReportSelect(report)}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-start justify-between">
                                <div className="flex-1 space-y-2">
                                  <div className="flex items-center gap-2">
                                    <h3 className="text-lg font-semibold flex items-center gap-2">
                                      {report.ticker}
                                      {report.in_watchlist && (
                                        <Star className="h-4 w-4 text-yellow-500 fill-current" />
                                      )}
                                    </h3>
                                    <Badge variant="outline">
                                      {report.report_type === 'market_report' ? '市场分析' :
                                       report.report_type === 'investment_plan' ? '投资计划' :
                                       report.report_type === 'final_trade_decision' ? '交易决策' :
                                       report.report_type || '分析报告'}
                                    </Badge>
                                    {report.legacy && (
                                      <Badge variant="secondary" className="text-xs">
                                        旧版
                                      </Badge>
                                    )}
                                  </div>
                                  
                                  <div className="flex items-center gap-4 text-sm text-gray-600">
                                    <div className="flex items-center gap-2">
                                      <Calendar className="h-4 w-4" />
                                      {report.date}
                                    </div>
                                    {report.created_at && (
                                      <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4" />
                                        {formatDate(report.created_at)}
                                      </div>
                                    )}
                                    {report.status && (
                                      <div className="flex items-center gap-2">
                                        {report.status === 'generated' ? (
                                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                                        ) : (
                                          <AlertCircle className="h-4 w-4 text-yellow-500" />
                                        )}
                                        {report.status === 'generated' ? '已生成' : report.status}
                                      </div>
                                    )}
                                  </div>
                                  
                                  {report.title && (
                                    <div className="text-sm text-gray-700 font-medium">
                                      {report.title}
                                    </div>
                                  )}
                                </div>
                                
                                <div className="flex items-center">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="flex items-center gap-1"
                                  >
                                    <Eye className="h-4 w-4" />
                                    查看
                                  </Button>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
