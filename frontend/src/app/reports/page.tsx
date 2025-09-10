'use client'

import { AnalysisReportsManager } from '@/components/AnalysisReportsManager'
import { FileText } from 'lucide-react'
import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'

function ReportsContent() {
  const searchParams = useSearchParams()
  const ticker = searchParams.get('ticker')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-2">
        <FileText className="h-8 w-8 text-blue-600" />
        <h1 className="text-3xl font-bold text-gray-900">分析报告</h1>
        {ticker && (
          <div className="text-lg text-gray-600">
            - {ticker}
          </div>
        )}
      </div>

      {/* Reports Manager */}
      <AnalysisReportsManager initialTicker={ticker || ''} />
    </div>
  )
}

export default function ReportsPage() {
  return (
    <Suspense fallback={<div>加载中...</div>}>
      <ReportsContent />
    </Suspense>
  )
}
