'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  TrendingUp, 
  TrendingDown,
  BarChart3,
  Activity,
  Eye,
  RefreshCw
} from 'lucide-react'
import { apiService, StockDataResponse, TechnicalIndicatorResponse } from '@/lib/api'
import { toast } from 'sonner'
import EChartsCandlestick from './EChartsCandlestick'
import EChartsWrapper from './EChartsWrapper'

interface StockChartsProps {
  symbol: string
  currentDate: string
  lookBackDays?: number
}

interface ChartData {
  date: string
  price: number
  volume: number
  open: number
  high: number
  low: number
  close: number
}

interface IndicatorData {
  [key: string]: any
}

// 生成更友好的指标显示名称
const getIndicatorDisplayName = (indicatorKey: string) => {
  switch (indicatorKey) {
    case 'close_50_sma': return 'SMA 50'
    case 'close_200_sma': return 'SMA 200'
    case 'close_10_ema': return 'EMA 10'
    case 'close_20_ema': return 'EMA 20'
    case 'macd': return 'MACD'
    case 'macds': return 'MACD信号'
    case 'macdh': return 'MACD柱'
    case 'rsi': return 'RSI'
    case 'rsi_6': return 'RSI 6'
    case 'rsi_14': return 'RSI 14'
    case 'boll': return '布林带'
    case 'boll_ub': return '布林上轨'
    case 'boll_lb': return '布林下轨'
    default: return indicatorKey.toUpperCase()
  }
}

