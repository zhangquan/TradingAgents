"""
Conversation Memory Service - 长期记忆系统用于保持trading_graph agent输出和会话状态
支持基于chat的会话恢复功能
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque

from backend.repositories import (
    ConversationRepository, ChatMessageRepository
)

logger = logging.getLogger(__name__)


def make_json_serializable(obj):
    """递归地将对象转换为JSON可序列化的格式"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, 'content') and hasattr(obj, 'type'):
        # Handle LangChain message objects
        return {
            'type': getattr(obj, 'type', str(type(obj).__name__)),
            'content': str(obj.content),
            'additional_kwargs': make_json_serializable(getattr(obj, 'additional_kwargs', {})),
            'response_metadata': make_json_serializable(getattr(obj, 'response_metadata', {})),
            'id': getattr(obj, 'id', None)
        }
    elif hasattr(obj, '__dict__'):
        # Handle other objects with __dict__
        return {k: make_json_serializable(v) for k, v in obj.__dict__.items()}
    else:
        # Convert unknown objects to string
        return str(obj)


@dataclass
class ConversationState:
    """完整的会话状态数据结构"""
    session_id: str
    user_id: str
    ticker: str
    analysis_date: str
    
    # 分析配置
    analysts: List[str]
    research_depth: int
    llm_config: Dict[str, Any]
    
    # Agent状态追踪
    agent_status: Dict[str, str]
    current_agent: Optional[str]
    
    # 消息和工具调用历史
    messages: List[Tuple[str, str, str]]  # (timestamp, type, content)
    tool_calls: List[Tuple[str, str, Dict[str, Any]]]  # (timestamp, tool_name, args)
    
    # 报告段落
    report_sections: Dict[str, Optional[str]]
    current_report: Optional[str]
    final_report: Optional[str]
    
    # 完整的trading graph状态
    final_state: Optional[Dict[str, Any]]
    processed_signal: Optional[Any]
    
    # 新增字段以匹配数据库模型
    task_id: Optional[str] = None
    execution_type: str = "manual"  # manual, scheduled
    last_interaction: Optional[str] = None
    is_finalized: bool = False
    
    # 元数据
    created_at: str = ""
    updated_at: str = ""


@dataclass
class ChatMessageData:
    """聊天消息数据结构"""
    message_id: str
    session_id: str
    timestamp: str
    role: str  # user, assistant, system, agent
    content: str
    agent_name: Optional[str] = None
    message_type: Optional[str] = None  # reasoning, tool_call, report_update, status_change
    metadata: Optional[Dict[str, Any]] = None


