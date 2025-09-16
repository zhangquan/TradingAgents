# TradingAgents 长期记忆系统

## 🧠 概述

TradingAgents 现在支持完整的长期记忆系统，能够保存和恢复 trading_graph agent 的执行状态，实现基于chat的会话恢复功能。

## ✨ 主要特性

### 🔄 会话状态管理
- **完整状态保存**: 保存所有Agent的执行状态、消息历史、工具调用和报告内容
- **实时状态更新**: 在分析过程中实时更新和同步状态
- **会话恢复**: 完整恢复历史分析会话的所有信息

### 💬 Chat-based 交互
- **交互式聊天**: 基于历史会话进行智能对话
- **状态查询**: 实时查看Agent执行状态和分析进度
- **报告访问**: 快速查看和讨论分析报告内容

### 🔌 API 集成
- **RESTful API**: 完整的API接口支持外部系统集成
- **实时更新**: 支持实时状态和报告更新
- **会话管理**: 创建、查询、更新和归档会话

## 🚀 快速开始

### 1. 运行演示脚本

```bash
# 运行完整的功能演示
python examples/memory_demo.py
```

这会创建示例会话并演示所有核心功能。

### 2. 使用CLI进行分析

```bash
# 运行新的分析（会自动启用记忆功能）
python -m cli.main analyze

# 分析完成后会显示session ID，例如：
# Session ID: 12345678-abcd-ef01-2345-123456789abc
```

### 3. 恢复和查看历史会话

```bash
# 查看所有会话
python -m cli.main sessions

# 恢复特定会话
python -m cli.main restore 12345678-abcd-ef01-2345-123456789abc

# 启动Chat界面
python -m cli.main chat 12345678-abcd-ef01-2345-123456789abc
```

### 4. 启动API服务器

```bash
# 启动后端API服务
python backend/main.py

# 访问API文档
# http://localhost:8000/docs
```

## 📁 新增文件结构

```
TradingAgents/
├── backend/
│   ├── services/
│   │   └── conversation_memory_service.py    # 🆕 核心记忆服务
│   └── routers/
│       └── conversation_memory.py            # 🆕 记忆API路由
├── examples/
│   └── memory_demo.py                        # 🆕 功能演示脚本
├── CONVERSATION_MEMORY_USAGE.md              # 🆕 详细使用指南
└── README_MEMORY_SYSTEM.md                   # 🆕 本文件
```

## 🔧 核心组件

### ConversationMemoryService
长期记忆的核心服务，提供：
- 会话创建和管理
- 状态实时更新和同步
- Chat消息历史管理
- 会话数据的完整恢复

### AnalysisRunnerService (增强版)
增加了记忆功能的分析运行服务：
- `run_sync_analysis_with_memory()`: 带记忆功能的分析执行
- 实时状态追踪和保存
- 与原有分析流程无缝集成

### ConversationMemoryAPI
提供完整的REST API接口：
- `/api/conversation/create`: 创建新会话
- `/api/conversation/restore/{session_id}`: 恢复会话
- `/api/conversation/{session_id}/state`: 获取会话状态
- `/api/conversation/{session_id}/message`: 添加聊天消息
- 更多API详见使用指南

## 💾 数据存储

### 会话状态 (ConversationState)
```python
{
    "session_id": "uuid",
    "ticker": "AAPL", 
    "analysis_date": "2025-01-15",
    "agent_status": {...},      # Agent执行状态
    "messages": [...],          # 消息历史
    "tool_calls": [...],        # 工具调用历史
    "report_sections": {...},   # 报告段落
    "final_state": {...},       # 最终状态
    "status": "completed"       # 会话状态
}
```

### 聊天消息 (ChatMessage)
```python
{
    "message_id": "uuid",
    "session_id": "uuid",
    "role": "user|assistant|system|agent",
    "content": "消息内容",
    "timestamp": "2025-01-15T10:30:15",
    "message_type": "reasoning|tool_call|report_update"
}
```

## 🎯 使用场景

### 1. 分析师工作流
- 运行分析 → 保存会话 → 后续讨论和修改
- 团队协作时共享分析会话ID
- 基于历史分析进行对比和趋势分析

### 2. 客户服务
- 为客户保存分析历史
- 基于历史数据提供个性化建议
- 客户可以随时回顾分析过程

### 3. 系统集成
- 通过API集成到现有交易系统
- 实时监控分析进度
- 自动化报告生成和分发

## 📊 性能优化

### 内存管理
- 消息历史限制在合理范围内
- 大型报告内容压缩存储
- 定期清理过期会话数据

### 数据库优化
- 索引优化提高查询速度
- 分片存储大量历史数据
- 缓存常用会话状态

## 🔐 安全考虑

### 数据保护
- 会话数据加密存储
- 用户权限控制
- API访问限流和认证

### 隐私保护
- 敏感信息脱敏
- 数据保留期限控制
- 用户数据删除权限

## 🚧 未来功能规划

### 智能化增强
- [ ] 基于历史数据的智能建议
- [ ] 分析模式学习和优化
- [ ] 自动异常检测和告警

### 扩展功能
- [ ] 多用户协作功能
- [ ] 实时流式分析状态推送
- [ ] 分析报告模板系统
- [ ] 与外部数据源的集成

### 性能优化
- [ ] 分布式会话存储
- [ ] 实时数据同步优化
- [ ] 大规模用户支持

## 📚 参考文档

- [详细使用指南](CONVERSATION_MEMORY_USAGE.md) - 完整的API和CLI使用说明
- [功能演示脚本](examples/memory_demo.py) - 可运行的功能演示
- [API文档](http://localhost:8000/docs) - 在线API文档 (需启动服务)

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个长期记忆系统！

---

**TradingAgents Team** - 让金融分析更智能，让决策更有依据
