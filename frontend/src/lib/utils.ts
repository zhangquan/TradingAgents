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
 * 格式化为完整的年月日时分秒
 * @param dateStr - UTC时间字符串
 * @returns YYYY年MM月DD日 HH:mm:ss格式的时间字符串
 */
export function formatFullTimestamp(dateStr: string): string {
  try {
    const date = parseUTCDate(dateStr)
    return format(date, 'yyyy年MM月dd日 HH:mm:ss')
  } catch {
    return dateStr
  }
}

/**
 * 格式化为紧凑的年月日时分
 * @param dateStr - UTC时间字符串
 * @returns YYYY-MM-DD HH:mm格式的时间字符串
 */
export function formatCompactDateTime(dateStr: string): string {
  try {
    const date = parseUTCDate(dateStr)
    return format(date, 'yyyy-MM-dd HH:mm')
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
 * 用户偏好设置管理
 */
const USER_PREFERENCES_KEY = 'tradingagents_user_preferences'

export interface UserPreferences {
  language: string        // AI报告生成语言
  timezone: string        // 时区设置
  theme?: string         // 主题设置（预留）
  dateFormat?: string    // 日期格式（预留）
  currency?: string      // 货币单位（预留）
}

/**
 * 自动检测用户语言偏好
 * @returns 语言代码
 */
export function detectUserLanguage(): string {
  // 优先级：navigator.language > navigator.languages[0] > 默认中文
  const browserLang = navigator.language || navigator.languages?.[0] || 'zh-CN'
  
  // 支持的语言列表
  const supportedLanguages = ['zh-CN', 'zh-TW', 'en-US', 'en-GB']
  
  // 精确匹配
  if (supportedLanguages.includes(browserLang)) {
    return browserLang
  }
  
  // 语言前缀匹配
  const langPrefix = browserLang.split('-')[0]
  const matchedLang = supportedLanguages.find(lang => lang.startsWith(langPrefix))
  
  return matchedLang || 'zh-CN' // 默认中文
}

/**
 * 获取默认用户偏好设置
 * @returns 默认偏好设置
 */
export function getDefaultPreferences(): UserPreferences {
  return {
    language: detectUserLanguage(),
    timezone: getUserTimeZone()
  }
}

/**
 * 获取用户偏好设置
 * @returns 用户偏好设置
 */
export function getUserPreferences(): UserPreferences {
  try {
    const saved = localStorage.getItem(USER_PREFERENCES_KEY)
    if (saved) {
      const preferences = JSON.parse(saved) as UserPreferences
      // 合并默认设置，确保新字段有默认值
      return { ...getDefaultPreferences(), ...preferences }
    }
  } catch (error) {
    console.warn('Failed to parse user preferences:', error)
  }
  
  return getDefaultPreferences()
}

/**
 * 设置用户偏好
 * @param preferences - 偏好设置
 */
export function setUserPreferences(preferences: Partial<UserPreferences>): void {
  const current = getUserPreferences()
  const updated = { ...current, ...preferences }
  localStorage.setItem(USER_PREFERENCES_KEY, JSON.stringify(updated))
}

/**
 * 重置用户偏好设置
 */
export function resetUserPreferences(): void {
  localStorage.removeItem(USER_PREFERENCES_KEY)
}

/**
 * 获取系统设置的时区（兼容旧版本，现在使用用户偏好）
 * @returns 系统时区字符串
 */
export function getSystemTimeZone(): string {
  return getUserPreferences().timezone
}

/**
 * 设置系统时区（兼容旧版本，现在使用用户偏好）
 * @param timezone - 时区字符串
 */
export function setSystemTimeZone(timezone: string): void {
  setUserPreferences({ timezone })
}

/**
 * 获取用户语言设置（用于AI报告生成）
 * @returns 语言代码
 */
export function getUserLanguage(): string {
  return getUserPreferences().language
}


/**
 * 获取时区显示名称
 * @param timezone - 时区标识符
 * @returns 时区显示名称
 */
export function getTimezoneDisplayName(timezone: string): string {
  try {
    const now = new Date()
    const formatter = new Intl.DateTimeFormat('zh-CN', {
      timeZone: timezone,
      timeZoneName: 'long'
    })
    const parts = formatter.formatToParts(now)
    const timeZoneName = parts.find(part => part.type === 'timeZoneName')?.value
    return timeZoneName || timezone
  } catch {
    return timezone
  }
}

/**
 * 获取时区偏移量显示
 * @param timezone - 时区标识符
 * @returns 时区偏移量字符串，如 "GMT+8"
 */
export function getTimezoneOffset(timezone: string): string {
  try {
    const now = new Date()
    const formatter = new Intl.DateTimeFormat('en', {
      timeZone: timezone,
      timeZoneName: 'short'
    })
    const parts = formatter.formatToParts(now)
    const timeZoneName = parts.find(part => part.type === 'timeZoneName')?.value
    return timeZoneName || timezone
  } catch {
    return timezone
  }
}

/**
 * 获取支持的语言列表（用于AI报告生成）
 * @returns 支持的语言配置数组
 */
export function getSupportedLanguages() {
  return [
    {
      value: 'zh-CN',
      label: '简体中文',
      nativeLabel: '简体中文',
      description: 'AI报告将使用简体中文生成',
      isDefault: true
    },
    {
      value: 'zh-TW',
      label: '繁體中文',
      nativeLabel: '繁體中文',
      description: 'AI报告将使用繁體中文生成',
      isDefault: false
    },
    {
      value: 'en-US',
      label: 'English (US)',
      nativeLabel: 'English (US)',
      description: 'AI reports will be generated in English',
      isDefault: false
    },
    {
      value: 'en-GB',
      label: 'English (UK)',
      nativeLabel: 'English (UK)',
      description: 'AI reports will be generated in English',
      isDefault: false
    }
  ]
}

/**
 * 获取语言显示名称
 * @param language - 语言代码
 * @returns 语言显示名称
 */
export function getLanguageDisplayName(language: string): string {
  const languages = getSupportedLanguages()
  const found = languages.find(lang => lang.value === language)
  return found?.label || language
}

/**
 * 获取常用时区列表
 * @returns 常用时区配置数组
 */
export function getCommonTimezones() {
  const userTz = getUserTimeZone()
  
  return [
    {
      value: userTz,
      label: `本地时区 (${userTz})`,
      offset: getTimezoneOffset(userTz),
      isLocal: true
    },
    {
      value: "UTC",
      label: "协调世界时 (UTC)",
      offset: "UTC",
      isLocal: false
    },
    {
      value: "Asia/Shanghai",
      label: "北京时间",
      offset: getTimezoneOffset("Asia/Shanghai"),
      isLocal: false
    },
    {
      value: "America/New_York",
      label: "美东时间",
      offset: getTimezoneOffset("America/New_York"),
      isLocal: false
    },
    {
      value: "America/Los_Angeles",
      label: "美西时间",
      offset: getTimezoneOffset("America/Los_Angeles"),
      isLocal: false
    },
    {
      value: "Europe/London",
      label: "伦敦时间",
      offset: getTimezoneOffset("Europe/London"),
      isLocal: false
    },
    {
      value: "Asia/Tokyo",
      label: "东京时间",
      offset: getTimezoneOffset("Asia/Tokyo"),
      isLocal: false
    }
  ]
}

/**
 * 格式化带时区信息的时间
 * @param dateStr - UTC时间字符串
 * @param timezone - 目标时区
 * @param options - 格式化选项
 * @returns 格式化的时间字符串
 */
export function formatTimeWithTimezone(
  dateStr: string, 
  timezone: string = getUserTimeZone(),
  options: {
    showDate?: boolean
    showTime?: boolean
    showTimezone?: boolean
    format?: 'full' | 'short'
  } = {}
): string {
  try {
    const date = parseUTCDate(dateStr)
    const {
      showDate = true,
      showTime = true,
      showTimezone = true,
      format = 'short'
    } = options

    const formatOptions: Intl.DateTimeFormatOptions = {
      timeZone: timezone
    }

    if (showDate) {
      formatOptions.year = 'numeric'
      formatOptions.month = '2-digit'
      formatOptions.day = '2-digit'
    }

    if (showTime) {
      formatOptions.hour = '2-digit'
      formatOptions.minute = '2-digit'
      if (format === 'full') {
        formatOptions.second = '2-digit'
      }
    }

    if (showTimezone) {
      formatOptions.timeZoneName = format === 'full' ? 'long' : 'short'
    }

    return date.toLocaleString('zh-CN', formatOptions)
  } catch {
    return dateStr
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
