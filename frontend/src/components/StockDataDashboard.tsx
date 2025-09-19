
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
import { stockApi } from '@/api/stock'
import { conversationApi } from '@/api/conversation'
import { MarketOverviewResponse, NoDataError, ConversationFullDetail } from '@/api/types'
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
 
  const navigate = useNavigate()
  const [currentDate] = useState(() => new Date().toISOString().split('T')[0])

  const [selectedStockSymbol, setSelectedStockSymbol] = useState<string | null>( null)
  const [stocksSource, setStocksSource] = useState<string>('')
  const [userId] = useState('demo_user')
  const [newestConversation, setNewestConversation] = useState<ConversationFullDetail | null>(null)
  const [loadingConversation, setLoadingConversation] = useState(false)


  // 监听 URL 参数变化
  useEffect(() => {
    if (selectedStockSymbol) {
      setSelectedStockSymbol(selectedStockSymbol)
      
      // 加载该股票的最新对话
      loadNewestConversation(selectedStockSymbol)
    }
  }, [ selectedStockSymbol])

 



  const loadNewestConversation = async (ticker: string) => {
    if (!ticker || loadingConversation) return
    
    setLoadingConversation(true)
    try {
      const conversation = await conversationApi.getNewestConversationByStock(userId, ticker)
      setNewestConversation(conversation)
    } catch (error) {
      console.error('Failed to load newest conversation:', error)
      setNewestConversation(null)
    } finally {
      setLoadingConversation(false)
    }
  }

  const handleStockSelect = (symbol: string) => {
    setSelectedStockSymbol(symbol)
       // 加载该股票的最新对话
    loadNewestConversation(symbol)
    // 更新 URL 以支持直接访问和刷新保持状态
    navigate(`/stocks/${symbol}`, { replace: true })
    
 
  }



  return (
    <div className="space-y-6 min-h-screen lg:h-screen flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-6 w-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">股票数据仪表板</h2>
          <Badge variant="outline" className="text-blue-600 border-blue-600">
            股票数据
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
          {/* Show newest conversation info */}
          {selectedStockSymbol && newestConversation && (
            <Badge variant="outline" className="text-purple-600 border-purple-600">
              最新对话: {newestConversation.analysis_date}
            </Badge>
          )}
          {selectedStockSymbol && loadingConversation && (
            <Badge variant="outline" className="text-gray-600 border-gray-600">
              <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
              加载对话...
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
         
        </div>
      </div>

      {/* Main Content - Left-Right Layout */}
      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
        {/* Left Panel - Stock List */}
        <StockList 
          selectedStockSymbol={selectedStockSymbol}
          onStockSelect={handleStockSelect}
          currentDate={currentDate}
        />

        {/* Right Panel - Details */}
        <div className="flex-1 flex flex-col min-h-96 lg:min-h-0 min-w-0">
          <StockDetailPanel 
            selectedStockSymbol={selectedStockSymbol}
            currentDate={currentDate}
            selectedSessionId={newestConversation?.session_id || null}
          />
        </div>
      </div>
    </div>
  )
}
