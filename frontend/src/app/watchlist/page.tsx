'use client'

import { WatchlistManager } from '@/components/WatchlistManager'

export default function WatchlistPage() {
  return (
    <div className="min-h-screen bg-gray-50 lg:pl-64">
      <div className="p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">关注股票管理</h1>
            <p className="mt-2 text-gray-600">
              管理您关注的股票，关注的股票将在可用股票列表中优先显示
            </p>
          </div>

          <WatchlistManager />
        </div>
      </div>
    </div>
  )
}
