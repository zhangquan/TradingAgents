
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Trash2, 
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
  X
} from 'lucide-react'
import { apiService, AnalysisReportItem } from '@/lib/api'
import { toast } from 'sonner'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { Link } from 'react-router-dom'


interface AnalysisReportsManagerProps {
  initialTicker?: string
}

export function AnalysisReportsManager({ initialTicker = '' }: AnalysisReportsManagerProps) {
  const [reports, setReports] = useState<AnalysisReportItem[]>([])
  const [selectedReports, setSelectedReports] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [showWatchlistOnly, setShowWatchlistOnly] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedReport, setSelectedReport] = useState<AnalysisReportItem | null>(null)
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
      toast.error("加载分析报告失败")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReports()
  }, [showWatchlistOnly, tickerFilter, reportTypeFilter])

  const handleSelectReport = (reportId: string, checked: boolean) => {
    const newSelected = new Set(selectedReports)
    if (checked) {
      newSelected.add(reportId)
    } else {
      newSelected.delete(reportId)
    }
    setSelectedReports(newSelected)
  }


  const handleDeleteSelected = async () => {
    if (selectedReports.size === 0) return

    try {
      setDeleting(true)
      
      // Separate report IDs, analysis IDs and legacy reports
      const reportIds: string[] = []
      const analysisIds: string[] = []
      const legacyReports: AnalysisReportItem[] = []
      
      selectedReports.forEach(reportId => {
        const report = reports.find(r => getReportId(r) === reportId)
        if (report) {
          if (report.legacy) {
            legacyReports.push(report)
          } else if (report.report_id) {
            reportIds.push(report.report_id)
          } else if (report.analysis_id) {
            analysisIds.push(report.analysis_id)
          }
        }
      })

      let deletedCount = 0
      
      // Delete new reports by report_id
      if (reportIds.length > 0) {
        await apiService.deleteMultipleReports(reportIds)
        deletedCount += reportIds.length
      }
      
      // Delete old reports by analysis_id (backward compatibility)
      if (analysisIds.length > 0) {
        await apiService.deleteMultipleAnalyses(analysisIds)
        deletedCount += analysisIds.length
      }

      // Note: Legacy reports can't be deleted through API for now
      if (legacyReports.length > 0) {
        toast.warning(`${legacyReports.length} 个旧版报告无法通过此功能删除`)
      }

      setSelectedReports(new Set())
      await loadReports()
      toast.success(`成功删除 ${deletedCount} 个分析报告`)
    } catch (error) {
      console.error('Failed to delete reports:', error)
      toast.error("删除分析报告失败")
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteSingle = async (report: AnalysisReportItem) => {
    if (report.legacy) {
      toast.warning("旧版报告无法通过此功能删除")
      return
    }

    try {
      setDeleting(true)
      
      if (report.report_id) {
        await apiService.deleteReport(report.report_id)
      } else if (report.analysis_id) {
        await apiService.deleteAnalysisReport(report.analysis_id)
      } else {
        throw new Error("无效的报告ID")
      }
      
      await loadReports()
      toast.success("分析报告已删除")
      setDeleteDialogOpen(false)
      setSelectedReport(null)
    } catch (error) {
      console.error('Failed to delete report:', error)
      toast.error("删除分析报告失败")
    } finally {
      setDeleting(false)
    }
  }

  
  const getReportViewUrl = (report: AnalysisReportItem) => {
    // Use report_id if available (new format), otherwise fall back to legacy format
    if (report.report_id) {
      return `/reports/${report.report_id}`
    }
    // Fallback to legacy format for backward compatibility
    return `/reports/${report.ticker}/${report.date}`
  }

  const getReportId = (report: AnalysisReportItem) => {
    return report.report_id || report.analysis_id || `${report.ticker}-${report.date}`
  }

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
  const getSelectedCount = () => selectedReports.size
  const getWatchlistCount = () => reports.filter(r => r.in_watchlist).length

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>分析报告管理</CardTitle>
          <CardDescription>管理您的股票分析报告</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="text-gray-500">加载中...</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            分析报告管理
          </CardTitle>
          <CardDescription>
            管理您的股票分析报告，支持按关注股票筛选和批量删除
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 筛选和操作区域 */}
          <div className="space-y-4">
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
                
                {selectedReports.size > 0 && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleDeleteSelected}
                    disabled={deleting}
                    className="flex items-center gap-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    删除选中 ({selectedReports.size})
                  </Button>
                )}
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

          {reports.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FolderOpen className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>暂无分析报告</p>
              <p className="text-sm">
                {showWatchlistOnly ? "您关注的股票还没有分析报告" : "还没有任何分析报告"}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {reports.map((report) => (
                <div key={getReportId(report)} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <Checkbox
                        checked={selectedReports.has(getReportId(report))}
                        onCheckedChange={(checked) => 
                          handleSelectReport(getReportId(report), checked as boolean)
                        }
                        className="mt-1"
                      />
                      <div className="flex-1 space-y-3">
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
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4" />
                                {formatDate(report.created_at)}
                              </div>
                              <div className="text-xs text-gray-500 ml-6">
                                {formatFullDate(report.created_at)}
                              </div>
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
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Link to={getReportViewUrl(report)}>
                        <Button
                          variant="default"
                          size="sm"
                          className="flex items-center gap-1"
                        >
                          <Eye className="h-4 w-4" />
                          查看报告
                        </Button>
                      </Link>
                      {!report.legacy && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedReport(report)
                            setDeleteDialogOpen(true)
                          }}
                          className="flex items-center gap-1"
                        >
                          <Trash2 className="h-4 w-4" />
                          删除
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 提示信息 */}
          {reports.some(r => r.legacy) && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                注意：标记为"旧版"的报告存储在文件系统中，暂不支持通过此界面删除
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              您确定要删除此分析报告吗？此操作无法撤销。
            </DialogDescription>
          </DialogHeader>
          
          {selectedReport && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="font-medium">{selectedReport.ticker}</div>
              <div className="text-sm text-gray-600">{selectedReport.date}</div>
              {selectedReport.title && (
                <div className="text-sm text-gray-700 mt-1 font-medium">{selectedReport.title}</div>
              )}
              <div className="text-sm text-gray-500 mt-1">
                {selectedReport.report_type ? (
                  `报告类型: ${selectedReport.report_type}`
                ) : (
                  `包含: ${(selectedReport.reports || []).join(', ')}`
                )}
              </div>
              {selectedReport.status && (
                <div className="text-sm text-gray-500 mt-1">
                  状态: {selectedReport.status === 'generated' ? '已生成' : selectedReport.status}
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() => selectedReport && handleDeleteSingle(selectedReport)}
              disabled={deleting}
            >
              {deleting ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
