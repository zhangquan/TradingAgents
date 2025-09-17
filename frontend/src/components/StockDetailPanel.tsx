
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  BarChart3, 
  MessageCircle,
  RefreshCw,
  Brain
} from 'lucide-react'
import { apiService, ConversationSession } from '@/lib/api'
import StockCharts from './StockCharts'
import { SessionAnalysisView } from './SessionAnalysisView'
import { toast } from 'sonner'

interface StockDetailPanelProps {
  selectedStockSymbol: string | null
  currentDate: string
  selectedSessionId?: string | null
}

interface ConversationState {
  conversations: ConversationSession[]
  selectedConversation: ConversationSession | null
  loading: boolean
  error?: string
}

interface EmptyOrErrorStateProps {
  hasError: boolean
  errorMessage?: string
  stockSymbol: string
  onReload: () => void
  onHistoryConversationSelect: (conversation: ConversationSession) => void
}

function EmptyOrErrorState({ hasError, errorMessage, stockSymbol, onReload, onHistoryConversationSelect }: EmptyOrErrorStateProps) {
  const icon = hasError ? MessageCircle : Brain
  const title = hasError ? "加载失败" : "暂无对话记录"
  const description = hasError 
    ? errorMessage 
    : `暂无 ${stockSymbol} 的分析对话记录，请创建新的分析任务`
  const buttonText = hasError ? "重新加载" : "加载对话记录"

  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        {icon === MessageCircle ? (
          <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        ) : (
          <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        )}
        <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-500 mb-4">{description}</p>
        <div className="flex justify-center">
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
  currentDate,
  selectedSessionId
}: StockDetailPanelProps) {
  const navigate = useNavigate()
  const [conversationState, setConversationState] = useState<ConversationState>({
    conversations: [],
    selectedConversation: null,
    loading: false
  })
  const [rightPanelTab, setRightPanelTab] = useState<'charts' | 'analysis'>('analysis')
  const [isHistoryConversation, setIsHistoryConversation] = useState(false)
  

  useEffect(() => {
    // 当选中的股票变化时，重置对话状态
    if (selectedStockSymbol) {
      setConversationState({
        conversations: [],
        selectedConversation: null,
        loading: false
      })
      setRightPanelTab('analysis')
      setIsHistoryConversation(false)
      // 自动加载对话记录
      loadConversations(selectedStockSymbol)
    }
  }, [selectedStockSymbol])

  // 监听 selectedSessionId 变化，加载对应的历史会话
  useEffect(() => {
    if (selectedSessionId && selectedStockSymbol) {
      loadHistoryConversation(selectedSessionId)
    } else if (!selectedSessionId && isHistoryConversation) {
      // 如果没有 sessionId 但当前显示的是历史会话，清除历史会话状态
      setIsHistoryConversation(false)
      setConversationState(prev => ({
        ...prev,
        selectedConversation: null
      }))
    }
  }, [selectedSessionId, selectedStockSymbol])

  const loadHistoryConversation = async (sessionId: string) => {
    try {
      setConversationState(prev => ({ ...prev, loading: true }))
      setIsHistoryConversation(true)
      
      // 从API加载具体的会话详情
      const conversationDetail = await apiService.restoreConversationSession(sessionId)
      
      // 构造ConversationSession对象
      const conversation: ConversationSession = {
        session_id: conversationDetail.session_info.session_id,
        user_id: 'demo_user',
        ticker: conversationDetail.session_info.ticker,
        analysis_date: conversationDetail.session_info.analysis_date,
        agent_status: conversationDetail.agent_status,
        is_finalized: conversationDetail.session_info.status === 'completed',
        created_at: conversationDetail.session_info.created_at,
        updated_at: conversationDetail.session_info.updated_at
      }
      
      setConversationState({
        conversations: [conversation],
        selectedConversation: conversation,
        loading: false
      })
      
      // 切换到分析标签
      setRightPanelTab('analysis')
      
      toast.success(`已加载历史对话 ${conversation.ticker}`)
    } catch (error) {
      console.error('Failed to load history conversation:', error)
      setConversationState(prev => ({ 
        ...prev,
        loading: false, 
        error: '加载历史记录失败' 
      }))
      toast.error('加载历史记录失败')
    }
  }

  const loadConversations = async (symbol: string) => {
    try {
      setConversationState(prev => ({ ...prev, loading: true }))
      
      // 获取用户的所有对话记录
      const conversations = await apiService.listUserConversations('demo_user', 50)
      
      // 筛选出与当前股票相关的对话记录
      const tickerConversations = conversations.filter(conv => 
        conv.ticker.toUpperCase() === symbol.toUpperCase()
      )
      
      if (tickerConversations.length > 0) {
        // 按创建时间排序，最新的在前面
        tickerConversations.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        
        // 选择最新的对话记录
        const latestConversation = tickerConversations[0]
        
        console.log(`找到 ${symbol} 的 ${tickerConversations.length} 条对话记录，选择最新的:`, latestConversation)
        
        setConversationState({
          conversations: tickerConversations,
          selectedConversation: latestConversation,
          loading: false
        })
      } else {
        console.log(`没有找到 ${symbol} 的对话记录`)
        setConversationState({
          conversations: [],
          selectedConversation: null,
          loading: false,
          error: '暂无对话记录'
        })
      }
    } catch (error) {
      console.error(`加载 ${symbol} 对话记录失败:`, error)
      setConversationState({
        conversations: [],
        selectedConversation: null,
        loading: false,
        error: '加载对话记录失败'
      })
    }
  }



  const handleTaskCreated = (taskId: string) => {
    // Optionally refresh conversations after task creation
    if (selectedStockSymbol) {
      setTimeout(() => {
        loadConversations(selectedStockSymbol)
      }, 2000) // Wait a bit for the analysis to potentially complete
    }
  }

  const handleTaskUpdated = () => {
    // Refresh conversations after task update
    if (selectedStockSymbol) {
      setTimeout(() => {
        loadConversations(selectedStockSymbol)
      }, 1000)
    }
  }

  const handleTaskManagementUpdated = () => {
    // 任务更新后可能需要刷新对话记录
    if (selectedStockSymbol) {
      setTimeout(() => {
        loadConversations(selectedStockSymbol)
      }, 1000)
    }
  }


  const handleHistoryConversationSelect = async (conversation: ConversationSession) => {
    try {
      // 在当前股票页面基础上添加会话参数
      if (selectedStockSymbol) {
        const sessionPath = `/stocks/${selectedStockSymbol}/session/${conversation.session_id}`
        navigate(sessionPath, { replace: true })
        toast.success(`已加载 ${conversation.ticker} 的历史对话`)
      } else {
        toast.error('无法加载历史对话：缺少股票符号')
      }
    } catch (error) {
      console.error('Failed to load history conversation:', error)
      toast.error('加载历史对话失败')
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
            // 当切换到分析对话标签页时，如果还没有对话数据，则自动加载
            if (tabValue === 'analysis' && selectedStockSymbol && !conversationState.selectedConversation && !conversationState.loading) {
              loadConversations(selectedStockSymbol)
            }
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
            {conversationState.loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
                  <p className="text-gray-600">加载对话记录中...</p>
                </div>
              </div>
            ) : conversationState.selectedConversation ? (
              <SessionAnalysisView 
                ticker={selectedStockSymbol}
                sessionId={selectedSessionId}
                selectedConversation={conversationState.selectedConversation}
                isHistoryConversation={isHistoryConversation}
                onHistoryConversationSelect={handleHistoryConversationSelect}
                onRefreshData={() => loadConversations(selectedStockSymbol)}
                onBackToLatest={() => {
                  // 清除URL中的会话参数，返回到普通股票页面
                  if (selectedStockSymbol) {
                    navigate(`/stocks/${selectedStockSymbol}`, { replace: true })
                  }
                }}
                onTaskCreated={handleTaskCreated}
                onTaskUpdated={handleTaskUpdated}
                onTaskManagementUpdated={handleTaskManagementUpdated}
                showBackToLatestButton={true}
                showSessionBadgeNavigation={true}
              />
            ) : (
              <EmptyOrErrorState 
                hasError={!!conversationState.error}
                errorMessage={conversationState.error}
                stockSymbol={selectedStockSymbol}
                onReload={() => loadConversations(selectedStockSymbol)}
                onHistoryConversationSelect={handleHistoryConversationSelect}
              />
            )}
          </TabsContent>
        </Tabs>
      </CardContent>

    </Card>
  )
}
