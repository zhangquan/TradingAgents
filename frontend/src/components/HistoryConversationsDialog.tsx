import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { 
  History, 
  MessageCircle, 
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
  ArrowLeft,
  ExternalLink
} from 'lucide-react'
import { useConversationStore } from '@/store/conversationStore'
import { ConversationSession } from '@/api/types'
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
import { formatTimestamp, getConversationStatus } from '@/lib/utils'

interface HistoryConversationsDialogProps {
  trigger?: React.ReactNode
  initialTicker?: string
  onConversationSelect?: (conversation: ConversationSession) => void
  currentStock?: string  // 当前查看的股票，用于路由连续性
}

export function HistoryConversationsDialog({ 
  trigger, 
  initialTicker = '',
  onConversationSelect,
  currentStock
}: HistoryConversationsDialogProps) {
  const navigate = useNavigate()
  
  // Use conversation store
  const { 
    sessions,
    isLoading,
    error,
    userId,
    loadUserSessions,
    clearError
  } = useConversationStore()

  const [open, setOpen] = useState(false)
  const [tickerFilter, setTickerFilter] = useState<string>(initialTicker)
  const [selectedConversation, setSelectedConversation] = useState<ConversationSession | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'detail'>('list')

  // Filter sessions based on ticker filter
  const filteredConversations = React.useMemo(() => {
    let filtered = sessions
    if (tickerFilter) {
      filtered = sessions.filter(conv => 
        conv.ticker.toUpperCase().includes(tickerFilter.toUpperCase())
      )
    }
    
    // Sort by creation time, newest first
    return filtered.sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  }, [sessions, tickerFilter])

  // Show error toast when store error changes
  useEffect(() => {
    if (error) {
      toast.error('加载对话历史失败: ' + error)
      clearError()
    }
  }, [error, clearError])

  const loadConversations = async () => {
    try {
      await loadUserSessions(userId, 100)
    } catch (error) {
      console.error('Failed to load conversations:', error)
      // Error is already handled by the store and useEffect above
    }
  }

  useEffect(() => {
    if (open) {
      loadConversations()
    }
  }, [open, tickerFilter])

  const handleConversationSelect = (conversation: ConversationSession) => {
    if (onConversationSelect) {
      onConversationSelect(conversation)
      setOpen(false)
    } else {
      setSelectedConversation(conversation)
      setViewMode('detail')
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      let date = new Date(dateStr)
      
      if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
        date = new Date(dateStr + 'Z')
      }
      
      return formatDistanceToNow(date, { addSuffix: true, locale: zhCN })
    } catch {
      return dateStr
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50'
      case 'active':
        return 'text-blue-600 bg-blue-50'
      case 'error':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'active':
        return <Clock className="h-4 w-4 text-blue-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getConversationDisplayStatus = (conversation: ConversationSession) => {
    const status = getConversationStatus(conversation.agent_status, conversation.is_finalized)
    return {
      status,
      displayText: status === 'completed' ? '已完成' : 
                   status === 'active' ? '进行中' :
                   status === 'error' ? '错误' :
                   status === 'pending' ? '等待中' : status
    }
  }

  const renderConversationsList = () => (
    <div className="space-y-4">
      {/* 筛选区域 */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 flex-1">
          <Search className="h-4 w-4 text-gray-400" />
          <Input
            placeholder="按股票代码筛选..."
            value={tickerFilter}
            onChange={(e) => setTickerFilter(e.target.value)}
            className="flex-1"
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
        <Button 
          variant="outline" 
          size="sm" 
          onClick={loadConversations}
          disabled={isLoading}
        >
          刷新
        </Button>
      </div>

      <Separator />

      {/* 对话列表 */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">加载中...</div>
      ) : filteredConversations.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FolderOpen className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>暂无对话记录</p>
          <p className="text-sm">
            {tickerFilter ? `没有找到 ${tickerFilter} 相关的对话记录` : "还没有任何对话记录"}
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {filteredConversations.map((conversation) => {
            const statusInfo = getConversationDisplayStatus(conversation)
            return (
              <div 
                key={conversation.session_id} 
                className="border rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                onClick={() => handleConversationSelect(conversation)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold flex items-center gap-2">
                        {conversation.ticker}
                      </h3>
                      <Badge variant="outline" className={getStatusColor(statusInfo.status)}>
                        {statusInfo.displayText}
                      </Badge>
                    </div>
                  
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      {conversation.analysis_date}
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      {formatDate(conversation.created_at)}
                    </div>
                  </div>
                  
                  <div className="text-xs">
                    <Badge 
                      variant="outline" 
                      className="text-xs cursor-pointer hover:bg-gray-100 transition-colors flex items-center gap-1"
                      onClick={(e) => {
                        e.stopPropagation()
                        // 如果有当前股票上下文，则包含在路由中
                        const sessionPath = currentStock 
                          ? `/session/${conversation.session_id}/from/${currentStock}`
                          : `/session/${conversation.session_id}`
                        navigate(sessionPath)
                        setOpen(false)
                      }}
                      title="点击查看Session详情"
                    >
                      Session: {conversation.session_id.slice(0, 8)}...
                      <ExternalLink className="h-3 w-3" />
                    </Badge>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  {getStatusIcon(statusInfo.status)}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleConversationSelect(conversation)
                    }}
                    className="flex items-center gap-1"
                  >
                    <Eye className="h-4 w-4" />
                    查看对话
                  </Button>
                </div>
              </div>
            </div>
          )
        })}
        </div>
      )}
    </div>
  )

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline">
            <History className="h-4 w-4 mr-2" />
            对话历史
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <MessageCircle className="h-5 w-5" />
                {viewMode === 'list' ? '对话历史' : '对话详情'}
              </DialogTitle>
              <DialogDescription>
                {viewMode === 'list' 
                  ? '查看和选择历史分析对话记录'
                  : `查看 ${selectedConversation?.ticker} 的对话详情`
                }
              </DialogDescription>
            </div>
            {viewMode === 'detail' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setViewMode('list')
                  setSelectedConversation(null)
                }}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回列表
              </Button>
            )}
          </div>
        </DialogHeader>
        
        <div className="flex-1 overflow-hidden">
          {viewMode === 'list' ? renderConversationsList() : (
            <div className="h-full">
              {selectedConversation && (
                <Card>
                  <CardHeader>
                    <CardTitle>对话详情</CardTitle>
                    <CardDescription>
                      {selectedConversation.ticker} - {selectedConversation.analysis_date}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-sm text-gray-500">股票代码</div>
                          <div className="font-medium">{selectedConversation.ticker}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-500">分析日期</div>
                          <div className="font-medium">{selectedConversation.analysis_date}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-500">状态</div>
                          {(() => {
                            const statusInfo = getConversationDisplayStatus(selectedConversation)
                            return (
                              <Badge className={getStatusColor(statusInfo.status)}>
                                {statusInfo.displayText}
                              </Badge>
                            )
                          })()}
                        </div>
                        <div>
                          <div className="text-sm text-gray-500">创建时间</div>
                          <div className="font-medium text-sm">
                            {formatTimestamp(selectedConversation.created_at)}
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-sm text-gray-500">Session ID</div>
                        <div className="font-mono text-sm">{selectedConversation.session_id}</div>
                      </div>
                      
                      <div className="flex justify-end">
                        <Button 
                          onClick={() => handleConversationSelect(selectedConversation)}
                        >
                          选择此对话
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
