'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { 
  FileText, 
  Download, 
  ArrowLeft,
  Calendar,
  TrendingUp,
  Brain,
  Newspaper,
  Users,
  Target,
  DollarSign,
  CheckCircle,
  Clock,
  History
} from 'lucide-react'
import { apiService } from '@/lib/api'
import { toast } from 'sonner'
import Link from 'next/link'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { MarkdownRenderer } from '@/components/MarkdownRenderer'

interface ReportDetail {
  report_id: string
  analysis_id: string
  ticker: string
  date: string
  title: string
  sections: { [key: string]: string }  // Unified sections structure
  status: string
  created_at: string
  updated_at: string
}

export default function ReportDetailPage() {
  const params = useParams()
  const reportId = params.id as string
  
  const [reportData, setReportData] = useState<ReportDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (reportId) {
      loadReport()
    }
  }, [reportId])

  const loadReport = async () => {
    try {
      const response = await apiService.getReportById(reportId)
      setReportData(response)
    } catch (error) {
      console.error('Failed to load report:', error)
      toast.error('加载报告失败')
    } finally {
      setLoading(false)
    }
  }

  const getReportTypeLabel = (reportType: string) => {
    const labels: Record<string, string> = {
      'market_report': '市场分析报告',
      'social_sentiment': '社交情绪分析', 
      'news_analysis': '新闻分析报告',
      'fundamentals_analysis': '基本面分析',
      'research_decision': '研究决策',
      'investment_plan': '投资计划',
      'final_trade_decision': '最终交易决策'
    }
    return labels[reportType] || reportType
  }

  const getReportTypeIcon = (reportType: string) => {
    const icons: Record<string, React.ReactNode> = {
      'market_report': <TrendingUp className="h-4 w-4" />,
      'social_sentiment': <Users className="h-4 w-4" />,
      'news_analysis': <Newspaper className="h-4 w-4" />,
      'fundamentals_analysis': <Brain className="h-4 w-4" />,
      'research_decision': <Target className="h-4 w-4" />,
      'investment_plan': <DollarSign className="h-4 w-4" />,
      'final_trade_decision': <CheckCircle className="h-4 w-4" />
    }
    return icons[reportType] || <FileText className="h-4 w-4" />
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

  const downloadReport = () => {
    if (!reportData) return
    
    // Combine all sections into a single markdown document
    let content = `# ${reportData.title}\n\n`
    content += `**股票代码:** ${reportData.ticker}\n`
    content += `**分析日期:** ${reportData.date}\n`
    content += `**生成时间:** ${formatDate(reportData.created_at)}\n\n`
    content += '---\n\n'
    
    // 直接从数据中获取所有sections，按字母顺序排列
    const sortedSections = Object.entries(reportData.sections || {}).sort(([a], [b]) => {
      return a.localeCompare(b)
    })
    
    sortedSections.forEach(([sectionKey, sectionContent]) => {
      const title = getSectionTitle(sectionKey)
      content += `## ${title}\n\n${sectionContent}\n\n---\n\n`
    })
    
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${reportData.ticker}_完整分析报告_${reportData.date}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success('报告下载成功')
  }

  const formatDate = (dateStr: string) => {
    try {
      // 将UTC时间字符串转换为本地时间
      let dateISO = dateStr
      
      // 如果时间字符串没有时区信息，假设它是UTC时间
      if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
        dateISO = dateStr + 'Z'
      }
      
      return format(parseISO(dateISO), 'yyyy年MM月dd日 HH:mm', { locale: zhCN })
    } catch {
      return dateStr
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 bg-gray-200 rounded animate-pulse" />
            <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
          </div>
          <Link href="/reports">
            <Button variant="default" size="sm">
              <History className="h-4 w-4 mr-2" />
              历史报告
            </Button>
          </Link>
        </div>
        <Card>
          <CardHeader>
            <div className="h-6 bg-gray-200 rounded animate-pulse mb-2" />
            <div className="h-4 bg-gray-200 rounded animate-pulse" />
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-gray-200 rounded animate-pulse" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!reportData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Link href="/reports">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回报告列表
            </Button>
          </Link>
          <Link href="/reports">
            <Button variant="default" size="sm">
              <History className="h-4 w-4 mr-2" />
              历史报告
            </Button>
          </Link>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">报告未找到</h3>
            <p className="text-gray-500 text-center mb-4">
              请检查报告ID是否正确或报告是否已被删除
            </p>
            <Link href="/reports">
              <Button>返回报告列表</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  const getSectionTitle = (sectionKey: string) => {
    // 将下划线转换为空格，并将每个单词首字母大写
    return sectionKey
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  const getSectionIcon = (sectionKey: string) => {
    // 根据section名称中的关键词选择合适的图标
    const key = sectionKey.toLowerCase()
    
    if (key.includes('market')) return <TrendingUp className="h-4 w-4" />
    if (key.includes('news')) return <Newspaper className="h-4 w-4" />
    if (key.includes('sentiment') || key.includes('social')) return <Users className="h-4 w-4" />
    if (key.includes('fundamental')) return <Brain className="h-4 w-4" />
    if (key.includes('investment') || key.includes('plan')) return <DollarSign className="h-4 w-4" />
    if (key.includes('decision') || key.includes('final')) return <CheckCircle className="h-4 w-4" />
    if (key.includes('trader') || key.includes('trade')) return <Target className="h-4 w-4" />
    if (key.includes('risk')) return <Users className="h-4 w-4" />
    
    // 默认图标
    return <FileText className="h-4 w-4" />
  }

  const renderSections = () => {
    if (!reportData.sections || typeof reportData.sections !== 'object') {
      return (
        <div className="text-gray-500 text-center py-8">
          无报告内容可显示
        </div>
      )
    }

    // 直接从数据中获取所有sections，按字母顺序排列
    const sortedSections = Object.entries(reportData.sections).sort(([a], [b]) => {
      return a.localeCompare(b)
    })

    if (sortedSections.length === 0) {
      return (
        <div className="text-gray-500 text-center py-8">
          无报告内容可显示
        </div>
      )
    }

    // 获取第一个section作为默认选中的tab
    const defaultSection = sortedSections[0][0]

    return (
      <Tabs defaultValue={defaultSection} className="w-full">
        <TabsList className={`grid w-full gap-1 bg-gray-100 p-1 ${sortedSections.length === 1 ? 'grid-cols-1' : sortedSections.length === 2 ? 'grid-cols-2' : 'grid-cols-1 sm:grid-cols-3'}`}>
          {sortedSections.map(([sectionKey]) => (
            <TabsTrigger 
              key={sectionKey} 
              value={sectionKey}
              className="flex items-center gap-2 text-sm px-3 py-2 data-[state=active]:bg-white data-[state=active]:shadow-sm transition-all duration-200"
            >
              {getSectionIcon(sectionKey)}
              <span className="hidden sm:inline font-medium">{getSectionTitle(sectionKey)}</span>
              <span className="sm:hidden font-medium text-xs">
                {getSectionTitle(sectionKey).length > 6 
                  ? getSectionTitle(sectionKey).substring(0, 4) + '..'
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
            className="mt-6 focus:outline-none"
          >
           <MarkdownRenderer 
                  content={content} 
                  className="prose prose-lg max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-ul:text-gray-700 prose-ol:text-gray-700 prose-li:text-gray-700 prose-blockquote:text-gray-600 prose-code:text-blue-600 prose-pre:bg-gray-50"
                />
          </TabsContent>
        ))}
      </Tabs>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/reports">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回列表
            </Button>
          </Link>
          <div className="flex items-center space-x-2">
            <FileText className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {reportData.ticker} 完整分析报告
              </h1>
              {reportData.title && (
                <p className="text-lg text-gray-600 mt-1">{reportData.title}</p>
              )}
              <div className="flex items-center space-x-4 text-gray-600 mt-2">
                <div className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4" />
                  <span>{reportData.date}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="h-4 w-4" />
                  <span>{formatDate(reportData.created_at)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge className={getStatusColor(reportData.status)}>
            {getStatusLabel(reportData.status)}
          </Badge>
          <Link href="/reports">
            <Button variant="outline" size="sm">
              <History className="h-4 w-4 mr-2" />
              历史报告
            </Button>
          </Link>
          <Button onClick={downloadReport}>
            <Download className="h-4 w-4 mr-2" />
            下载报告
          </Button>
        </div>
      </div>

      {/* Report Content */}
      <Card className="shadow-lg">
     
        <CardContent className="p-6">
          {renderSections()}
        </CardContent>
      </Card>

      {/* Report Metadata */}
      <Card className="shadow-md">
        <CardHeader className="bg-gray-50 border-b">
          <CardTitle className="text-lg flex items-center gap-2">
            <div className="p-2 bg-blue-100 rounded-full">
              <FileText className="h-4 w-4 text-blue-600" />
            </div>
            报告信息
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors duration-200">
              <div className="text-2xl font-bold text-blue-600 mb-1">{reportData.ticker}</div>
              <div className="text-sm text-gray-600 font-medium">股票代码</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors duration-200">
              <div className="text-2xl font-bold text-green-600 mb-1">
                {Object.keys(reportData.sections || {}).length}
              </div>
              <div className="text-sm text-gray-600 font-medium">分析章节</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors duration-200">
              <div className="text-2xl font-bold text-purple-600 mb-1">
                {getStatusLabel(reportData.status)}
              </div>
              <div className="text-sm text-gray-600 font-medium">状态</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors duration-200">
              <div className="text-2xl font-bold text-orange-600 mb-1">
                {Math.round(Object.values(reportData.sections || {}).join('').length / 1000)}K
              </div>
              <div className="text-sm text-gray-600 font-medium">字符数</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
