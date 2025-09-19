"""
Conversation Memory API Router - API接口用于会话记忆管理和chat恢复
提供基于chat的会话状态保存、恢复和管理功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from backend.services.conversation_memory_service import conversation_memory_service, ConversationState
from backend.services.analysis_runner_service import analysis_runner_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversation", tags=["conversation-memory"])


class CreateConversationRequest(BaseModel):
    """创建会话请求"""
    ticker: str = Field(..., description="股票代码")
    analysis_date: str = Field(..., description="分析日期 (YYYY-MM-DD)")
    analysts: List[str] = Field(..., description="分析师列表")
    research_depth: int = Field(1, description="研究深度")
    user_id: str = Field("demo_user", description="用户ID")


class RestoreConversationResponse(BaseModel):
    """恢复会话响应"""
    session_info: Dict[str, Any]
    analysis_config: Dict[str, Any]
    agent_status: Dict[str, str]
    current_agent: Optional[str]
    reports: Dict[str, Any]
    final_results: Dict[str, Any]
    chat_history: List[Dict[str, Any]]
    statistics: Dict[str, int]


class ConversationListItem(BaseModel):
    """会话列表项"""
    session_id: str
    ticker: str
    analysis_date: str
    agent_status: Dict[str, str]
    is_finalized: bool
    created_at: str
    updated_at: str


class ConversationDetail(BaseModel):
    """会话详细信息"""
    session_id: str
    user_id: str
    ticker: str
    analysis_date: str
    task_id: Optional[str]
    analysts: List[str]
    research_depth: int
    llm_config: Dict[str, Any]
    agent_status: Dict[str, str]
    current_agent: Optional[str]
    messages: List[Any]
    tool_calls: List[Any]
    report_sections: Dict[str, Any]
    current_report: Optional[str]
    final_report: Optional[str]
    final_state: Optional[Dict[str, Any]]
    processed_signal: Optional[Any]
    execution_type: str
    last_interaction: Optional[str]
    is_finalized: bool
    created_at: str
    updated_at: str


class UpdateAgentStatusRequest(BaseModel):
    """更新Agent状态请求"""
    agent_name: str
    status: str


class UpdateReportRequest(BaseModel):
    """更新报告请求"""
    section_name: str
    content: str


class AddMessageRequest(BaseModel):
    """添加消息请求"""
    role: str = Field(..., description="消息角色: user, assistant, system, agent")
    content: str = Field(..., description="消息内容")
    agent_name: Optional[str] = Field(None, description="Agent名称")
    message_type: Optional[str] = Field(None, description="消息类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


@router.post("/create", response_model=Dict[str, str])
async def create_conversation(request: CreateConversationRequest):
    """
    创建新的会话session
    """
    try:
        session_id = conversation_memory_service.create_conversation_session(
            user_id=request.user_id,
            ticker=request.ticker,
            analysis_date=request.analysis_date,
            analysts=request.analysts,
            research_depth=request.research_depth
        )
        
        return {
            "session_id": session_id,
            "status": "created",
            "message": f"Created conversation session for {request.ticker}"
        }
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/restore/{session_id}", response_model=RestoreConversationResponse)
async def restore_conversation(session_id: str):
    """
    恢复会话状态用于chat界面
    """
    try:
        restored_data = analysis_runner_service.get_conversation_session(session_id)
        
        if not restored_data:
            raise HTTPException(status_code=404, detail=f"Conversation session {session_id} not found")
        
        return RestoreConversationResponse(**restored_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring conversation {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restore conversation: {str(e)}")


@router.get("/list", response_model=List[ConversationListItem])
async def list_conversations(
    user_id: str = Query("demo_user", description="用户ID"),
    limit: int = Query(20, description="返回数量限制")
):
    """
    列出用户的会话历史
    """
    try:
        conversations = analysis_runner_service.list_user_conversations(user_id)
        
        # 转换为响应格式
        result = []
        for conv in conversations[:limit]:
            result.append(ConversationListItem(
                session_id=conv["session_id"],
                ticker=conv["ticker"],
                analysis_date=conv["analysis_date"],
                agent_status=conv.get("agent_status", {}),
                is_finalized=conv.get("is_finalized", False),
                created_at=conv["created_at"],
                updated_at=conv["updated_at"]
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing conversations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/by-stock", response_model=List[ConversationDetail])
async def get_conversations_by_stock_and_user(
    user_id: str = Query(..., description="用户ID"),
    ticker: str = Query(..., description="股票代码"),
    limit: int = Query(20, description="返回数量限制")
):
    """
    根据股票代码和用户ID查询对话列表
    """
    try:
        conversations = conversation_memory_service.get_conversations_by_stock_and_user(
            user_id=user_id,
            ticker=ticker,
            limit=limit
        )
        
        # 转换为响应格式
        result = []
        for conv in conversations:
            result.append(ConversationDetail(
                session_id=conv["session_id"],
                user_id=conv["user_id"],
                ticker=conv["ticker"],
                analysis_date=conv["analysis_date"],
                task_id=conv.get("task_id"),
                analysts=conv.get("analysts", []),
                research_depth=conv.get("research_depth", 1),
                llm_config=conv.get("llm_config", {}),
                agent_status=conv.get("agent_status", {}),
                current_agent=conv.get("current_agent"),
                messages=conv.get("messages", []),
                tool_calls=conv.get("tool_calls", []),
                report_sections=conv.get("report_sections", {}),
                current_report=conv.get("current_report"),
                final_report=conv.get("final_report"),
                final_state=conv.get("final_state"),
                processed_signal=conv.get("processed_signal"),
                execution_type=conv.get("execution_type", "manual"),
                last_interaction=conv.get("last_interaction"),
                is_finalized=conv.get("is_finalized", False),
                created_at=conv["created_at"],
                updated_at=conv["updated_at"]
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting conversations for user {user_id} and ticker {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")


@router.get("/newest-by-stock", response_model=Optional[ConversationDetail])
async def get_newest_conversation_by_stock(
    user_id: str = Query(..., description="用户ID"),
    ticker: str = Query(..., description="股票代码")
):
    """
    根据股票代码和用户ID获取最新的对话
    """
    try:
        conversation = conversation_memory_service.get_newest_conversation_by_stock(
            user_id=user_id,
            ticker=ticker
        )
        
        if not conversation:
            return None
        
        # 转换为响应格式
        return ConversationDetail(
            session_id=conversation["session_id"],
            user_id=conversation["user_id"],
            ticker=conversation["ticker"],
            analysis_date=conversation["analysis_date"],
            task_id=conversation.get("task_id"),
            analysts=conversation.get("analysts", []),
            research_depth=conversation.get("research_depth", 1),
            llm_config=conversation.get("llm_config", {}),
            agent_status=conversation.get("agent_status", {}),
            current_agent=conversation.get("current_agent"),
            messages=conversation.get("messages", []),
            tool_calls=conversation.get("tool_calls", []),
            report_sections=conversation.get("report_sections", {}),
            current_report=conversation.get("current_report"),
            final_report=conversation.get("final_report"),
            final_state=conversation.get("final_state"),
            processed_signal=conversation.get("processed_signal"),
            execution_type=conversation.get("execution_type", "manual"),
            last_interaction=conversation.get("last_interaction"),
            is_finalized=conversation.get("is_finalized", False),
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"Error getting newest conversation for user {user_id} and ticker {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get newest conversation: {str(e)}")


@router.get("/{session_id}/state", response_model=Dict[str, Any])
async def get_conversation_state(session_id: str):
    """
    获取会话当前状态
    """
    try:
        state = conversation_memory_service.get_conversation_state(session_id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
        
        return {
            "session_id": state.session_id,
            "ticker": state.ticker,
            "analysis_date": state.analysis_date,
            "status": state.status,
            "current_agent": state.current_agent,
            "agent_status": state.agent_status,
            "report_sections": state.report_sections,
            "created_at": state.created_at,
            "updated_at": state.updated_at,
            "statistics": {
                "total_messages": len(state.messages),
                "total_tool_calls": len(state.tool_calls),
                "completed_reports": len([r for r in state.report_sections.values() if r])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation state {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation state: {str(e)}")


@router.post("/{session_id}/agent-status")
async def update_agent_status(session_id: str, request: UpdateAgentStatusRequest):
    """
    更新Agent状态
    """
    try:
        success = conversation_memory_service.update_agent_status(
            session_id=session_id,
            agent_name=request.agent_name,
            status=request.status
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
        
        return {
            "status": "success",
            "message": f"Updated {request.agent_name} status to {request.status}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent status for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update agent status: {str(e)}")


@router.post("/{session_id}/report")
async def update_report_section(session_id: str, request: UpdateReportRequest):
    """
    更新报告段落
    """
    try:
        success = conversation_memory_service.update_report_section(
            session_id=session_id,
            section_name=request.section_name,
            content=request.content
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
        
        return {
            "status": "success",
            "message": f"Updated report section {request.section_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating report for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update report: {str(e)}")


@router.post("/{session_id}/message")
async def add_chat_message(session_id: str, request: AddMessageRequest):
    """
    添加聊天消息
    """
    try:
        message_id = conversation_memory_service.add_chat_message(
            session_id=session_id,
            role=request.role,
            content=request.content,
            agent_name=request.agent_name,
            message_type=request.message_type,
            metadata=request.metadata
        )
        
        if not message_id:
            raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
        
        return {
            "message_id": message_id,
            "status": "success",
            "message": "Message added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message to session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.get("/{session_id}/chat-history", response_model=List[Dict[str, Any]])
async def get_chat_history(
    session_id: str,
    limit: int = Query(100, description="消息数量限制")
):
    """
    获取聊天历史
    """
    try:
        chat_history = conversation_memory_service.get_chat_history(session_id, limit)
        
        return [
            {
                "message_id": msg.message_id,
                "timestamp": msg.timestamp,
                "role": msg.role,
                "content": msg.content,
                "agent_name": msg.agent_name,
                "message_type": msg.message_type,
                "metadata": msg.metadata
            }
            for msg in chat_history
        ]
        
    except Exception as e:
        logger.error(f"Error getting chat history for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@router.post("/{session_id}/finalize")
async def finalize_conversation(
    session_id: str,
    final_state: Optional[Dict[str, Any]] = None,
    processed_signal: Optional[Any] = None
):
    """
    完成会话并保存最终状态
    """
    try:
        success = conversation_memory_service.finalize_conversation(
            session_id=session_id,
            final_state=final_state or {},
            processed_signal=processed_signal
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
        
        return {
            "status": "success",
            "message": "Conversation finalized successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing conversation {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to finalize conversation: {str(e)}")


@router.delete("/{session_id}")
async def archive_conversation(session_id: str):
    """
    归档会话（将状态设为archived）
    """
    try:
        success = conversation_memory_service.update_conversation_state(
            session_id, {"status": "archived"}
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
        
        return {
            "status": "success",
            "message": "Conversation archived successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving conversation {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to archive conversation: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "service": "conversation-memory",
        "message": "Conversation memory service is running"
    }
