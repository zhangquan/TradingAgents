
import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  BarChart3, 
  FileText,
  RefreshCw,
  Brain,
  Play,
  Settings,
  Plus,
  Clock,
  ArrowLeft,
  MessageCircle
} from 'lucide-react'
import { apiService } from '@/lib/api'
import { Link } from 'react-router-dom'
import StockCharts from './StockCharts'
import { ReportDisplay } from './ReportDisplay'
import { AnalysisTaskDialog } from './AnalysisTaskDialog'
import { TaskManagementDialog } from './TaskManagementDialog'
import { HistoryReportsDialog } from './HistoryReportsDialog'
import { AgentChatDialog } from './AgentChatDialog'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

interface AnalysisReportData {
  report_id?: string
  analysis_id?: string
  ticker: string
  date: string
  title?: string
  sections: { [key: string]: string }
  status?: string
  created_at?: string
  updated_at?: string
  session_id?: string
}

interface AnalysisReport {
  reportData?: AnalysisReportData
  loading: boolean
  error?: string
}

interface StockDetailPanelProps {
  selectedStockSymbol: string | null
  currentDate: string
}

interface EmptyOrErrorStateProps {
  hasError: boolean
  errorMessage?: string
  stockSymbol: string
  onReload: () => void
  onHistoryReportSelect: (report: any) => void
}

