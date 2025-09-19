# TradingAgents 用户偏好设置最终方案

## 概述

经过设计调整，TradingAgents 现在实现了以下用户偏好管理方案：
- **语言设置**：控制 AI 报告生成语言，替换原有模型配置中的语言设置
- **时区设置**：系统统一时区管理，影响所有时间显示和任务执行
- **界面语言**：暂时保持中文，不进行国际化

## 核心特性

### 1. 用户偏好管理系统

#### 数据结构
```typescript
export interface UserPreferences {
  language: string        // AI报告生成语言
  timezone: string        // 时区设置
  theme?: string         // 主题设置（预留）
  dateFormat?: string    // 日期格式（预留）
  currency?: string      // 货币单位（预留）
}
```

#### 存储机制
- 使用 `localStorage` 持久化存储
- 键名：`tradingagents_user_preferences`
- 自动合并默认设置，确保向后兼容

### 2. 语言设置功能

#### 支持的语言
```typescript
const supportedLanguages = [
  {
    value: 'zh-CN',
    label: '简体中文',
    description: 'AI报告将使用简体中文生成',
    isDefault: true
  },
  {
    value: 'zh-TW', 
    label: '繁體中文',
    description: 'AI报告将使用繁體中文生成'
  },
  {
    value: 'en-US',
    label: 'English (US)',
    description: 'AI reports will be generated in English'
  },
  {
    value: 'en-GB',
    label: 'English (UK)', 
    description: 'AI reports will be generated in English'
  }
]
```

#### 自动检测逻辑
1. 读取 `navigator.language` 或 `navigator.languages[0]`
2. 精确匹配支持的语言列表
3. 语言前缀匹配（如 `en` 匹配 `en-US`）
4. 默认回退到 `zh-CN`

#### API 函数
```typescript
// 获取用户设置的语言（用于AI报告生成）
export function getUserLanguage(): string

// 自动检测用户语言偏好
export function detectUserLanguage(): string

// 获取语言显示名称
export function getLanguageDisplayName(language: string): string

// 获取支持的语言列表
export function getSupportedLanguages()
```

### 3. 时区设置功能

#### 时区管理
- 自动检测用户设备时区作为默认值
- 支持常用时区快速选择
- 显示时区偏移量信息

#### API 函数（保持向后兼容）
```typescript
// 获取系统时区（现在来自用户偏好）
export function getSystemTimeZone(): string

// 设置系统时区（现在更新用户偏好）
export function setSystemTimeZone(timezone: string): void

// 获取用户时区（原浏览器时区）
export function getUserTimeZone(): string
```

### 4. 用户偏好设置界面

#### 组件特性
- 统一的偏好管理界面
- 实时预览功能
- 自动检测提示
- 清晰的功能说明

#### 界面布局
```
┌─────────────────────────────────────┐
│ 用户偏好设置                          │
├─────────────────────────────────────┤
│ [当前设置显示]                        │
├─────────────────────────────────────┤
│ AI报告语言                           │
│ [语言选择器] + 自动检测提示            │
├─────────────────────────────────────┤
│ 时区设置                             │
│ [时区选择器] + 自动检测提示            │
├─────────────────────────────────────┤
│ [预览变更] (有变更时显示)              │
├─────────────────────────────────────┤
│ [保存] [重置] [取消]                  │
├─────────────────────────────────────┤
│ [功能说明]                           │
└─────────────────────────────────────┘
```

## 与 AI 模型集成

### 语言设置的使用

#### 后端集成点
1. **分析任务创建时**：
   - 读取用户语言偏好
   - 传递给 AI 模型配置
   - 替换原有的硬编码语言设置

2. **报告生成时**：
   - 使用 `getUserLanguage()` 获取用户语言
   - 配置 AI 模型的输出语言
   - 确保报告符合用户语言偏好

#### API 调用示例
```typescript
// 前端获取用户语言
import { getUserLanguage } from '@/lib/utils'

const userLanguage = getUserLanguage() // 例如: 'zh-CN'

// 传递给后端API
const analysisConfig = {
  ticker: 'AAPL',
  analysts: ['market_analyst'],
  research_depth: 2,
  language: userLanguage  // 替换原有的模型配置语言
}
```

### 时区设置的使用

#### 任务调度
- 新创建的任务自动使用系统时区
- 任务执行时间基于用户设置的时区
- 时间显示统一使用用户时区

#### 时间显示
- 所有界面时间显示使用用户时区
- 提供时区信息标识
- 支持时区转换和格式化

## 向后兼容性

### 数据迁移
- 自动检测并迁移旧的时区设置
- 为缺失的字段提供默认值
- 保持现有功能正常运行

### API 兼容
- 保留原有的时区 API 函数
- 内部重定向到新的偏好系统
- 不影响现有代码调用

## 最佳实践

### 1. 语言设置
- AI 报告生成时始终使用 `getUserLanguage()`
- 避免硬编码语言设置
- 为不支持的语言提供合理的默认值

### 2. 时区设置
- 新功能统一使用 `getSystemTimeZone()`
- 时间显示包含时区信息
- 任务创建时自动应用用户时区

### 3. 用户体验
- 提供自动检测功能降低配置门槛
- 显示预览帮助用户理解设置效果
- 提供清晰的功能说明和影响范围

## 开发指南

### 前端集成
```typescript
// 获取用户偏好
import { getUserPreferences, getUserLanguage, getSystemTimeZone } from '@/lib/utils'

const preferences = getUserPreferences()
const reportLanguage = getUserLanguage()  // 用于AI报告
const systemTimezone = getSystemTimeZone() // 用于时间显示
```

### 后端集成
```python
# 预期后端会接收到语言参数
def create_analysis_task(ticker, analysts, research_depth, language, timezone):
    # 使用用户语言配置AI模型
    model_config = {
        'language': language,  # 来自用户偏好，而非模型配置
        'output_format': 'detailed_report'
    }
    
    # 使用用户时区配置任务调度
    schedule_config = {
        'timezone': timezone,
        'execution_time': schedule_time
    }
```

## 总结

新的用户偏好系统实现了：

✅ **语言设置**：控制 AI 报告生成语言，替换模型配置  
✅ **时区设置**：系统统一时区管理  
✅ **自动检测**：基于浏览器设置的智能默认值  
✅ **向后兼容**：不影响现有功能  
✅ **用户友好**：直观的设置界面和预览功能  

这个方案既满足了用户个性化需求，又保持了系统的一致性和易用性。
