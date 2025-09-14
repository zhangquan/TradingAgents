

import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { 
  TrendingUp,
  DollarSign,
  CheckCircle,
  FileText,
  Calendar,
  Clock
} from 'lucide-react'
import { MarkdownRenderer } from './MarkdownRenderer'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface ReportData {
  report_id?: string
  analysis_id?: string
  ticker: string
  date: string
  title?: string
  sections: { [key: string]: string }
  status?: string
  created_at?: string
  updated_at?: string
}

interface ReportDisplayProps {
  reportData: ReportData
  showHeader?: boolean
  compact?: boolean
  className?: string
}

export function ReportDisplay({ 
  reportData, 
  showHeader = false, 
  compact = true,
  className = "" 
}: ReportDisplayProps) {
  
  const getSectionTitle = (sectionKey: string) => {
    const titles: { [key: string]: string } = {
      'market_report': '市场分析报告',
      'investment_plan': '投资计划',
      'final_trade_decision': '最终交易决策',
      'social_sentiment': '社交情绪分析',
      'news_analysis': '新闻分析报告',
      'fundamentals_analysis': '基本面分析',
      'research_decision': '研究决策'
    }
    return titles[sectionKey] || sectionKey.replace(/_/g, ' ')
  }

  const getSectionIcon = (sectionKey: string) => {
    const icons: { [key: string]: React.ReactNode } = {
      'market_report': <TrendingUp className="h-4 w-4" />,
      'investment_plan': <DollarSign className="h-4 w-4" />,
      'final_trade_decision': <CheckCircle className="h-4 w-4" />,
      'social_sentiment': <FileText className="h-4 w-4" />,
      'news_analysis': <FileText className="h-4 w-4" />,
      'fundamentals_analysis': <FileText className="h-4 w-4" />,
      'research_decision': <FileText className="h-4 w-4" />
    }
    return icons[sectionKey] || <FileText className="h-4 w-4" />
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'generated': 'bg-green-100 text-green-800',
      'reviewed': 'bg-blue-100 text-blue-800',
      'archived': 'bg-gray-100 text-gray-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      'generated': '已生成',
      'reviewed': '已审核',
      'archived': '已归档'
    }
    return labels[status] || status
  }

  const formatDate = (dateStr: string) => {
    try {
      let dateISO = dateStr
      if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
        dateISO = dateStr + 'Z'
      }
      return format(parseISO(dateISO), 'yyyy年MM月dd日 HH:mm', { locale: zhCN })
    } catch {
      return dateStr
    }
  }

  const renderSections = () => {
    if (!reportData.sections || typeof reportData.sections !== 'object') {
      return (
        <div className="text-gray-500 text-center py-8">
          无报告内容可显示
        </div>
      )
    }

    const sectionOrder = ['market_report', 'investment_plan', 'final_trade_decision', 'social_sentiment', 'news_analysis', 'fundamentals_analysis', 'research_decision']
    const sortedSections = Object.entries(reportData.sections).sort(([a], [b]) => {
      const aIndex = sectionOrder.indexOf(a)
      const bIndex = sectionOrder.indexOf(b)
      return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex)
    })

    if (sortedSections.length === 0) {
      return (
        <div className="text-gray-500 text-center py-8">
          无报告内容可显示
        </div>
      )
    }

    const defaultSection = sortedSections[0][0]

    return (
      <Tabs defaultValue={defaultSection} className="w-full">
        <TabsList className={`grid w-full gap-1 bg-gray-100 p-1 ${
          sortedSections.length === 1 ? 'grid-cols-1' : 
          sortedSections.length === 2 ? 'grid-cols-2' : 
          sortedSections.length === 3 ? 'grid-cols-1 sm:grid-cols-3' :
          'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4'
        }`}>
          {sortedSections.map(([sectionKey]) => (
            <TabsTrigger 
              key={sectionKey} 
              value={sectionKey}
              className={`flex items-center gap-2 ${compact ? 'text-xs px-2 py-1.5' : 'text-sm px-3 py-2'} data-[state=active]:bg-white data-[state=active]:shadow-sm transition-all duration-200`}
            >
              {getSectionIcon(sectionKey)}
              <span className={`${compact ? 'hidden sm:inline text-xs' : 'hidden sm:inline'} font-medium`}>
                {getSectionTitle(sectionKey)}
              </span>
              <span className={`sm:hidden font-medium ${compact ? 'text-xs' : 'text-xs'}`}>
                {getSectionTitle(sectionKey).length > 4 
                  ? getSectionTitle(sectionKey).substring(0, 3) + '..'
                  : getSectionTitle(sectionKey)
                }
              </span>
            </TabsTrigger>
          ))}
        </TabsList>
        
        {sortedSections.map(([sectionKey, content]) => (
          <TabsContent 
            key={sectionKey} 
            value={sectionKey}
            className={`${compact ? 'mt-4' : 'mt-6'} focus:outline-none`}
          >
            <MarkdownRenderer 
              content={content} 
              className={`prose ${compact ? 'prose-sm' : 'prose-lg'} max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-ul:text-gray-700 prose-ol:text-gray-700 prose-li:text-gray-700 prose-blockquote:text-gray-600 prose-code:text-blue-600 prose-pre:bg-gray-50`}
            />
          </TabsContent>
        ))}
      </Tabs>
    )
  }

  return (
    <div className={className}>
      {showHeader && (
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {reportData.ticker} {reportData.title || '分析报告'}
              </h3>
              <div className="flex items-center space-x-4 text-gray-600">
                {reportData.date && (
                  <div className="flex items-center space-x-1">
                    <Calendar className="h-4 w-4" />
                    <span className="text-sm">{reportData.date}</span>
                  </div>
                )}
                {reportData.created_at && (
                  <div className="flex items-center space-x-1">
                    <Clock className="h-4 w-4" />
                    <span className="text-sm">{formatDate(reportData.created_at)}</span>
                  </div>
                )}
              </div>
            </div>
            {reportData.status && (
              <Badge className={getStatusColor(reportData.status)}>
                {getStatusLabel(reportData.status)}
              </Badge>
            )}
          </div>
        </div>
      )}
      
      <Card className={compact ? '' : 'shadow-lg'}>
        <CardContent className={compact ? 'p-4' : 'p-6'}>
          {renderSections()}
        </CardContent>
      </Card>
    </div>
  )
}
