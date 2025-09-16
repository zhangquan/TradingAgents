
import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

import { 
  TrendingUp, 
  TrendingDown,
  Activity, 
  BarChart3, 
  DollarSign,
  Volume2,
  ArrowUpIcon,
  ArrowDownIcon,
  RefreshCw,
  Calendar,
  Eye,
  Star
} from 'lucide-react'
import { apiService, StockSummary, MarketOverviewResponse, NoDataError } from '@/lib/api'
import { toast } from 'sonner'
import { Link } from 'react-router-dom'
import SimpleLineChart from './SimpleLineChart'
import StockDetailPanel from './StockDetailPanel'

interface ChartData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface StockItem {
  symbol: string
  summary?: StockSummary
  chartData?: ChartData[]
  simpleChartData?: { date: string; close: number }[]
  loading: boolean
  error?: string
  noDataInfo?: {
    error: string
    error_type: string
    symbol: string
    requested_period: string
    requested_date: string
    suggestions: string[]
    available_symbols: string[]
  }
}


export default function StockDataDashboard() {
  const [availableStocks, setAvailableStocks] = useState<string[]>([])
  const [selectedStocks, setSelectedStocks] = useState<StockItem[]>([])
  const [marketOverview, setMarketOverview] = useState<MarketOverviewResponse | null>(null)
  const [supportedIndicators, setSupportedIndicators] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [currentDate] = useState(() => new Date().toISOString().split('T')[0])
  const [showCharts, setShowCharts] = useState(false)
  const [selectedStockSymbol, setSelectedStockSymbol] = useState<string | null>(null)
  const [stocksSource, setStocksSource] = useState<string>('')
  const [userId] = useState('demo_user')

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      setLoading(true)
      
      // 并行加载所有初始数据
      const [stocksResponse, indicatorsResponse] = await Promise.all([
        apiService.getAvailableStocks(),
        apiService.getSupportedIndicators()
      ])

      // 设置可用股票
      setAvailableStocks(stocksResponse.stocks || [])
      setStocksSource(stocksResponse.source || 'all_available')
      
      // 设置支持的指标
      setSupportedIndicators(indicatorsResponse.indicators || {})

      // 自动加载股票数据
      const stocksToLoad = (stocksResponse.stocks || []).slice(0, 5)
      if (stocksToLoad.length > 0) {
        await loadStockData(stocksToLoad)
      }

    } catch (error) {
      console.error('加载初始数据失败:', error)
      toast.error('加载股票数据失败')
    } finally {
      setLoading(false)
    }
  }

  const loadStockData = async (symbols: string[]) => {
    // 初始化股票项
    const stockItems: StockItem[] = symbols.map(symbol => ({
      symbol,
      loading: true
    }))
    setSelectedStocks(stockItems)

    // 为每个股票加载数据
    const updatedStocks = await Promise.all(
      symbols.map(async (symbol) => {
        try {
          // 并行加载摘要数据和图表数据
          const [summaryResult, stockDataResponse] = await Promise.all([
            apiService.getStockSummary(symbol, currentDate, 30),
            apiService.getStockData(symbol, currentDate, 7) // 只加载7天的数据用于小图表
              .catch(e => {
                console.warn(`获取 ${symbol} 图表数据失败:`, e)
                return { data: [] }
              })
          ])

          // Check if summary result is a NoDataError
          if ('error_type' in summaryResult && summaryResult.error_type === 'no_data') {
            return {
              symbol,
              loading: false,
              noDataInfo: summaryResult as NoDataError
            }
          }

          const summary = summaryResult as StockSummary

          // 转换图表数据格式
          const chartData: ChartData[] = stockDataResponse.data && Array.isArray(stockDataResponse.data) 
            ? stockDataResponse.data.map(item => ({
                date: new Date(item.Date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }),
                open: item.Open || 0,
                high: item.High || 0,
                low: item.Low || 0,
                close: item.Close || 0,
                volume: item.Volume || 0
              }))
            : []

          // 为简单折线图准备数据
          const simpleChartData = chartData.map(item => ({
            date: item.date,
            close: item.close
          }))

          return {
            symbol,
            summary,
            chartData,
            simpleChartData,
            loading: false
          }
        } catch (error) {
          console.error(`加载 ${symbol} 数据失败:`, error)
          return {
            symbol,
            loading: false,
            error: '加载失败'
          }
        }
      })
    )

    setSelectedStocks(updatedStocks)
  }

  const refreshData = async () => {
    setRefreshing(true)
    try {
      // 刷新市场概览
      const marketResponse = await apiService.getMarketOverviewNew(undefined, currentDate)
      setMarketOverview(marketResponse)

      // 刷新选中的股票数据
      if (selectedStocks.length > 0) {
        const symbols = selectedStocks.map(stock => stock.symbol)
        await loadStockData(symbols)
      }

      toast.success('数据刷新成功')
    } catch (error) {
      console.error('刷新数据失败:', error)
      toast.error('刷新数据失败')
    } finally {
      setRefreshing(false)
    }
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price)
  }

  const formatChange = (change: number, isPercent: boolean = false) => {
    const formatted = isPercent 
      ? `${change > 0 ? '+' : ''}${change.toFixed(2)}%`
      : `${change > 0 ? '+' : ''}${formatPrice(change)}`
    
    return (
      <span className={`flex items-center ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
        {change >= 0 ? <ArrowUpIcon className="h-3 w-3 mr-1" /> : <ArrowDownIcon className="h-3 w-3 mr-1" />}
        {formatted}
      </span>
    )
  }

  const formatVolume = (volume: number) => {
    if (volume >= 1_000_000) {
      return `${(volume / 1_000_000).toFixed(1)}M`
    } else if (volume >= 1_000) {
      return `${(volume / 1_000).toFixed(1)}K`
    }
    return volume.toString()
  }


  const handleStockSelect = (symbol: string) => {
    setSelectedStockSymbol(symbol)
  }




  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-6 w-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">股票数据仪表板</h2>
          </div>
        </div>
        
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="h-6 bg-gray-200 rounded animate-pulse" />
                <div className="h-4 bg-gray-200 rounded animate-pulse" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-8 bg-gray-200 rounded animate-pulse" />
                  <div className="h-4 bg-gray-200 rounded animate-pulse" />
                  <div className="h-4 bg-gray-200 rounded animate-pulse" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 min-h-screen lg:h-screen flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-6 w-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">股票数据仪表板</h2>
          <Badge variant="outline" className="text-blue-600 border-blue-600">
            {availableStocks.length} 支股票可用
          </Badge>
          {stocksSource === 'user_watchlist' && (
            <Badge variant="default" className="bg-green-100 text-green-800 border-green-300">
              关注列表
            </Badge>
          )}
          {stocksSource === 'all_available' && (
            <Badge variant="secondary">
              全部股票
            </Badge>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <div className="text-sm text-gray-500 flex items-center">
            <Calendar className="h-4 w-4 mr-1" />
            {currentDate}
          </div>
          <Link to="/watchlist">
            <Button variant="outline" size="sm">
              <Star className="h-4 w-4 mr-2" />
              管理关注
            </Button>
          </Link>
          <Button variant="outline" size="sm" onClick={refreshData} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* Main Content - Left-Right Layout */}
      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
        {/* Left Panel - Stock Cards */}
        <div className="w-full lg:w-80 flex flex-col h-96 lg:h-auto flex-shrink-0">
          <Card className="flex-1 min-h-0">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">股票列表</CardTitle>
              <CardDescription>选择股票查看详细信息</CardDescription>
            </CardHeader>
            <CardContent className="p-0 flex-1 min-h-0">
              <div className="h-full overflow-y-auto px-4 pb-4">
                <div className="space-y-3">
                  {selectedStocks.map((stock) => (
                    <Card 
                      key={stock.symbol} 
                      className={`cursor-pointer transition-all ${
                        selectedStockSymbol === stock.symbol 
                          ? 'ring-2 ring-blue-500 bg-blue-50' 
                          : 'hover:shadow-md'
                      }`}
                      onClick={() => handleStockSelect(stock.symbol)}
                    >
                      <CardContent className="p-4">
                        {stock.loading ? (
                          <div className="space-y-3">
                            <div className="h-5 bg-gray-200 rounded animate-pulse" />
                            <div className="h-12 bg-gray-200 rounded animate-pulse" />
                            <div className="h-4 bg-gray-200 rounded animate-pulse" />
                          </div>
                        ) : stock.noDataInfo ? (
                          <div className="space-y-4">
                            <div className="flex items-center space-x-2">
                              <Badge variant="outline" className="text-gray-600">
                                {stock.noDataInfo.symbol}
                              </Badge>
                              <Badge variant="secondary" className="text-orange-600">
                                无数据
                              </Badge>
                            </div>
                            <div className="text-sm text-gray-600">
                              <p className="font-medium text-gray-800 mb-2">
                                {stock.noDataInfo.error}
                              </p>
                              <div className="space-y-1 text-xs">
                                <p><span className="font-medium">请求期间:</span> {stock.noDataInfo.requested_period}</p>
                                <p><span className="font-medium">请求日期:</span> {stock.noDataInfo.requested_date}</p>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <p className="text-xs font-medium text-gray-700">建议:</p>
                              <ul className="text-xs text-gray-600 space-y-1">
                                {stock.noDataInfo.suggestions.map((suggestion, index) => (
                                  <li key={index} className="flex items-start">
                                    <span className="text-gray-400 mr-1">•</span>
                                    {suggestion}
                                  </li>
                                ))}
                              </ul>
                            </div>
                            {stock.noDataInfo.available_symbols.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-xs font-medium text-gray-700">可用股票:</p>
                                <div className="flex flex-wrap gap-1">
                                  {stock.noDataInfo.available_symbols.slice(0, 5).map((symbol) => (
                                    <Badge 
                                      key={symbol} 
                                      variant="outline" 
                                      className="text-xs cursor-pointer hover:bg-blue-50"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        loadStockData([symbol])
                                      }}
                                    >
                                      {symbol}
                                    </Badge>
                                  ))}
                                  {stock.noDataInfo.available_symbols.length > 5 && (
                                    <Badge variant="outline" className="text-xs">
                                      +{stock.noDataInfo.available_symbols.length - 5}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        ) : stock.error ? (
                          <div className="text-red-600 text-sm">{stock.error}</div>
                        ) : stock.summary ? (
                          <>
                            {/* 顶部：股票代码和操作按钮 */}
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex-1 min-w-0">
                                <h3 className="font-bold text-lg text-gray-900 truncate">{stock.symbol}</h3>
                                <div className="flex items-baseline gap-2 mt-1">
                                  <span className="text-lg font-semibold text-gray-900">
                                    {formatPrice(stock.summary.price_info.current_price)}
                                  </span>
                                  <div className="text-sm">
                                    {formatChange(stock.summary.price_info.price_change_pct, true)}
                                  </div>
                                </div>
                              </div>
                              <div className="flex gap-1 ml-2">
                                <Button 
                                  variant={selectedStockSymbol === stock.symbol ? 'default' : 'outline'}
                                  size="sm"
                                  className="h-7 w-7 p-0"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleStockSelect(stock.symbol)
                                  }}
                                  title="查看详情"
                                >
                                  <BarChart3 className="h-3.5 w-3.5" />
                                </Button>
                              </div>
                            </div>

                            {/* 中部：价格趋势图 */}
                            <div className="mb-3">
                              <SimpleLineChart 
                                data={stock.simpleChartData || []} 
                                width={280}
                                height={60}
                                className="w-full"
                              />
                            </div>

                            {/* 底部：价格区间和额外信息 */}
                            <div className="space-y-2">
                              {/* 价格区间 */}
                              <div className="flex justify-between items-center text-sm">
                                <div className="flex items-center gap-2">
                                  <span className="text-gray-500">区间</span>
                                  <span className="font-medium text-gray-700">
                                    {formatPrice(stock.summary?.price_info?.low_price)}
                                  </span>
                                  <span className="text-gray-400">-</span>
                                  <span className="font-medium text-gray-700">
                                    {formatPrice(stock.summary?.price_info?.high_price)}
                                  </span>
                                </div>
                                <div className="text-xs text-gray-500">
                                  {stock.chartData?.length || 0}天
                                </div>
                              </div>
                              
                              {/* 成交量 */}
                              <div className="flex justify-between items-center text-xs text-gray-500">
                                <span>成交量</span>
                                <span className="font-medium">
                                  {formatVolume(stock.summary?.volume_info?.latest_volume)}
                                </span>
                              </div>
                            </div>
                          </>
                        ) : null}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Panel - Details */}
        <div className="flex-1 flex flex-col min-h-96 lg:min-h-0 min-w-0">
          <StockDetailPanel 
            selectedStockSymbol={selectedStockSymbol}
            currentDate={currentDate}
          />
        </div>
      </div>
    </div>
  )
}
