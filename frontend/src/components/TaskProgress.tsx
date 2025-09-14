

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  PlayCircle, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  StopCircle,
  Activity,

} from 'lucide-react'

import { apiService, TaskInfo } from '@/lib/api'
import { toast } from 'sonner'

interface TaskProgressProps {
  taskId: string
  onComplete?: (results: any) => void
  onCancel?: () => void
}

export function TaskProgress({ taskId, onComplete, onCancel }: TaskProgressProps) {
  const [task, setTask] = useState<TaskInfo | null>(null)
  const [loading, setLoading] = useState(true)



  // Initial task load (only on page refresh/mount)
  useEffect(() => {
    const loadTask = async () => {
      try {
        const taskData = await apiService.getTaskProgress(taskId)
        setTask(taskData)
        
        // Trigger completion callback if task is already completed
        if (taskData.status === 'completed' && taskData.results) {
          onComplete?.(taskData.results)
        }
      } catch (error) {
        console.error('Failed to load task:', error)
        toast.error('获取任务信息失败')
      } finally {
        setLoading(false)
      }
    }

    loadTask()
  }, [taskId, onComplete])

  const handleCancel = async () => {
    // Task cancellation not implemented for scheduled tasks
    toast.info('任务取消功能暂未实现')
    onCancel?.()
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'running':
        return <PlayCircle className="h-5 w-5 text-blue-600" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />
      default:
        return <Clock className="h-5 w-5 text-yellow-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'running':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'cancelled':
        return 'bg-gray-100 text-gray-800 border-gray-200'
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    }
  }

  const getStatusLabel = (status: string) => {
    const labels = {
      starting: '启动中',
      running: '分析中',
      completed: '已完成',
      error: '错误',
      cancelled: '已取消'
    }
    return labels[status as keyof typeof labels] || status
  }



  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Activity className="h-6 w-6 animate-spin text-blue-600" />
            <span className="ml-2">加载任务信息...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!task) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">
            未找到任务信息
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon(task.status)}
            <div>
              <CardTitle className="text-lg">
                {task.request?.ticker || 'Unknown'} 分析任务
              </CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <Badge 
                  variant="outline" 
                  className={getStatusColor(task.status)}
                >
                  {getStatusLabel(task.status)}
                </Badge>

              </div>
            </div>
          </div>
          {task.status === 'running' && (
            <Button variant="outline" size="sm" onClick={handleCancel}>
              <StopCircle className="h-4 w-4 mr-2" />
              取消任务
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Task Configuration */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">股票代码:</span>
              <span className="ml-2 font-medium">{task.request?.ticker}</span>
            </div>
            <div>
              <span className="text-gray-600">分析日期:</span>
              <span className="ml-2 font-medium">{task.request?.analysis_date}</span>
            </div>
            <div>
              <span className="text-gray-600">LLM提供商:</span>
              <span className="ml-2 font-medium">{task.request?.llm_provider}</span>
            </div>
            <div>
              <span className="text-gray-600">研究深度:</span>
              <span className="ml-2 font-medium">级别 {task.request?.research_depth}</span>
            </div>
          </div>

          {/* Simple Status Display */}
          {task.status === 'running' && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2 text-sm p-2 bg-blue-50 rounded-md">
                <Activity className="h-4 w-4 text-blue-600 animate-spin" />
                <span className="text-blue-700">正在进行分析，请等待...</span>
              </div>
            </div>
          )}

          {/* Error Display */}
          {task.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm font-medium text-red-800">错误信息</span>
              </div>
              <p className="text-sm text-red-700 mt-1">{task.error}</p>
            </div>
          )}

          {/* Completion Info */}
          {task.status === 'completed' && task.results && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-800">分析完成</span>
              </div>
              <p className="text-sm text-green-700 mt-1">
                分析已成功完成，报告已生成
              </p>
              {task.results.analysis_id && (
                <div className="text-xs text-green-600 mt-1">
                  分析ID: {task.results.analysis_id}
                </div>
              )}
            </div>
          )}

          {/* Task Info */}
          <div className="text-xs text-gray-500">
            <span>任务ID: {taskId}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
