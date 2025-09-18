import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { format, parseISO, formatDistanceToNow } from "date-fns"
import { zhCN } from "date-fns/locale"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 时间处理工具函数
 * 用于将后端UTC时间转换为本地时间并格式化显示
 */

/**
 * 解析UTC时间字符串为Date对象
 * @param dateStr - UTC时间字符串
 * @returns Date对象
 */
function parseUTCDate(dateStr: string): Date {
  try {
    // 如果时间字符串没有时区信息，假设它是UTC时间
    if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
      return new Date(dateStr + 'Z')
    }
    return new Date(dateStr)
  } catch {
    return new Date()
  }
}

/**
 * 格式化为相对时间（如：2小时前）
 * @param dateStr - UTC时间字符串
 * @returns 相对时间字符串
 */
export function formatRelativeTime(dateStr: string): string {
  try {
    const date = parseUTCDate(dateStr)
    return formatDistanceToNow(date, { addSuffix: true, locale: zhCN })
  } catch {
    return dateStr
  }
}

/**
 * 格式化为完整的本地时间
 * @param dateStr - UTC时间字符串
 * @param options - 格式化选项
 * @returns 本地时间字符串
 */
export function formatLocalDateTime(
  dateStr: string, 
  options?: {
    showTimeZone?: boolean
    showSeconds?: boolean
    dateOnly?: boolean
    timeOnly?: boolean
  }
): string {
  try {
    const date = parseUTCDate(dateStr)
    const { showTimeZone = true, showSeconds = true, dateOnly = false, timeOnly = false } = options || {}
    
    if (dateOnly) {
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    }
    
    if (timeOnly) {
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        ...(showSeconds && { second: '2-digit' }),
        ...(showTimeZone && { timeZoneName: 'short' })
      })
    }
    
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      ...(showSeconds && { second: '2-digit' }),
      ...(showTimeZone && { timeZoneName: 'short' })
    })
  } catch {
    return dateStr
  }
}

/**
 * 格式化为紧凑的时间显示（适合表格和卡片）
 * @param dateStr - UTC时间字符串
 * @returns 紧凑格式的时间字符串
 */
export function formatCompactTime(dateStr: string): string {
  try {
    const date = parseUTCDate(dateStr)
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short'
    })
  } catch {
    return dateStr
  }
}

/**
 * 格式化为时间戳（仅时间部分）
 * @param dateStr - UTC时间字符串
 * @returns HH:mm:ss格式的时间字符串
 */
export function formatTimestamp(dateStr: string): string {
  try {
    const date = parseUTCDate(dateStr)
    return format(date, 'HH:mm:ss')
  } catch {
    return dateStr
  }
}

/**
 * 格式化为ISO日期字符串（YYYY-MM-DD）
 * @param dateStr - UTC时间字符串
 * @returns YYYY-MM-DD格式的日期字符串
 */
export function formatISODate(dateStr: string): string {
  try {
    const date = parseUTCDate(dateStr)
    return format(date, 'yyyy-MM-dd')
  } catch {
    return dateStr
  }
}

/**
 * 获取当前用户的时区
 * @returns 时区字符串
 */
export function getUserTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

/**
 * 自动设置用户时区到服务器
 * 在应用初始化时调用
 */
export async function autoSetUserTimezone() {
  try {
    const userTimezone = getUserTimeZone()
    
    // 检查当前服务器存储的时区
    const { apiService } = await import('@/lib/api')
    const currentConfig = await apiService.getUserTimezone()
    
    // 如果时区不同，更新服务器设置
    if (currentConfig.timezone !== userTimezone) {
      await apiService.setUserTimezone(userTimezone)
      console.log(`Auto-updated user timezone to: ${userTimezone}`)
    }
  } catch (error) {
    console.warn('Failed to auto-set user timezone:', error)
  }
}

/**
 * 检查时间字符串是否为今天
 * @param dateStr - UTC时间字符串
 * @returns 是否为今天
 */
export function isToday(dateStr: string): boolean {
  try {
    const date = parseUTCDate(dateStr)
    const today = new Date()
    return date.toDateString() === today.toDateString()
  } catch {
    return false
  }
}

/**
 * 获取智能时间显示（今天显示时间，其他显示日期）
 * @param dateStr - UTC时间字符串
 * @returns 智能格式的时间字符串
 */
export function formatSmartTime(dateStr: string): string {
  try {
    const date = parseUTCDate(dateStr)
    if (isToday(dateStr)) {
      return format(date, 'HH:mm')
    } else {
      const now = new Date()
      const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
      
      if (diffDays < 7) {
        return formatRelativeTime(dateStr)
      } else {
        return format(date, 'MM-dd')
      }
    }
  } catch {
    return dateStr
  }
}

/**
 * 格式化分析报告时间显示（优化版）
 * @param dateStr - UTC时间字符串
 * @returns 优化的分析报告时间字符串
 */
export function formatAnalysisReportTime(dateStr: string): string {
  try {
    const date = parseUTCDate(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    // 如果是今天
    if (isToday(dateStr)) {
      if (diffMinutes < 1) {
        return '刚刚生成'
      } else if (diffMinutes < 60) {
        return `${diffMinutes}分钟前生成`
      } else {
        return `今天 ${format(date, 'HH:mm')} 生成`
      }
    }
    
    // 如果是昨天
    if (diffDays === 1) {
      return `昨天 ${format(date, 'HH:mm')} 生成`
    }
    
    // 如果是一周内
    if (diffDays < 7) {
      return `${diffDays}天前 ${format(date, 'HH:mm')} 生成`
    }
    
    // 超过一周
    return `${format(date, 'MM月dd日 HH:mm')} 生成`
  } catch {
    return dateStr
  }
}

/**
 * 从agent_status推断整体会话状态
 * @param agentStatus - agent状态字典
 * @param isFinalized - 是否已完成
 * @returns 会话状态字符串
 */
export function getConversationStatus(agentStatus: { [key: string]: string }, isFinalized: boolean): string {
  if (isFinalized) {
    return 'completed'
  }
  
  if (!agentStatus || Object.keys(agentStatus).length === 0) {
    return 'pending'
  }
  
  const statuses = Object.values(agentStatus)
  
  // 如果有任何agent在运行中
  if (statuses.some(status => status === 'in_progress' || status === 'running')) {
    return 'active'
  }
  
  // 如果有任何agent出错
  if (statuses.some(status => status === 'error' || status === 'failed')) {
    return 'error'
  }
  
  // 如果所有agent都完成了
  if (statuses.every(status => status === 'completed')) {
    return 'completed'
  }
  
  // 如果有一些完成了，一些还在等待
  if (statuses.some(status => status === 'completed')) {
    return 'active'
  }
  
  // 默认为等待状态
  return 'pending'
}
