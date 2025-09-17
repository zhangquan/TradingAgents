

import React, { useState } from 'react'

interface ChartData {
  date: string
  close: number
}

interface SimpleLineChartProps {
  data: ChartData[]
  width?: number
  height?: number
  className?: string
  showTooltip?: boolean
}

export default function SimpleLineChart({ 
  data, 
  width = 200, 
  height = 60, 
  className = "",
  showTooltip = false
}: SimpleLineChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; data: ChartData; index: number } | null>(null)
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
  
  // 生成SVG路径和坐标点
  const plotPoints = data.map((item, index) => {
    const x = (index / (data.length - 1)) * (width - 20) + 10 // 10px 边距
    const y = height - 10 - ((item.close - minPrice) / priceRange) * (height - 20) // 10px 边距
    return { x, y, data: item, index }
  })

  const pathD = plotPoints.length > 0 ? 
    `M ${plotPoints[0].x} ${plotPoints[0].y} ` + 
    plotPoints.slice(1).map(p => `L ${p.x} ${p.y}`).join(' ') : ''
  
  // 格式化价格显示
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price)
  }

  // 鼠标悬停处理
  const handleMouseMove = (event: React.MouseEvent<SVGElement>) => {
    if (!showTooltip) return
    
    const rect = event.currentTarget.getBoundingClientRect()
    const mouseX = event.clientX - rect.left
    
    // 找到最近的数据点
    let closestPoint = plotPoints[0]
    let minDistance = Math.abs(mouseX - plotPoints[0].x)
    
    plotPoints.forEach(point => {
      const distance = Math.abs(mouseX - point.x)
      if (distance < minDistance) {
        minDistance = distance
        closestPoint = point
      }
    })
    
    setHoveredPoint(closestPoint)
  }

  const handleMouseLeave = () => {
    setHoveredPoint(null)
  }

  return (
    <div className={`relative ${className}`} style={{ width, height }}>
      <svg 
        width="100%" 
        height={height} 
        viewBox={`0 0 ${width} ${height}`}
        className="absolute inset-0"
        preserveAspectRatio="none"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        {/* 背景渐变 */}
        <defs>
          <linearGradient id={`gradient-${isUp ? 'up' : 'down'}-${data.length}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={isUp ? '#10B981' : '#EF4444'} stopOpacity="0.2" />
            <stop offset="100%" stopColor={isUp ? '#10B981' : '#EF4444'} stopOpacity="0.05" />
          </linearGradient>
        </defs>
        
        {/* 水平网格线 */}
        {data.length > 2 && (
          <>
            <line
              x1="10"
              y1={height - 10 - ((minPrice - minPrice) / priceRange) * (height - 20)}
              x2={width - 10}
              y2={height - 10 - ((minPrice - minPrice) / priceRange) * (height - 20)}
              stroke="#E5E7EB"
              strokeWidth="0.5"
              strokeDasharray="2,2"
            />
            <line
              x1="10"
              y1={height - 10 - ((maxPrice - minPrice) / priceRange) * (height - 20)}
              x2={width - 10}
              y2={height - 10 - ((maxPrice - minPrice) / priceRange) * (height - 20)}
              stroke="#E5E7EB"
              strokeWidth="0.5"
              strokeDasharray="2,2"
            />
          </>
        )}
        
        {/* 填充区域 */}
        {pathD && (
          <path
            d={`${pathD} L ${width - 10},${height - 10} L 10,${height - 10} Z`}
            fill={`url(#gradient-${isUp ? 'up' : 'down'}-${data.length})`}
          />
        )}
        
        {/* 价格线 */}
        {pathD && (
          <path
            d={pathD}
            fill="none"
            stroke={isUp ? '#10B981' : '#EF4444'}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
        
        {/* 数据点 */}
        {plotPoints.map((point, index) => {
          const isFirst = index === 0
          const isLast = index === plotPoints.length - 1
          const isHovered = hoveredPoint?.index === index
          
          return (
            <circle
              key={index}
              cx={point.x}
              cy={point.y}
              r={isFirst || isLast || isHovered ? 3 : 1.5}
              fill={isUp ? '#10B981' : '#EF4444'}
              fillOpacity={isFirst || isLast ? 1 : isHovered ? 0.8 : 0.6}
              stroke="white"
              strokeWidth={isFirst || isLast || isHovered ? 1 : 0}
              className={showTooltip ? 'cursor-pointer' : ''}
            />
          )
        })}
        
        {/* 悬停指示线 */}
        {hoveredPoint && showTooltip && (
          <line
            x1={hoveredPoint.x}
            y1="10"
            x2={hoveredPoint.x}
            y2={height - 10}
            stroke="#6B7280"
            strokeWidth="1"
            strokeDasharray="3,3"
            opacity="0.5"
          />
        )}
      </svg>
      
      {/* 工具提示 */}
      {hoveredPoint && showTooltip && (
        <div
          className="absolute z-10 bg-gray-900 text-white text-xs rounded px-2 py-1 pointer-events-none transform -translate-x-1/2 -translate-y-full"
          style={{
            left: hoveredPoint.x,
            top: hoveredPoint.y - 8,
          }}
        >
          <div className="font-medium">{formatPrice(hoveredPoint.data.close)}</div>
          <div className="text-gray-300">{hoveredPoint.data.date}</div>
        </div>
      )}
    </div>
  )
}
