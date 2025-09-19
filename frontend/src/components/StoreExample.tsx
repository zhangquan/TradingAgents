import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useWatchlistStore } from '@/store/watchlistStore'
import { useStockStore } from '@/store/stockStore'
import { useNotificationsStore } from '@/store/notificationsStore'
import { useAnalysisStore } from '@/store/analysisStore'
import { useReportsStore } from '@/store/reportsStore'
import { Star, TrendingUp, Bell, FileText, Settings } from 'lucide-react'

/**
 * Example component demonstrating how to use multiple Zustand stores
 * This component shows a dashboard that uses data from different stores
 */
export function StoreExample() {
  // Use multiple stores
  const { symbols: watchlistSymbols, loadWatchlist } = useWatchlistStore()
  const { availableStocks, loadAvailableStocks } = useStockStore()
  const { unreadCount, loadNotifications } = useNotificationsStore()
  const { tasks, loadTasks } = useAnalysisStore()
  const { reports, loadReports } = useReportsStore()

  // Load data from all stores on mount
  useEffect(() => {
    loadWatchlist()
    loadAvailableStocks()
    loadNotifications()
    loadTasks()
    loadReports()
  }, [])

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
      {/* Watchlist Summary */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">关注股票</CardTitle>
          <Star className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{watchlistSymbols.length}</div>
          <p className="text-xs text-muted-foreground">
            共 {availableStocks.length} 个可用股票
          </p>
          <div className="mt-2">
            {watchlistSymbols.slice(0, 3).map(symbol => (
              <Badge key={symbol} variant="secondary" className="mr-1">
                {symbol}
              </Badge>
            ))}
            {watchlistSymbols.length > 3 && (
              <Badge variant="outline">+{watchlistSymbols.length - 3}</Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stock Data Summary */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">股票数据</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{availableStocks.length}</div>
          <p className="text-xs text-muted-foreground">
            可用股票总数
          </p>
          <div className="mt-2">
            <Badge variant="default">数据源已连接</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Notifications Summary */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">通知</CardTitle>
          <Bell className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{unreadCount}</div>
          <p className="text-xs text-muted-foreground">
            未读通知
          </p>
          <div className="mt-2">
            {unreadCount > 0 ? (
              <Badge variant="destructive">需要处理</Badge>
            ) : (
              <Badge variant="secondary">全部已读</Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Analysis Tasks Summary */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">分析任务</CardTitle>
          <Settings className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{tasks.length}</div>
          <p className="text-xs text-muted-foreground">
            当前任务总数
          </p>
          <div className="mt-2">
            {tasks.filter(task => task.enabled).length > 0 ? (
              <Badge variant="default">
                {tasks.filter(task => task.enabled).length} 个已启用
              </Badge>
            ) : (
              <Badge variant="secondary">无启用任务</Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Reports Summary */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">分析报告</CardTitle>
          <FileText className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{reports.length}</div>
          <p className="text-xs text-muted-foreground">
            总报告数量
          </p>
          <div className="mt-2">
            <Badge variant="default">已同步</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Actions Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">快速操作</CardTitle>
          <CardDescription>
            使用 Zustand stores 进行状态管理
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button 
            size="sm" 
            onClick={() => {
              loadWatchlist()
              loadAvailableStocks()
              loadNotifications()
              loadTasks()
              loadReports()
            }}
            className="w-full"
          >
            刷新所有数据
          </Button>
          <p className="text-xs text-muted-foreground">
            所有数据将从各自的 store 重新加载
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
