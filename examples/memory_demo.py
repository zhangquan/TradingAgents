#!/usr/bin/env python3
"""
TradingAgents 长期记忆系统演示脚本
Demo script for TradingAgents conversation memory system
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.conversation_memory_service import conversation_memory_service
from backend.services.analysis_runner_service import analysis_runner_service
import uuid


def demo_memory_system():
    """演示长期记忆系统的功能"""
    print("🧠 TradingAgents 长期记忆系统演示")
    print("=" * 50)
    
    # 1. 创建新的会话
    print("\n1. 创建新的分析会话...")
    session_id = conversation_memory_service.create_conversation_session(
        user_id="demo_user",
        ticker="AAPL",
        analysis_date="2025-01-15",
        analysts=["market", "news", "fundamentals"],
        research_depth=1,
        llm_config={
            "llm_provider": "openai",
            "backend_url": "http://localhost:11434/v1",
            "quick_think_llm": "llama3.2:3b",
            "deep_think_llm": "llama3.2:3b"
        }
    )
    print(f"✅ 创建会话成功: {session_id[:8]}...")
    
    # 2. 模拟分析过程 - 更新agent状态
    print("\n2. 模拟分析执行过程...")
    
    # 模拟市场分析师开始工作
    conversation_memory_service.update_agent_status(session_id, "Market Analyst", "in_progress")
    conversation_memory_service.add_message(session_id, "Reasoning", "开始进行AAPL的市场分析...")
    
    # 模拟工具调用
    conversation_memory_service.add_tool_call(session_id, "get_stock_data", {
        "ticker": "AAPL",
        "period": "1mo"
    })
    
    # 模拟市场分析完成
    market_report = """## 市场分析报告 - AAPL
    
**股价表现**: AAPL当前股价为$150.25，较上月上涨3.2%
**技术指标**: RSI指标显示股票处于中性区间，MACD线呈现轻微上涨趋势
**交易量**: 近期交易量保持稳定，显示投资者信心较强
**支撑位和阻力位**: 支撑位$145，阻力位$155

**总结**: AAPL技术面表现良好，短期内有继续上涨的潜力。
    """
    
    conversation_memory_service.update_report_section(session_id, "market_report", market_report)
    conversation_memory_service.update_agent_status(session_id, "Market Analyst", "completed")
    print("✅ 市场分析完成")
    
    # 模拟新闻分析师工作
    conversation_memory_service.update_agent_status(session_id, "News Analyst", "in_progress")
    conversation_memory_service.add_message(session_id, "Reasoning", "分析AAPL相关新闻...")
    
    news_report = """## 新闻分析报告 - AAPL
    
**最新消息**:
- 苹果公司宣布新一代iPhone销量超预期
- CEO库克在财报会议上对未来增长前景表示乐观
- 新的AI功能获得市场积极反响

**市场情绪**: 整体新闻情绪偏向积极，投资者对公司未来发展保持信心
**风险因素**: 供应链压力和全球经济不确定性仍需关注

**总结**: 新闻面对AAPL股价形成支撑，短期内正面消息较多。
    """
    
    conversation_memory_service.update_report_section(session_id, "news_report", news_report)
    conversation_memory_service.update_agent_status(session_id, "News Analyst", "completed")
    print("✅ 新闻分析完成")
    
    # 模拟最终决策
    final_decision = """## 投资组合管理决策
    
**综合评估**: 基于市场技术分析和新闻面分析，AAPL表现出良好的投资价值
**建议操作**: 建议适度增持AAPL股票
**目标价位**: $158
**风险控制**: 设置止损位于$142
**仓位建议**: 占投资组合的8-10%