export default function StockCharts({ symbol, currentDate, lookBackDays = 30 }: StockChartsProps) {
  const [stockData, setStockData] = useState<ChartData[]>([])
  const [indicators, setIndicators] = useState<Record<string, IndicatorData[]>>({})
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(['close_50_sma', 'rsi'])
  const [supportedIndicators, setSupportedIndicators] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const chartType = 'candlestick' // 固定为K线图
  const [showMA, setShowMA] = useState(true)
  const [showBollinger, setShowBollinger] = useState(true)
  const [showVolume, setShowVolume] = useState(true)
  const [showRSI, setShowRSI] = useState(false)
  const [showMACD, setShowMACD] = useState(false)
  const [maTypes, setMaTypes] = useState([5, 10, 20])

  useEffect(() => {
    loadChartData()
  }, [symbol, currentDate, lookBackDays])

  const loadChartData = async () => {
    try {
      setLoading(true)
      
      // 并行加载股票数据和支持的指标
      const [stockResponse, indicatorsResponse] = await Promise.all([
        apiService.getStockData(symbol, currentDate, lookBackDays).catch(e => {
          console.error('获取股票数据失败:', e)
          return { data: [] }
        }),
        apiService.getSupportedIndicators().catch(e => {
          console.error('获取支持的指标失败:', e)
          return { indicators: {} }
        })
      ])

      // 验证并转换股票数据格式
      if (stockResponse.data && Array.isArray(stockResponse.data) && stockResponse.data.length > 0) {
        const chartData: ChartData[] = stockResponse.data.map(item => ({
          date: new Date(item.Date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
          price: item.Close || 0,
          volume: item.Volume || 0,
          open: item.Open || 0,
          high: item.High || 0,
          low: item.Low || 0,
          close: item.Close || 0
        }))
        setStockData(chartData)
      } else {
        setStockData([])
        toast.error(`未找到 ${symbol} 的股票数据`)
      }

      setSupportedIndicators(indicatorsResponse.indicators || {})

      // 仅在有数据时加载默认技术指标
      if (stockResponse.data && stockResponse.data.length > 0) {
        await loadIndicators(selectedIndicators)
      }

    } catch (error) {
      console.error('加载图表数据失败:', error)
      toast.error('加载图表数据失败')
      setStockData([])
      setSupportedIndicators({})
    } finally {
      setLoading(false)
    }
  }

  const loadIndicators = async (indicatorNames: string[]) => {
    if (!indicatorNames || indicatorNames.length === 0) {
      return
    }

    try {
      const indicatorData: Record<string, IndicatorData[]> = {}
      
      // 并行加载所有指标，但跳过无效的指标
      const validIndicators = indicatorNames.filter(name => name && name.trim())
      
      if (validIndicators.length === 0) {
        return
      }

      const responses = await Promise.all(
        validIndicators.map(async (indicator) => {
          try {
            const response = await apiService.getTechnicalIndicator(symbol, indicator, currentDate, lookBackDays)
            return { indicator, response }
          } catch (error) {
            console.warn(`加载指标 ${indicator} 失败:`, error)
            return { indicator, response: null }
          }
        })
      )

      responses.forEach(({ indicator, response }) => {
        if (response && response.data && Array.isArray(response.data) && response.data.length > 0) {
          indicatorData[indicator] = response.data.map((item: any) => ({
            ...item,
            date: new Date(item.Date || item.date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
          }))
        }
      })

      setIndicators(indicatorData)
    } catch (error) {
      console.error('加载技术指标失败:', error)
      // 不显示错误toast，因为指标加载失败不应该阻止主要功能
    }
  }

  const refreshData = async () => {
    setRefreshing(true)
    try {
      await loadChartData()
      toast.success('图表数据刷新成功')
    } catch (error) {
      toast.error('刷新数据失败')
    } finally {
      setRefreshing(false)
    }
  }

  const toggleIndicator = async (indicator: string) => {
    const newSelectedIndicators = selectedIndicators.includes(indicator)
      ? selectedIndicators.filter(i => i !== indicator)
      : [...selectedIndicators, indicator]
    
    setSelectedIndicators(newSelectedIndicators)
    await loadIndicators(newSelectedIndicators)
  }

  const formatPrice = (value: number) => {
    return `$${value.toFixed(2)}`
  }

  const formatVolume = (value: number) => {
    if (value >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(1)}M`
    } else if (value >= 1_000) {
      return `${(value / 1_000).toFixed(1)}K`
    }
    return value.toString()
  }

  const getIndicatorColor = (indicator: string) => {
    const colors: Record<string, string> = {
      sma: '#8884d8',
      ema: '#82ca9d',
      rsi: '#ffc658',
      macd: '#ff7300',
      bb_upper: '#8dd1e1',
      bb_lower: '#d084d0',
      atr: '#87d068'
    }
    return colors[indicator] || '#8884d8'
  }

  // 生成价格图表的ECharts选项
  // 计算移动平均线
  const calculateMA = (data: ChartData[], period: number) => {
    const result: (number | null)[] = []
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(null)
      } else {
        let sum = 0
        for (let j = 0; j < period; j++) {
          sum += data[i - j].close
        }
        result.push(sum / period)
      }
    }
    return result
  }

  // 计算布林带
  const calculateBollingerBands = (data: ChartData[], period: number = 20, multiplier: number = 2) => {
    const ma = calculateMA(data, period)
    const upper: (number | null)[] = []
    const lower: (number | null)[] = []
    
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1 || ma[i] === null) {
        upper.push(null)
        lower.push(null)
      } else {
        // 计算标准差
        let sum = 0
        for (let j = 0; j < period; j++) {
          sum += Math.pow(data[i - j].close - ma[i]!, 2)
        }
        const std = Math.sqrt(sum / period)
        upper.push(ma[i]! + multiplier * std)
        lower.push(ma[i]! - multiplier * std)
      }
    }
    return { ma, upper, lower }
  }

  // 计算RSI
  const calculateRSI = (data: ChartData[], period: number = 14) => {
    const rsi: (number | null)[] = []
    const gains: number[] = []
    const losses: number[] = []
    
    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        gains.push(0)
        losses.push(0)
        rsi.push(null)
      } else {
        const change = data[i].close - data[i - 1].close
        gains.push(change > 0 ? change : 0)
        losses.push(change < 0 ? Math.abs(change) : 0)
        
        if (i < period) {
          rsi.push(null)
        } else {
          const avgGain = gains.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period
          const avgLoss = losses.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period
          const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
          rsi.push(100 - (100 / (1 + rs)))
        }
      }
    }
    return rsi
  }

  // 计算MACD
  const calculateMACD = (data: ChartData[], fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9) => {
    const emaFast = calculateEMA(data, fastPeriod)
    const emaSlow = calculateEMA(data, slowPeriod)
    
    const macd: (number | null)[] = []
    for (let i = 0; i < data.length; i++) {
      if (emaFast[i] !== null && emaSlow[i] !== null) {
        macd.push(emaFast[i]! - emaSlow[i]!)
      } else {
        macd.push(null)
      }
    }
    
    const signal = calculateEMAFromArray(macd, signalPeriod)
    const histogram: (number | null)[] = []
    
    for (let i = 0; i < data.length; i++) {
      if (macd[i] !== null && signal[i] !== null) {
        histogram.push(macd[i]! - signal[i]!)
      } else {
        histogram.push(null)
      }
    }
    
    return { macd, signal, histogram }
  }

  // 计算EMA
  const calculateEMA = (data: ChartData[], period: number) => {
    const ema: (number | null)[] = []
    const multiplier = 2 / (period + 1)
    
    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        ema.push(data[i].close)
      } else if (i < period) {
        // 使用简单平均作为初始值
        const sum = data.slice(0, i + 1).reduce((acc, item) => acc + item.close, 0)
        ema.push(sum / (i + 1))
      } else {
        ema.push((data[i].close * multiplier) + (ema[i - 1]! * (1 - multiplier)))
      }
    }
    return ema
  }

  // 从数组计算EMA（用于MACD信号线）
  const calculateEMAFromArray = (data: (number | null)[], period: number) => {
    const ema: (number | null)[] = []
    const multiplier = 2 / (period + 1)
    let validCount = 0
    let sum = 0
    
    for (let i = 0; i < data.length; i++) {
      if (data[i] !== null) {
        validCount++
        sum += data[i]!
        
        if (validCount === 1) {
          ema.push(data[i])
        } else if (validCount < period) {
          ema.push(sum / validCount)
        } else {
          ema.push((data[i]! * multiplier) + (ema[i - 1]! * (1 - multiplier)))
        }
      } else {
        ema.push(null)
      }
    }
    return ema
  }

  const getPriceChartOption = () => {
    if (!stockData || stockData.length === 0) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#999',
            fontSize: 14
          }
        }
      }
    }

    const dates = stockData.map(item => item.date)
    
    if (chartType === 'candlestick') {
      const ohlcData = stockData.map(item => [item.open, item.close, item.low, item.high])
      const volumeData = stockData.map(item => item.volume)
      
      // 计算技术指标
      const bollinger = calculateBollingerBands(stockData, 20, 2)
      const rsi = showRSI ? calculateRSI(stockData, 14) : []
      const macd = showMACD ? calculateMACD(stockData, 12, 26, 9) : { macd: [], signal: [], histogram: [] }
      
      const series: any[] = [
        {
          name: 'K线',
          type: 'candlestick',
          data: ohlcData,
          itemStyle: {
            color: '#ef4444',
            color0: '#10b981',
            borderColor: '#ef4444',
            borderColor0: '#10b981'
          },
          emphasis: {
            itemStyle: {
              color: '#ff6b6b',
              color0: '#51cf66',
              borderColor: '#ff6b6b',
              borderColor0: '#51cf66'
            }
          }
        }
      ]

      // 条件性添加移动平均线
      if (showMA) {
        const maColors = ['#ff9800', '#2196f3', '#9c27b0', '#4caf50']
        maTypes.forEach((type, index) => {
          const maData = calculateMA(stockData, type)
          series.push({
            name: `MA${type}`,
            type: 'line',
            data: maData,
            smooth: true,
            lineStyle: { color: maColors[index % maColors.length], width: 1.5 },
            showSymbol: false
          })
        })
      }

      // 条件性添加布林带
      if (showBollinger) {
        series.push(
          {
            name: '布林上轨',
            type: 'line',
            data: bollinger.upper,
            smooth: true,
            lineStyle: { color: '#ff7043', width: 1, type: 'dashed' },
            showSymbol: false
          },
          {
            name: '布林中轨',
            type: 'line',
            data: bollinger.ma,
            smooth: true,
            lineStyle: { color: '#607d8b', width: 1, type: 'dashed' },
            showSymbol: false
          },
          {
            name: '布林下轨',
            type: 'line',
            data: bollinger.lower,
            smooth: true,
            lineStyle: { color: '#4caf50', width: 1, type: 'dashed' },
            showSymbol: false
          }
        )
      }

      // 条件性添加成交量
      if (showVolume) {
        series.push({
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumeData,
          itemStyle: {
            color: function(params: any) {
              const dataIndex = params.dataIndex
              if (dataIndex >= 1) {
                return stockData[dataIndex].close >= stockData[dataIndex].open ? '#ef444433' : '#10b98133'
              }
              return '#ef444433'
            }
          }
        })
      }

      // 动态生成图例数据
      const legendData = ['K线']
      if (showMA) {
        maTypes.forEach(type => legendData.push(`MA${type}`))
      }
      if (showBollinger) {
        legendData.push('布林上轨', '布林中轨', '布林下轨')
      }
      if (showVolume) {
        legendData.push('成交量')
      }

      return {
        animation: false,
        backgroundColor: '#ffffff',
        tooltip: {
          trigger: 'axis',
          axisPointer: { 
            type: 'cross',
            lineStyle: { color: '#999', width: 1, type: 'dashed' }
          },
          backgroundColor: 'rgba(50, 50, 50, 0.9)',
          borderColor: '#333',
          borderWidth: 1,
          textStyle: { color: '#fff', fontSize: 12 },
          formatter: function (params: any) {
            let result = `<div style="font-weight: bold; margin-bottom: 5px;">${params[0].name}</div>`
            
            params.forEach((param: any) => {
              if (param.seriesName === 'K线' && param.data) {
                const data = param.data
                const change = data[1] - data[0]
                const changePercent = ((change / data[0]) * 100).toFixed(2)
                result += `
                  <div style="margin: 3px 0;">
                    <span style="color: #fff;">开盘:</span> <span style="color: #ffd700;">${formatPrice(data[0])}</span><br/>
                    <span style="color: #fff;">收盘:</span> <span style="color: ${data[1] >= data[0] ? '#10b981' : '#ef4444'};">${formatPrice(data[1])}</span><br/>
                    <span style="color: #fff;">最高:</span> <span style="color: #ffd700;">${formatPrice(data[3])}</span><br/>
                    <span style="color: #fff;">最低:</span> <span style="color: #ffd700;">${formatPrice(data[2])}</span><br/>
                    <span style="color: #fff;">涨跌:</span> <span style="color: ${change >= 0 ? '#10b981' : '#ef4444'};">${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent}%)</span>
                  </div>
                `
              } else if (param.seriesName === '成交量') {
                result += `<div style="margin: 3px 0;"><span style="color: #fff;">成交量:</span> <span style="color: #06b6d4;">${formatVolume(param.value)}</span></div>`
              } else if (param.value !== null && param.value !== undefined && param.value !== '-') {
                result += `<div style="margin: 2px 0;"><span style="color: #fff;">${param.seriesName}:</span> <span style="color: ${param.color};">${formatPrice(param.value)}</span></div>`
              }
            })
            return result
          }
        },
        legend: {
          data: legendData,
          top: 5,
          textStyle: { fontSize: 12 },
          icon: 'line'
        },
        grid: showVolume ? [
          { 
            id: 'gd1', 
            left: '50', 
            right: '50', 
            top: '15%', 
            height: '55%',
            backgroundColor: '#fafafa',
            borderColor: '#e0e0e0'
          },
          { 
            id: 'gd2', 
            left: '50', 
            right: '50', 
            top: '75%', 
            height: '20%',
            backgroundColor: '#fafafa',
            borderColor: '#e0e0e0'
          }
        ] : [
          { 
            id: 'gd1', 
            left: '50', 
            right: '50', 
            top: '15%', 
            height: '80%',
            backgroundColor: '#fafafa',
            borderColor: '#e0e0e0'
          }
        ],
        xAxis: showVolume ? [
          {
            type: 'category',
            data: dates,
            boundaryGap: false,
            axisLine: { onZero: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            axisTick: { show: false }
          },
          {
            type: 'category',
            gridIndex: 1,
            data: dates,
            boundaryGap: false,
            axisLine: { onZero: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { 
              show: true,
              fontSize: 10,
              interval: Math.floor(dates.length / 8),
              margin: 8
            }
          }
        ] : [
          {
            type: 'category',
            data: dates,
            boundaryGap: false,
            axisLine: { onZero: false },
            splitLine: { show: false },
            axisLabel: { 
              show: true,
              fontSize: 10,
              interval: Math.floor(dates.length / 6),
              margin: 8
            },
            axisTick: { show: false }
          }
        ],
        yAxis: showVolume ? [
          {
            type: 'value',
            scale: true,
            position: 'right',
            axisLabel: { 
              formatter: (value: number) => formatPrice(value),
              fontSize: 10
            },
            splitLine: { 
              show: true,
              lineStyle: { color: '#e8e8e8', type: 'dashed' }
            }
          },
          {
            type: 'value',
            gridIndex: 1,
            scale: true,
            position: 'right',
            axisLabel: { 
              formatter: formatVolume,
              fontSize: 10
            },
            splitLine: { show: false }
          }
        ] : [
          {
            type: 'value',
            scale: true,
            position: 'right',
            axisLabel: { 
              formatter: (value: number) => formatPrice(value),
              fontSize: 10
            },
            splitLine: { 
              show: true,
              lineStyle: { color: '#e8e8e8', type: 'dashed' }
            }
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: Math.max(0, 100 - (50 / dates.length) * 100),
            end: 100
          }
        ],
        toolbox: {
          show: false
        },
        brush: {
          xAxisIndex: 'all',
          brushLink: 'all',
          outOfBrush: { colorAlpha: 0.1 }
        },
        series
      }
    } else if (chartType === 'line') {
      const priceData = stockData.map(item => item.price)
      return {
        animation: false,
        tooltip: {
          trigger: 'axis',
          formatter: (params: any) => `${params[0].name}<br/>价格: ${formatPrice(params[0].value)}`
        },
        grid: { left: '3%', right: '4%', top: '10%', bottom: '10%' },
        xAxis: { type: 'category', data: dates },
        yAxis: { type: 'value', scale: true },
        series: [{
          name: '价格',
          type: 'line',
          data: priceData,
          lineStyle: { color: '#2563eb', width: 2 },
          showSymbol: false
        }]
      }
    } else { // area
      const priceData = stockData.map(item => item.price)
      return {
        animation: false,
        tooltip: {
          trigger: 'axis',
          formatter: (params: any) => `${params[0].name}<br/>价格: ${formatPrice(params[0].value)}`
        },
        grid: { left: '3%', right: '4%', top: '10%', bottom: '10%' },
        xAxis: { type: 'category', data: dates },
        yAxis: { type: 'value', scale: true },
        series: [{
          name: '价格',
          type: 'line',
          data: priceData,
          lineStyle: { color: '#2563eb', width: 2 },
          areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
          showSymbol: false
        }]
      }
    }
  }

  // 生成成交量图表的ECharts选项
  const getVolumeChartOption = () => {
    if (!stockData || stockData.length === 0) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#999', fontSize: 14 }
        }
      }
    }

    const dates = stockData.map(item => item.date)
    const volumeData = stockData.map(item => item.volume)

    return {
      animation: false,
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => `${params[0].name}<br/>成交量: ${formatVolume(params[0].value)}`
      },
      grid: { left: '3%', right: '4%', top: '10%', bottom: '10%' },
      xAxis: { type: 'category', data: dates },
      yAxis: { 
        type: 'value',
        axisLabel: { formatter: formatVolume }
      },
      series: [{
        name: '成交量',
        type: 'bar',
        data: volumeData,
        itemStyle: { color: '#06b6d4' }
      }]
    }
  }

  // 生成RSI图表的ECharts选项
  const getRSIChartOption = () => {
    if (!stockData || stockData.length === 0) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#999', fontSize: 14 }
        }
      }
    }

    const dates = stockData.map(item => item.date)
    const rsi = calculateRSI(stockData, 14)

    return {
      animation: false,
      backgroundColor: '#ffffff',
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = `${params[0].name}<br/>`
          params.forEach((param: any) => {
            if (param.value !== null && param.value !== undefined) {
              result += `${param.seriesName}: ${param.value.toFixed(2)}<br/>`
            }
          })
          return result
        }
      },
      grid: { left: '50', right: '50', top: '15%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: { fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { fontSize: 10 },
        splitLine: {
          show: true,
          lineStyle: { color: '#e8e8e8', type: 'dashed' }
        }
      },
      series: [
        {
          name: 'RSI',
          type: 'line',
          data: rsi,
          lineStyle: { color: '#ff7300', width: 2 },
          areaStyle: { 
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(255, 115, 0, 0.3)' },
                { offset: 1, color: 'rgba(255, 115, 0, 0.1)' }
              ]
            }
          },
          showSymbol: false,
          markLine: {
            silent: true,
            lineStyle: { color: '#999', type: 'dashed' },
            data: [
              { yAxis: 70, label: { formatter: '超买线 70' } },
              { yAxis: 30, label: { formatter: '超卖线 30' } },
              { yAxis: 50, label: { formatter: '中线 50' } }
            ]
          }
        }
      ]
    }
  }

  // 生成MACD图表的ECharts选项
  const getMACDChartOption = () => {
    if (!stockData || stockData.length === 0) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#999', fontSize: 14 }
        }
      }
    }

    const dates = stockData.map(item => item.date)
    const macdData = calculateMACD(stockData, 12, 26, 9)

    return {
      animation: false,
      backgroundColor: '#ffffff',
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = `${params[0].name}<br/>`
          params.forEach((param: any) => {
            if (param.value !== null && param.value !== undefined) {
              result += `${param.seriesName}: ${param.value.toFixed(4)}<br/>`
            }
          })
          return result
        }
      },
      legend: {
        data: ['MACD', '信号线', '柱状图'],
        top: 5,
        textStyle: { fontSize: 12 }
      },
      grid: { left: '50', right: '50', top: '20%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: { fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        axisLabel: { fontSize: 10 },
        splitLine: {
          show: true,
          lineStyle: { color: '#e8e8e8', type: 'dashed' }
        }
      },
      series: [
        {
          name: 'MACD',
          type: 'line',
          data: macdData.macd,
          lineStyle: { color: '#2196f3', width: 2 },
          showSymbol: false
        },
        {
          name: '信号线',
          type: 'line',
          data: macdData.signal,
          lineStyle: { color: '#ff9800', width: 2 },
          showSymbol: false
        },
        {
          name: '柱状图',
          type: 'bar',
          data: macdData.histogram,
          itemStyle: {
            color: function(params: any) {
              return params.value >= 0 ? '#ef4444' : '#10b981'
            }
          }
        }
      ]
    }
  }

  // 生成技术指标图表的ECharts选项
  const getIndicatorChartOption = (indicator: string) => {
    const indicatorData = indicators[indicator]
    if (!indicatorData || indicatorData.length === 0) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#999', fontSize: 12 }
        }
      }
    }

    const dates = indicatorData.map(item => item.date)
    const series: any[] = []

    // 获取指标的所有数值字段
    const dataKeys = Object.keys(indicatorData[0] || {}).filter(key => key !== 'date' && key !== 'Date')
    
    dataKeys.forEach((key, index) => {
      const data = indicatorData.map(item => item[key])
      series.push({
        name: key,
        type: 'line',
        data: data,
        lineStyle: { color: getIndicatorColor(indicator), width: 1 },
        showSymbol: false
      })
    })

    return {
      animation: false,
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', top: '10%', bottom: '10%' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value' },
      series
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="h-6 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded animate-pulse w-2/3" />
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-gray-200 rounded animate-pulse" />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Chart Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-6 w-6 text-blue-600" />
          <h3 className="text-xl font-bold">{symbol} 股票图表</h3>
          <Badge variant="outline">
            {stockData.length} 天数据
          </Badge>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={refreshData} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* 紧凑的技术指标工具栏 */}
      <div className="bg-gray-50 p-3 rounded-lg border">
        <div className="flex flex-wrap items-center gap-4">
          <span className="text-sm font-medium text-gray-700">技术指标:</span>
          
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="showMA"
              checked={showMA}
              onChange={(e) => setShowMA(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="showMA" className="text-sm">MA</label>
          </div>
          
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="showBollinger"
              checked={showBollinger}
              onChange={(e) => setShowBollinger(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="showBollinger" className="text-sm">布林带</label>
          </div>
          
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="showVolume"
              checked={showVolume}
              onChange={(e) => setShowVolume(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="showVolume" className="text-sm">成交量</label>
          </div>
          
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="showRSI"
              checked={showRSI}
              onChange={(e) => setShowRSI(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="showRSI" className="text-sm">RSI</label>
          </div>
          
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="showMACD"
              checked={showMACD}
              onChange={(e) => setShowMACD(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="showMACD" className="text-sm">MACD</label>
          </div>

          {/* MA周期快捷选择 */}
          {showMA && (
            <>
              <span className="text-sm text-gray-400">|</span>
              <span className="text-xs text-gray-600">MA:</span>
              {[5, 10, 20].map((period) => (
                <Button
                  key={period}
                  variant={maTypes.includes(period) ? 'default' : 'outline'}
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={() => {
                    const newMaTypes = maTypes.includes(period)
                      ? maTypes.filter(t => t !== period)
                      : [...maTypes, period].sort((a, b) => a - b)
                    setMaTypes(newMaTypes)
                  }}
                >
                  {period}
                </Button>
              ))}
            </>
          )}
        </div>
      </div>


      {/* Main Chart Container */}
      <div className="space-y-6">
        {/* Price Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>K线图</span>
              <div className="flex items-center space-x-2 text-sm">
                {stockData.length > 0 && (
                  <>
                    <span className="text-gray-600">当前价格:</span>
                    <span className="font-bold text-lg">{formatPrice(stockData[stockData.length - 1]?.price || 0)}</span>
                    {stockData.length > 1 && (
                      <span className={`flex items-center ${
                        stockData[stockData.length - 1]?.price >= stockData[stockData.length - 2]?.price 
                          ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {stockData[stockData.length - 1]?.price >= stockData[stockData.length - 2]?.price 
                          ? <TrendingUp className="h-4 w-4 mr-1" /> 
                          : <TrendingDown className="h-4 w-4 mr-1" />
                        }
                        {((stockData[stockData.length - 1]?.price - stockData[stockData.length - 2]?.price) / stockData[stockData.length - 2]?.price * 100).toFixed(2)}%
                      </span>
                    )}
                  </>
                )}
              </div>
            </CardTitle>
            <CardDescription>
              {lookBackDays} 天价格变化趋势
              {showMA && ` · 包含 MA${maTypes.join('/')}`}
              {showBollinger && ' · 布林带'}
              {showVolume && ' · 成交量'}
              {showRSI && ' · RSI'}
              {showMACD && ' · MACD'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="w-full h-[500px]">
              <EChartsWrapper
                option={getPriceChartOption()}
                style={{ height: '100%', width: '100%' }}
              />
            </div>
          </CardContent>
        </Card>
      </div>



      {/* RSI Chart */}
      {showRSI && (
        <Card>
          <CardHeader>
            <CardTitle>RSI 相对强弱指标</CardTitle>
            <CardDescription>
              RSI值: 70以上超买，30以下超卖
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="w-full h-64">
              <EChartsWrapper
                option={getRSIChartOption()}
                style={{ height: '100%', width: '100%' }}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* MACD Chart */}
      {showMACD && (
        <Card>
          <CardHeader>
            <CardTitle>MACD 指标</CardTitle>
            <CardDescription>
              MACD线、信号线和柱状图
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="w-full h-64">
              <EChartsWrapper
                option={getMACDChartOption()}
                style={{ height: '100%', width: '100%' }}
              />
            </div>
          </CardContent>
        </Card>
      )}

    
    </div>
  )
}
