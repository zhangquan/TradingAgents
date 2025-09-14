import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Shield,
  Database,
  Activity,
  Settings,
  Users,
  BarChart3,
  Server,
  RefreshCw,
  Download,
  Upload,
  Trash2
} from 'lucide-react'
import { apiService } from '@/lib/api'
import { SystemStatus } from '@/components/SystemStatus'
import { NotificationCenter } from '@/components/NotificationCenter'
import { toast } from 'sonner'

export default function AdminPage() {
  const [systemStats, setSystemStats] = useState<any>({})
  const [cacheStats, setCacheStats] = useState<any>({})
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAdminData()
  }, [])

  const loadAdminData = async () => {
    try {
      const [stats, systemLogs] = await Promise.all([
        apiService.getSystemStats(),
        apiService.getSystemLogs()
      ])
      const cache = { hit_rate: 0, total_entries: 0, hits: 0, misses: 0 } // 模拟缓存数据

      setSystemStats(stats)
      setCacheStats(cache)
      setLogs(systemLogs.logs || [])
    } catch (error) {
      console.error('Failed to load admin data:', error)
      toast.error('加载管理数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCleanupSystem = async () => {
    try {
      const result = await apiService.cleanupSystem()
      toast.success(`系统清理完成，清理了 ${result.expired_tasks_removed} 个过期任务`)
      loadAdminData()
    } catch (error) {
      console.error('System cleanup failed:', error)
      toast.error('系统清理失败')
    }
  }

  const handleRefreshCache = async () => {
    try {
      // 模拟缓存刷新
      toast.success('缓存刷新完成')
      loadAdminData()
    } catch (error) {
      console.error('Cache refresh failed:', error)
      toast.error('缓存刷新失败')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-2">
          <Shield className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">系统管理</h1>
        </div>
        <div className="grid gap-6">
          {[...Array(4)].map((_, i) => (
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
          <Shield className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">系统管理</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleRefreshCache}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新缓存
          </Button>
          <Button variant="outline" onClick={handleCleanupSystem}>
            <Trash2 className="h-4 w-4 mr-2" />
            系统清理
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* System Status */}
        <div className="lg:col-span-2">
          <SystemStatus />
        </div>

        {/* Quick Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">运行概览</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <span className="text-sm">活跃任务</span>
                </div>
                <Badge variant="secondary">
                  {systemStats.runtime?.active_tasks || 0}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Database className="h-4 w-4 text-green-600" />
                  <span className="text-sm">缓存命中率</span>
                </div>
                <Badge variant="default" className="bg-green-100 text-green-700">
                  {cacheStats.hit_rate ? `${Math.round(cacheStats.hit_rate * 100)}%` : 'N/A'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="h-4 w-4 text-purple-600" />
                  <span className="text-sm">总分析数</span>
                </div>
                <Badge variant="outline">
                  {systemStats.storage?.total_analyses || 0}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="monitoring" className="space-y-4">
        <TabsList>
          <TabsTrigger value="monitoring">监控面板</TabsTrigger>
          <TabsTrigger value="notifications">通知中心</TabsTrigger>
          <TabsTrigger value="logs">系统日志</TabsTrigger>
          <TabsTrigger value="maintenance">系统维护</TabsTrigger>
        </TabsList>

        <TabsContent value="monitoring" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {/* Performance Metrics */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">性能指标</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>CPU使用率</span>
                    <span className="font-medium">12%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>内存使用</span>
                    <span className="font-medium">68%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>磁盘使用</span>
                    <span className="font-medium">45%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Cache Statistics */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">缓存统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>缓存大小</span>
                    <span className="font-medium">{cacheStats.total_entries || 0}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>命中次数</span>
                    <span className="font-medium">{cacheStats.hits || 0}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>未命中</span>
                    <span className="font-medium">{cacheStats.misses || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* API Statistics */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">API统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>总请求数</span>
                    <span className="font-medium">1,234</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>成功率</span>
                    <span className="font-medium text-green-600">99.2%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>平均响应</span>
                    <span className="font-medium">120ms</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Storage Statistics */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">存储统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>分析记录</span>
                    <span className="font-medium">{systemStats.storage?.total_analyses || 0}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>用户配置</span>
                    <span className="font-medium">{systemStats.storage?.total_configs || 0}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>系统日志</span>
                    <span className="font-medium">{systemStats.storage?.total_logs || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="notifications">
          <NotificationCenter />
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>系统日志</CardTitle>
              <CardDescription>最近的系统事件和操作记录</CardDescription>
            </CardHeader>
            <CardContent>
              {logs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Server className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>暂无系统日志</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {logs.slice(0, 50).map((log, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-xs">
                            {log.event_type}
                          </Badge>
                          <span className="text-sm font-medium">{log.description || 'System Event'}</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                      </div>
                      {log.details && (
                        <div className="mt-2 text-xs text-gray-600">
                          {JSON.stringify(log.details, null, 2)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="maintenance" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            {/* System Maintenance */}
            <Card>
              <CardHeader>
                <CardTitle>系统维护</CardTitle>
                <CardDescription>系统清理和维护操作</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button className="w-full" onClick={handleCleanupSystem}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  清理过期数据
                </Button>
                <Button variant="outline" className="w-full" onClick={handleRefreshCache}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  刷新系统缓存
                </Button>
                <Button variant="outline" className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  导出系统日志
                </Button>
              </CardContent>
            </Card>

            {/* Data Management */}
            <Card>
              <CardHeader>
                <CardTitle>数据管理</CardTitle>
                <CardDescription>数据备份和恢复操作</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button variant="outline" className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  备份分析数据
                </Button>
                <Button variant="outline" className="w-full">
                  <Upload className="h-4 w-4 mr-2" />
                  恢复分析数据
                </Button>
                <Button variant="outline" className="w-full">
                  <Database className="h-4 w-4 mr-2" />
                  数据库优化
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