**决策置信度**: 75%
**决策依据**: 技术面积极 + 基本面稳健 + 新闻面支撑
    """
    
    conversation_memory_service.update_report_section(session_id, "final_trade_decision", final_decision)
    conversation_memory_service.update_agent_status(session_id, "Portfolio Manager", "completed")
    print("✅ 投资决策完成")
    
    # 3. 完成会话
    print("\n3. 完成分析会话...")
    final_state = {
        "market_report": market_report,
        "news_report": news_report,
        "final_trade_decision": final_decision,
        "ticker": "AAPL",
        "analysis_date": "2025-01-15"
    }
    
    processed_signal = {
        "action": "BUY",
        "confidence": 0.75,
        "target_price": 158.0,
        "stop_loss": 142.0
    }
    
    conversation_memory_service.finalize_conversation(session_id, final_state, processed_signal)
    print("✅ 会话已完成并保存")
    
    # 4. 演示会话恢复
    print("\n4. 演示会话恢复功能...")
    restored_data = conversation_memory_service.restore_conversation_for_chat(session_id)
    
    if restored_data:
        session_info = restored_data["session_info"]
        print(f"✅ 会话恢复成功:")
        print(f"   - 股票代码: {session_info['ticker']}")
        print(f"   - 分析日期: {session_info['analysis_date']}")
        print(f"   - 状态: {session_info['status']}")
        
        agent_status = restored_data["agent_status"]
        completed_agents = [name for name, status in agent_status.items() if status == "completed"]
        print(f"   - 已完成的Agent: {len(completed_agents)}个")
        
        statistics = restored_data["statistics"]
        print(f"   - 总消息数: {statistics['total_messages']}")
        print(f"   - 工具调用数: {statistics['total_tool_calls']}")
        print(f"   - 完成报告数: {statistics['completed_reports']}")
        
        # 显示部分最终报告
        final_report = restored_data["reports"].get("final_report")
        if final_report:
            print(f"\n📊 最终分析报告预览:")
            print("-" * 40)
            # 只显示前200个字符
            preview = final_report[:200] + "..." if len(final_report) > 200 else final_report
            print(preview)
            print("-" * 40)
    
    # 5. 演示聊天历史
    print("\n5. 演示聊天历史...")
    chat_history = conversation_memory_service.get_chat_history(session_id, limit=5)
    
    if chat_history:
        print("💬 最近的聊天消息:")
        for msg in chat_history[-3:]:  # 显示最后3条消息
            role_emoji = {
                "user": "👤",
                "assistant": "🤖", 
                "system": "⚙️",
                "agent": "🧠"
            }.get(msg.role, "📝")
            
            content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            print(f"   {role_emoji} {msg.role.upper()}: {content_preview}")
    
    # 6. 演示API功能预览
    print("\n6. API访问信息:")
    print(f"🌐 恢复会话API: GET /api/conversation/restore/{session_id}")
    print(f"🌐 获取状态API: GET /api/conversation/{session_id}/state")
    print(f"🌐 聊天历史API: GET /api/conversation/{session_id}/chat-history")
    
    print(f"\n🎉 演示完成! 会话ID: {session_id}")
    print(f"💡 您可以使用以下命令继续探索:")
    print(f"   python -m cli.main restore {session_id}")
    print(f"   python -m cli.main chat {session_id}")
    
    return session_id


def demo_multiple_sessions():
    """演示多会话管理"""
    print("\n" + "=" * 50)
    print("🔄 演示多会话管理")
    print("=" * 50)
    
    # 创建多个不同的会话
    tickers = ["SPY", "QQQ", "TSLA"]
    session_ids = []
    
    for ticker in tickers:
        print(f"\n创建 {ticker} 分析会话...")
        session_id = conversation_memory_service.create_conversation_session(
            user_id="demo_user",
            ticker=ticker,
            analysis_date="2025-01-15",
            analysts=["market", "news"],
            research_depth=1
        )
        session_ids.append(session_id)
        
        # 快速模拟一些基本状态
        conversation_memory_service.update_agent_status(session_id, "Market Analyst", "completed")
        conversation_memory_service.update_report_section(
            session_id, 
            "market_report", 
            f"## {ticker} 市场分析\n\n基本的市场分析内容..."
        )
        print(f"✅ {ticker} 会话创建完成: {session_id[:8]}...")
    
    print(f"\n📈 成功创建 {len(session_ids)} 个会话")
    print("💡 您可以使用 'python -m cli.main sessions' 查看所有会话")
    
    return session_ids


if __name__ == "__main__":
    try:
        print("开始TradingAgents长期记忆系统演示...\n")
        
        # 演示单个详细会话
        main_session_id = demo_memory_system()
        
        # 演示多会话管理
        multiple_sessions = demo_multiple_sessions()
        
        print(f"\n🎯 演示总结:")
        print(f"   - 主要演示会话: {main_session_id[:8]}...")
        print(f"   - 额外创建会话: {len(multiple_sessions)}个")
        print(f"   - 总计会话数: {len(multiple_sessions) + 1}个")
        
        print(f"\n🚀 下一步可以尝试:")
        print(f"   1. 启动API服务器: python backend/main.py")
        print(f"   2. 使用CLI恢复会话: python -m cli.main restore {main_session_id}")
        print(f"   3. 尝试Chat界面: python -m cli.main chat {main_session_id}")
        print(f"   4. 查看API文档: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
