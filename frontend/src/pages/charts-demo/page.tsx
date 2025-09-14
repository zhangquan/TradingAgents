import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { BarChart3, TrendingUp, Activity } from 'lucide-react'
import { apiService } from '@/lib/api'
import { toast } from 'sonner'
import EChartsCandlestick from '@/components/EChartsCandlestick'
import MiniEChartsCandlestick from '@/components/MiniEChartsCandlestick'
import AdvancedKLineChart from '@/components/AdvancedKLineChart'

interface ChartData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export default function ChartsDemoPage() {
  const [stockData, setStockData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL')
  const [availableStocks, setAvailableStocks] = useState<string[]>([])
  
  // 图表配置状态
  const [showVolume, setShowVolume] = useState(true)
  const [showMA, setShowMA] = useState(true)
  const [showMACD, setShowMACD] = useState(false)
  const [showRSI, setShowRSI] = useState(false)
  const [maTypes, setMATypes] = useState([5, 10, 20, 60])

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (selectedSymbol) {
      loadChartData(selectedSymbol)
    }
  }, [selectedSymbol])

  const loadInitialData = async () => {
    try {
      const stocksResponse = await apiService.getAvailableStocks()
      setAvailableStocks(stocksResponse.stocks || [])
      
      if (stocksResponse.stocks && stocksResponse.stocks.length > 0) {
        setSelectedSymbol(stocksResponse.stocks[0])
      }
    } catch (error) {
      console.error('加载初始数据失败:', error)
      toast.error('加载股票列表失败')
    }
  }

  const loadChartData = async (symbol: string) => {
    try {
      setLoading(true)
      const currentDate = new Date().toISOString().split('T')[0]
      const response = await apiService.getStockData(symbol, currentDate, 60)
      
      if (response.data && Array.isArray(response.data)) {
        const chartData: ChartData[] = response.data.map(item => ({
          date: new Date(item.Date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
          open: item.Open || 0,
          high: item.High || 0,
          low: item.Low || 0,
          close: item.Close || 0,
          volume: item.Volume || 0
        }))
        setStockData(chartData)
      } else {
        setStockData([])
        toast.error(`未找到 ${symbol} 的数据`)
      }
    } catch (error) {
      console.error('加载图表数据失败:', error)
      toast.error('加载图表数据失败')
      setStockData([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="space-y-6">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-6 w-6 text-blue-600" />
            <h1 className="text-3xl font-bold">ECharts 图表演示</h1>
          </div>
          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <div className="h-6 bg-gray-200 rounded animate-pulse" />
              </CardHeader>
              <CardContent>
                <div className="h-96 bg-gray-200 rounded animate-pulse" />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-6 w-6 text-blue-600" />
            <h1 className="text-3xl font-bold">ECharts 6.0.0 图表演示</h1>
            <Badge variant="outline" className="text-blue-600 border-blue-600">
              专业级K线图
            </Badge>
          </div>
        </div>

        {/* 股票选择器 */}
        <Card>
          <CardHeader>
            <CardTitle>股票选择</CardTitle>
            <CardDescription>选择要查看的股票</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {availableStocks.slice(0, 10).map(symbol => (
                <Button
                  key={symbol}
                  variant={selectedSymbol === symbol ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedSymbol(symbol)}
                >
                  {symbol}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 图表配置 */}
        <Card>
          <CardHeader>
            <CardTitle>图表配置</CardTitle>
            <CardDescription>自定义图表显示选项</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-volume"
                  checked={showVolume}
                  onCheckedChange={setShowVolume}
                />
                <Label htmlFor="show-volume">显示成交量</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-ma"
                  checked={showMA}
                  onCheckedChange={setShowMA}
                />
                <Label htmlFor="show-ma">显示移动平均线</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-macd"
                  checked={showMACD}
                  onCheckedChange={setShowMACD}
                />
                <Label htmlFor="show-macd">显示MACD</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-rsi"
                  checked={showRSI}
                  onCheckedChange={setShowRSI}
                />
                <Label htmlFor="show-rsi">显示RSI</Label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 图表展示 */}
        <Tabs defaultValue="advanced" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="advanced">高级K线图</TabsTrigger>
            <TabsTrigger value="basic">基础K线图</TabsTrigger>
            <TabsTrigger value="mini">迷你K线图</TabsTrigger>
            <TabsTrigger value="comparison">对比展示</TabsTrigger>
          </TabsList>

          <TabsContent value="advanced" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5" />
                  <span>高级K线图 - {selectedSymbol}</span>
                </CardTitle>
                <CardDescription>
                  完整功能的专业级K线图，支持成交量、技术指标等
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AdvancedKLineChart
                  data={stockData}
                  height="600px"
                  showVolume={showVolume}
                  showMA={showMA}
                  showMACD={showMACD}
                  showRSI={showRSI}
                  maTypes={maTypes}
                  title={`${selectedSymbol} 高级K线图`}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="basic" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5" />
                  <span>基础K线图 - {selectedSymbol}</span>
                </CardTitle>
                <CardDescription>
                  基础K线图，支持成交量和移动平均线
                </CardDescription>
              </CardHeader>
              <CardContent>
                <EChartsCandlestick
                  data={stockData}
                  height="400px"
                  showVolume={showVolume}
                  showMA={showMA}
                  maTypes={maTypes}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="mini" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5" />
                  <span>迷你K线图 - {selectedSymbol}</span>
                </CardTitle>
                <CardDescription>
                  紧凑的K线图，适用于卡片和小空间显示
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <h4 className="font-medium">标准尺寸</h4>
                    <MiniEChartsCandlestick
                      data={stockData.slice(-7)}
                      height="128px"
                    />
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">中等尺寸</h4>
                    <MiniEChartsCandlestick
                      data={stockData.slice(-10)}
                      height="160px"
                    />
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">大尺寸</h4>
                    <MiniEChartsCandlestick
                      data={stockData.slice(-14)}
                      height="200px"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="comparison" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>基础K线图</CardTitle>
                  <CardDescription>简洁的K线显示</CardDescription>
                </CardHeader>
                <CardContent>
                  <EChartsCandlestick
                    data={stockData}
                    height="300px"
                    showVolume={false}
                    showMA={false}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>带移动平均线</CardTitle>
                  <CardDescription>包含MA指标</CardDescription>
                </CardHeader>
                <CardContent>
                  <EChartsCandlestick
                    data={stockData}
                    height="300px"
                    showVolume={false}
                    showMA={true}
                    maTypes={[5, 20]}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>带成交量</CardTitle>
                  <CardDescription>K线图 + 成交量</CardDescription>
                </CardHeader>
                <CardContent>
                  <EChartsCandlestick
                    data={stockData}
                    height="300px"
                    showVolume={true}
                    showMA={false}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>完整功能</CardTitle>
                  <CardDescription>所有功能启用</CardDescription>
                </CardHeader>
                <CardContent>
                  <EChartsCandlestick
                    data={stockData}
                    height="300px"
                    showVolume={true}
                    showMA={true}
                    maTypes={[5, 10, 20]}
                  />
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* 数据统计 */}
        <Card>
          <CardHeader>
            <CardTitle>数据统计</CardTitle>
            <CardDescription>当前数据的基本统计信息</CardDescription>
          </CardHeader>
          <CardContent>
            {stockData.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">数据点数</p>
                  <p className="text-lg font-bold">{stockData.length}</p>
                </div>
                <div>
                  <p className="text-gray-600">最新价格</p>
                  <p className="text-lg font-bold">${stockData[stockData.length - 1]?.close.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-gray-600">最高价</p>
                  <p className="text-lg font-bold">${Math.max(...stockData.map(d => d.high)).toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-gray-600">最低价</p>
                  <p className="text-lg font-bold">${Math.min(...stockData.map(d => d.low)).toFixed(2)}</p>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">暂无数据</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
