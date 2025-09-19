import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { 
  MessageCircle,
  BarChart3, 
  ArrowLeft,
  RefreshCw,
  Clock,
  AlertCircle,
  Loader2,
  Settings,
  Brain
} from 'lucide-react'
import { conversationApi } from '@/api/conversation'
import { ConversationSession, ConversationDetail } from '@/api/types'
import StockCharts from '@/components/StockCharts'
import { SessionAnalysisView } from '@/components/SessionAnalysisView'
import { toast } from 'sonner'
import { formatTimestamp, getConversationStatus } from '@/lib/utils'

interface SessionState {
  sessionInfo: ConversationSession | null
  sessionDetail: ConversationDetail | null
  loading: boolean
  error?: string
}

export default function SessionDetailPage() {
  const { sessionId, fromStock } = useParams<{ sessionId: string, fromStock?: string }>()
  const navigate = useNavigate()
  
  const [sessionState, setSessionState] = useState<SessionState>({
    sessionInfo: null,
    sessionDetail: null,
    loading: false
  })
  
  const [rightPanelTab, setRightPanelTab] = useState<'charts' | 'analysis'>('analysis')

  useEffect(() => {
    if (sessionId) {
      loadSessionData(sessionId)
    }
  }, [sessionId])

  const loadSessionData = async (sessionId: string) => {
    try {
      setSessionState(prev => ({ ...prev, loading: true, error: undefined }))
      
      // 获取完整的session详情，这个API包含了所有需要的信息
      const sessionDetail = await conversationApi.restoreConversationSession(sessionId)
      
      // 构造session info对象（从session detail中提取）
      const sessionInfo: ConversationSession = {
        session_id: sessionDetail.session_info.session_id,
        user_id: 'demo_user', // 从API中没有返回，使用默认值
        ticker: sessionDetail.session_info.ticker,
        analysis_date: sessionDetail.session_info.analysis_date,
        agent_status: sessionDetail.agent_status,
        is_finalized: sessionDetail.session_info.status === 'completed',
        created_at: sessionDetail.session_info.created_at,
        updated_at: sessionDetail.session_info.updated_at
      }
      
      setSessionState({
        sessionInfo,
        sessionDetail,
        loading: false
      })
      
    } catch (error) {
      console.error('加载Session数据失败:', error)
      setSessionState({
        sessionInfo: null,
        sessionDetail: null,
        loading: false,
        error: '加载Session数据失败，可能Session不存在或已被删除'
      })
      toast.error('加载Session数据失败')
    }
  }

  const handleTaskCreated = (taskId: string) => {
    // 可选择性地刷新session数据
    if (sessionId) {
      setTimeout(() => {
        loadSessionData(sessionId)
      }, 2000)
    }
  }

  const handleTaskUpdated = () => {
    // 任务更新后刷新session数据
    if (sessionId) {
      setTimeout(() => {
        loadSessionData(sessionId)
      }, 1000)
    }
  }

  const handleTaskManagementUpdated = () => {
    // 任务更新后可能需要刷新session数据
    if (sessionId) {
      setTimeout(() => {
        loadSessionData(sessionId)
      }, 1000)
    }
  }

  const handleHistoryConversationSelect = async (conversation: ConversationSession) => {
    // 导航到选中的对话session页面
    navigate(`/session/${conversation.session_id}`)
    toast.success(`已切换到 ${conversation.ticker} 的对话`)
  }

  // 如果没有sessionId，显示错误信息
  if (!sessionId) {
    return (
      <Card className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">无效的Session ID</h3>
          <p className="text-gray-500 mb-4">URL中缺少或包含无效的Session ID参数</p>
          <Button onClick={() => fromStock ? navigate(`/stocks/${fromStock}`) : navigate(-1)}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            {fromStock ? `返回到 ${fromStock}` : '返回上一页'}
          </Button>
        </div>
      </Card>
    )
  }

  // 如果正在加载，显示加载状态
  if (sessionState.loading) {
    return (
      <Card className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-blue-600" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">加载Session数据</h3>
          <p className="text-gray-500">正在获取Session详细信息...</p>
        </div>
      </Card>
    )
  }

  // 如果有错误，显示错误状态
  if (sessionState.error || !sessionState.sessionInfo) {
    return (
      <Card className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">加载失败</h3>
          <p className="text-gray-500 mb-4">
            {sessionState.error || 'Session数据不存在或已被删除'}
          </p>
          <div className="flex gap-2 justify-center">
            <Button variant="outline" onClick={() => fromStock ? navigate(`/stocks/${fromStock}`) : navigate(-1)}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              {fromStock ? `返回到 ${fromStock}` : '返回上一页'}
            </Button>
            <Button onClick={() => sessionId && loadSessionData(sessionId)}>
              <RefreshCw className="h-4 w-4 mr-2" />
              重新加载
            </Button>
          </div>
        </div>
      </Card>
    )
  }

  const { sessionInfo } = sessionState
  const currentDate = sessionInfo.analysis_date
  const selectedStockSymbol = sessionInfo.ticker

  return (
    <div className="space-y-6">
      {/* 页面标题和导航 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => fromStock ? navigate(`/stocks/${fromStock}`) : navigate(-1)}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            {fromStock ? `返回到 ${fromStock}` : '返回'}
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Session 详情</h1>
            <p className="text-gray-500">
              {selectedStockSymbol} · {formatTimestamp(sessionInfo.created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
         
        </div>
      </div>

      {/* 主要内容区域 */}
      <Card className="flex-1 flex flex-col min-h-96">
        <CardHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <CardTitle className="text-xl truncate">{selectedStockSymbol}</CardTitle>
              <CardDescription>
                Session分析详情 · {sessionInfo.analysis_date}
              </CardDescription>
            </div>
            <Tabs value={rightPanelTab} onValueChange={(value) => {
              const tabValue = value as 'charts' | 'analysis'
              setRightPanelTab(tabValue)
            }}>
              <TabsList className="grid w-48 grid-cols-2">
                <TabsTrigger value="analysis" className="flex items-center gap-2">
                  <MessageCircle className="h-4 w-4" />
                  <span className="hidden sm:inline">分析对话</span>
                  <span className="sm:hidden">对话</span>
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
              <SessionAnalysisView 
                ticker={selectedStockSymbol}
                sessionId={sessionId}
                selectedConversation={sessionInfo}
                isHistoryConversation={true}
                onHistoryConversationSelect={handleHistoryConversationSelect}
                onRefreshData={() => sessionId && loadSessionData(sessionId)}
                onTaskCreated={handleTaskCreated}
                onTaskUpdated={handleTaskUpdated}
                onTaskManagementUpdated={handleTaskManagementUpdated}
                showSessionBadgeNavigation={false}
                containerClassName=""
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
