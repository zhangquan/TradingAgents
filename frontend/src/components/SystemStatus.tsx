

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Server,
  Activity,
  Database,
  Cloud,
  Cpu,
  HardDrive,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react'
import { apiService } from '@/lib/api'

interface SystemStatusProps {
  className?: string
}

interface ServiceStatus {
  name: string
  status: 'healthy' | 'warning' | 'error'
  message: string
  lastCheck: string
}

export function SystemStatus({ className }: SystemStatusProps) {
  const [systemHealth, setSystemHealth] = useState<'healthy' | 'warning' | 'error'>('healthy')
  const [services, setServices] = useState<ServiceStatus[]>([])
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    loadSystemStatus()
    
    // Refresh every 30 seconds
    const interval = setInterval(loadSystemStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadSystemStatus = async () => {
    try {
      setRefreshing(true)
      
      const [healthResponse, systemStats] = await Promise.all([
        apiService.health(),
        apiService.getSystemStats()
      ])

      // Determine overall system health
      let overallHealth: 'healthy' | 'warning' | 'error' = 'healthy'
      
      // Check individual services
      const servicesStatus: ServiceStatus[] = [
        {
          name: 'API服务',
          status: healthResponse.status === 'healthy' ? 'healthy' : 'error',
          message: healthResponse.status === 'healthy' ? '运行正常' : '服务异常',
          lastCheck: new Date().toISOString()
        },
        {
          name: '数据存储',
          status: systemStats.storage ? 'healthy' : 'warning',
          message: systemStats.storage ? '存储正常' : '存储警告',
          lastCheck: new Date().toISOString()
        },
        {
          name: '任务处理',
          status: systemStats.runtime?.active_tasks !== undefined ? 'healthy' : 'warning',
          message: systemStats.runtime ? '处理正常' : '处理器警告',
          lastCheck: new Date().toISOString()
        },
        {
          name: '缓存系统',
          status: systemStats.cache ? 'healthy' : 'warning',
          message: systemStats.cache ? '缓存正常' : '缓存警告',
          lastCheck: new Date().toISOString()
        }
      ]

      // Determine overall health based on services
      const hasErrors = servicesStatus.some(s => s.status === 'error')
      const hasWarnings = servicesStatus.some(s => s.status === 'warning')
      
      if (hasErrors) {
        overallHealth = 'error'
      } else if (hasWarnings) {
        overallHealth = 'warning'
      }

      setSystemHealth(overallHealth)
      setServices(servicesStatus)
      setStats(systemStats)
    } catch (error) {
      console.error('Failed to load system status:', error)
      setSystemHealth('error')
      setServices([
        {
          name: '系统连接',
          status: 'error',
          message: '无法连接到系统',
          lastCheck: new Date().toISOString()
        }
      ])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const getStatusIcon = (status: 'healthy' | 'warning' | 'error') => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />
    }
  }

  const getStatusBadge = (status: 'healthy' | 'warning' | 'error') => {
    const variants = {
      healthy: 'bg-green-100 text-green-700 border-green-200',
      warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      error: 'bg-red-100 text-red-700 border-red-200'
    }

    const labels = {
      healthy: '正常',
      warning: '警告',
      error: '错误'
    }

    return (
      <Badge variant="outline" className={variants[status]}>
        {getStatusIcon(status)}
        <span className="ml-1">{labels[status]}</span>
      </Badge>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Server className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">系统状态</CardTitle>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusBadge(systemHealth)}
            <Button 
              variant="outline" 
              size="sm"
              onClick={loadSystemStatus}
              disabled={refreshing}
            >
              <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="h-4 bg-gray-200 rounded animate-pulse w-24" />
                <div className="h-4 bg-gray-200 rounded animate-pulse w-16" />
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Service Status */}
            <div className="space-y-3">
              {services.map((service, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(service.status)}
                    <span className="text-sm font-medium">{service.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">{service.message}</div>
                    <div className="text-xs text-gray-400">
                      {new Date(service.lastCheck).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* System Metrics */}
            {stats.runtime && (
              <div className="pt-4 border-t space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center space-x-2">
                    <Activity className="h-4 w-4 text-blue-600" />
                    <div>
                      <div className="font-medium">活跃任务</div>
                      <div className="text-gray-600">{stats.runtime.active_tasks}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <div>
                      <div className="font-medium">已完成</div>
                      <div className="text-gray-600">{stats.runtime.completed_tasks}</div>
                    </div>
                  </div>
                </div>
                
                {stats.runtime.cached_graphs > 0 && (
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2">
                      <Database className="h-4 w-4 text-purple-600" />
                      <span>缓存图表</span>
                    </div>
                    <span className="text-gray-600">{stats.runtime.cached_graphs}</span>
                  </div>
                )}
              </div>
            )}

            {/* Storage Info */}
            {stats.storage && (
              <div className="pt-3 border-t">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <HardDrive className="h-4 w-4 text-gray-600" />
                    <span>存储使用</span>
                  </div>
                  <span className="text-gray-600">
                    {stats.storage.total_analyses || 0} 分析记录
                  </span>
                </div>
              </div>
            )}

            {/* Last Update */}
            <div className="pt-3 border-t text-xs text-gray-500 text-center">
              最后更新: {new Date().toLocaleString()}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
