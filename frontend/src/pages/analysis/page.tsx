import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { 
  Activity, 
  Plus, 
  TrendingUp,
  Timer,
  Settings,
  Pause,
  Play,
  RotateCcw,
  Trash2,
  Filter,
  Edit
} from 'lucide-react'
import { 
  apiService, 
  AnalysisConfig, 
  ScheduledAnalysisRequest, 
  ScheduledTaskInfo 
} from '@/lib/api'
import { toast } from 'sonner'

export default function AnalysisPage() {
  const [scheduledTasks, setScheduledTasks] = useState<Record<string, ScheduledTaskInfo>>({})
  const [loading, setLoading] = useState(true)
  const [isScheduleDialogOpen, setIsScheduleDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null)
  const [analysts, setAnalysts] = useState<any[]>([])
  const [defaultConfig, setDefaultConfig] = useState<AnalysisConfig | null>(null)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [watchlist, setWatchlist] = useState<string[]>([])
  const [watchlistLoading, setWatchlistLoading] = useState(false)

  // Task form state (scheduled only)
  const [scheduleFormData, setScheduleFormData] = useState<ScheduledAnalysisRequest>({
    ticker: '',
    analysts: [],
    research_depth: 1,
    schedule_type: 'daily',
    schedule_time: '09:00',
    timezone: 'UTC',
    enabled: true
  })

  // Edit form state
  const [editFormData, setEditFormData] = useState<ScheduledAnalysisRequest>({
    ticker: '',
    analysts: [],
    research_depth: 1,
    schedule_type: 'daily',
    schedule_time: '09:00',
    timezone: 'UTC',
    enabled: true
  })

  useEffect(() => {
    loadScheduledTasks()
    loadAnalysts()
    loadDefaultConfig()
    loadWatchlist()
  }, [])

  const loadScheduledTasks = async () => {
    try {
      const response = await apiService.getAllTasks()
      setScheduledTasks(response.scheduled_tasks || {})
    } catch (error) {
      console.error('Failed to load scheduled tasks:', error)
      toast.error('加载定时任务失败')
    } finally {
      setLoading(false)
    }
  }

  const loadAnalysts = async () => {
    try {
      const response = await apiService.getAnalysts()
      setAnalysts(response.analysts || [])
    } catch (error) {
      console.error('Failed to load analysts:', error)
    }
  }

  const loadDefaultConfig = async () => {
    try {
      const response = await apiService.getAnalysisConfig()
      setDefaultConfig(response.default_config)
      // Set default form values from config
      setScheduleFormData(prev => ({
        ...prev,
        research_depth: response.default_config.research_depth,
        analysts: response.default_config.analysts
      }))
    } catch (error) {
      console.error('Failed to load default config:', error)
    }
  }

  const loadWatchlist = async () => {
    try {
      setWatchlistLoading(true)
      const response = await apiService.getWatchlist()
      setWatchlist(response.available_stocks || [])
    } catch (error) {
      console.error('Failed to load watchlist:', error)
      toast.error('加载关注股票列表失败')
    } finally {
      setWatchlistLoading(false)
    }
  }

  const handleScheduleAnalystToggle = (analystValue: string) => {
    setScheduleFormData(prev => ({
      ...prev,
      analysts: prev.analysts.includes(analystValue) 
        ? prev.analysts.filter(a => a !== analystValue)
        : [...prev.analysts, analystValue]
    }))
  }

  const handleEditAnalystToggle = (analystValue: string) => {
    setEditFormData(prev => ({
      ...prev,
      analysts: prev.analysts.includes(analystValue) 
        ? prev.analysts.filter(a => a !== analystValue)
        : [...prev.analysts, analystValue]
    }))
  }

  const handleEditTask = (taskId: string) => {
    const task = scheduledTasks[taskId]
    if (!task) {
      toast.error('任务不存在')
      return
    }
    
    // Populate edit form with task data
    setEditFormData({
      ticker: task.ticker,
      analysts: task.analysts,
      research_depth: task.research_depth,
      schedule_type: task.schedule_type,
      schedule_time: task.schedule_time,
      schedule_date: task.schedule_date || '',
      timezone: task.timezone,
      enabled: task.enabled
    })
    
    setEditingTaskId(taskId)
    setIsEditDialogOpen(true)
  }

  const handleUpdateTask = async () => {
    if (!editingTaskId || !editFormData.ticker || editFormData.analysts.length === 0) {
      toast.error('请填写股票代码并选择至少一个分析师')
      return
    }

    try {
      await apiService.updateTask(editingTaskId, editFormData)
      toast.success('任务已更新')
      setIsEditDialogOpen(false)
      setEditingTaskId(null)
      
      loadScheduledTasks()
      
      // Reset edit form
      setEditFormData({
        ticker: '',
        analysts: defaultConfig?.analysts || [],
        research_depth: defaultConfig?.research_depth || 1,
        schedule_type: 'daily',
        schedule_time: '09:00',
        timezone: 'UTC',
        enabled: true
      })
    } catch (error) {
      console.error('Failed to update task:', error)
      toast.error('更新任务失败')
    }
  }

  const handleCreateScheduledTask = async () => {
    if (!scheduleFormData.ticker || scheduleFormData.analysts.length === 0) {
      toast.error('请填写股票代码并选择至少一个分析师')
      return
    }

    try {
      await apiService.createTask(scheduleFormData)
      toast.success('定时任务已创建')
      setIsScheduleDialogOpen(false)
      
      loadScheduledTasks()
      
      // Reset form
      setScheduleFormData({
        ticker: '',
        analysts: defaultConfig?.analysts || [],
        research_depth: defaultConfig?.research_depth || 1,
        schedule_type: 'daily',
        schedule_time: '09:00',
        timezone: 'UTC',
        enabled: true
      })
    } catch (error) {
      console.error('Failed to create scheduled task:', error)
      toast.error('创建定时任务失败')
    }
  }

  const handleToggleTask = async (taskId: string) => {
    try {
      await apiService.toggleTask(taskId)
      toast.success('定时任务状态已更新')
      loadScheduledTasks()
    } catch (error) {
      console.error('Failed to toggle task:', error)
      toast.error('更新定时任务状态失败')
    }
  }

  const handleDeleteTask = async (taskId: string) => {
    try {
      await apiService.deleteScheduledTask(taskId)
      toast.success('定时任务已删除')
      loadScheduledTasks()
    } catch (error) {
      console.error('Failed to delete task:', error)
      toast.error('删除定时任务失败')
    }
  }

  const handleRunTaskNow = async (taskId: string) => {
    try {
      await apiService.runTaskNow(taskId)
      toast.success('定时任务已立即执行')
      loadScheduledTasks() // Refresh to update last_run info
    } catch (error) {
      console.error('Failed to run task now:', error)
      toast.error('立即执行定时任务失败')
    }
  }

  const getFilteredTasks = () => {
    return Object.entries(scheduledTasks).filter(([_, task]) => {
      if (filterStatus === 'all') return true
      if (filterStatus === 'enabled' && task.enabled) return true
      if (filterStatus === 'disabled' && !task.enabled) return true
      return false
    })
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-2">
          <Activity className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">定时任务管理</h1>
        </div>
        <div className="grid gap-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="h-6 bg-gray-200 rounded animate-pulse" />
                <div className="h-4 bg-gray-200 rounded animate-pulse" />
              </CardHeader>
              <CardContent>
                <div className="h-20 bg-gray-200 rounded animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">定时任务管理</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Dialog open={isScheduleDialogOpen} onOpenChange={setIsScheduleDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Timer className="h-4 w-4 mr-2" />
                创建定时任务
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>创建定时分析任务</DialogTitle>
                <DialogDescription>
                  配置股票分析参数和执行计划。定时任务将按照设定的时间自动执行分析。
                </DialogDescription>
                {watchlist.length > 0 && (
                  <div className="flex items-center space-x-2 text-sm text-blue-600 bg-blue-50 p-2 rounded-md">
                    <TrendingUp className="h-4 w-4" />
                    <span>当前关注 {watchlist.length} 只股票: {watchlist.join(', ')}</span>
                  </div>
                )}
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <Label htmlFor="schedule-ticker">股票代码</Label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={loadWatchlist}
                        disabled={watchlistLoading}
                        className="h-6 px-2 text-xs"
                      >
                        <RotateCcw className={`h-3 w-3 mr-1 ${watchlistLoading ? 'animate-spin' : ''}`} />
                        刷新
                      </Button>
                    </div>
                    <Select 
                      value={scheduleFormData.ticker} 
                      onValueChange={(value) => setScheduleFormData(prev => ({...prev, ticker: value}))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={watchlistLoading ? "加载中..." : (watchlist.length === 0 ? "无关注股票" : "选择股票代码")} />
                      </SelectTrigger>
                      <SelectContent>
                        {watchlist.length === 0 ? (
                          <div className="px-3 py-2 text-sm text-gray-500">
                            暂无关注股票，请先添加股票到关注列表
                          </div>
                        ) : (
                          <>
                            {watchlist.map((symbol) => (
                              <SelectItem key={symbol} value={symbol}>
                                <div className="flex items-center space-x-2">
                                  <span className="font-medium">{symbol}</span>
                                  <span className="text-sm text-gray-500">📈</span>
                                </div>
                              </SelectItem>
                            ))}
                            <div className="border-t border-gray-200 my-1"></div>
                            <div className="px-3 py-2 text-sm text-blue-600 cursor-pointer hover:bg-blue-50" 
                                 onClick={() => {
                                   toast.info('请在股票数据页面管理您的关注股票列表')
                                 }}>
                              <div className="flex items-center space-x-2">
                                <Plus className="h-4 w-4" />
                                <span>管理关注股票列表</span>
                              </div>
                            </div>
                          </>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="schedule-type">执行频率</Label>
                    <Select 
                      value={scheduleFormData.schedule_type} 
                      onValueChange={(value) => setScheduleFormData(prev => ({...prev, schedule_type: value}))}
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
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="schedule-time">执行时间</Label>
                    <Input
                      id="schedule-time"
                      type="time"
                      value={scheduleFormData.schedule_time}
                      onChange={(e) => setScheduleFormData(prev => ({...prev, schedule_time: e.target.value}))}
                    />
                  </div>
                  {scheduleFormData.schedule_type === 'once' && (
                    <div>
                      <Label htmlFor="schedule-date">执行日期</Label>
                      <Input
                        id="schedule-date"
                        type="date"
                        value={scheduleFormData.schedule_date || ''}
                        onChange={(e) => setScheduleFormData(prev => ({...prev, schedule_date: e.target.value}))}
                      />
                    </div>
                  )}
                </div>

                <div>
                  <Label>选择分析师</Label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {analysts.map((analyst) => (
                      <div
                        key={analyst.value}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          scheduleFormData.analysts.includes(analyst.value)
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => handleScheduleAnalystToggle(analyst.value)}
                      >
                        <div className="flex items-center space-x-2">
                          <TrendingUp className="h-4 w-4" />
                          <span className="text-sm font-medium">{analyst.label}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label htmlFor="schedule-depth">研究深度</Label>
                  <Select 
                    value={scheduleFormData.research_depth.toString()} 
                    onValueChange={(value) => setScheduleFormData(prev => ({...prev, research_depth: parseInt(value)}))}
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

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsScheduleDialogOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={handleCreateScheduledTask}>
                    创建定时任务
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          {/* Edit Task Dialog */}
          <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>编辑定时分析任务</DialogTitle>
                <DialogDescription>
                  修改股票分析参数和执行计划。任务将按照新设定的时间执行分析。
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="edit-ticker">股票代码</Label>
                    <Select 
                      value={editFormData.ticker} 
                      onValueChange={(value) => setEditFormData(prev => ({...prev, ticker: value}))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择股票代码" />
                      </SelectTrigger>
                      <SelectContent>
                        {watchlist.map((symbol) => (
                          <SelectItem key={symbol} value={symbol}>
                            <div className="flex items-center space-x-2">
                              <span className="font-medium">{symbol}</span>
                              <span className="text-sm text-gray-500">📈</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="edit-schedule-type">执行频率</Label>
                    <Select 
                      value={editFormData.schedule_type} 
                      onValueChange={(value) => setEditFormData(prev => ({...prev, schedule_type: value}))}
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
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="edit-schedule-time">执行时间</Label>
                    <Input
                      id="edit-schedule-time"
                      type="time"
                      value={editFormData.schedule_time}
                      onChange={(e) => setEditFormData(prev => ({...prev, schedule_time: e.target.value}))}
                    />
                  </div>
                  {editFormData.schedule_type === 'once' && (
                    <div>
                      <Label htmlFor="edit-schedule-date">执行日期</Label>
                      <Input
                        id="edit-schedule-date"
                        type="date"
                        value={editFormData.schedule_date || ''}
                        onChange={(e) => setEditFormData(prev => ({...prev, schedule_date: e.target.value}))}
                      />
                    </div>
                  )}
                </div>

                <div>
                  <Label>选择分析师</Label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {analysts.map((analyst) => (
                      <div
                        key={analyst.value}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          editFormData.analysts.includes(analyst.value)
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => handleEditAnalystToggle(analyst.value)}
                      >
                        <div className="flex items-center space-x-2">
                          <TrendingUp className="h-4 w-4" />
                          <span className="text-sm font-medium">{analyst.label}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label htmlFor="edit-research-depth">研究深度</Label>
                  <Select 
                    value={editFormData.research_depth.toString()} 
                    onValueChange={(value) => setEditFormData(prev => ({...prev, research_depth: parseInt(value)}))}
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

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={handleUpdateTask}>
                    更新任务
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="flex items-center justify-between bg-gray-50 p-4 rounded-lg">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">筛选:</span>
          </div>
          
          {/* Status Filter */}
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="状态筛选" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="enabled">已启用</SelectItem>
              <SelectItem value="disabled">已禁用</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <span>定时任务: {Object.keys(scheduledTasks).length}</span>
        </div>
      </div>

      {/* Tasks List */}
      <div className="space-y-4">
        {getFilteredTasks().length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Activity className="h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">暂无定时任务</h3>
              <p className="text-gray-500 text-center mb-4">
                创建您的第一个定时分析任务，支持每日、每周、每月或自定义时间执行
              </p>
              <Button onClick={() => setIsScheduleDialogOpen(true)}>
                <Timer className="h-4 w-4 mr-2" />
                创建定时任务
              </Button>
            </CardContent>
          </Card>
        ) : (
          getFilteredTasks().map(([taskId, task]) => {
            const getScheduleDescription = () => {
              switch (task.schedule_type) {
                case 'daily': return `每日 ${task.schedule_time} 执行`
                case 'weekly': return `每周一 ${task.schedule_time} 执行`
                case 'monthly': return `每月1日 ${task.schedule_time} 执行`
                case 'once': return `${task.schedule_date} ${task.schedule_time} 执行一次`
                default: return '定时执行'
              }
            }
            
            return (
              <Card key={taskId}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Timer className="h-5 w-5 text-purple-600" />
                      <div className={`h-3 w-3 rounded-full ${task.enabled ? 'bg-green-500' : 'bg-gray-400'}`} />
                      <div>
                        <CardTitle className="text-lg">
                          {task.ticker} 定时分析任务
                        </CardTitle>
                        <CardDescription>
                          {getScheduleDescription()} · 
                          分析师: {task.analysts.join(', ')}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={task.enabled ? 'default' : 'secondary'}>
                        {task.enabled ? '已启用' : '已禁用'}
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleTask(taskId)}
                      >
                        {task.enabled ? (
                          <>
                            <Pause className="h-4 w-4 mr-2" />
                            暂停
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4 mr-2" />
                            启用
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditTask(taskId)}
                      >
                        <Edit className="h-4 w-4 mr-2" />
                        编辑
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRunTaskNow(taskId)}
                      >
                        <RotateCcw className="h-4 w-4 mr-2" />
                        立即执行
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteTask(taskId)}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        删除
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">研究深度:</span>
                        <span className="ml-2 font-medium">级别 {task.research_depth}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">已执行次数:</span>
                        <span className="ml-2 font-medium">{task.execution_count} 次</span>
                      </div>
                      <div>
                        <span className="text-gray-600">创建时间:</span>
                        <span className="ml-2 font-medium">{new Date(task.created_at).toLocaleString()}</span>
                      </div>
                      {task.last_run && (
                        <div>
                          <span className="text-gray-600">最后执行:</span>
                          <span className="ml-2 font-medium">{new Date(task.last_run).toLocaleString()}</span>
                        </div>
                      )}
                    </div>

                    {task.last_error && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                        <p className="text-sm text-red-700">最后执行错误: {task.last_error}</p>
                      </div>
                    )}

                    {!task.enabled && (
                      <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                        <p className="text-sm text-gray-700">定时任务已禁用，不会自动执行</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}