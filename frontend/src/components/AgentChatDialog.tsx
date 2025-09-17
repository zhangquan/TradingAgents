import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
// ScrollArea component not available, using div with overflow
import { Separator } from '@/components/ui/separator'
import { 
  MessageCircle, 
  Bot, 
  User, 
  Settings, 
  Activity,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  TrendingUp,
  Newspaper,
  Brain,
  Users,
  Target,
  DollarSign,
  X
} from 'lucide-react'
import { apiService, ChatMessage, ConversationDetail } from '@/lib/api'
import { toast } from 'sonner'
import { formatTimestamp } from '@/lib/utils'
import { MarkdownRenderer } from '@/components/MarkdownRenderer'

interface AgentChatDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  reportId?: string
  sessionId?: string
}

export function AgentChatDialog({ open, onOpenChange, reportId, sessionId }: AgentChatDialogProps) {
  const [conversationData, setConversationData] = useState<ConversationDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (open && sessionId) {
      loadConversationData()
    }
  }, [open, sessionId])

  const loadConversationData = async () => {
    if (!sessionId) return
    
    try {
      setLoading(true)
      const data = await apiService.restoreConversationSession(sessionId)
      setConversationData(data)
    } catch (error) {
      console.error('Failed to load conversation data:', error)
      toast.error('无法加载Agent对话数据')
    } finally {
      setLoading(false)
    }
  }

  const getAgentStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'in_progress':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getAgentStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50'
      case 'in_progress':
        return 'text-blue-600 bg-blue-50'
      case 'error':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getMessageIcon = (role: string) => {
    switch (role) {
      case 'user':
        return <User className="h-4 w-4 text-blue-500" />
      case 'assistant':
      case 'agent':
        return <Bot className="h-4 w-4 text-green-500" />
      case 'system':
        return <Settings className="h-4 w-4 text-gray-500" />
      default:
        return <MessageCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const getMessageTypeIcon = (messageType?: string) => {
    switch (messageType) {
      case 'reasoning':
        return <Brain className="h-3 w-3" />
      case 'tool_call':
        return <Settings className="h-3 w-3" />
      case 'report_update':
        return <TrendingUp className="h-3 w-3" />
      case 'status_change':
        return <Activity className="h-3 w-3" />
      default:
        return null
    }
  }

  // 使用统一的时间工具函数

  const renderAgentOverview = () => {
    if (!conversationData) return null

    const { session_info, agent_status, statistics } = conversationData

    return (
      <div className="space-y-6">
        {/* Session Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              分析会话信息
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">股票代码</div>
                <div className="font-medium">{session_info.ticker}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">分析日期</div>
                <div className="font-medium">{session_info.analysis_date}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">会话状态</div>
                <Badge className={getAgentStatusColor(session_info.status)}>
                  {session_info.status === 'completed' ? '已完成' : 
                   session_info.status === 'active' ? '进行中' : session_info.status}
                </Badge>
              </div>
              <div>
                <div className="text-sm text-gray-500">创建时间</div>
                <div className="font-medium text-sm">
                  {formatTimestamp(session_info.created_at)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Agent Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Agent执行状态
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(agent_status).map(([agentName, status]) => (
                <div key={agentName} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-2">
                    {getAgentStatusIcon(status)}
                    <span className="font-medium text-sm">{agentName}</span>
                  </div>
                  <Badge variant="outline" className={getAgentStatusColor(status)}>
                    {status === 'completed' ? '已完成' :
                     status === 'in_progress' ? '进行中' :
                     status === 'pending' ? '等待' :
                     status === 'error' ? '错误' : status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              会话统计
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">{statistics.total_messages}</div>
                <div className="text-sm text-gray-500">总消息数</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{statistics.total_tool_calls}</div>
                <div className="text-sm text-gray-500">工具调用</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">{statistics.completed_reports}</div>
                <div className="text-sm text-gray-500">完成报告</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderChatHistory = () => {
    if (!conversationData?.chat_history) return null

    return (
      <div className="h-[500px] overflow-y-auto pr-4">
        <div className="space-y-4">
          {conversationData.chat_history.map((message, index) => (
            <div key={message.message_id || index} className="flex gap-3">
              <div className="flex-shrink-0 mt-1">
                {getMessageIcon(message.role)}
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium capitalize">
                    {message.role === 'user' ? '用户' :
                     message.role === 'assistant' ? '助手' :
                     message.role === 'agent' ? message.agent_name || 'Agent' :
                     message.role === 'system' ? '系统' : message.role}
                  </span>
                  {message.message_type && (
                    <Badge variant="outline" className="text-xs flex items-center gap-1">
                      {getMessageTypeIcon(message.message_type)}
                      {message.message_type === 'reasoning' ? '推理' :
                       message.message_type === 'tool_call' ? '工具调用' :
                       message.message_type === 'report_update' ? '报告更新' :
                       message.message_type === 'status_change' ? '状态变更' : message.message_type}
                    </Badge>
                  )}
                  <span className="text-gray-400 text-xs">
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>
                <div className="text-sm bg-gray-50 rounded-lg p-3">
                  <MarkdownRenderer content={message.content} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderAnalysisReports = () => {
    if (!conversationData?.reports?.sections) return null

    const sections = conversationData.reports.sections

    return (
      <div className="space-y-4">
        {Object.entries(sections).map(([sectionKey, content]) => {
          if (!content) return null

          const getSectionTitle = (key: string) => {
            switch (key) {
              case 'market_report': return '市场分析'
              case 'sentiment_report': return '情绪分析'
              case 'news_report': return '新闻分析'
              case 'fundamentals_report': return '基本面分析'
              case 'investment_plan': return '投资计划'
              case 'trader_investment_plan': return '交易计划'
              case 'final_trade_decision': return '最终决策'
              default: return key
            }
          }

          const getSectionIcon = (key: string) => {
            switch (key) {
              case 'market_report': return <TrendingUp className="h-4 w-4" />
              case 'sentiment_report': return <Users className="h-4 w-4" />
              case 'news_report': return <Newspaper className="h-4 w-4" />
              case 'fundamentals_report': return <Brain className="h-4 w-4" />
              case 'investment_plan': return <Target className="h-4 w-4" />
              case 'trader_investment_plan': return <DollarSign className="h-4 w-4" />
              case 'final_trade_decision': return <CheckCircle className="h-4 w-4" />
              default: return <MessageCircle className="h-4 w-4" />
            }
          }

          return (
            <Card key={sectionKey}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  {getSectionIcon(sectionKey)}
                  {getSectionTitle(sectionKey)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <MarkdownRenderer content={content} />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    )
  }

  if (!sessionId) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              Agent对话
            </DialogTitle>
            <DialogDescription>
              无法找到与此报告关联的会话ID
            </DialogDescription>
          </DialogHeader>
          <div className="text-center py-8 text-gray-500">
            <MessageCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>此报告没有关联的Agent对话记录</p>
            <p className="text-sm">可能是旧版本的报告或分析过程中未启用对话记录</p>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[80vw] sm:max-w-none max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            Agent对话记录
          </DialogTitle>
          <DialogDescription>
            查看分析过程中的Agent交互和执行状态
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">加载对话数据...</span>
          </div>
        ) : (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                概览
              </TabsTrigger>
              <TabsTrigger value="chat" className="flex items-center gap-2">
                <MessageCircle className="h-4 w-4" />
                对话历史
              </TabsTrigger>
              <TabsTrigger value="reports" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                分析报告
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="mt-6">
              <div className="h-[60vh] overflow-y-auto pr-4">
                {renderAgentOverview()}
              </div>
            </TabsContent>

            <TabsContent value="chat" className="mt-6">
              {renderChatHistory()}
            </TabsContent>

            <TabsContent value="reports" className="mt-6">
              <div className="h-[60vh] overflow-y-auto pr-4">
                {renderAnalysisReports()}
              </div>
            </TabsContent>
          </Tabs>
        )}

        <div className="flex justify-between items-center pt-4 border-t">
          <Button variant="outline" onClick={loadConversationData} disabled={loading}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新数据
          </Button>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
