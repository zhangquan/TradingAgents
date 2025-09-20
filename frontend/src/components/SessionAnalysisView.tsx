import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  MessageCircle,
  RefreshCw,
  Settings,
  Clock,
  ArrowLeft,
  ExternalLink
} from 'lucide-react'
import { ConversationSession } from '@/api/types'

import { TaskManagementDialog } from './TaskManagementDialog'
import { HistoryConversationsDialog } from './HistoryConversationsDialog'
import { AgentConversationViewer } from './AgentConversationViewer'
import { useConversationStore } from '@/store/conversationStore'
import { toast } from 'sonner'
import { formatTimestamp, getConversationStatus } from '@/lib/utils'

interface SessionAnalysisViewProps {
  // 基本信息
  ticker: string
  sessionId?: string | null
  
  // 会话状态
  isHistoryConversation?: boolean
  
  // 回调函数
  onHistoryConversationSelect: (conversation: ConversationSession) => void
  onRefreshData?: () => void
  onBackToLatest?: () => void
  
  // 任务管理相关回调
  onTaskCreated?: (taskId: string) => void
  onTaskUpdated?: () => void
  onTaskManagementUpdated?: () => void
  
  // 可选配置
  showBackToLatestButton?: boolean
  showSessionBadgeNavigation?: boolean
  containerClassName?: string
}

export function SessionAnalysisView({
  ticker,
  sessionId,
  isHistoryConversation = false,
  onHistoryConversationSelect,
  onRefreshData,
  onBackToLatest,
  onTaskCreated,
  onTaskUpdated,
  onTaskManagementUpdated,
  showBackToLatestButton = false,
  showSessionBadgeNavigation = true,
  containerClassName = "mx-6"
}: SessionAnalysisViewProps) {
  const navigate = useNavigate()
  
  // Get conversation data from store
  const {
    currentSession,
    userId
  } = useConversationStore()
  
  // Derive selectedConversation from currentSession
  const selectedConversation = currentSession ? {
    session_id: currentSession.session_info.session_id,
    user_id: userId,
    ticker: currentSession.session_info.ticker,
    analysis_date: currentSession.session_info.analysis_date,
    agent_status: currentSession.agent_status,
    is_finalized: currentSession.session_info.status === 'completed',
    created_at: currentSession.session_info.created_at,
    updated_at: currentSession.session_info.updated_at
  } as ConversationSession : null
  
  // Analysis task dialog states
  const [analysisDialogOpen, setAnalysisDialogOpen] = useState(false)
  const [analysisDialogMode, setAnalysisDialogMode] = useState<'immediate' | 'scheduled' | 'edit'>('immediate')
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null)
  const [taskManagementDialogOpen, setTaskManagementDialogOpen] = useState(false)

  const handleTaskCreated = (taskId: string) => {
    toast.success('分析任务已创建')
    onTaskCreated?.(taskId)
  }

  const handleTaskUpdated = () => {
    toast.success('任务已更新')
    setEditingTaskId(null)
    onTaskUpdated?.()
  }

  const handleOpenTaskManagement = () => {
    setTaskManagementDialogOpen(true)
  }

  const handleTaskManagementUpdated = () => {
    onTaskManagementUpdated?.()
  }

  const handleSessionBadgeClick = () => {
    if (selectedConversation && showSessionBadgeNavigation) {
      const sessionPath = ticker 
        ? `/session/${selectedConversation.session_id}/from/${ticker}`
        : `/session/${selectedConversation.session_id}`
      navigate(sessionPath)
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className={`p-6 pb-4 ${containerClassName}`}>
        <div className="flex items-center justify-between mb-4">
          {/* 左侧：历史记录按钮 */}
          <div className="flex items-center gap-2">
               {/* 对话信息展示区域 */}
      {selectedConversation && (
        <div className={`p-1 border rounded-lg ${
          isHistoryConversation 
            ? 'bg-blue-50 border-blue-200' 
            : 'bg-green-50 border-green-200'
        }`}>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <div className="flex items-center gap-2">
                <Clock className={`h-4 w-4 ${
                  isHistoryConversation ? 'text-blue-600' : 'text-green-600'
                }`} />
                <span className={`text-sm font-medium ${
                  isHistoryConversation ? 'text-blue-800' : 'text-green-800'
                }`}>
                  {isHistoryConversation ? '正在查看历史对话' : '最新分析对话'}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
               

                {/* Session ID 显示 - 可选择性点击跳转到详情页 */}
                <Badge 
                  variant="outline" 
                  className={`text-xs ${showSessionBadgeNavigation ? 'cursor-pointer hover:bg-gray-100 transition-colors' : ''} flex items-center gap-1`}
                  onClick={showSessionBadgeNavigation ? handleSessionBadgeClick : undefined}
                  title={showSessionBadgeNavigation ? "点击查看Session详情" : undefined}
                >
                
                  {showSessionBadgeNavigation && <ExternalLink className="h-3 w-3" />}
                </Badge>
                
                {/* 状态显示 */}
                <Badge variant="outline" className="text-xs">
                  {(() => {
                    const status = getConversationStatus(
                      selectedConversation.agent_status, 
                      selectedConversation.is_finalized
                    )
                    return status === 'completed' ? '已完成' : 
                           status === 'active' ? '进行中' : 
                           status === 'error' ? '错误' :
                           status === 'pending' ? '等待中' : status
                  })()}
                </Badge>
              </div>
            </div>
            
            {/* 右侧操作按钮 */}
            <div className="flex items-center gap-2">
              
           
            </div>
          </div>
        </div>
      )}
          </div>
          
          {/* 右侧：其他操作按钮 */}
          <div className="flex items-center gap-2">
          <HistoryConversationsDialog 
              initialTicker={ticker}
              currentStock={ticker}
              onConversationSelect={onHistoryConversationSelect}
              trigger={
                <Button
                  variant="outline"
                  size="sm"
                >
                  <MessageCircle className="h-4 w-4 mr-2" />
                  历史对话
                </Button>
              }
            />
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
      
     
      
      {/* Agent 对话内容 - 使用独立组件 */}
      <div className="px-6">
        <AgentConversationViewer 
          sessionId={sessionId || selectedConversation?.session_id}
        />
      </div>

     

      {/* Task Management Dialog */}
      {ticker && (
        <TaskManagementDialog
          open={taskManagementDialogOpen}
          onOpenChange={setTaskManagementDialogOpen}
          ticker={ticker}
          onTaskUpdated={handleTaskManagementUpdated}
        />
      )}
    </div>
  )
}
