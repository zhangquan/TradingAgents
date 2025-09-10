'use client'

import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Area,
  AreaChart,
  ResponsiveContainer
} from 'recharts'

interface StockChartProps {
  data: Array<{
    date: string
    price: number
    volume?: number
    open?: number
    high?: number
    low?: number
    close?: number
  }>
  height?: number
  showVolume?: boolean
  color?: string
  type?: 'line' | 'area'
}

export function StockChart({ 
  data, 
  height = 300, 
  showVolume = false, 
  color = '#3b82f6',
  type = 'line' 
}: StockChartProps) {
  const formatTooltipValue = (value: number, name: string) => {
    if (name === 'price' || name === 'open' || name === 'high' || name === 'low' || name === 'close') {
      return [`$${value.toFixed(2)}`, name]
    }
    if (name === 'volume') {
      return [value.toLocaleString(), name]
    }
    return [value, name]
  }

  const formatXAxisLabel = (tickItem: string) => {
    const date = new Date(tickItem)
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }

  if (type === 'area') {
    return (
      <div className="w-full" style={{ height: height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.8}/>
                <stop offset="95%" stopColor={color} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              tickFormatter={formatXAxisLabel}
              tick={{ fontSize: 12 }}
            />
            <YAxis 
              domain={['dataMin - 5', 'dataMax + 5']}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip 
              formatter={formatTooltipValue}
              labelFormatter={(label) => new Date(label).toLocaleDateString('zh-CN')}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px'
              }}
            />
            <Area 
              type="monotone" 
              dataKey="price" 
              stroke={color}
              fillOpacity={1}
              fill="url(#colorPrice)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="w-full" style={{ height: height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatXAxisLabel}
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            domain={['dataMin - 5', 'dataMax + 5']}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <Tooltip 
            formatter={formatTooltipValue}
            labelFormatter={(label) => new Date(label).toLocaleDateString('zh-CN')}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '12px'
            }}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke={color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: color }}
          />
          {showVolume && (
            <Line 
              type="monotone" 
              dataKey="volume" 
              stroke="#94a3b8"
              strokeWidth={1}
              dot={false}
              yAxisId="volume"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
