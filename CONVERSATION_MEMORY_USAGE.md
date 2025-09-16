# TradingAgents 长期记忆系统使用指南

## 概述

TradingAgents 现在支持长期记忆功能，能够保存和恢复 trading_graph agent 的完整执行状态。这使得您可以：

- **保存分析会话**：完整保存所有agent的执行状态、消息历史和报告
- **恢复会话**：重新查看之前的分析结果
- **Chat界面**：基于历史会话进行交互式对话
- **API访问**：通过REST API管理会话记忆

## 功能特性

### 1. 会话状态保存
- ✅ Agent执行状态跟踪（pending/in_progress/completed/error）
- ✅ 实时消息和工具调用历史
- ✅ 分阶段报告内容（市场分析、新闻分析、投资决策等）
- ✅ 完整的最终状态和处理结果
- ✅ 配置信息和元数据

### 2. Chat-based 会话恢复
- ✅ 完整会话历史查看
- ✅ 交互式聊天界面
- ✅ 实时状态查询
- ✅ 报告内容访问

### 3. API 接口
- ✅ 创建、获取、更新会话
- ✅ 实时状态和报告更新
- ✅ 聊天消息管理
- ✅ 会话归档和管理

## CLI 使用方法

### 1. 运行新的分析（自动启用记忆）

```bash
# 运行分析（会自动创建会话并保存状态）
python -m cli.main analyze
```

分析完成后，会显示session ID，例如：
```
Session saved for chat recovery:
Session ID: 12345678-abcd-ef01-2345-123456789abc
Use 'python -m cli.main restore 12345678-abcd-ef01-2345-123456789abc' to view this analysis again
Use 'python -m cli.main chat 12345678-abcd-ef01-2345-123456789abc' for interactive chat
```

### 2. 查看用户的所有会话

```bash
# 列出所有会话
python -m cli.main sessions --user-id demo_user
```

输出示例：
```
Conversation Sessions for demo_user:
┏━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Session ID ┃ Ticker ┃ Date       ┃ Status    ┃ Created             ┃
┡━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 12345678...│ SPY    │ 2025-01-15 │ completed │ 2025-01-15 10:30:15 │
│ 87654321...│ AAPL   │ 2025-01-14 │ completed │ 2025-01-14 14:20:30 │
└────────────┴────────┴────────────┴───────────┴─────────────────────┘
```

### 3. 恢复和查看历史会话

```bash
# 恢复特定会话的完整信息
python -m cli.main restore 12345678-abcd-ef01-2345-123456789abc
```

这会显示：
- 会话基本信息（ticker、日期、状态）
- 所有agent的执行状态
- 完整的分析报告
- 会话统计信息

### 4. 启动交互式Chat界面

```bash
# 基于历史会话开始聊天
python -m cli.main chat 12345678-abcd-ef01-2345-123456789abc
```

Chat界面支持的命令：
- 输入任何文本：发送消息给AI助手
- `status`：查看当前agent状态
- `reports`：查看最新报告
- `exit`：退出聊天

示例会话：
```
Chat Interface - Session 12345678...
Ticker: SPY | Date: 2025-01-15
Type 'exit' to quit, 'status' for agent status, 'reports' for latest reports

SYSTEM [10:30:15]: Analysis session started for SPY on 2025-01-15
ASSISTANT [10:32:20]: Updated market_report: ## Market Analysis...
SYSTEM [10:45:30]: Agent Market Analyst status changed to completed

You: 这个分析的主要结论是什么？
ASSISTANT: 根据SPY在2025-01-15的分析，主要结论是...

You: status
  Market Analyst: completed
  Social Analyst: completed
  News Analyst: completed
  Fundamentals Analyst: completed
  ...

You: exit
Chat session ended
```

## API 使用方法

### 1. 创建新会话

```bash
curl -X POST "http://localhost:8000/api/conversation/create" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "SPY",
    "analysis_date": "2025-01-15",
    "analysts": ["market", "news", "fundamentals"],
    "research_depth": 1,
    "user_id": "demo_user"
  }'
```

### 2. 恢复会话用于Chat

```bash
curl "http://localhost:8000/api/conversation/restore/{session_id}"
```

### 3. 获取会话状态

```bash
curl "http://localhost:8000/api/conversation/{session_id}/state"
```

### 4. 更新Agent状态

```bash
curl -X POST "http://localhost:8000/api/conversation/{session_id}/agent-status" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "Market Analyst",
    "status": "completed"
  }'
```

### 5. 更新报告内容

```bash
curl -X POST "http://localhost:8000/api/conversation/{session_id}/report" \
  -H "Content-Type: application/json" \
  -d '{
    "section_name": "market_report",
    "content": "## Market Analysis\n\nDetailed market analysis content..."
  }'
```

### 6. 添加聊天消息

```bash
curl -X POST "http://localhost:8000/api/conversation/{session_id}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "What are the key findings from this analysis?",
    "message_type": "question"
  }'
```

### 7. 获取聊天历史

```bash
curl "http://localhost:8000/api/conversation/{session_id}/chat-history?limit=50"
```

