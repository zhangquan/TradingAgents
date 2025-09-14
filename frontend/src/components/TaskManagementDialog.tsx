

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Timer, 
  Play, 
  Pause, 
  Edit, 
  Trash2, 
  Filter,
  Settings,
  Plus,
  RefreshCw,
  Calendar,
  Clock
} from 'lucide-react'
import { 
  apiService, 
  ScheduledTaskInfo 
} from '@/lib/api'
import { toast } from 'sonner'
import { AnalysisTaskDialog } from './AnalysisTaskDialog'

interface TaskManagementDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  ticker?: string // 如果提供ticker，则只显示该股票的任务
  onTaskUpdated?: () => void
}

export function TaskManagementDialog({ 
  open, 
  onOpenChange, 
  ticker,
  onTaskUpdated 
}: TaskManagementDialogProps) {
  const [scheduledTasks, setScheduledTasks] = useState<Record<string, ScheduledTaskInfo>>({})
  const [loading, setLoading] = useState(false)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  
  // Task dialog states
  const [taskDialogOpen, setTaskDialogOpen] = useState(false)
  const [taskDialogMode, setTaskDialogMode] = useState<'immediate' | 'scheduled' | 'edit'>('scheduled')
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      loadScheduledTasks()
    }
  }, [open])

  const loadScheduledTasks = async () => {
    try {
      setLoading(true)
      const response = await apiService.getAllTasks()
      setScheduledTasks(response.scheduled_tasks || {})
    } catch (error) {
      console.error('Failed to load scheduled tasks:', error)
      toast.error('加载定时任务失败')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleTask = async (taskId: string) => {
    try {
      await apiService.toggleTask(taskId)
      toast.success('定时任务状态已更新')
      loadScheduledTasks()
      onTaskUpdated?.()
    } catch (error) {
      console.error('Failed to toggle task:', error)
      toast.error('更新定时任务状态失败')
    }
  }

  const handleDeleteTask = async (taskId: string) => {
    if (!confirm('确定要删除这个定时任务吗？')) return
    
    try {
      await apiService.deleteScheduledTask(taskId)
      toast.success('定时任务已删除')
      loadScheduledTasks()
      onTaskUpdated?.()
    } catch (error) {
      console.error('Failed to delete task:', error)
      toast.error('删除定时任务失败')
    }
  }

  const handleRunTaskNow = async (taskId: string) => {
    try {
      await apiService.runTaskNow(taskId)
      toast.success('定时任务已立即执行')
      loadScheduledTasks()
      onTaskUpdated?.()
    } catch (error) {
      console.error('Failed to run task now:', error)
      toast.error('立即执行定时任务失败')
    }
  }

  const handleEditTask = (taskId: string) => {
    setEditingTaskId(taskId)
    setTaskDialogMode('edit')
    setTaskDialogOpen(true)
  }

  const handleCreateTask = () => {
    setEditingTaskId(null)
    setTaskDialogMode('scheduled')
    setTaskDialogOpen(true)
  }

  const handleTaskCreated = () => {
    loadScheduledTasks()
    onTaskUpdated?.()
  }

  const handleTaskUpdatedInDialog = () => {
    loadScheduledTasks()
    onTaskUpdated?.()
    setEditingTaskId(null)
  }

  const getFilteredTasks = () => {
    let tasks = Object.entries(scheduledTasks)
    
    // 如果指定了ticker，只显示该股票的任务
    if (ticker) {
      tasks = tasks.filter(([_, task]) => task.ticker === ticker)
    }
    
    // 按状态筛选
    return tasks.filter(([_, task]) => {
      if (filterStatus === 'all') return true
      if (filterStatus === 'enabled' && task.enabled) return true
      if (filterStatus === 'disabled' && !task.enabled) return true
      return false
    })
  }

  const getScheduleDescription = (task: ScheduledTaskInfo) => {
    switch (task.schedule_type) {
      case 'daily': return `每日 ${task.schedule_time} 执行`
      case 'weekly': return `每周一 ${task.schedule_time} 执行`
      case 'monthly': return `每月1日 ${task.schedule_time} 执行`
      case 'once': return `${task.schedule_date} ${task.schedule_time} 执行一次`
      default: return '定时执行'
    }
  }

  const filteredTasks = getFilteredTasks()

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="w-[80vw] sm:max-w-none max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Timer className="h-5 w-5 text-blue-600" />
              {ticker ? `${ticker} 任务管理` : '定时任务管理'}
            </DialogTitle>
            <DialogDescription>
              {ticker 
                ? `管理 ${ticker} 的分析任务，支持编辑、执行和删除操作`
                : '管理所有股票的定时分析任务，支持编辑、执行和删除操作'
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex flex-col h-full">
            {/* 操作栏 */}
            <div className="flex items-center justify-between mb-4 pb-4 border-b">
              <div className="flex items-center gap-4">
                <Button onClick={handleCreateTask} size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  创建任务
                </Button>
                
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={loadScheduledTasks}
                  disabled={loading}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  刷新
                </Button>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-gray-600" />
                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger className="w-[120px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部状态</SelectItem>
                      <SelectItem value="enabled">已启用</SelectItem>
                      <SelectItem value="disabled">已禁用</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="text-sm text-gray-600">
                  任务数: {filteredTasks.length}
                </div>
              </div>
            </div>

            {/* 任务列表 */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
                  <span className="ml-2">加载中...</span>
                </div>
              ) : filteredTasks.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Timer className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p className="text-lg font-medium mb-2">
                    {ticker ? `${ticker} 暂无定时任务` : '暂无定时任务'}
                  </p>
                  <p className="text-sm mb-4">
                    创建您的第一个定时分析任务，支持每日、每周、每月或自定义时间执行
                  </p>
                  <Button onClick={handleCreateTask}>
                    <Plus className="h-4 w-4 mr-2" />
                    创建任务
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredTasks.map(([taskId, task]) => (
                    <div key={taskId} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3 flex-1">
                          <div className={`h-3 w-3 rounded-full ${task.enabled ? 'bg-green-500' : 'bg-gray-400'}`} />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-medium">{task.ticker} 定时分析任务</h3>
                              <Badge variant={task.enabled ? 'default' : 'secondary'}>
                                {task.enabled ? '已启用' : '已禁用'}
                              </Badge>
                            </div>
                            
                            <div className="text-sm text-gray-600 space-y-1">
                              <div className="flex items-center gap-4">
                                <div className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {getScheduleDescription(task)}
                                </div>
                                <div>
                                  分析师: {task.analysts.join(', ')}
                                </div>
                                <div>
                                  深度: 级别 {task.research_depth}
                                </div>
                              </div>
                              
                              <div className="flex items-center gap-4 text-xs">
                                <div>
                                  已执行: {task.execution_count} 次
                                </div>
                                {task.last_run && (
                                  <div>
                                    最后执行: {new Date(task.last_run).toLocaleString()}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggleTask(taskId)}
                          >
                            {task.enabled ? (
                              <>
                                <Pause className="h-4 w-4 mr-1" />
                                暂停
                              </>
                            ) : (
                              <>
                                <Play className="h-4 w-4 mr-1" />
                                启用
                              </>
                            )}
                          </Button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditTask(taskId)}
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            编辑
                          </Button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRunTaskNow(taskId)}
                          >
                            <Play className="h-4 w-4 mr-1" />
                            执行
                          </Button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteTask(taskId)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="h-4 w-4 mr-1" />
                            删除
                          </Button>
                        </div>
                      </div>
                      
                      {task.last_error && (
                        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                          最后执行错误: {task.last_error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Task Creation/Edit Dialog */}
      <AnalysisTaskDialog
        open={taskDialogOpen}
        onOpenChange={setTaskDialogOpen}
        ticker={ticker || ''}
        mode={taskDialogMode}
        taskId={editingTaskId || undefined}
        onTaskCreated={handleTaskCreated}
        onTaskUpdated={handleTaskUpdatedInDialog}
      />
    </>
  )
}
