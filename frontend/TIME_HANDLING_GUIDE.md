# 前端时间处理指南

## 概述

在TradingAgents项目中，后端使用SQLAlchemy的`DateTime(timezone=True)`储存UTC时间，前端需要将这些UTC时间转换为用户的本地时间进行显示。

## 后端时间存储

```python
# backend/database/models.py
created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- 后端统一存储UTC时间
- 数据库字段包含时区信息
- API返回的时间格式通常为：`2025-09-17T10:30:00Z` 或 `2025-09-17T10:30:00.123Z`

## 前端时间工具函数

在 `frontend/src/lib/utils.ts` 中提供了完整的时间处理工具：

### 核心函数

| 函数名 | 用途 | 输出示例 | 适用场景 |
|--------|------|----------|----------|
| `formatRelativeTime()` | 相对时间 | "2小时前", "3天前" | 消息列表、活动动态 |
| `formatLocalDateTime()` | 完整本地时间 | "2025/09/17 18:30:45 GMT+8" | 报告详情、系统日志 |
| `formatCompactTime()` | 紧凑时间 | "09/17 18:30 GMT+8" | 表格、卡片显示 |
| `formatTimestamp()` | 时间戳 | "18:30:45" | 聊天记录、调试信息 |
| `formatSmartTime()` | 智能时间 | 今天："18:30", 其他："09/17" | 通用自适应场景 |

### 辅助函数

- `formatISODate()`: 格式化为ISO日期 (YYYY-MM-DD)
- `getUserTimeZone()`: 获取用户时区
- `isToday()`: 判断是否为今天

## 使用示例

### 1. 基本使用

```tsx
import { formatRelativeTime, formatLocalDateTime } from '@/lib/utils'

function ReportCard({ report }) {
  return (
    <div>
      <h3>{report.title}</h3>
      {/* 显示相对时间 */}
      <span>创建于 {formatRelativeTime(report.created_at)}</span>
      
      {/* 显示完整时间 */}
      <div>详细时间: {formatLocalDateTime(report.created_at)}</div>
    </div>
  )
}
```

### 2. 自定义格式选项

```tsx
import { formatLocalDateTime } from '@/lib/utils'

// 仅显示日期
formatLocalDateTime(timestamp, { dateOnly: true })
// 输出: 2025/09/17

// 仅显示时间
formatLocalDateTime(timestamp, { timeOnly: true })
// 输出: 18:30:45 GMT+8

// 不显示秒和时区
formatLocalDateTime(timestamp, { showSeconds: false, showTimeZone: false })
// 输出: 2025/09/17 18:30
```

### 3. 表格中的时间显示

```tsx
import { formatCompactTime, formatSmartTime } from '@/lib/utils'

function ReportsTable({ reports }) {
  return (
    <table>
      <thead>
        <tr>
          <th>股票代码</th>
          <th>创建时间</th>
          <th>更新时间</th>
        </tr>
      </thead>
      <tbody>
        {reports.map(report => (
          <tr key={report.id}>
            <td>{report.ticker}</td>
            <td>{formatCompactTime(report.created_at)}</td>
            <td>{formatSmartTime(report.updated_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

## 迁移现有代码

### 替换旧的时间处理代码

**旧代码：**
```tsx
const formatDate = (dateStr: string) => {
  try {
    let date = new Date(dateStr)
    if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
      date = new Date(dateStr + 'Z')
    }
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZoneName: 'short'
    })
  } catch {
    return dateStr
  }
}
```

**新代码：**
```tsx
import { formatLocalDateTime } from '@/lib/utils'

// 直接使用工具函数
{formatLocalDateTime(timestamp)}
```

## 时区处理原理

### UTC时间解析

工具函数会自动处理不同格式的UTC时间：

```tsx
// 自动识别这些格式
'2025-09-17T10:30:00Z'           // 标准UTC格式
'2025-09-17T10:30:00.123Z'       // 包含毫秒
'2025-09-17 10:30:00'            // 无时区信息，假设为UTC
'2025-09-17T10:30:00+00:00'      // 明确的UTC格式
```

### 本地时间转换

```tsx
function parseUTCDate(dateStr: string): Date {
  // 如果没有时区信息，假设为UTC
  if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
    return new Date(dateStr + 'Z')
  }
  return new Date(dateStr)
}
```

### 本地化显示

```tsx
// 使用浏览器的本地化API
date.toLocaleString('zh-CN', {
  year: 'numeric',
  month: '2-digit', 
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  timeZoneName: 'short'  // 显示时区缩写
})
```

## 最佳实践

### 1. 选择合适的格式函数

- **列表和动态**: 使用 `formatRelativeTime()` 显示"2小时前"
- **详情页面**: 使用 `formatLocalDateTime()` 显示完整时间
- **表格数据**: 使用 `formatCompactTime()` 节省空间
- **通用场景**: 使用 `formatSmartTime()` 自动选择格式

### 2. 一致性原则

- 在同一个界面中使用一致的时间格式
- 重要信息使用完整时间格式
- 次要信息可使用相对时间

### 3. 用户体验

- 提供时区信息让用户了解时间基准
- 在详情页面显示完整时间信息
- 考虑不同时区用户的需求

### 4. 性能考虑

- 时间格式化函数已优化，可以安全地在渲染中使用
- 避免在循环中重复创建Date对象
- 合理使用缓存避免重复计算

## 测试和验证

### 本地测试

```tsx
// 在浏览器控制台测试
import { formatLocalDateTime, getUserTimeZone } from '@/lib/utils'

console.log('用户时区:', getUserTimeZone())
console.log('格式化时间:', formatLocalDateTime('2025-09-17T10:30:00Z'))
```

### 不同时区测试

可以在浏览器开发者工具中模拟不同时区：
1. 打开开发者工具
2. 按 Ctrl+Shift+P (Windows) 或 Cmd+Shift+P (Mac)
3. 输入 "timezone" 搜索时区设置
4. 选择不同时区进行测试

## 常见问题

### Q: 时间显示不正确怎么办？
A: 检查后端返回的时间格式，确保包含时区信息或符合UTC格式。

### Q: 如何处理无时区信息的时间？
A: 工具函数会自动假设为UTC时间，在字符串后添加'Z'。

### Q: 用户在不同时区看到的时间一致吗？
A: 是的，工具函数会自动转换为用户本地时区，确保显示正确的本地时间。

### Q: 如何自定义时间格式？
A: 使用 `formatLocalDateTime()` 的options参数，或直接使用JavaScript的Intl.DateTimeFormat API。

## 相关文件

- `frontend/src/lib/utils.ts` - 时间工具函数
- `frontend/src/examples/TimeDisplayExample.tsx` - 使用示例
- `backend/database/models.py` - 后端时间字段定义
