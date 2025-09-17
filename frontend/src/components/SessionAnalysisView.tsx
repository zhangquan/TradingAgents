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
import { ConversationSession } from '@/lib/api'
import { AnalysisTaskDialog } from './AnalysisTaskDialog'
import { TaskManagementDialog } from './TaskManagementDialog'
import { HistoryConversationsDialog } from './HistoryConversationsDialog'
import { AgentConversationViewer } from './AgentConversationViewer'
import { toast } from 'sonner'
import { formatTimestamp, getConversationStatus } from '@/lib/utils'

interface SessionAnalysisViewProps {
  // 基本信息
  ticker: string
  sessionId?: string | null
  
  // 会话状态
  selectedConversation: ConversationSession | null
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
  selectedConversation,
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
      
      {/* 对话信息展示区域 */}
      {selectedConversation && (
        <div className={`mb-4 mx-6 p-3 border rounded-lg ${
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
                <span className={`text-sm ${
                  isHistoryConversation ? 'text-blue-600' : 'text-green-600'
                }`}>
                  {formatTimestamp(selectedConversation.created_at)}
                </span>

                {/* Session ID 显示 - 可选择性点击跳转到详情页 */}
                <Badge 
                  variant="outline" 
                  className={`text-xs ${showSessionBadgeNavigation ? 'cursor-pointer hover:bg-gray-100 transition-colors' : ''} flex items-center gap-1`}
                  onClick={showSessionBadgeNavigation ? handleSessionBadgeClick : undefined}
                  title={showSessionBadgeNavigation ? "点击查看Session详情" : undefined}
                >
                  Session: {selectedConversation.session_id.slice(0, 8)}...
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
              {showBackToLatestButton && isHistoryConversation && onBackToLatest && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onBackToLatest}
                  className="text-blue-600 border-blue-300 hover:bg-blue-100"
                >
                  <ArrowLeft className="h-4 w-4 mr-1" />
                  返回最新对话
                </Button>
              )}
              
              {onRefreshData && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRefreshData}
                  className={isHistoryConversation 
                    ? "text-blue-600 border-blue-300 hover:bg-blue-100"
                    : "text-green-600 border-green-300 hover:bg-green-100"
                  }
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  刷新数据
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Agent 对话内容 - 使用独立组件 */}
      <div className="px-6">
        <AgentConversationViewer 
          sessionId={sessionId || selectedConversation?.session_id}
        />
      </div>

      {/* Analysis Task Dialog */}
      {ticker && (
        <AnalysisTaskDialog
          open={analysisDialogOpen}
          onOpenChange={setAnalysisDialogOpen}
          ticker={ticker}
          mode={analysisDialogMode}
          taskId={editingTaskId || undefined}
          onTaskCreated={handleTaskCreated}
          onTaskUpdated={handleTaskUpdated}
        />
      )}

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
