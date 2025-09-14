

import React from 'react'

interface ChartData {
  date: string
  close: number
}

interface SimpleLineChartProps {
  data: ChartData[]
  width?: number
  height?: number
  className?: string
}

export default function SimpleLineChart({ 
  data, 
  width = 200, 
  height = 60, 
  className = "" 
}: SimpleLineChartProps) {
  if (!data || data.length === 0) {
    return (
      <div 
        className={`flex items-center justify-center bg-gray-100 rounded ${className}`}
        style={{ width, height }}
      >
        <span className="text-xs text-gray-400">暂无数据</span>
      </div>
    )
  }

  // 计算数据范围
  const prices = data.map(d => d.close).filter(price => price > 0)
  if (prices.length === 0) {
    return (
      <div 
        className={`flex items-center justify-center bg-gray-100 rounded ${className}`}
        style={{ width, height }}
      >
        <span className="text-xs text-gray-400">无效数据</span>
      </div>
    )
  }

  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const priceRange = maxPrice - minPrice || 1

  // 计算第一个和最后一个有效价格，用于确定颜色
  const firstPrice = prices[0]
  const lastPrice = prices[prices.length - 1]
  const isUp = lastPrice >= firstPrice
  
  // 生成SVG路径
  const points = data.map((item, index) => {
    const x = (index / (data.length - 1)) * (width - 20) + 10 // 10px 边距
    const y = height - 10 - ((item.close - minPrice) / priceRange) * (height - 20) // 10px 边距
    return `${x},${y}`
  }).join(' ')

  const pathD = `M ${points.replace(/,/g, ' ').split(' ').map((val, i) => 
    i % 2 === 0 ? val : `${val} ${i === 1 ? 'L' : ''}`
  ).join(' ')}`

  return (
    <div className={`relative ${className}`} style={{ width, height }}>
      <svg 
        width="100%" 
        height={height} 
        viewBox={`0 0 ${width} ${height}`}
        className="absolute inset-0"
        preserveAspectRatio="none"
      >
        {/* 背景渐变 */}
        <defs>
          <linearGradient id={`gradient-${isUp ? 'up' : 'down'}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={isUp ? '#10B981' : '#EF4444'} stopOpacity="0.2" />
            <stop offset="100%" stopColor={isUp ? '#10B981' : '#EF4444'} stopOpacity="0.05" />
          </linearGradient>
        </defs>
        
        {/* 填充区域 */}
        <path
          d={`${pathD} L ${width - 10},${height - 10} L 10,${height - 10} Z`}
          fill={`url(#gradient-${isUp ? 'up' : 'down'})`}
        />
        
        {/* 价格线 */}
        <path
          d={pathD}
          fill="none"
          stroke={isUp ? '#10B981' : '#EF4444'}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* 起始点 */}
        <circle
          cx={10}
          cy={height - 10 - ((firstPrice - minPrice) / priceRange) * (height - 20)}
          r="2"
          fill={isUp ? '#10B981' : '#EF4444'}
          fillOpacity="0.8"
        />
        
        {/* 结束点 */}
        <circle
          cx={width - 10}
          cy={height - 10 - ((lastPrice - minPrice) / priceRange) * (height - 20)}
          r="2"
          fill={isUp ? '#10B981' : '#EF4444'}
        />
      </svg>
    </div>
  )
}
