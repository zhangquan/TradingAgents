# Reports Service Layer

## 概述

ReportsService 是一个独立的服务层，专门处理 TradingAgents 系统中所有与报告相关的业务逻辑。该服务层将报告管理从路由层分离，提供了更清晰的架构和更好的可维护性。

## 主要功能

### 1. 核心报告管理

#### 创建统一报告
```python
create_unified_report(analysis_id, user_id, ticker, sections, title=None) -> str
```
- 为分析创建包含多个部分的统一报告
- 支持验证输入参数和部分内容
- 自动记录系统事件

#### 获取报告详情
```python
get_report_by_id(report_id, user_id) -> Optional[Dict[str, Any]]
```
- 根据ID获取特定报告
- 返回增强的报告数据，包括计算字段
- 自动检查权限

#### 列出报告
```python
list_reports(user_id, ticker=None, analysis_id=None, watchlist_only=False, limit=100) -> List[Dict[str, Any]]
```
- 支持多种过滤条件
- 自动增强报告数据
- 支持观察列表过滤

#### 按股票代码获取报告
```python
get_reports_by_ticker(ticker, user_id, report_type=None, limit=50) -> List[Dict[str, Any]]
```
- 获取特定股票的所有报告
- 支持报告类型过滤
- 自动增强数据

### 2. 报告删除功能

#### 单个报告删除
```python
delete_report(report_id, user_id) -> Dict[str, Any]
```
- 安全删除单个报告
- 记录删除事件
- 返回详细的操作结果

#### 批量报告删除
```python
batch_delete_reports(report_ids, user_id) -> Dict[str, Any]
```
- 高效的批量删除操作
- 错误处理和回滚
- 详细的操作统计

### 3. 报告分析和统计

#### 报告统计
```python
get_report_statistics(user_id) -> Dict[str, Any]
```
返回的统计信息包括：
- 总报告数量
- 唯一股票数量
- 最常分析的股票
- 按股票分组的报告数
- 按月份分组的报告数
- 部分统计（投资计划、市场报告、交易决策）
- 每个股票的平均报告数

#### 最近报告
```python
get_recent_reports(user_id, days=7, limit=20) -> List[Dict[str, Any]]
```
- 获取指定天数内的最近报告
- 支持限制返回数量
- 自动增强数据

### 4. 报告验证和质量检查

#### 验证报告部分
```python
validate_report_sections(sections) -> Dict[str, Any]
```
验证功能包括：
- 检查必需的部分
- 内容质量分析
- 字数统计
- 空内容检查
- 未知部分警告

返回验证结果：
```json
{
  "valid": true,
  "warnings": [],
  "errors": [],
  "section_analysis": {
    "market_report": {
      "present": true,
      "length": 1500,
      "word_count": 250,
      "empty": false
    }
  },
  "total_sections": 3,
  "total_content_length": 4500
}
```

## API 端点

### 现有端点（已重构）

- `GET /reports` - 获取报告列表
- `GET /reports/report/{report_id}` - 获取特定报告
- `GET /reports/ticker/{ticker}` - 按股票代码获取报告
- `DELETE /reports/{report_id}` - 删除报告
- `DELETE /reports/batch/reports` - 批量删除报告

### 新增端点

- `GET /reports/statistics` - 获取报告统计
- `GET /reports/recent` - 获取最近报告
- `POST /reports` - 创建新报告
- `POST /reports/validate` - 验证报告部分

## 数据增强

ReportsService 为所有报告数据添加了以下增强字段：

```json
{
  "report_id": "report_AAPL_...",
  "analysis_id": "analysis_AAPL_...",
  "ticker": "AAPL",
  "date": "2025-01-15T10:30:00",
  "report_type": "unified_analysis",
  "title": "AAPL Complete Analysis Report",
  "sections": {...},
  "sections_count": 3,
  "status": "generated",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00",
  "in_watchlist": true,
  "has_investment_plan": true,
  "has_market_report": true,
  "has_trade_decision": true
}
```

## 错误处理

ReportsService 提供了强大的错误处理机制：

1. **输入验证** - 验证所有必需参数
2. **业务逻辑验证** - 检查业务规则违反
3. **数据库错误处理** - 处理数据库连接和操作错误
4. **日志记录** - 详细的错误日志记录
5. **用户友好错误消息** - 返回清晰的错误信息

## 使用示例

### 创建报告

```python
from backend.services.reports_service import reports_service

# 创建新报告
report_id = reports_service.create_unified_report(
    analysis_id="analysis_AAPL_20250115_103000",
    user_id="demo_user",
    ticker="AAPL",
    sections={
        "market_report": "市场分析内容...",
        "investment_plan": "投资计划内容...",
        "final_trade_decision": "交易决策内容..."
    },
    title="AAPL 综合分析报告"
)
```

### 获取统计信息

```python
# 获取用户报告统计
stats = reports_service.get_report_statistics("demo_user")
print(f"总报告数: {stats['total_reports']}")
print(f"最常分析股票: {stats['most_analyzed_ticker']['ticker']}")
```

### 验证报告内容

```python
# 验证报告部分
validation = reports_service.validate_report_sections({
    "market_report": "详细的市场分析...",
    "investment_plan": "投资策略...",
    "final_trade_decision": "买入决策..."
})

if validation["valid"]:
    print("报告验证通过")
else:
    print(f"验证错误: {validation['errors']}")
```

## 集成说明

### 与现有系统的集成

1. **DatabaseStorage** - 继续使用现有的数据库存储层
2. **Analysis Service** - 可以调用 ReportsService 创建分析报告
3. **Scheduler Service** - 可以在计划任务完成后创建报告

### 向后兼容性

ReportsService 完全向后兼容现有的 API：
- 所有现有端点继续工作
- 响应格式保持一致
- 添加了新的增强字段，不影响现有客户端

## 性能优化

1. **数据库查询优化** - 使用索引和限制查询
2. **缓存策略** - 统计数据可以缓存
3. **批量操作** - 支持高效的批量删除
4. **分页支持** - 所有列表操作支持限制返回数量

## 未来扩展

ReportsService 设计为可扩展的，未来可以添加：

1. **报告模板** - 预定义的报告格式
2. **报告导出** - PDF、Excel 等格式导出
3. **报告分享** - 用户间报告分享功能
4. **报告订阅** - 自动生成和推送报告
5. **高级分析** - 报告趋势分析和预测

## 配置

ReportsService 使用系统默认配置，无需额外配置文件。所有设置通过 DatabaseStorage 管理。

## 测试

建议为 ReportsService 编写以下测试：

1. **单元测试** - 测试所有方法的基本功能
2. **集成测试** - 测试与数据库的交互
3. **性能测试** - 测试大量数据的处理能力
4. **错误处理测试** - 测试各种错误情况的处理
