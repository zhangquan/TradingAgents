'use client'

import { useMemo } from 'react'
import EChartsWrapper from './EChartsWrapper'

interface CandlestickData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

interface EChartsCandlestickProps {
  data: CandlestickData[]
  height?: string
  width?: string
  showVolume?: boolean
  showMA?: boolean
  maTypes?: number[]
  className?: string
}

export default function EChartsCandlestick({
  data,
  height = '300px',
  width = '100%',
  showVolume = false,
  showMA = false,
  maTypes = [5, 10, 20],
  className = ''
}: EChartsCandlestickProps) {
  
  const option = useMemo(() => {
    if (!data || data.length === 0) {
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

    // 准备数据
    const dates = data.map(item => item.date)
    const ohlcData = data.map(item => [item.open, item.close, item.low, item.high])
    const volumeData = data.map(item => item.volume || 0)

    // 计算移动平均线
    const calculateMA = (dayCount: number) => {
      const result = []
      for (let i = 0; i < data.length; i++) {
        if (i < dayCount - 1) {
          result.push('-')
        } else {
          let sum = 0
          for (let j = 0; j < dayCount; j++) {
            sum += data[i - j].close
          }
          result.push((sum / dayCount).toFixed(2))
        }
      }
      return result
    }

    const series: any[] = [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlcData,
        itemStyle: {
          color: '#ef4444',  // 阳线颜色 (红色)
          color0: '#10b981', // 阴线颜色 (绿色)
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

    // 添加移动平均线
    if (showMA) {
      const maColors = ['#ff9800', '#2196f3', '#9c27b0', '#4caf50']
      maTypes.forEach((type, index) => {
        series.push({
          name: `MA${type}`,
          type: 'line',
          data: calculateMA(type),
          smooth: true,
          lineStyle: {
            width: 1,
            color: maColors[index % maColors.length]
          },
          showSymbol: false
        })
      })
    }

    // 添加成交量
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
              return data[dataIndex].close >= data[dataIndex].open ? '#ef4444' : '#10b981'
            }
            return '#ef4444'
          }
        }
      })
    }

    const grid = showVolume 
      ? [
          { left: '3%', right: '4%', top: '10%', height: '60%' },
          { left: '3%', right: '4%', top: '75%', height: '20%' }
        ]
      : [{ left: '3%', right: '4%', top: '10%', bottom: '10%' }]

    const xAxis = showVolume
      ? [
          { type: 'category', data: dates, gridIndex: 0, axisLabel: { show: false } },
          { type: 'category', data: dates, gridIndex: 1 }
        ]
      : [{ type: 'category', data: dates }]

    const yAxis = showVolume
      ? [
          { type: 'value', gridIndex: 0, scale: true },
          { type: 'value', gridIndex: 1, scale: true, axisLabel: { formatter: (value: number) => {
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
            return value.toString()
          }}}
        ]
      : [{ type: 'value', scale: true }]

    return {
      animation: false,
      color: ['#c23531', '#2f4554', '#61a0a8', '#d48265'],
      title: {
        text: '',
        left: 0
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        backgroundColor: 'rgba(245, 245, 245, 0.8)',
        borderWidth: 1,
        borderColor: '#ccc',
        padding: 10,
        textStyle: {
          color: '#000'
        },
        formatter: function (params: any) {
          let result = `${params[0].name}<br/>`
          params.forEach((param: any) => {
            if (param.seriesName === 'K线') {
              const data = param.data
              result += `开盘: ${data[0]}<br/>`
              result += `收盘: ${data[1]}<br/>`
              result += `最低: ${data[2]}<br/>`
              result += `最高: ${data[3]}<br/>`
            } else if (param.seriesName === '成交量') {
              const volume = param.value
              let volumeStr = volume.toString()
              if (volume >= 1000000) {
                volumeStr = `${(volume / 1000000).toFixed(1)}M`
              } else if (volume >= 1000) {
                volumeStr = `${(volume / 1000).toFixed(1)}K`
              }
              result += `成交量: ${volumeStr}<br/>`
            } else {
              result += `${param.seriesName}: ${param.value}<br/>`
            }
          })
          return result
        }
      },
      legend: {
        data: ['K线', ...(showMA ? maTypes.map(type => `MA${type}`) : []), ...(showVolume ? ['成交量'] : [])],
        top: 0
      },
      grid,
      xAxis,
      yAxis,
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: showVolume ? [0, 1] : [0],
          start: 0,
          end: 100
        },
        {
          show: true,
          xAxisIndex: showVolume ? [0, 1] : [0],
          type: 'slider',
          top: showVolume ? '95%' : '90%',
          start: 0,
          end: 100
        }
      ],
      series
    }
  }, [data, showVolume, showMA, maTypes])

  return (
    <EChartsWrapper
      option={option}
      style={{ height, width }}
      className={className}
    />
  )
}
