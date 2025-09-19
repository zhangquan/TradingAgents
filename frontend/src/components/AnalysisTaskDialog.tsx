

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { 
  TrendingUp, 
  Play, 
  Calendar, 
  Clock, 
  Settings,
  Loader2
} from 'lucide-react'
import { 
  apiService, 
  AnalysisConfig, 
  ScheduledAnalysisRequest 
} from '@/lib/api'
import { toast } from 'sonner'
import { 
  getSystemTimeZone, 
  getTimezoneOffset 
} from '@/lib/utils'

interface AnalysisTaskDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  ticker: string
  mode: 'immediate' | 'scheduled' | 'edit'
  taskId?: string // For edit mode
  onTaskCreated?: (taskId: string) => void
  onTaskUpdated?: () => void
}

export function AnalysisTaskDialog({ 
  open, 
  onOpenChange, 
  ticker, 
  mode, 
  taskId,
  onTaskCreated, 
  onTaskUpdated 
}: AnalysisTaskDialogProps) {
  const [analysts, setAnalysts] = useState<any[]>([])
  const [defaultConfig, setDefaultConfig] = useState<AnalysisConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // Form state
  const [formData, setFormData] = useState<ScheduledAnalysisRequest>({
    ticker: ticker,
    analysts: [],
    research_depth: 1,
    schedule_type: 'once',
    schedule_time: '09:00',
    timezone: getSystemTimeZone(), // 使用系统设置的时区
    enabled: true
  })

  useEffect(() => {
    if (open) {
      loadAnalysts()
      loadDefaultConfig()
      if (mode === 'edit' && taskId) {
        loadTaskData()
      }
    }
  }, [open, mode, taskId])

  useEffect(() => {
    setFormData(prev => ({ ...prev, ticker }))
  }, [ticker])

  // 确保使用系统时区
  useEffect(() => {
    setFormData(prev => ({ ...prev, timezone: getSystemTimeZone() }))
  }, [open])

  const loadAnalysts = async () => {
    try {
      const response = await apiService.getAnalysts()
      setAnalysts(response.analysts || [])
    } catch (error) {
      console.error('Failed to load analysts:', error)
      toast.error('加载分析师列表失败')
    }
  }

  const loadDefaultConfig = async () => {
    try {
      const response = await apiService.getAnalysisConfig()
      setDefaultConfig(response.default_config)
      
      // Set default form values from config
      setFormData(prev => ({
        ...prev,
        research_depth: response.default_config.research_depth,
        analysts: response.default_config.analysts
      }))
    } catch (error) {
      console.error('Failed to load default config:', error)
    }
  }

  const loadTaskData = async () => {
    if (!taskId) return
    
    try {
      setLoading(true)
      const task = await apiService.getTask(taskId)
      setFormData({
        ticker: task.ticker,
        analysts: task.analysts,
        research_depth: task.research_depth,
        schedule_type: task.schedule_type,
        schedule_time: task.schedule_time,
        schedule_date: task.schedule_date || '',
        timezone: task.timezone,
        enabled: task.enabled
      })
    } catch (error) {
      console.error('Failed to load task data:', error)
      toast.error('加载任务数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalystToggle = (analystValue: string) => {
    setFormData(prev => ({
      ...prev,
      analysts: prev.analysts.includes(analystValue) 
        ? prev.analysts.filter(a => a !== analystValue)
        : [...prev.analysts, analystValue]
    }))
  }

  const handleSubmit = async () => {
    if (!formData.ticker || formData.analysts.length === 0) {
      toast.error('请填写股票代码并选择至少一个分析师')
      return
    }

    try {
      setSubmitting(true)
      
      if (mode === 'immediate') {
        // For immediate execution, create a 'once' type task with current time
        const now = new Date()
        const immediateFormData = {
          ...formData,
          schedule_type: 'once' as const,
          schedule_date: now.toISOString().split('T')[0],
          schedule_time: now.toTimeString().split(' ')[0].substring(0, 5)
        }
        
        const response = await apiService.createTask(immediateFormData)
        
        // Immediately run the task
        await apiService.runTaskNow(response.task_id)
        
        toast.success('分析任务已立即执行')
        onTaskCreated?.(response.task_id)
      } else if (mode === 'scheduled') {
        const response = await apiService.createTask(formData)
        toast.success('定时任务已创建')
        onTaskCreated?.(response.task_id)
      } else if (mode === 'edit' && taskId) {
        await apiService.updateTask(taskId, formData)
        toast.success('任务已更新')
        onTaskUpdated?.()
      }
      
      onOpenChange(false)
      
      // Reset form for next use
      setFormData({
        ticker: ticker,
        analysts: defaultConfig?.analysts || [],
        research_depth: defaultConfig?.research_depth || 1,
        schedule_type: 'once',
        schedule_time: '09:00',
        timezone: getSystemTimeZone(), // 重置时使用系统时区
        enabled: true
      })
    } catch (error) {
      console.error('Failed to handle task:', error)
      toast.error(
        mode === 'immediate' ? '立即执行分析失败' : 
        mode === 'scheduled' ? '创建定时任务失败' : 
        '更新任务失败'
      )
    } finally {
      setSubmitting(false)
    }
  }

  const getDialogTitle = () => {
    switch (mode) {
      case 'immediate':
        return '立即执行分析'
      case 'scheduled':
        return '创建定时任务'
      case 'edit':
        return '编辑分析任务'
      default:
        return '分析任务'
    }
  }

  const getDialogDescription = () => {
    switch (mode) {
      case 'immediate':
        return `为 ${ticker} 配置分析参数并立即执行分析任务`
      case 'scheduled':
        return `为 ${ticker} 配置定时分析任务，系统将按照设定的时间自动执行`
      case 'edit':
        return `修改 ${ticker} 的分析任务配置`
      default:
        return '配置分析任务参数'
    }
  }

  const getSubmitButtonText = () => {
    if (submitting) {
      return mode === 'immediate' ? '执行中...' : mode === 'edit' ? '更新中...' : '创建中...'
    }
    return mode === 'immediate' ? '立即执行' : mode === 'edit' ? '更新任务' : '创建任务'
  }

  if (loading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-2">加载中...</span>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {mode === 'immediate' ? (
              <Play className="h-5 w-5 text-green-600" />
            ) : mode === 'scheduled' ? (
              <Clock className="h-5 w-5 text-blue-600" />
            ) : (
              <Settings className="h-5 w-5 text-orange-600" />
            )}
            {getDialogTitle()}
          </DialogTitle>
          <DialogDescription>
            {getDialogDescription()}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Stock Symbol Display */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              <span className="font-medium text-blue-800">目标股票: {ticker}</span>
            </div>
          </div>

          {/* Schedule Configuration (not for immediate mode) */}
          {mode !== 'immediate' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="schedule-type">执行频率</Label>
                  <Select 
                    value={formData.schedule_type} 
                    onValueChange={(value) => setFormData(prev => ({...prev, schedule_type: value}))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="once">执行一次</SelectItem>
                      <SelectItem value="daily">每日执行</SelectItem>
                      <SelectItem value="weekly">每周执行</SelectItem>
                      <SelectItem value="monthly">每月执行</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="schedule-time">执行时间</Label>
                  <Input
                    id="schedule-time"
                    type="time"
                    value={formData.schedule_time}
                    onChange={(e) => setFormData(prev => ({...prev, schedule_time: e.target.value}))}
                  />
                </div>
              </div>
              
              {/* Timezone Display */}
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-800">系统时区</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-blue-700">{getSystemTimeZone()}</span>
                    <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                      {getTimezoneOffset(getSystemTimeZone())}
                    </span>
                  </div>
                </div>
                {formData.schedule_time && (
                  <div className="text-xs text-blue-600 mt-2">
                    任务将在 {formData.schedule_time} ({getTimezoneOffset(getSystemTimeZone())}) 执行
                  </div>
                )}
                <div className="text-xs text-gray-600 mt-1">
                  时区设置可在用户偏好中修改
                </div>
              </div>
            </div>
          )}

          {/* Date picker for 'once' type */}
          {mode !== 'immediate' && formData.schedule_type === 'once' && (
            <div>
              <Label htmlFor="schedule-date">执行日期</Label>
              <Input
                id="schedule-date"
                type="date"
                value={formData.schedule_date || ''}
                onChange={(e) => setFormData(prev => ({...prev, schedule_date: e.target.value}))}
              />
            </div>
          )}

          {/* Analysts Selection */}
          <div>
            <Label>选择分析师</Label>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {analysts.map((analyst) => (
                <div
                  key={analyst.value}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    formData.analysts.includes(analyst.value)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleAnalystToggle(analyst.value)}
                >
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="h-4 w-4" />
                    <span className="text-sm font-medium">{analyst.label}</span>
                  </div>
                </div>
              ))}
            </div>
            {formData.analysts.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {formData.analysts.map(analyst => (
                  <Badge key={analyst} variant="secondary" className="text-xs">
                    {analysts.find(a => a.value === analyst)?.label || analyst}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Research Depth */}
          <div>
            <Label htmlFor="research-depth">研究深度</Label>
            <Select 
              value={formData.research_depth.toString()} 
              onValueChange={(value) => setFormData(prev => ({...prev, research_depth: parseInt(value)}))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">浅层分析</SelectItem>
                <SelectItem value="2">标准分析</SelectItem>
                <SelectItem value="3">深度分析</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button 
              variant="outline" 
              onClick={() => onOpenChange(false)}
              disabled={submitting}
            >
              取消
            </Button>
            <Button 
              onClick={handleSubmit}
              disabled={submitting || formData.analysts.length === 0}
              className={mode === 'immediate' ? 'bg-green-600 hover:bg-green-700' : ''}
            >
              {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {getSubmitButtonText()}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