class ConversationMemoryService:
    """
    会话记忆服务 - 管理trading agents的长期记忆和会话状态
    
    主要功能：
    1. 保存和恢复完整的分析会话状态
    2. 实时追踪agent执行进度
    3. 存储消息历史和工具调用记录
    4. 支持基于chat的会话恢复
    """
    
    def __init__(self):
        self.conversation_repo = ConversationRepository()
        self.chat_message_repo = ChatMessageRepository()
    
    def create_conversation_session(self, 
                                  user_id: str,
                                  ticker: str,
                                  analysis_date: str,
                                  analysts: List[str],
                                  research_depth: int = 1,
                                  llm_config: Dict[str, Any] = None,
                                  execution_type: str = "manual") -> str:
        """创建新的会话session"""
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # 初始化agent状态
        agent_status = {
            # Analyst Team
            "Market Analyst": "pending",
            "Social Analyst": "pending", 
            "News Analyst": "pending",
            "Fundamentals Analyst": "pending",
            # Research Team
            "Bull Researcher": "pending",
            "Bear Researcher": "pending",
            "Research Manager": "pending",
            # Trading Team
            "Trader": "pending",
            # Risk Management Team
            "Risky Analyst": "pending",
            "Neutral Analyst": "pending",
            "Safe Analyst": "pending",
            # Portfolio Management Team
            "Portfolio Manager": "pending",
        }
        
        # 初始化报告段落
        report_sections = {
            "market_report": None,
            "sentiment_report": None,
            "news_report": None,
            "fundamentals_report": None,
            "investment_plan": None,
            "trader_investment_plan": None,
            "final_trade_decision": None,
        }
        
        # 创建会话状态
        conversation_state = ConversationState(
            session_id=session_id,
            user_id=user_id,
            ticker=ticker,
            analysis_date=analysis_date,
            analysts=analysts,
            research_depth=research_depth,
            llm_config=llm_config or {},
            agent_status=agent_status,
            current_agent=None,
            messages=[],
            tool_calls=[],
            report_sections=report_sections,
            current_report=None,
            final_report=None,
            final_state=None,
            processed_signal=None,
            execution_type=execution_type,
            created_at=timestamp,
            updated_at=timestamp
        )
        
        # 保存到数据库
        self._save_conversation_state(conversation_state)
        
        # 记录初始化消息
        self.add_chat_message(
            session_id=session_id,
            role="system",
            content=f"Analysis session started for {ticker} on {analysis_date}",
            message_type="session_start"
        )
        
        logger.info(f"Created conversation session {session_id} for user {user_id}")
        return session_id
    
    def get_conversation_state(self, session_id: str) -> Optional[ConversationState]:
        """获取会话状态"""
        try:
            # 从数据库读取会话状态
            state_data = self.conversation_repo.get_conversation_state(session_id)
            if state_data:
                return ConversationState(**state_data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving conversation state {session_id}: {e}")
            return None
    
    def update_conversation_state(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """更新会话状态"""
        try:
            state = self.get_conversation_state(session_id)
            if not state:
                logger.warning(f"Conversation state {session_id} not found")
                return False
            
            # 更新状态字段
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            
            state.updated_at = datetime.now().isoformat()
            
            # 保存更新后的状态
            self._save_conversation_state(state)
            return True
            
        except Exception as e:
            logger.error(f"Error updating conversation state {session_id}: {e}")
            return False
    
    def update_agent_status(self, session_id: str, agent_name: str, status: str) -> bool:
        """更新agent状态"""
        try:
            state = self.get_conversation_state(session_id)
            if not state:
                return False
            
            state.agent_status[agent_name] = status
            state.current_agent = agent_name
            state.updated_at = datetime.now().isoformat()
            
            self._save_conversation_state(state)
            
            # 记录状态变化消息
            self.add_chat_message(
                session_id=session_id,
                role="system",
                content=f"Agent {agent_name} status changed to {status}",
                message_type="status_change",
                metadata={"agent": agent_name, "status": status}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent status for session {session_id}: {e}")
            return False
    
    def update_report_section(self, session_id: str, section_name: str, content: str) -> bool:
        """更新报告段落"""
        try:
            state = self.get_conversation_state(session_id)
            if not state:
                return False
            
            state.report_sections[section_name] = content
            state.updated_at = datetime.now().isoformat()
            
            # 更新当前报告显示
            self._update_current_report(state)
            
            self._save_conversation_state(state)
            
            # 记录报告更新消息
            self.add_chat_message(
                session_id=session_id,
                role="assistant",
                content=f"Updated {section_name}: {content[:200]}...",
                message_type="report_update",
                metadata={"section": section_name, "content_length": len(content)}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating report section for session {session_id}: {e}")
            return False
    
    def _update_current_report(self, state: ConversationState):
        """更新当前报告显示（模拟CLI的逻辑）"""
        # 找到最近更新的段落
        latest_section = None
        latest_content = None
        
        for section, content in state.report_sections.items():
            if content is not None:
                latest_section = section
                latest_content = content
        
        if latest_section and latest_content:
            section_titles = {
                "market_report": "Market Analysis",
                "sentiment_report": "Social Sentiment", 
                "news_report": "News Analysis",
                "fundamentals_report": "Fundamentals Analysis",
                "investment_plan": "Research Team Decision",
                "trader_investment_plan": "Trading Team Plan",
                "final_trade_decision": "Portfolio Management Decision",
            }
            state.current_report = f"### {section_titles[latest_section]}\n{latest_content}"
        
        # 更新完整报告
        self._update_final_report(state)
    
    def _update_final_report(self, state: ConversationState):
        """更新完整的最终报告"""
        report_parts = []
        
        # Analyst Team Reports
        if any(state.report_sections[section] for section in 
               ["market_report", "sentiment_report", "news_report", "fundamentals_report"]):
            report_parts.append("## Analyst Team Reports")
            if state.report_sections["market_report"]:
                report_parts.append(f"### Market Analysis\n{state.report_sections['market_report']}")
            if state.report_sections["sentiment_report"]:
                report_parts.append(f"### Social Sentiment\n{state.report_sections['sentiment_report']}")
            if state.report_sections["news_report"]:
                report_parts.append(f"### News Analysis\n{state.report_sections['news_report']}")
            if state.report_sections["fundamentals_report"]:
                report_parts.append(f"### Fundamentals Analysis\n{state.report_sections['fundamentals_report']}")
        
        # Research Team Reports
        if state.report_sections["investment_plan"]:
            report_parts.append("## Research Team Decision")
            report_parts.append(f"{state.report_sections['investment_plan']}")
        
        # Trading Team Reports
        if state.report_sections["trader_investment_plan"]:
            report_parts.append("## Trading Team Plan")
            report_parts.append(f"{state.report_sections['trader_investment_plan']}")
        
        # Portfolio Management Decision
        if state.report_sections["final_trade_decision"]:
            report_parts.append("## Portfolio Management Decision")
            report_parts.append(f"{state.report_sections['final_trade_decision']}")
        
        state.final_report = "\n\n".join(report_parts) if report_parts else None
    
    def add_message(self, session_id: str, message_type: str, content: str) -> bool:
        """添加消息到会话历史"""
        try:
            state = self.get_conversation_state(session_id)
            if not state:
                return False
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            state.messages.append((timestamp, message_type, content))
            state.updated_at = datetime.now().isoformat()
            
            self._save_conversation_state(state)
            return True
            
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False
    
    def add_tool_call(self, session_id: str, tool_name: str, args: Dict[str, Any]) -> bool:
        """添加工具调用到会话历史"""
        try:
            state = self.get_conversation_state(session_id)
            if not state:
                return False
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            state.tool_calls.append((timestamp, tool_name, args))
            state.updated_at = datetime.now().isoformat()
            
            self._save_conversation_state(state)
            
            # 记录工具调用消息
            self.add_chat_message(
                session_id=session_id,
                role="assistant",
                content=f"Tool call: {tool_name}",
                message_type="tool_call",
                metadata={"tool_name": tool_name, "args": args}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding tool call to session {session_id}: {e}")
            return False
    
    def add_chat_message(self, 
                        session_id: str,
                        role: str,
                        content: str,
                        agent_name: Optional[str] = None,
                        message_type: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加聊天消息"""
        try:
            message_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            chat_message = ChatMessageData(
                message_id=message_id,
                session_id=session_id,
                timestamp=timestamp,
                role=role,
                content=content,
                agent_name=agent_name,
                message_type=message_type,
                metadata=metadata
            )
            
            # 获取会话状态以获取user_id
            state = self.get_conversation_state(session_id)
            if not state:
                raise Exception(f"Session {session_id} not found")
            
            # 保存到数据库 - 使用专门的聊天消息存储
            saved_message_id = self.chat_message_repo.save_chat_message(
                session_id=session_id,
                user_id=state.user_id,
                message_data=asdict(chat_message)
            )
            
            # 同时将消息添加到会话状态的消息历史中
            if message_type in ["reasoning", "tool_call", "report_update"]:
                self.add_message(session_id, role, content)
            
            return message_id
            
        except Exception as e:
            logger.error(f"Error adding chat message to session {session_id}: {e}")
            return ""
    
    def get_chat_history(self, session_id: str, limit: int = 100) -> List[ChatMessageData]:
        """获取聊天历史"""
        try:
            # 这里简化实现，实际应该从专门的消息表查询
            state = self.get_conversation_state(session_id)
            if not state:
                return []
            
            # 从会话状态重建聊天历史
            chat_messages = []
            
            # 添加系统消息
            for timestamp, msg_type, content in state.messages[-limit:]:
                chat_messages.append(ChatMessageData(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    timestamp=timestamp,
                    role="assistant" if msg_type == "Reasoning" else "system",
                    content=content,
                    message_type=msg_type.lower()
                ))
            
            return chat_messages
            
        except Exception as e:
            logger.error(f"Error retrieving chat history for session {session_id}: {e}")
            return []
    
    def finalize_conversation(self, session_id: str, final_state: Dict[str, Any], processed_signal: Any) -> bool:
        """完成会话并保存最终状态"""
        try:
            updates = {
                "final_state": final_state,
                "processed_signal": processed_signal
            }
            
            # 确保所有agent状态都标记为完成
            state = self.get_conversation_state(session_id)
            if state:
                for agent in state.agent_status:
                    state.agent_status[agent] = "completed"
                updates["agent_status"] = state.agent_status
            
            result = self.update_conversation_state(session_id, updates)
            
            if result:
                # 记录完成消息
                self.add_chat_message(
                    session_id=session_id,
                    role="system",
                    content="Analysis completed successfully",
                    message_type="session_complete"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error finalizing conversation {session_id}: {e}")
            return False
    
    def _save_conversation_state(self, state: ConversationState):
        """保存会话状态到数据库"""
        try:
            state_dict = asdict(state)
            
            # 处理JSON序列化 - 确保所有字段都是JSON可序列化的
            state_dict = make_json_serializable(state_dict)
            
            # 处理datetime字段 - 从字符串转换为datetime对象或确保正确格式
            now = datetime.now()
            if isinstance(state_dict.get('created_at'), str):
                # 如果是空字符串，使用当前时间
                if not state_dict['created_at']:
                    state_dict['created_at'] = now
                else:
                    try:
                        state_dict['created_at'] = datetime.fromisoformat(state_dict['created_at'].replace('Z', '+00:00'))
                    except ValueError:
                        state_dict['created_at'] = now
            
            if isinstance(state_dict.get('updated_at'), str):
                if not state_dict['updated_at']:
                    state_dict['updated_at'] = now
                else:
                    try:
                        state_dict['updated_at'] = datetime.fromisoformat(state_dict['updated_at'].replace('Z', '+00:00'))
                    except ValueError:
                        state_dict['updated_at'] = now
            
            # 总是更新updated_at为当前时间
            state_dict['updated_at'] = now
            
            success = self.conversation_repo.save_conversation_state(
                session_id=state.session_id,
                user_id=state.user_id,
                ticker=state.ticker,
                state_data=state_dict
            )
            if not success:
                raise Exception(f"Failed to save conversation state {state.session_id}")
        except Exception as e:
            logger.error(f"Error saving conversation state {state.session_id}: {e}")
            raise
    
    def list_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """列出用户的会话历史"""
        try:
            return self.conversation_repo.list_conversation_states(user_id=user_id, limit=limit)
        except Exception as e:
            logger.error(f"Error listing conversations for user {user_id}: {e}")
            return []
    
    def get_conversations_by_stock_and_user(self, user_id: str, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """根据股票代码和用户ID获取对话列表"""
        try:
            return self.conversation_repo.get_conversations_by_stock_and_user(
                user_id=user_id, 
                ticker=ticker, 
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id} and ticker {ticker}: {e}")
            return []
    
    def get_newest_conversation_by_stock(self, user_id: str, ticker: str) -> Optional[Dict[str, Any]]:
        """根据股票代码和用户ID获取最新的对话"""
        try:
            return self.conversation_repo.get_newest_conversation_by_stock(
                user_id=user_id,
                ticker=ticker
            )
        except Exception as e:
            logger.error(f"Error getting newest conversation for user {user_id} and ticker {ticker}: {e}")
            return None
    
    def restore_conversation_for_chat(self, session_id: str) -> Optional[Dict[str, Any]]:
        """为chat界面恢复会话状态"""
        try:
            state = self.get_conversation_state(session_id)
            if not state:
                return None
            
            # 获取聊天历史
            chat_history = self.get_chat_history(session_id)
            
            return {
                "session_info": {
                    "session_id": state.session_id,
                    "ticker": state.ticker,
                    "analysis_date": state.analysis_date,
                    "execution_type": state.execution_type,
                    "created_at": state.created_at,
                    "updated_at": state.updated_at
                },
                "analysis_config": {
                    "analysts": state.analysts,
                    "research_depth": state.research_depth,
                    "llm_config": state.llm_config
                },
                "agent_status": state.agent_status,
                "current_agent": state.current_agent,
                "reports": {
                    "sections": state.report_sections,
                    "current_report": state.current_report,
                    "final_report": state.final_report
                },
                "final_results": {
                    "final_state": state.final_state,
                    "processed_signal": state.processed_signal
                },
                "chat_history": [asdict(msg) for msg in chat_history],
                "statistics": {
                    "total_messages": len(state.messages),
                    "total_tool_calls": len(state.tool_calls),
                    "completed_reports": len([r for r in state.report_sections.values() if r])
                }
            }
            
        except Exception as e:
            logger.error(f"Error restoring conversation for chat {session_id}: {e}")
            return None

    def get_chat_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取会话的聊天消息"""
        try:
            return self.chat_message_repo.get_chat_messages(session_id=session_id, limit=limit)
        except Exception as e:
            logger.error(f"Error getting chat messages for session {session_id}: {e}")
            return []


# 全局服务实例
conversation_memory_service = ConversationMemoryService()
