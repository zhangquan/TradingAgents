

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Trash2, Plus, Star, StarOff, AlertCircle, Check } from 'lucide-react'
import { useWatchlistStore } from '@/store/watchlistStore'
import { useStockStore } from '@/store/stockStore'
import { toast } from 'sonner'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function WatchlistManager() {
  const [newSymbol, setNewSymbol] = useState('')
  const [addingStock, setAddingStock] = useState(false)
  
  // Zustand stores
  const {
    symbols: watchlistSymbols,
    isLoading: watchlistLoading,
    error: watchlistError,
    loadWatchlist,
    addToWatchlist,
    removeFromWatchlist,
    clearError: clearWatchlistError,
    isInWatchlist
  } = useWatchlistStore()
  
  const {
    availableStocks,
    isLoading: stocksLoading,
    error: stocksError,
    loadAvailableStocks,
    clearError: clearStocksError
  } = useStockStore()
  
  const loading = watchlistLoading || stocksLoading

  useEffect(() => {
    loadWatchlist()
    loadAvailableStocks()
  }, [])

  const handleAddStock = async () => {
    if (!newSymbol.trim()) return

    const symbol = newSymbol.trim().toUpperCase()
    
    try {
      setAddingStock(true)
      await addToWatchlist(symbol)
      setNewSymbol('')
      toast.success(`股票 ${symbol} 已添加到关注列表`)
    } catch (error: any) {
      console.error('Failed to add stock:', error)
      const errorMsg = error.response?.data?.detail || "添加股票失败"
      toast.error(errorMsg)
    } finally {
      setAddingStock(false)
    }
  }

  const handleRemoveStock = async (symbol: string) => {
    try {
      await removeFromWatchlist(symbol)
      toast.success(`股票 ${symbol} 已从关注列表中移除`)
    } catch (error: any) {
      console.error('Failed to remove stock:', error)
      const errorMsg = error.response?.data?.detail || "移除股票失败"
      toast.error(errorMsg)
    }
  }

  const getStockBadgeVariant = (symbol: string) => {
    return availableStocks.includes(symbol) ? "default" : "destructive"
  }

  const getStockStatus = (symbol: string) => {
    return availableStocks.includes(symbol) ? "available" : "unavailable"
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>关注股票管理</CardTitle>
          <CardDescription>管理您关注的股票列表</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="text-gray-500">加载中...</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Star className="h-5 w-5" />
          关注股票管理
        </CardTitle>
        <CardDescription>
          管理您关注的股票列表，关注的股票将在股票数据中优先显示
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 添加新股票 */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium">添加股票到关注列表</h3>
          <div className="flex gap-2">
            <Input
              placeholder="输入股票代码 (如: AAPL)"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              onKeyPress={(e) => e.key === 'Enter' && handleAddStock()}
              className="flex-1"
            />
            <Button 
              onClick={handleAddStock} 
              disabled={!newSymbol.trim() || addingStock}
              className="flex items-center gap-2"
            >
              {addingStock ? (
                <>加载中...</>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  添加
                </>
              )}
            </Button>
          </div>
          <div className="text-xs text-gray-500">
            可用股票: {availableStocks.length} 个
          </div>
        </div>

        {/* 当前关注列表 */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">当前关注列表</h3>
            <Badge variant="outline">
              {watchlistSymbols.length} 个股票
            </Badge>
          </div>

          {/* Show error alerts */}
          {(watchlistError || stocksError) && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {watchlistError || stocksError}
              </AlertDescription>
            </Alert>
          )}

          {/* Show unavailable stocks */}
          {watchlistSymbols.length > 0 && (
            <div>
              {watchlistSymbols.filter(symbol => !availableStocks.includes(symbol)).length > 0 && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    注意：{watchlistSymbols.filter(symbol => !availableStocks.includes(symbol)).length} 个关注的股票暂无数据: {watchlistSymbols.filter(symbol => !availableStocks.includes(symbol)).join(', ')}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}

          {watchlistSymbols.length > 0 ? (
            <div className="grid gap-2">
              {watchlistSymbols.map((symbol) => {
                const status = getStockStatus(symbol)
                return (
                  <div
                    key={symbol}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        {status === 'available' ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        )}
                        <span className="font-medium">{symbol}</span>
                      </div>
                      <Badge variant={getStockBadgeVariant(symbol)}>
                        {status === 'available' ? '有数据' : '无数据'}
                      </Badge>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRemoveStock(symbol)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <StarOff className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>您还没有关注任何股票</p>
              <p className="text-sm">添加股票到关注列表以便快速访问</p>
            </div>
          )}
        </div>

        {/* 统计信息 */}
        {watchlistSymbols.length > 0 && (
          <div className="grid grid-cols-3 gap-4 pt-4 border-t">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {watchlistSymbols.length}
              </div>
              <div className="text-xs text-gray-500">总关注</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {watchlistSymbols.filter(symbol => availableStocks.includes(symbol)).length}
              </div>
              <div className="text-xs text-gray-500">有数据</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {watchlistSymbols.filter(symbol => !availableStocks.includes(symbol)).length}
              </div>
              <div className="text-xs text-gray-500">无数据</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