### 8. 完成会话

```bash
curl -X POST "http://localhost:8000/api/conversation/{session_id}/finalize" \
  -H "Content-Type: application/json" \
  -d '{
    "final_state": {...},
    "processed_signal": {...}
  }'
```

## 数据结构

### 会话状态 (ConversationState)

```python
{
    "session_id": "uuid-string",
    "user_id": "demo_user", 
    "ticker": "SPY",
    "analysis_date": "2025-01-15",
    "analysts": ["market", "news", "fundamentals"],
    "research_depth": 1,
    "llm_config": {...},
    "agent_status": {
        "Market Analyst": "completed",
        "News Analyst": "in_progress",
        ...
    },
    "current_agent": "News Analyst",
    "messages": [
        ("10:30:15", "System", "Analysis started"),
        ("10:32:20", "Reasoning", "Market analysis reasoning..."),
        ...
    ],
    "tool_calls": [
        ("10:31:10", "get_stock_data", {"ticker": "SPY"}),
        ...
    ],
    "report_sections": {
        "market_report": "## Market Analysis\n...",
        "news_report": "## News Analysis\n...",
        ...
    },
    "current_report": "### Market Analysis\n...",
    "final_report": "## Complete Analysis Report\n...",
    "final_state": {...},
    "processed_signal": {...},
    "created_at": "2025-01-15T10:30:15",
    "updated_at": "2025-01-15T10:45:30", 
    "status": "completed"
}
```

### 聊天消息 (ChatMessage)

```python
{
    "message_id": "uuid-string",
    "session_id": "uuid-string", 
    "timestamp": "2025-01-15T10:30:15",
    "role": "user|assistant|system|agent",
    "content": "Message content",
    "agent_name": "Market Analyst",  # optional
    "message_type": "reasoning|tool_call|report_update|status_change",  # optional
    "metadata": {...}  # optional
}
```

## 集成到现有应用

### 1. 在Backend Analysis Service中启用记忆

```python
from backend.services.analysis_runner_service import analysis_runner_service

# 使用带记忆功能的分析
result = analysis_runner_service.run_sync_analysis_with_memory(
    task_id="task_123",
    ticker="SPY",
    analysis_date="2025-01-15",
    analysts=["market", "news", "fundamentals"],
    research_depth=1,
    user_id="demo_user",
    enable_memory=True  # 启用记忆功能
)

# 获取session_id用于后续Chat
session_id = result["session_id"]
```

### 2. 恢复会话用于Chat界面

```python
from backend.services.conversation_memory_service import conversation_memory_service

# 恢复会话数据
restored_data = conversation_memory_service.restore_conversation_for_chat(session_id)

if restored_data:
    session_info = restored_data["session_info"]
    agent_status = restored_data["agent_status"]
    chat_history = restored_data["chat_history"]
    reports = restored_data["reports"]
    # 使用这些数据构建Chat界面
```

### 3. 实时更新会话状态

```python
# 更新agent状态
conversation_memory_service.update_agent_status(
    session_id, "Market Analyst", "completed"
)

# 更新报告段落
conversation_memory_service.update_report_section(
    session_id, "market_report", report_content
)

# 添加聊天消息
conversation_memory_service.add_chat_message(
    session_id=session_id,
    role="assistant",
    content="Analysis completed",
    message_type="status_update"
)
```

## 注意事项

1. **存储空间**：会话数据存储在数据库中，大型分析会话可能占用较多空间
2. **过期机制**：聊天消息默认7天过期，会话状态默认30天过期
3. **并发访问**：同一会话的并发更新是安全的
4. **错误处理**：API会返回适当的错误信息，CLI会显示友好的错误提示

## 故障排除

### 问题：会话ID找不到
```bash
python -m cli.main restore invalid-session-id
# 输出：Session invalid-session-id not found
```
**解决**：使用 `python -m cli.main sessions` 查看有效的会话ID

### 问题：API返回500错误
**检查**：
1. 数据库连接是否正常
2. 会话ID格式是否正确
3. 服务是否正在运行

### 问题：Chat界面无响应
**检查**：
1. 会话状态是否为active或completed
2. 网络连接是否正常
3. 使用Ctrl+C可以强制退出

## 扩展功能

这个长期记忆系统为以下功能提供了基础：

1. **智能Chat助手**：基于分析历史的智能对话
2. **分析对比**：比较不同时间的分析结果
3. **趋势分析**：基于历史会话数据的趋势分析
4. **用户偏好学习**：根据历史交互学习用户偏好
5. **自动报告生成**：基于模板和历史数据生成报告

## 总结

TradingAgents的长期记忆系统提供了完整的会话状态管理功能，支持：

- ✅ 完整的分析状态保存和恢复
- ✅ 基于Chat的交互式会话恢复  
- ✅ 丰富的API接口用于集成
- ✅ CLI工具用于便捷操作
- ✅ 可扩展的架构支持未来功能

通过这个系统，您可以轻松地保存、恢复和交互分析会话，为构建更智能的金融分析应用奠定基础。
