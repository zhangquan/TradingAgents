

import { useMemo } from 'react'
import EChartsWrapper from './EChartsWrapper'

interface KLineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface AdvancedKLineChartProps {
  data: KLineData[]
  height?: string
  width?: string
  showVolume?: boolean
  showMA?: boolean
  maTypes?: number[]
  showMACD?: boolean
  showRSI?: boolean
  className?: string
  title?: string
}

export default function AdvancedKLineChart({
  data,
  height = '600px',
  width = '100%',
  showVolume = true,
  showMA = true,
  maTypes = [5, 10, 20, 60],
  showMACD = false,
  showRSI = false,
  className = '',
  title = 'K线图'
}: AdvancedKLineChartProps) {

  const option = useMemo(() => {
    if (!data || data.length === 0) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#999',
            fontSize: 16
          }
        }
      }
    }

    // 准备数据
    const dates = data.map(item => item.date)
    const ohlcData = data.map(item => [item.open, item.close, item.low, item.high])
    const volumeData = data.map(item => item.volume)

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
          result.push(Number((sum / dayCount).toFixed(2)))
        }
      }
      return result
    }

    // 计算MACD
    const calculateMACD = () => {
      const ema12: number[] = []
      const ema26: number[] = []
      const dif: number[] = []
      const dea: number[] = []
      const macd = []

      for (let i = 0; i < data.length; i++) {
        if (i === 0) {
          ema12[i] = data[i].close
          ema26[i] = data[i].close
        } else {
          ema12[i] = (2 * data[i].close + 11 * ema12[i - 1]) / 13
          ema26[i] = (2 * data[i].close + 25 * ema26[i - 1]) / 27
        }
        dif[i] = ema12[i] - ema26[i]

        if (i === 0) {
          dea[i] = dif[i]
        } else {
          dea[i] = (2 * dif[i] + 8 * dea[i - 1]) / 10
        }
        macd[i] = 2 * (dif[i] - dea[i])
      }

      return { dif, dea, macd }
    }

    // 计算RSI
    const calculateRSI = (period: number = 14) => {
      const rsi = []
      let gains = 0
      let losses = 0

      for (let i = 0; i < data.length; i++) {
        if (i === 0) {
          rsi[i] = 50
          continue
        }

        const change = data[i].close - data[i - 1].close
        const gain = change > 0 ? change : 0
        const loss = change < 0 ? -change : 0

        if (i < period) {
          gains += gain
          losses += loss
          if (i === period - 1) {
            gains /= period
            losses /= period
          }
          rsi[i] = 50
        } else {
          gains = (gains * (period - 1) + gain) / period
          losses = (losses * (period - 1) + loss) / period
          const rs = gains / (losses || 0.001)
          rsi[i] = 100 - (100 / (1 + rs))
        }
      }

      return rsi
    }

    // 构建网格配置
    const grids = []
    let currentTop = 5

    // 主图网格（K线图）
    grids.push({
      left: '3%',
      right: '8%',
      top: `${currentTop}%`,
      height: showVolume ? (showMACD || showRSI ? '45%' : '60%') : (showMACD || showRSI ? '60%' : '80%')
    })
    currentTop += (showVolume ? (showMACD || showRSI ? 45 : 60) : (showMACD || showRSI ? 60 : 80)) + 5

    // 成交量网格
    if (showVolume) {
      grids.push({
        left: '3%',
        right: '8%',
        top: `${currentTop}%`,
        height: showMACD || showRSI ? '15%' : '25%'
      })
      currentTop += (showMACD || showRSI ? 15 : 25) + 5
    }

    // MACD网格
    if (showMACD) {
      grids.push({
        left: '3%',
        right: '8%',
        top: `${currentTop}%`,
        height: showRSI ? '15%' : '20%'
      })
      currentTop += (showRSI ? 15 : 20) + 5
    }

    // RSI网格
    if (showRSI) {
      grids.push({
        left: '3%',
        right: '8%',
        top: `${currentTop}%`,
        height: '15%'
      })
    }

    // 构建坐标轴
    const xAxes = grids.map((_, index) => ({
      type: 'category',
      data: dates,
      gridIndex: index,
      axisLabel: {
        show: index === grids.length - 1 // 只在最后一个图表显示x轴标签
      }
    }))

    const yAxes = grids.map((_, index) => ({
      type: 'value',
      gridIndex: index,
      scale: index === 0, // 只有主图使用scale
      ...(index === 1 && showVolume && {
        axisLabel: {
          formatter: (value: number) => {
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
            return value.toString()
          }
        }
      })
    }))

    // 构建系列数据
    const series: any[] = []
    let gridIndex = 0

    // K线图
    series.push({
      name: 'K线',
      type: 'candlestick',
      data: ohlcData,
      xAxisIndex: gridIndex,
      yAxisIndex: gridIndex,
      itemStyle: {
        color: '#ef4444',        // 阳线颜色
        color0: '#10b981',       // 阴线颜色
        borderColor: '#ef4444',
        borderColor0: '#10b981'
      }
    })

    // 移动平均线
    if (showMA) {
      const maColors = ['#ff9800', '#2196f3', '#9c27b0', '#4caf50', '#ff5722']
      maTypes.forEach((type, index) => {
        series.push({
          name: `MA${type}`,
          type: 'line',
          data: calculateMA(type),
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          lineStyle: {
            width: 1.5,
            color: maColors[index % maColors.length]
          },
          showSymbol: false,
          smooth: true
        })
      })
    }

    gridIndex++

    // 成交量
    if (showVolume) {
      series.push({
        name: '成交量',
        type: 'bar',
        data: volumeData,
        xAxisIndex: gridIndex,
        yAxisIndex: gridIndex,
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
      gridIndex++
    }

    // MACD
    if (showMACD) {
      const macdData = calculateMACD()
      series.push(
        {
          name: 'DIF',
          type: 'line',
          data: macdData.dif,
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          lineStyle: { width: 1, color: '#ff6b6b' },
          showSymbol: false
        },
        {
          name: 'DEA',
          type: 'line',
          data: macdData.dea,
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          lineStyle: { width: 1, color: '#4ecdc4' },
          showSymbol: false
        },
        {
          name: 'MACD',
          type: 'bar',
          data: macdData.macd,
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          itemStyle: {
            color: function(params: any) {
              return params.value >= 0 ? '#ef4444' : '#10b981'
            }
          }
        }
      )
      gridIndex++
    }

    // RSI
    if (showRSI) {
      const rsiData = calculateRSI(14)
      series.push({
        name: 'RSI',
        type: 'line',
        data: rsiData,
        xAxisIndex: gridIndex,
        yAxisIndex: gridIndex,
        lineStyle: { width: 1.5, color: '#ffc658' },
        showSymbol: false,
        markLine: {
          silent: true,
          lineStyle: {
            color: '#999',
            type: 'dashed'
          },
          data: [
            { yAxis: 70 },
            { yAxis: 30 }
          ]
        }
      })
    }

    return {
      animation: false,
      title: {
        text: title,
        left: 0,
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          link: [{ xAxisIndex: 'all' }]
        },
        formatter: function (params: any) {
          let result = `${params[0].name}<br/>`
          
          params.forEach((param: any) => {
            if (param.seriesName === 'K线') {
              const data = param.data
              result += `开盘: $${data[0].toFixed(2)}<br/>`
              result += `收盘: $${data[1].toFixed(2)}<br/>`
              result += `最低: $${data[2].toFixed(2)}<br/>`
              result += `最高: $${data[3].toFixed(2)}<br/>`
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
        data: [
          'K线', 
          ...(showMA ? maTypes.map(type => `MA${type}`) : []), 
          ...(showVolume ? ['成交量'] : []),
          ...(showMACD ? ['DIF', 'DEA', 'MACD'] : []),
          ...(showRSI ? ['RSI'] : [])
        ],
        top: 30
      },
      grid: grids,
      xAxis: xAxes,
      yAxis: yAxes,
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: Array.from({ length: grids.length }, (_, i) => i),
          start: 50,
          end: 100
        },
        {
          show: true,
          xAxisIndex: Array.from({ length: grids.length }, (_, i) => i),
          type: 'slider',
          bottom: 0,
          start: 50,
          end: 100
        }
      ],
      series
    }
  }, [data, showVolume, showMA, maTypes, showMACD, showRSI, title])

  return (
    <EChartsWrapper
      option={option}
      style={{ height, width }}
      className={className}
    />
  )
}
