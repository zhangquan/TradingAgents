import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  BarChart3, 
  ArrowUpIcon,
  ArrowDownIcon
} from 'lucide-react'
import SimpleLineChart from './SimpleLineChart'

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

interface StockListProps {
  stocks: StockItem[]
  selectedStockSymbol: string | null
  onStockSelect: (symbol: string) => void
  onLoadStockData: (symbols: string[]) => void
}

export default function StockList({ 
  stocks, 
  selectedStockSymbol, 
  onStockSelect,
  onLoadStockData
}: StockListProps) {
  
  const formatPrice = (price: number) => {
    if(!price) return ''
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price)
  }

  const formatChange = (change: number, isPercent: boolean = false) => {
    if(!change) return ''
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
    if(!volume) return;
    if (volume >= 1_000_000) {
      return `${(volume / 1_000_000).toFixed(1)}M`
    } else if (volume >= 1_000) {
      return `${(volume / 1_000).toFixed(1)}K`
    }
    return volume.toString()
  }

  return (
    <div className="w-full lg:w-80 flex flex-col h-96 lg:h-auto flex-shrink-0">
      <Card className="flex-1 min-h-0">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">股票列表</CardTitle>
          <CardDescription>选择股票查看详细信息</CardDescription>
        </CardHeader>
        <CardContent className="p-0 flex-1 min-h-0">
          <div className="h-full overflow-y-auto px-4 pb-4">
            <div className="space-y-3">
              {stocks.map((stock) => (
                <Card 
                  key={stock.symbol} 
                  className={`cursor-pointer transition-all ${
                    selectedStockSymbol === stock.symbol 
                      ? 'ring-2 ring-blue-500 bg-blue-50' 
                      : 'hover:shadow-md'
                  }`}
                  onClick={() => onStockSelect(stock.symbol)}
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
                                    onLoadStockData([symbol])
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
                    ) : stock.currentPrice !== undefined ? (
                      <>
                        {/* 顶部：股票代码和操作按钮 */}
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1 min-w-0">
                            <h3 className="font-bold text-lg text-gray-900 truncate">{stock.symbol}</h3>
                            <div className="flex items-baseline gap-2 mt-1">
                              <span className="text-lg font-semibold text-gray-900">
                                {formatPrice(stock.currentPrice || 0)}
                              </span>
                              <div className="text-sm">
                                {formatChange(stock.priceChangePct || 0, true)}
                              </div>
                            </div>
                            {stock.latestPriceDate && (
                              <div className="text-xs text-gray-500 mt-1">
                                截至 {stock.latestPriceDate}
                              </div>
                            )}
                          </div>
                          <div className="flex gap-1 ml-2">
                            <Button 
                              variant={selectedStockSymbol === stock.symbol ? 'default' : 'outline'}
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={(e) => {
                                e.stopPropagation()
                                onStockSelect(stock.symbol)
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
                            showTooltip={true}
                          />
                        </div>

                        {/* 底部：额外信息 */}
                        <div className="space-y-2">
                          {/* 成交量 */}
                          <div className="flex justify-between items-center text-xs text-gray-500">
                            <span>成交量</span>
                            <span className="font-medium">
                              {formatVolume(stock.volume || 0)}
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
  )
}
