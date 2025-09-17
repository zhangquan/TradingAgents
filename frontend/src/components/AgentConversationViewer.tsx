import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { 
  MessageCircle,
  Bot, 
  User, 
  Activity,
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
  Settings,
  Clock
} from 'lucide-react'
import { apiService, ConversationDetail } from '@/lib/api'
import { toast } from 'sonner'
import { formatTimestamp } from '@/lib/utils'
import { MarkdownRenderer } from './MarkdownRenderer'

interface AgentConversationViewerProps {
  sessionId?: string
  className?: string
}

export function AgentConversationViewer({ sessionId, className = '' }: AgentConversationViewerProps) {
  const [conversationData, setConversationData] = useState<ConversationDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('reports')
  const [activeReportTab, setActiveReportTab] = useState('')

  useEffect(() => {
    if (sessionId) {
      loadConversationData()
    } else {
      setConversationData(null)
    }
  }, [sessionId])

  // 当 conversationData 变化时，初始化 activeReportTab
  useEffect(() => {
    if (conversationData?.reports?.sections) {
      const availableSections = Object.entries(conversationData.reports.sections).filter(([_, content]) => content)
      if (availableSections.length > 0 && !activeReportTab) {
        setActiveReportTab(availableSections[0][0])
      }
    }
  }, [conversationData, activeReportTab])

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

  // Agent状态相关的辅助函数
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

  // 渲染Agent概览
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

  // 渲染聊天历史
  const renderChatHistory = () => {
    if (!conversationData?.chat_history) return null

    return (
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
    )
  }

  // 渲染分析报告
  const renderAnalysisReports = () => {
    if (!conversationData?.reports?.sections) return null

    const sections = conversationData.reports.sections
    const availableSections = Object.entries(sections).filter(([_, content]) => content)
    
    if (availableSections.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <TrendingUp className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>暂无分析报告数据</p>
        </div>
      )
    }

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

    // 如果只有一个报告，直接显示内容，不使用 tabs
    if (availableSections.length === 1) {
      const [sectionKey, content] = availableSections[0]
      return (
        <Card>
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
    }

    // 多个报告使用 tabs 展示
    // 确保 activeReportTab 有有效的默认值
    const currentActiveTab = activeReportTab && availableSections.some(([key]) => key === activeReportTab) 
      ? activeReportTab 
      : availableSections[0][0]

    return (
      <Tabs value={currentActiveTab} onValueChange={setActiveReportTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-1">
          {availableSections.map(([sectionKey]) => (
            <TabsTrigger
              key={sectionKey}
              value={sectionKey}
              className="flex items-center gap-1 text-xs px-2 py-1.5"
            >
              {getSectionIcon(sectionKey)}
              <span className="hidden sm:inline">{getSectionTitle(sectionKey)}</span>
              <span className="sm:hidden">{getSectionTitle(sectionKey).slice(0, 4)}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {availableSections.map(([sectionKey, content]) => (
          <TabsContent key={sectionKey} value={sectionKey} className="mt-4">
            <Card>
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
          </TabsContent>
        ))}
      </Tabs>
    )
  }

  // 如果没有sessionId，显示提示信息
  if (!sessionId) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        <MessageCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p>此报告没有关联的Agent对话记录</p>
        <p className="text-sm">可能是旧版本的报告或分析过程中未启用对话记录</p>
      </div>
    )
  }

  // 如果正在加载，显示加载状态
  if (loading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">加载Agent对话数据...</span>
      </div>
    )
  }

  // 如果没有数据，显示错误状态
  if (!conversationData) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        <MessageCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p>无法加载Agent对话数据</p>
        <p className="text-sm">可能是网络问题或数据暂时不可用</p>
        <Button 
          variant="outline" 
          className="mt-4"
          onClick={loadConversationData}
        >
          重试加载
        </Button>
      </div>
    )
  }

  // 渲染主要内容
  return (
    <div className={className}>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
     
        <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="reports" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            分析报告
          </TabsTrigger>
         
          <TabsTrigger value="chat" className="flex items-center gap-2">
            <MessageCircle className="h-4 w-4" />
            对话历史
          </TabsTrigger>
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            概览
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <div className="h-[60vh] overflow-y-auto pr-4">
            {renderAgentOverview()}
          </div>
        </TabsContent>

        <TabsContent value="chat" className="mt-6">
          <div className="h-[60vh] overflow-y-auto pr-4">
            {renderChatHistory()}
          </div>
        </TabsContent>

        <TabsContent value="reports" className="mt-6">
          <div className="h-[60vh] overflow-y-auto pr-4">
            {renderAnalysisReports()}
          </div>
        </TabsContent>

        <div className="flex justify-between items-center pt-4 border-t">
          <Button variant="outline" onClick={loadConversationData} disabled={loading}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新数据
          </Button>
        </div>
      </Tabs>
    </div>
  )
}