function EmptyOrErrorState({ hasError, errorMessage, stockSymbol, onReload, onHistoryReportSelect }: EmptyOrErrorStateProps) {
  const icon = hasError ? FileText : Brain
  const title = hasError ? "加载失败" : "暂无分析报告"
  const description = hasError 
    ? errorMessage 
    : `点击下方按钮加载 ${stockSymbol} 的最新分析报告`
  const buttonText = hasError ? "重新加载" : "加载最新报告"

  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        {icon === FileText ? (
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        ) : (
          <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        )}
        <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-500 mb-4">{description}</p>
        <div className="flex flex-col sm:flex-row gap-2 justify-center items-center">
          <HistoryReportsDialog 
            initialTicker={stockSymbol}
            onReportSelect={onHistoryReportSelect}
            trigger={
              <Button variant="outline">
                <FileText className="h-4 w-4 mr-2" />
                查看历史报告
              </Button>
            }
          />
          <Button onClick={onReload}>
            {buttonText}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function StockDetailPanel({ 
  selectedStockSymbol, 
  currentDate 
}: StockDetailPanelProps) {
  const [analysisReport, setAnalysisReport] = useState<AnalysisReport>({ loading: false })
  const [rightPanelTab, setRightPanelTab] = useState<'charts' | 'analysis'>('analysis')
  const [isHistoryReport, setIsHistoryReport] = useState(false)
  
  // Analysis task dialog states
  const [analysisDialogOpen, setAnalysisDialogOpen] = useState(false)
  const [analysisDialogMode, setAnalysisDialogMode] = useState<'immediate' | 'scheduled' | 'edit'>('immediate')
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null)
  const [taskManagementDialogOpen, setTaskManagementDialogOpen] = useState(false)
  
  // Agent chat dialog states
  const [agentChatDialogOpen, setAgentChatDialogOpen] = useState(false)

  useEffect(() => {
    // 当选中的股票变化时，重置分析报告状态
    if (selectedStockSymbol) {
      setAnalysisReport({ loading: false })
      setRightPanelTab('analysis')
      setIsHistoryReport(false)
      // 自动加载分析报告
      loadAnalysisReport(selectedStockSymbol)
    }
  }, [selectedStockSymbol])

  const loadAnalysisReport = async (symbol: string) => {
    try {
      setAnalysisReport({ loading: true })
      
      // 首先尝试获取该股票的所有报告，然后选择最新的一个
      const reports = await apiService.getReportsByTicker(symbol, undefined, 1)
      
      if (reports && reports.length > 0) {
        const latestReport = reports[0]
        
        // 如果有report_id，使用新的API获取报告详情
        if (latestReport.report_id) {
          const reportData = await apiService.getReportById(latestReport.report_id) as AnalysisReportData
          console.log('通过 report_id 加载的报告数据:', reportData)
          
          // 验证报告数据格式
          if (!reportData || !reportData.sections || typeof reportData.sections !== 'object') {
            console.warn('报告数据格式异常:', reportData)
            setAnalysisReport({ 
              loading: false, 
              error: '报告数据格式异常' 
            })
            return
          }
          
          setAnalysisReport({ 
            reportData, 
            loading: false 
          })
        } else {
          // 否则使用旧的API方式
          const oldReportData = await apiService.getReport(latestReport.ticker, latestReport.date)
          console.log('通过 ticker/date 加载的报告数据:', oldReportData)
          
          // 验证旧格式报告数据并转换为新格式
          if (!oldReportData || !oldReportData.reports || typeof oldReportData.reports !== 'object') {
            console.warn('报告数据格式异常:', oldReportData)
            setAnalysisReport({ 
              loading: false, 
              error: '报告数据格式异常' 
            })
            return
          }
          
          // 转换旧格式到新格式
          const reportData: AnalysisReportData = {
            ticker: oldReportData.ticker,
            date: oldReportData.date,
            sections: oldReportData.reports,
            title: `${oldReportData.ticker} 分析报告`
          }
          
          setAnalysisReport({ 
            reportData, 
            loading: false 
          })
        }
      } else {
        // 如果没有找到报告，尝试使用当前日期查找
        try {
          const oldReportData = await apiService.getReport(symbol, currentDate)
          console.log('通过 currentDate 加载的报告数据:', oldReportData)
          
          // 验证旧格式报告数据并转换为新格式
          if (!oldReportData || !oldReportData.reports || typeof oldReportData.reports !== 'object') {
            console.warn('报告数据格式异常:', oldReportData)
            setAnalysisReport({ 
              loading: false, 
              error: '报告数据格式异常' 
            })
            return
          }
          
          // 转换旧格式到新格式
          const reportData: AnalysisReportData = {
            ticker: oldReportData.ticker,
            date: oldReportData.date,
            sections: oldReportData.reports,
            title: `${oldReportData.ticker} 分析报告`
          }
          
          setAnalysisReport({ 
            reportData, 
            loading: false 
          })
        } catch (fallbackError) {
          console.warn(`没有找到 ${symbol} 的分析报告`)
          setAnalysisReport({ 
            loading: false, 
            error: '暂无分析报告' 
          })
        }
      }
    } catch (error) {
      console.error(`加载 ${symbol} 分析报告失败:`, error)
      setAnalysisReport({ 
        loading: false, 
        error: '加载分析报告失败' 
      })
    }
  }



  const handleTaskCreated = (taskId: string) => {
    toast.success('分析任务已创建')
    // Optionally refresh reports after task creation
    if (selectedStockSymbol) {
      setTimeout(() => {
        loadAnalysisReport(selectedStockSymbol)
      }, 2000) // Wait a bit for the analysis to potentially complete
    }
  }

  const handleTaskUpdated = () => {
    toast.success('任务已更新')
    setEditingTaskId(null)
  }


  const handleOpenTaskManagement = () => {
    setTaskManagementDialogOpen(true)
  }

  const handleTaskManagementUpdated = () => {
    // 任务更新后可能需要刷新报告
    if (selectedStockSymbol) {
      setTimeout(() => {
        loadAnalysisReport(selectedStockSymbol)
      }, 1000)
    }
  }

  const formatReportTime = (dateStr: string) => {
    try {
      // 将UTC时间字符串转换为本地时间
      let date = new Date(dateStr)
      
      // 如果时间字符串没有时区信息，假设它是UTC时间
      if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
        date = new Date(dateStr + 'Z')
      }
      
      // 转换为本地时间并格式化
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
      })
    } catch {
      return dateStr
    }
  }

  const handleHistoryReportSelect = async (report: any) => {
    try {
      setAnalysisReport({ loading: true })
      setIsHistoryReport(true)
      
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
      
      setAnalysisReport({
        loading: false,
        reportData: reportData
      })
      
      // 切换到分析报告标签
      setRightPanelTab('analysis')
      
      toast.success(`已加载 ${report.ticker} 的历史报告`)
    } catch (error) {
      console.error('Failed to load history report:', error)
      setAnalysisReport({ 
        loading: false, 
        error: '加载历史报告失败' 
      })
      toast.error('加载历史报告失败')
    }
  }

  if (!selectedStockSymbol) {
    return (
      <Card className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">选择股票查看详情</h3>
          <p className="text-gray-500">
            从左侧列表中选择一支股票来查看详细的图表分析和报告
          </p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="flex-1 flex flex-col min-h-96 lg:min-h-0">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="min-w-0 flex-1">
            <CardTitle className="text-xl truncate">{selectedStockSymbol}</CardTitle>
            <CardDescription>详细分析和图表</CardDescription>
          </div>
          <Tabs value={rightPanelTab} onValueChange={(value) => {
            const tabValue = value as 'charts' | 'analysis'
            setRightPanelTab(tabValue)
            // 当切换到分析报告标签页时，如果还没有报告数据，则自动加载
            if (tabValue === 'analysis' && selectedStockSymbol && !analysisReport.reportData && !analysisReport.loading) {
              loadAnalysisReport(selectedStockSymbol)
            }
          }}>
            <TabsList className="grid w-48 grid-cols-2">
            <TabsTrigger value="analysis" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                <span className="hidden sm:inline">分析报告</span>
                <span className="sm:hidden">报告</span>
              </TabsTrigger>
              <TabsTrigger value="charts" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">图表分析</span>
                <span className="sm:hidden">图表</span>
              </TabsTrigger>
             
            </TabsList>
          </Tabs>
        </div>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 p-0 overflow-hidden">
        <Tabs value={rightPanelTab} className="h-full flex flex-col">
          <TabsContent value="charts" className="flex-1 min-h-0 m-0 overflow-hidden">
            <div className="h-full p-6 overflow-y-auto">
              <div className="min-h-full">
                <StockCharts
                  symbol={selectedStockSymbol}
                  currentDate={currentDate}
                  lookBackDays={30}
                />
              </div>
            </div>
          </TabsContent>
          <TabsContent value="analysis" className="flex-1 min-h-0 m-0 overflow-hidden">
            <div className="h-full overflow-y-auto">
              {analysisReport.loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
                    <p className="text-gray-600">加载分析报告中...</p>
                  </div>
                </div>
              ) : analysisReport.reportData?.sections && Object.keys(analysisReport.reportData.sections).length > 0 ? (
                <div className="h-full overflow-y-auto">
                  <div className="p-6 pb-4">
                    <div className="flex items-center justify-between mb-4">
                      {/* 左侧：历史报告按钮 */}
                      <div className="flex items-center gap-2">
                        <HistoryReportsDialog 
                          initialTicker={selectedStockSymbol}
                          onReportSelect={handleHistoryReportSelect}
                          trigger={
                            <Button
                              variant="outline"
                              size="sm"
                            >
                              <FileText className="h-4 w-4 mr-2" />
                              历史报告
                            </Button>
                          }
                        />
                      </div>
                      
                      {/* 右侧：其他操作按钮 */}
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleOpenTaskManagement}
                        >
                          <Settings className="h-4 w-4 mr-2" />
                          任务管理
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  {/* 报告信息展示区域 */}
                  {analysisReport.reportData && (
                    <div className={`mb-4 p-3 border rounded-lg ${
                      isHistoryReport 
                        ? 'bg-blue-50 border-blue-200' 
                        : 'bg-green-50 border-green-200'
                    }`}>
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                          <div className="flex items-center gap-2">
                            <Clock className={`h-4 w-4 ${
                              isHistoryReport ? 'text-blue-600' : 'text-green-600'
                            }`} />
                            <span className={`text-sm font-medium ${
                              isHistoryReport ? 'text-blue-800' : 'text-green-800'
                            }`}>
                              {isHistoryReport ? '正在查看历史报告' : '最新分析报告'}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 flex-wrap">
                            {analysisReport.reportData?.date && (
                              <Badge variant="outline" className={
                                isHistoryReport 
                                  ? 'text-blue-600 border-blue-300' 
                                  : 'text-green-600 border-green-300'
                              }>
                                {analysisReport.reportData.date}
                              </Badge>
                            )}
                            {analysisReport.reportData?.created_at && (
                              <span className={`text-xs ${
                                isHistoryReport ? 'text-blue-600' : 'text-green-600'
                              }`}>
                                生成于 {formatReportTime(analysisReport.reportData.created_at)}
                              </span>
                            )}

                            {/* Agent对话入口 */}
                            {analysisReport.reportData?.session_id && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setAgentChatDialogOpen(true)}
                                className="text-indigo-600 border-indigo-300 hover:bg-indigo-50"
                              >
                                <MessageCircle className="h-3 w-3 mr-1" />
                                Agent对话
                              </Button>
                            )}
                            
                          </div>
                        </div>
                        {isHistoryReport && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setIsHistoryReport(false)
                              if (selectedStockSymbol) {
                                loadAnalysisReport(selectedStockSymbol)
                              }
                            }}
                            className="text-blue-600 border-blue-300 hover:bg-blue-100"
                          >
                            <ArrowLeft className="h-4 w-4 mr-1" />
                            返回最新报告
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                  
                  <ReportDisplay 
                    reportData={analysisReport.reportData}
                    compact={true}
                    showHeader={false}
                    className="h-full"
                  />
                </div>
              ) : (
                <EmptyOrErrorState 
                  hasError={!!analysisReport.error}
                  errorMessage={analysisReport.error}
                  stockSymbol={selectedStockSymbol}
                  onReload={() => loadAnalysisReport(selectedStockSymbol)}
                  onHistoryReportSelect={handleHistoryReportSelect}
                />
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
      
      {/* Analysis Task Dialog */}
      {selectedStockSymbol && (
        <AnalysisTaskDialog
          open={analysisDialogOpen}
          onOpenChange={setAnalysisDialogOpen}
          ticker={selectedStockSymbol}
          mode={analysisDialogMode}
          taskId={editingTaskId || undefined}
          onTaskCreated={handleTaskCreated}
          onTaskUpdated={handleTaskUpdated}
        />
      )}


      {/* Task Management Dialog */}
      {selectedStockSymbol && (
        <TaskManagementDialog
          open={taskManagementDialogOpen}
          onOpenChange={setTaskManagementDialogOpen}
          ticker={selectedStockSymbol}
          onTaskUpdated={handleTaskManagementUpdated}
        />
      )}

      {/* Agent Chat Dialog */}
      {selectedStockSymbol && analysisReport.reportData?.session_id && (
        <AgentChatDialog
          open={agentChatDialogOpen}
          onOpenChange={setAgentChatDialogOpen}
          reportId={analysisReport.reportData.report_id}
          sessionId={analysisReport.reportData.session_id}
        />
      )}
    </Card>
  )
}
