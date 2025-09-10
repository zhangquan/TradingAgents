'use client'

import { useMemo } from 'react'
import EChartsWrapper from './EChartsWrapper'
import { BarChart3 } from 'lucide-react'

interface CandlestickData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

interface MiniEChartsCandlestickProps {
  data: CandlestickData[]
  height?: string
  className?: string
}

export default function MiniEChartsCandlestick({
  data,
  height = '128px',
  className = ''
}: MiniEChartsCandlestickProps) {
  
  const option = useMemo(() => {
    if (!data || data.length === 0) {
      return null
    }

    // 准备数据
    const dates = data.map(item => item.date)
    const ohlcData = data.map(item => [item.open, item.close, item.low, item.high])

    return {
      animation: false,
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        backgroundColor: 'rgba(245, 245, 245, 0.95)',
        borderWidth: 1,
        borderColor: '#ccc',
        padding: 8,
        textStyle: {
          color: '#000',
          fontSize: 12
        },
        formatter: function (params: any) {
          const param = params[0]
          if (param && param.data) {
            const data = param.data
            return `${param.name}<br/>
                    开盘: $${data[0].toFixed(2)}<br/>
                    收盘: $${data[1].toFixed(2)}<br/>
                    最低: $${data[2].toFixed(2)}<br/>
                    最高: $${data[3].toFixed(2)}`
          }
          return ''
        }
      },
      grid: {
        left: '5%',
        right: '5%',
        top: '5%',
        bottom: '5%',
        containLabel: false
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { 
          show: false
        },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { 
          show: false
        },
        splitLine: { 
          show: true,
          lineStyle: {
            color: '#f0f0f0',
            width: 1
          }
        }
      },
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: ohlcData,
          itemStyle: {
            color: '#ef4444',        // 阳线颜色 (红色)
            color0: '#10b981',       // 阴线颜色 (绿色)
            borderColor: '#ef4444',
            borderColor0: '#10b981',
            borderWidth: 1
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
    }
  }, [data])

  if (!data || data.length === 0) {
    return (
      <div className={`flex items-center justify-center bg-gray-50 rounded ${className}`} style={{ height }}>
        <div className="text-center">
          <BarChart3 className="h-6 w-6 text-gray-400 mx-auto mb-1" />
          <p className="text-xs text-gray-500">暂无图表数据</p>
        </div>
      </div>
    )
  }

  return (
    <EChartsWrapper
      option={option}
      style={{ height, width: '100%' }}
      className={className}
    />
  )
}
