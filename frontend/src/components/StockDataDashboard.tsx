
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

import { 
  BarChart3, 
  RefreshCw,
  Calendar,
  Star
} from 'lucide-react'
import { apiService, MarketOverviewResponse, NoDataError } from '@/lib/api'
import { toast } from 'sonner'
import { Link, useParams, useNavigate } from 'react-router-dom'
import StockList from './StockList'
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
  // 计算出的价格信息
  currentPrice?: number
  priceChange?: number
  priceChangePct?: number
  volume?: number
  latestPriceDate?: string  // 最新价格的日期
}


export default function StockDataDashboard() {
  const { symbol, sessionId } = useParams<{ symbol?: string, sessionId?: string }>()
  const navigate = useNavigate()
  
  const [availableStocks, setAvailableStocks] = useState<string[]>([])
  const [selectedStocks, setSelectedStocks] = useState<StockItem[]>([])
  const [marketOverview, setMarketOverview] = useState<MarketOverviewResponse | null>(null)
  const [supportedIndicators, setSupportedIndicators] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [currentDate] = useState(() => new Date().toISOString().split('T')[0])
  const [showCharts, setShowCharts] = useState(false)
  const [selectedStockSymbol, setSelectedStockSymbol] = useState<string | null>(symbol || null)
  const [stocksSource, setStocksSource] = useState<string>('')
  const [userId] = useState('demo_user')

  useEffect(() => {
    loadInitialData()
  }, [])

  // 监听 URL 参数变化
  useEffect(() => {
    if (symbol && symbol !== selectedStockSymbol) {
      setSelectedStockSymbol(symbol)
      
      // 如果该股票不在当前加载的列表中，则加载它
      const isStockLoaded = selectedStocks.some(stock => stock.symbol === symbol)
      if (!isStockLoaded && !loading) {
        // 将新股票添加到列表中
        const currentSymbols = selectedStocks.map(stock => stock.symbol)
        if (!currentSymbols.includes(symbol)) {
          loadStockData([...currentSymbols, symbol])
        }
      }
    }
  }, [symbol, selectedStocks, loading])

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
          // 只使用 getStockData 加载数据
          const stockDataResponse = await apiService.getStockData(symbol, currentDate, 30) // 加载30天的数据用于小图表

          // 检查是否有数据
          if (!stockDataResponse.data || !Array.isArray(stockDataResponse.data) || stockDataResponse.data.length === 0) {
            return {
              symbol,
              loading: false,
              noDataInfo: {
                error: `没有找到 ${symbol} 的数据`,
                error_type: 'no_data',
                symbol: symbol,
                requested_period: '30天',
                requested_date: currentDate,
                suggestions: ['检查股票代码是否正确', '尝试选择不同的日期范围'],
                available_symbols: []
              }
            }
          }

          // 转换图表数据格式
          const chartData: ChartData[] = stockDataResponse.data.map(item => ({
            date: new Date(item.Date).toLocaleDateString('zh-CN', { 
              month: 'short', 
              day: 'numeric',
              weekday: 'short'
            }),
            open: item.Open || 0,
            high: item.High || 0,
            low: item.Low || 0,
            close: item.Close || 0,
            volume: item.Volume || 0
          }))

          // 为简单折线图准备数据
          const simpleChartData = chartData.map(item => ({
            date: item.date,
            close: item.close
          }))

          // 计算价格信息 - 使用最新和最早的数据
          const latestData = stockDataResponse.data[stockDataResponse.data.length - 1]
          const earliestData = stockDataResponse.data[0]
          
          const currentPrice = latestData?.Close || 0
          const previousPrice = earliestData?.Close || 0
          const priceChange = currentPrice - previousPrice
          const priceChangePct = previousPrice > 0 ? (priceChange / previousPrice) * 100 : 0
          const volume = latestData?.Volume || 0
          const latestPriceDate = latestData?.Date ? new Date(latestData.Date).toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
          }) : ''

          return {
            symbol,
            chartData,
            simpleChartData,
            currentPrice,
            priceChange,
            priceChangePct,
            volume,
            latestPriceDate,
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



  const handleStockSelect = (symbol: string) => {
    setSelectedStockSymbol(symbol)
    // 更新 URL 以支持直接访问和刷新保持状态
    navigate(`/stocks/${symbol}`, { replace: true })
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
        {/* Left Panel - Stock List */}
        <StockList 
          stocks={selectedStocks}
          selectedStockSymbol={selectedStockSymbol}
          onStockSelect={handleStockSelect}
          onLoadStockData={loadStockData}
        />

        {/* Right Panel - Details */}
        <div className="flex-1 flex flex-col min-h-96 lg:min-h-0 min-w-0">
          <StockDetailPanel 
            selectedStockSymbol={selectedStockSymbol}
            currentDate={currentDate}
            selectedSessionId={sessionId}
          />
        </div>
      </div>
    </div>
  )
}
