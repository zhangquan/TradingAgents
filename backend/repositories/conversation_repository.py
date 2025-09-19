"""
Conversation Repository - 对话相关数据访问
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from .base import BaseRepository
from ..database.models import ConversationState, ChatMessage

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository[ConversationState]):
    """对话状态数据访问Repository"""
    
    def __init__(self, session_factory=None):
        super().__init__(ConversationState)
    
    def save_conversation_state(self, session_id: str, user_id: str, ticker: str, 
                               state_data: Dict[str, Any]) -> bool:
        """保存或更新对话状态"""
        try:
            with self._get_session() as db:
                # 检查对话状态是否已存在
                existing_state = db.query(ConversationState).filter(
                    ConversationState.session_id == session_id
                ).first()
                
                if existing_state:
                    # 更新现有状态
                    for key, value in state_data.items():
                        if hasattr(existing_state, key):
                            # 处理可能是字符串的datetime字段
                            if key in ["last_interaction", "created_at", "updated_at"] and isinstance(value, str):
                                try:
                                    setattr(existing_state, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                                except ValueError:
                                    continue
                            elif key in ["created_at", "updated_at"] and value is None:
                                continue
                            else:
                                setattr(existing_state, key, value)
                    
                    existing_state.updated_at = datetime.now()
                    db.commit()
                    logger.info(f"Updated conversation state: {session_id}")
                    return True
                else:
                    # 创建新对话状态
                    conversation_state = ConversationState(
                        session_id=session_id,
                        user_id=user_id,
                        ticker=ticker.upper(),
                        analysis_date=state_data.get("analysis_date"),
                        task_id=state_data.get("task_id"),
                        analysis_id=state_data.get("analysis_id"),
                        analysts=state_data.get("analysts", []),
                        research_depth=state_data.get("research_depth", 1),
                        llm_config=state_data.get("llm_config", {}),
                        agent_status=state_data.get("agent_status", {}),
                        current_agent=state_data.get("current_agent"),
                        messages=state_data.get("messages", []),
                        tool_calls=state_data.get("tool_calls", []),
                        report_sections=state_data.get("report_sections", {}),
                        current_report=state_data.get("current_report"),
                        final_report=state_data.get("final_report"),
                        final_state=state_data.get("final_state"),
                        processed_signal=state_data.get("processed_signal"),
                        execution_type=state_data.get("execution_type", "manual"),
                        last_interaction=datetime.now(),
                        is_finalized=state_data.get("is_finalized", False)
                    )
                    
                    db.add(conversation_state)
                    db.commit()
                    db.refresh(conversation_state)
                    
                    logger.info(f"Created conversation state: {session_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving conversation state {session_id}: {e}")
            return False
    
    def get_conversation_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """根据session ID获取对话状态"""
        try:
            with self._get_session() as db:
                state = db.query(ConversationState).filter(
                    ConversationState.session_id == session_id
                ).first()
                
                if not state:
                    return None
                
                return self._to_dict(state)
        except Exception as e:
            logger.error(f"Error getting conversation state {session_id}: {e}")
            return None
    
    def list_conversation_states(self, user_id: str, ticker: str = None, 
                                finalized_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """列出用户的对话状态"""
        try:
            with self._get_session() as db:
                query = db.query(ConversationState).filter(ConversationState.user_id == user_id)
                
                if ticker:
                    query = query.filter(ConversationState.ticker == ticker.upper())
                if finalized_only:
                    query = query.filter(ConversationState.is_finalized == True)
                
                states = query.order_by(desc(ConversationState.last_interaction)).limit(limit).all()
                
                return [self._to_dict_summary(state) for state in states]
        except Exception as e:
            logger.error(f"Error listing conversation states for user {user_id}: {e}")
            return []
    
    def finalize_conversation_state(self, session_id: str) -> bool:
        """标记对话状态为已完成"""
        try:
            with self._get_session() as db:
                state = db.query(ConversationState).filter(
                    ConversationState.session_id == session_id
                ).first()
                
                if state:
                    state.is_finalized = True
                    state.last_interaction = datetime.now()
                    db.commit()
                    
                    logger.info(f"Finalized conversation state: {session_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error finalizing conversation state {session_id}: {e}")
            return False
    
    def update_conversation_state(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """更新对话状态"""
        try:
            with self._get_session() as db:
                state = db.query(ConversationState).filter(
                    ConversationState.session_id == session_id
                ).first()
                
                if not state:
                    return False
                
                # 更新字段
                for key, value in updates.items():
                    if hasattr(state, key):
                        if key in ["last_interaction"] and isinstance(value, str):
                            try:
                                setattr(state, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                            except ValueError:
                                continue
                        else:
                            setattr(state, key, value)
                
                state.updated_at = datetime.now()
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating conversation state {session_id}: {e}")
            return False
    
    def delete_conversation_state(self, session_id: str) -> bool:
        """删除对话状态"""
        try:
            with self._get_session() as db:
                state = db.query(ConversationState).filter(
                    ConversationState.session_id == session_id
                ).first()
                
                if state:
                    db.delete(state)
                    db.commit()
                    
                    logger.info(f"Deleted conversation state: {session_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting conversation state {session_id}: {e}")
            return False
    
    def _to_dict(self, state: ConversationState) -> Dict[str, Any]:
        """将ConversationState模型转换为字典"""
        return {
            "session_id": state.session_id,
            "user_id": state.user_id,
            "ticker": state.ticker,
            "analysis_date": state.analysis_date,
            "task_id": state.task_id,
            "analysis_id": state.analysis_id,
            "analysts": state.analysts,
            "research_depth": state.research_depth,
            "llm_config": state.llm_config,
            "agent_status": state.agent_status,
            "current_agent": state.current_agent,
            "messages": state.messages,
            "tool_calls": state.tool_calls,
            "report_sections": state.report_sections,
            "current_report": state.current_report,
            "final_report": state.final_report,
            "final_state": state.final_state,
            "processed_signal": state.processed_signal,
            "execution_type": state.execution_type,
            "last_interaction": state.last_interaction.isoformat() if state.last_interaction else None,
            "is_finalized": state.is_finalized,
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None
        }
    
    def _to_dict_summary(self, state: ConversationState) -> Dict[str, Any]:
        """将ConversationState模型转换为摘要字典（用于列表）"""
        return {
            "session_id": state.session_id,
            "user_id": state.user_id,
            "ticker": state.ticker,
            "analysis_date": state.analysis_date,
            "task_id": state.task_id,
            "analysis_id": state.analysis_id,
            "current_agent": state.current_agent,
            "is_finalized": state.is_finalized,
            "execution_type": state.execution_type,
            "agent_status": state.agent_status if state.agent_status else {},
            "last_interaction": state.last_interaction.isoformat() if state.last_interaction else None,
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None
        }


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """聊天消息数据访问Repository"""
    
    def __init__(self, session_factory=None):
        super().__init__(ChatMessage)
    
    def save_chat_message(self, session_id: str, user_id: str, message_data: Dict[str, Any]) -> str:
        """保存聊天消息"""
        try:
            with self._get_session() as db:
                message_id = message_data.get("message_id") or f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                
                chat_message = ChatMessage(
                    message_id=message_id,
                    session_id=session_id,
                    user_id=user_id,
                    role=message_data["role"],
                    content=message_data["content"],
                    message_type=message_data.get("message_type", "text"),
                    message_metadata=message_data.get("metadata", {})
                )
                
                db.add(chat_message)
                db.commit()
                db.refresh(chat_message)
                
                logger.info(f"Saved chat message: {message_id}")
                return message_id
                
        except Exception as e:
            logger.error(f"Error saving chat message for session {session_id}: {e}")
            raise
    
    def get_chat_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取会话的聊天消息"""
        try:
            with self._get_session() as db:
                messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(ChatMessage.created_at).limit(limit).all()
                
                return [self._to_dict(msg) for msg in messages]
        except Exception as e:
            logger.error(f"Error getting chat messages for session {session_id}: {e}")
            return []
    
    def delete_chat_messages_by_session(self, session_id: str) -> bool:
        """删除会话的所有聊天消息"""
        try:
            with self._get_session() as db:
                db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
                db.commit()
                logger.info(f"Deleted chat messages for session: {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting chat messages for session {session_id}: {e}")
            return False
    
    def _to_dict(self, message: ChatMessage) -> Dict[str, Any]:
        """将ChatMessage模型转换为字典"""
        return {
            "message_id": message.message_id,
            "session_id": message.session_id,
            "user_id": message.user_id,
            "role": message.role,
            "content": message.content,
            "message_type": message.message_type,
            "metadata": message.message_metadata,
            "created_at": message.created_at.isoformat() if message.created_at else None
        }
