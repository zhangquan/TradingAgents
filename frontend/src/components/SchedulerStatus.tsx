import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Calendar,
  Activity,
  Clock,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Play,
  Square,
  RotateCcw,
  Trash2,
  Eye,
  EyeOff,
  Settings,
  TrendingUp
} from 'lucide-react'
import { useSchedulerStore } from '@/store/schedulerStore'
import { toast } from 'sonner'

interface SchedulerStatusProps {
  className?: string
  showFullView?: boolean
}

export function SchedulerStatus({ className, showFullView = false }: SchedulerStatusProps) {
  const {
    status,
    metrics,
    taskExecutions,
    isLoading,
    error,
    lastUpdated,
    loadSchedulerStatus,
    loadSchedulerMetrics,
    loadTaskExecutions,
    restartScheduler,
    refreshAll,
    clearError,
    deleteTask
  } = useSchedulerStore()

  const [refreshing, setRefreshing] = useState(false)
  const [restarting, setRestarting] = useState(false)
  const [showTaskDetails, setShowTaskDetails] = useState(false)
  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null)

  useEffect(() => {
    // Load initial data
    loadSchedulerStatus()
    loadSchedulerMetrics()
    loadTaskExecutions()
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadSchedulerStatus()
      loadTaskExecutions()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [loadSchedulerStatus, loadSchedulerMetrics, loadTaskExecutions])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await refreshAll()
      toast.success('调度器状态已刷新')
    } catch (error) {
      toast.error('刷新调度器状态失败')
    } finally {
      setRefreshing(false)
    }
  }

  const handleRestart = async () => {
    setRestarting(true)
    try {
      await restartScheduler()
      toast.success('调度器重启成功')
    } catch (error) {
      toast.error('调度器重启失败')
    } finally {
      setRestarting(false)
    }
  }

  const handleDeleteTask = async (taskId: string, ticker: string) => {
    if (!confirm(`确定要删除任务 ${ticker} (${taskId}) 吗？此操作不可撤销。`)) {
      return
    }

    setDeletingTaskId(taskId)
    try {
      await deleteTask(taskId)
      toast.success(`任务 ${ticker} 删除成功`)
    } catch (error) {
      toast.error(`删除任务 ${ticker} 失败`)
    } finally {
      setDeletingTaskId(null)
    }
  }

  const getStatusIcon = (isRunning: boolean) => {
    if (isRunning) {
      return <CheckCircle className="h-4 w-4 text-green-600" />
    } else {
      return <XCircle className="h-4 w-4 text-red-600" />
    }
  }

  const getStatusBadge = (isRunning: boolean) => {
    if (isRunning) {
      return (
        <Badge variant="outline" className="bg-green-100 text-green-700 border-green-200">
          <Play className="h-3 w-3 mr-1" />
          运行中
        </Badge>
      )
    } else {
      return (
        <Badge variant="outline" className="bg-red-100 text-red-700 border-red-200">
          <Square className="h-3 w-3 mr-1" />
          已停止
        </Badge>
      )
    }
  }

  if (error && !status) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              <CardTitle className="text-lg">{showFullView ? '调度器管理' : '调度器状态'}</CardTitle>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                clearError()
                loadSchedulerStatus()
              }}
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              重试
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2 text-red-600">
            <XCircle className="h-4 w-4" />
            <span className="text-sm">无法连接到调度器服务</span>
          </div>
          <p className="text-xs text-gray-500 mt-2">{error}</p>
        </CardContent>
      </Card>
    )
  }

  // Full page view for scheduler management
  if (showFullView) {
    return (
      <div className={className}>
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">调度器管理</h1>
            <p className="text-muted-foreground mt-2">
              管理和监控分析任务的调度执行
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge 
              variant={status?.is_running ? "default" : "secondary"}
              className={status?.is_running ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}
            >
              {status?.is_running ? "运行中" : "已停止"}
            </Badge>
            <Button 
              variant="outline" 
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">总任务数</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{status?.total_tasks || 0}</div>
              <p className="text-xs text-muted-foreground">
                调度器中的所有任务
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">启用任务</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{status?.enabled_tasks || 0}</div>
              <p className="text-xs text-muted-foreground">
                正在执行的任务
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">禁用任务</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{status?.disabled_tasks || 0}</div>
              <p className="text-xs text-muted-foreground">
                暂停执行的任务
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">调度器作业</CardTitle>
              <Settings className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{status?.jobs_in_scheduler || 0}</div>
              <p className="text-xs text-muted-foreground">
                调度器中的作业
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content with Tabs */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">概览</TabsTrigger>
            <TabsTrigger value="tasks">任务列表</TabsTrigger>
            <TabsTrigger value="metrics">性能指标</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <SchedulerStatus className="w-full" showFullView={false} />
          </TabsContent>

          <TabsContent value="tasks" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>调度任务详情</CardTitle>
                <CardDescription>
                  查看和管理所有调度的分析任务
                </CardDescription>
              </CardHeader>
              <CardContent>
                {taskExecutions && taskExecutions.length > 0 ? (
                  <div className="space-y-4">
                    {taskExecutions.map((task) => (
                      <div 
                        key={task.task_id} 
                        className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <h3 className="font-semibold">{task.ticker}</h3>
                              <Badge 
                                variant={task.enabled ? "default" : "secondary"}
                                className={task.enabled ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}
                              >
                                {task.enabled ? "启用" : "禁用"}
                              </Badge>
                              {task.last_error && (
                                <Badge variant="destructive">有错误</Badge>
                              )}
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                              <div>任务ID: {task.task_id}</div>
                              <div>调度: {task.schedule_type} @ {task.schedule_time}</div>
                              <div>分析师: {task.analysts.join(', ')}</div>
                              <div>执行次数: {task.execution_count}</div>
                            </div>
                            {task.last_run && (
                              <div className="text-sm text-gray-500">
                                最后运行: {new Date(task.last_run).toLocaleString()}
                              </div>
                            )}
                            {task.next_run && (
                              <div className="text-sm text-gray-500">
                                下次运行: {new Date(task.next_run).toLocaleString()}
                              </div>
                            )}
                            {task.last_error && (
                              <div className="text-sm text-red-600 mt-2 p-2 bg-red-50 rounded">
                                错误: {task.last_error}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            {task.avg_execution_time && (
                              <div className="text-right text-sm">
                                <div className="text-gray-500">平均执行时间</div>
                                <div className="font-medium">{task.avg_execution_time.toFixed(1)}s</div>
                              </div>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteTask(task.task_id, task.ticker)}
                              disabled={deletingTaskId === task.task_id}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              title={`删除任务 ${task.ticker}`}
                            >
                              {deletingTaskId === task.task_id ? (
                                <RefreshCw className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>暂无调度任务</p>
                    <p className="text-sm">在分析页面创建新的调度任务</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="metrics" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>性能指标</CardTitle>
                <CardDescription>
                  调度器执行统计和性能数据
                </CardDescription>
              </CardHeader>
              <CardContent>
                {metrics ? (
                  <div className="space-y-6">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <div className="text-3xl font-bold text-blue-700">
                          {metrics.total_executions_today}
                        </div>
                        <div className="text-blue-600 mt-1">今日总执行</div>
                      </div>
                      <div className="text-center p-4 bg-green-50 rounded-lg">
                        <div className="text-3xl font-bold text-green-700">
                          {metrics.successful_executions_today}
                        </div>
                        <div className="text-green-600 mt-1">成功执行</div>
                      </div>
                      <div className="text-center p-4 bg-red-50 rounded-lg">
                        <div className="text-3xl font-bold text-red-700">
                          {metrics.failed_executions_today}
                        </div>
                        <div className="text-red-600 mt-1">执行失败</div>
                      </div>
                    </div>
                    {metrics.total_executions_today > 0 && (
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <div className="text-sm font-medium mb-2">今日成功率</div>
                        <div className="flex items-center space-x-4">
                          <div className="flex-1 bg-gray-200 rounded-full h-3">
                            <div 
                              className="bg-green-600 h-3 rounded-full transition-all duration-300"
                              style={{ 
                                width: `${(metrics.successful_executions_today / metrics.total_executions_today) * 100}%` 
                              }}
                            />
                          </div>
                          <div className="text-sm font-medium">
                            {Math.round((metrics.successful_executions_today / metrics.total_executions_today) * 100)}%
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>暂无性能数据</p>
                    <p className="text-sm">开始执行任务后将显示详细统计</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">调度器状态</CardTitle>
          </div>
          <div className="flex items-center space-x-2">
            {status && getStatusBadge(status.is_running)}
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing || isLoading}
            >
              <RefreshCw className={`h-3 w-3 ${refreshing || isLoading ? 'animate-spin' : ''}`} />
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleRestart}
              disabled={restarting || isLoading}
            >
              <RotateCcw className={`h-3 w-3 mr-1 ${restarting ? 'animate-spin' : ''}`} />
              重启
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && !status ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="h-4 bg-gray-200 rounded animate-pulse w-24" />
                <div className="h-4 bg-gray-200 rounded animate-pulse w-16" />
              </div>
            ))}
          </div>
        ) : status ? (
          <div className="space-y-4">
            {/* Basic Status Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(status.is_running)}
                    <span className="text-sm font-medium">服务状态</span>
                  </div>
                  <span className="text-sm text-gray-600">
                    {status.is_running ? '正常运行' : '服务停止'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Activity className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium">总任务数</span>
                  </div>
                  <span className="text-sm text-gray-600">{status.total_tasks}</span>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium">启用任务</span>
                  </div>
                  <span className="text-sm text-gray-600">{status.enabled_tasks}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    <span className="text-sm font-medium">禁用任务</span>
                  </div>
                  <span className="text-sm text-gray-600">{status.disabled_tasks}</span>
                </div>
              </div>
            </div>

            {/* Scheduler Job Count */}
            <div className="pt-3 border-t">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-purple-600" />
                  <span className="text-sm font-medium">调度器中的作业</span>
                </div>
                <span className="text-sm text-gray-600">{status.jobs_in_scheduler}</span>
              </div>
            </div>

            {/* Task Distribution */}
            {status.total_tasks > 0 && (
              <div className="pt-3 border-t">
                <div className="text-sm font-medium mb-2">任务分布</div>
                <div className="flex space-x-2">
                  <div className="flex-1 bg-green-100 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full transition-all duration-300"
                      style={{ 
                        width: `${(status.enabled_tasks / status.total_tasks) * 100}%` 
                      }}
                    />
                  </div>
                  <div className="text-xs text-gray-500">
                    {Math.round((status.enabled_tasks / status.total_tasks) * 100)}% 启用
                  </div>
                </div>
              </div>
            )}

            {/* Metrics */}
            {metrics && (
              <div className="pt-3 border-t space-y-3">
                <div className="text-sm font-medium">今日执行统计</div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="text-center p-2 bg-blue-50 rounded">
                    <div className="font-medium text-blue-700">
                      {metrics.total_executions_today}
                    </div>
                    <div className="text-blue-600">总执行</div>
                  </div>
                  <div className="text-center p-2 bg-green-50 rounded">
                    <div className="font-medium text-green-700">
                      {metrics.successful_executions_today}
                    </div>
                    <div className="text-green-600">成功</div>
                  </div>
                  <div className="text-center p-2 bg-red-50 rounded">
                    <div className="font-medium text-red-700">
                      {metrics.failed_executions_today}
                    </div>
                    <div className="text-red-600">失败</div>
                  </div>
                </div>
              </div>
            )}

            {/* Task List Section */}
            {taskExecutions && Array.isArray(taskExecutions) && taskExecutions.length > 0 && (
              <div className="pt-3 border-t space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">调度任务列表 ({taskExecutions.length})</div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowTaskDetails(!showTaskDetails)}
                    className="text-xs"
                  >
                    {showTaskDetails ? (
                      <>
                        <EyeOff className="h-3 w-3 mr-1" />
                        隐藏详情
                      </>
                    ) : (
                      <>
                        <Eye className="h-3 w-3 mr-1" />
                        显示详情
                      </>
                    )}
                  </Button>
                </div>
                
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {taskExecutions.map((task) => (
                    <div key={task.task_id} className="flex items-center justify-between p-3 bg-gray-50 rounded border hover:bg-gray-100 transition-colors">
                      <div className="flex flex-col space-y-1 flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-gray-900">{task.ticker}</span>
                          <Badge 
                            variant={task.enabled ? "default" : "secondary"} 
                            className={`text-xs ${task.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}
                          >
                            {task.enabled ? '启用' : '禁用'}
                          </Badge>
                          {task.last_error && (
                            <Badge variant="destructive" className="text-xs">
                              有错误
                            </Badge>
                          )}
                        </div>
                        
                        {showTaskDetails && (
                          <>
                            <div className="text-xs text-gray-600">
                              ID: {task.task_id}
                            </div>
                            <div className="text-xs text-gray-600">
                              计划: {task.schedule_type} @ {task.schedule_time}
                            </div>
                            <div className="text-xs text-gray-600">
                              分析师: {task.analysts.join(', ')}
                            </div>
                            {task.last_run && (
                              <div className="text-xs text-gray-500">
                                最后运行: {new Date(task.last_run).toLocaleString()}
                              </div>
                            )}
                            {task.next_run && (
                              <div className="text-xs text-gray-500">
                                下次运行: {new Date(task.next_run).toLocaleString()}
                              </div>
                            )}
                            {task.last_error && (
                              <div className="text-xs text-red-600 mt-1" title={task.last_error}>
                                错误: {task.last_error.length > 50 ? task.last_error.substring(0, 50) + '...' : task.last_error}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        <div className="text-right">
                          <div className="text-sm font-medium text-blue-700">
                            {task.execution_count} 次
                          </div>
                          {task.avg_execution_time && (
                            <div className="text-xs text-gray-500">
                              平均 {task.avg_execution_time.toFixed(1)}s
                            </div>
                          )}
                        </div>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteTask(task.task_id, task.ticker)}
                          disabled={deletingTaskId === task.task_id}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0"
                          title={`删除任务 ${task.ticker}`}
                        >
                          {deletingTaskId === task.task_id ? (
                            <RefreshCw className="h-3 w-3 animate-spin" />
                          ) : (
                            <Trash2 className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Last Update */}
            <div className="pt-3 border-t text-xs text-gray-500 text-center">
              最后更新: {lastUpdated ? new Date(lastUpdated).toLocaleString() : '未知'}
            </div>
          </div>
        ) : (
          <div className="text-center py-4 text-gray-500">
            <Calendar className="h-8 w-8 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">无法获取调度器状态</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
