
import { useEffect, useState, useCallback } from 'react'
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

import { ConversationSession } from '@/api/types'
import StockCharts from './StockCharts'
import { SessionAnalysisView } from './SessionAnalysisView'
import { toast } from 'sonner'

interface StockDetailPanelProps {
  selectedStockSymbol: string | null
  currentDate: string
  selectedSessionId?: string | null
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
  const [rightPanelTab, setRightPanelTab] = useState<'charts' | 'analysis'>('analysis')
  const [isHistoryConversation, setIsHistoryConversation] = useState(false)
  


  useEffect(() => {
    // 当选中的股票变化时，清除错误状态并切换到分析标签
    if (selectedStockSymbol) {
      setRightPanelTab('analysis')
      setIsHistoryConversation(false)
    }
  }, [selectedStockSymbol])

  // 监听 selectedSessionId 变化，设置历史对话状态
  useEffect(() => {
    if (selectedSessionId && selectedStockSymbol) {
      setIsHistoryConversation(true)
    } else if (!selectedSessionId && isHistoryConversation) {
      setIsHistoryConversation(false)
    }
  }, [selectedSessionId, selectedStockSymbol, isHistoryConversation])



  const handleHistoryConversationSelect = useCallback(async (conversation: ConversationSession) => {
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
  }, [selectedStockSymbol, navigate])

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
            {selectedSessionId ? (
              <SessionAnalysisView 
                ticker={selectedStockSymbol}
                sessionId={selectedSessionId}
                isHistoryConversation={isHistoryConversation}
                onHistoryConversationSelect={handleHistoryConversationSelect}
                onRefreshData={() => {
                  // Refresh handled by SessionAnalysisView
                  console.log('Refresh data requested')
                }}
                onBackToLatest={() => {
                  // 清除URL中的会话参数，返回到普通股票页面
                  if (selectedStockSymbol) {
                    navigate(`/stocks/${selectedStockSymbol}`, { replace: true })
                  }
                }}
               
                showBackToLatestButton={true}
                showSessionBadgeNavigation={true}
              />
            ) : (
              <EmptyOrErrorState 
                hasError={false}
                errorMessage={ undefined}
                stockSymbol={selectedStockSymbol}
                onReload={() => {
                
                }}
                onHistoryConversationSelect={handleHistoryConversationSelect}
              />
            )}
          </TabsContent>
        </Tabs>
      </CardContent>

    </Card>
  )
}
