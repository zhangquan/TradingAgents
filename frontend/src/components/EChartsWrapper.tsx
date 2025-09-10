'use client'

import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface EChartsWrapperProps {
  option: any
  style?: React.CSSProperties
  className?: string
  theme?: string
  onChartReady?: (chart: echarts.ECharts) => void
}

export default function EChartsWrapper({ 
  option, 
  style = { height: '300px', width: '100%' }, 
  className = '',
  theme = 'light',
  onChartReady 
}: EChartsWrapperProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (chartRef.current) {
      // 初始化图表
      chartInstance.current = echarts.init(chartRef.current, theme)
      
      if (onChartReady) {
        onChartReady(chartInstance.current)
      }

      // 监听窗口大小变化
      const handleResize = () => {
        chartInstance.current?.resize()
      }
      window.addEventListener('resize', handleResize)

      return () => {
        window.removeEventListener('resize', handleResize)
        chartInstance.current?.dispose()
      }
    }
  }, [theme, onChartReady])

  useEffect(() => {
    if (chartInstance.current && option) {
      chartInstance.current.setOption(option, true)
    }
  }, [option])

  return <div ref={chartRef} style={style} className={className} />
}
