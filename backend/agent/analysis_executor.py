"""
Analysis Executor for Agent Runner Service.
Handles the core analysis execution logic, report processing, and result management.
"""

import logging
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

from backend.repositories import (
    AnalysisTaskRepository, ReportRepository, SystemRepository, 
    ConversationRepository, ChatMessageRepository
)
from .config_handler import ConfigHandler
from .memory_tracker import MemoryTracker

logger = logging.getLogger(__name__)


class AnalysisExecutor:
    """
    Handles the core analysis execution logic.
    Manages analysis lifecycle, report generation, and result storage.
    """
    
    def __init__(self):
        """Initialize the analysis executor."""
        self.analysis_task_repo = AnalysisTaskRepository()
        self.report_repo = ReportRepository()
        self.system_repo = SystemRepository()
        self.conversation_repo = ConversationRepository()
        self.chat_message_repo = ChatMessageRepository()
        self.config_handler = ConfigHandler()
        self.memory_tracker = MemoryTracker()
    
    def create_conversation_session(self, user_id: str, ticker: str, analysis_date: str, 
                                  analysts: List[str], research_depth: int = 1,
                                  llm_config: Dict[str, Any] = None, 
                                  execution_type: str = "manual") -> str:
        """Create a new conversation session"""
        import uuid
        session_id = str(uuid.uuid4())
        
        # Initialize agent status
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
        
        # Initialize report sections
        report_sections = {
            "market_report": None,
            "sentiment_report": None,
            "news_report": None,
            "fundamentals_report": None,
            "investment_plan": None,
            "trader_investment_plan": None,
            "final_trade_decision": None,
        }
        
        state_data = {
            "analysis_date": analysis_date,
            "analysts": analysts,
            "research_depth": research_depth,
            "llm_config": llm_config or {},
            "agent_status": agent_status,
            "current_agent": None,
            "messages": [],
            "tool_calls": [],
            "report_sections": report_sections,
            "current_report": None,
            "final_report": None,
            "final_state": None,
            "processed_signal": None,
            "execution_type": execution_type,
            "last_interaction": datetime.now(),
            "is_finalized": False
        }
        
        self.conversation_repo.save_conversation_state(session_id, user_id, ticker, state_data)
        return session_id
    
    def update_conversation_state(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update conversation state"""
        return self.conversation_repo.update_conversation_state(session_id, updates)
    
    def finalize_conversation(self, session_id: str, final_state: Dict[str, Any], 
                            processed_signal: Any) -> bool:
        """Finalize conversation with results"""
        updates = {
            "final_state": final_state,
            "processed_signal": processed_signal,
            "is_finalized": True
        }
        return self.conversation_repo.update_conversation_state(session_id, updates)
    
    def extract_reports_from_state(self, final_state: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract reports from final state.
        
        Args:
            final_state: Final state from analysis
            
        Returns:
            Dict containing extracted reports
        """
        return {
            "market_report": final_state.get("market_report", ""),
            "sentiment_report": final_state.get("sentiment_report", ""),
            "news_report": final_state.get("news_report", ""),
            "fundamentals_report": final_state.get("fundamentals_report", ""),
            "investment_plan": final_state.get("investment_plan", ""),
            "final_trade_decision": final_state.get("final_trade_decision", "")
        }
    
    def create_task_result(self, 
                          analysis_id: str,
                          reports: Dict[str, str],
                          processed_signal: Any) -> Dict[str, Any]:
        """
        Create task result structure.
        
        Args:
            analysis_id: Unique analysis identifier
            reports: Extracted reports
            processed_signal: Processed signal from analysis
            
        Returns:
            Task result dictionary
        """
        return {
            "analysis_id": analysis_id,
            "final_state": reports,
            "decision": processed_signal,
            "trace": ["initialization", "market_analysis", "sentiment_analysis", "news_analysis", "final_decision"],
            "completed_at": datetime.now().isoformat()
        }
    
    def execute_analysis_with_memory(self,
                                   task_id: str,
                                   ticker: str,
                                   analysis_date: str,
                                   analysts: List[str],
                                   research_depth: int = 1,
                                   user_id: str = "demo_user",
                                   execution_type: str = "manual") -> Dict[str, Any]:
        """
        Execute analysis with conversation memory support for session persistence.
        
        Args:
            task_id: Unique task identifier
            ticker: Stock ticker symbol
            analysis_date: Date for analysis
            analysts: List of analyst types to use
            research_depth: Depth of research (default: 1)
            user_id: User identifier (default: "demo_user")
            execution_type: Type of execution (manual/scheduled)
            
        Returns:
            Dict containing analysis results and session_id for chat recovery
        """
        # Record analysis start time
        analysis_start_time = datetime.now()
        start_timestamp = time.time()
        
        # Update task status
        self.analysis_task_repo.update_analysis_task_status(task_id, "running")
        
        # Prepare configuration using system-wide language settings
        config, user_config = self.config_handler.prepare_analysis_config(user_id)
        
        # Add analysts to config before getting trading graph
        config["analysts"] = analysts
        
        # Create conversation session with execution type
        session_id = self.create_conversation_session(
            user_id=user_id,
            ticker=ticker,
            analysis_date=analysis_date,
            analysts=analysts,
            research_depth=research_depth,
            llm_config=config,
            execution_type=execution_type
        )
        
        # Add session_id to config for tracking
        config["session_id"] = session_id
        
        # Get trading graph instance
        trading_graph = self.config_handler.get_trading_graph(config)
        
        try:
            # Run analysis with memory tracking
            final_state, processed_signal = self.memory_tracker.run_analysis_with_memory_tracking(
                trading_graph, ticker, analysis_date, session_id
            )
            
            # Process results
            return self._process_analysis_results(
                task_id, analysis_start_time, start_timestamp, final_state, 
                processed_signal, ticker, user_id, session_id
            )
            
        except Exception as e:
            logger.error(f"Analysis failed for task {task_id}: {e}")
            
            # Update task status to failed
            self.analysis_task_repo.update_analysis_task_status(task_id, "failed", 
                                          error_message=str(e))
            
            # Update conversation memory
            self.update_conversation_state(session_id, {
                "status": "failed",
                "error_message": str(e)
            })
            
            raise
    
    def execute_standard_analysis(self, 
                                task_id: str,
                                ticker: str,
                                analysis_date: str,
                                analysts: List[str],
                                research_depth: int = 1,
                                user_id: str = "demo_user") -> Dict[str, Any]:
        """
        Execute standard analysis without memory tracking.
        
        Args:
            task_id: Unique task identifier
            ticker: Stock ticker symbol
            analysis_date: Date for analysis
            analysts: List of analyst types to use
            research_depth: Depth of research (default: 1)
            user_id: User identifier (default: "demo_user")
            
        Returns:
            Dict containing analysis results
        """
        # Record analysis start time
        analysis_start_time = datetime.now()
        start_timestamp = time.time()
        
        # Update task status
        self.analysis_task_repo.update_analysis_task_status(task_id, "running")
        
        # Prepare configuration using system-wide language settings
        config, user_config = self.config_handler.prepare_analysis_config(user_id)
        
        # Add analysts to config before getting trading graph
        config["analysts"] = analysts
        
        # Get trading graph instance
        trading_graph = self.config_handler.get_trading_graph(config)
        
        try:
            # Run the actual analysis (synchronous)
            final_state, processed_signal = trading_graph.propagate(ticker, analysis_date)
            
            # Process results
            return self._process_analysis_results(
                task_id, analysis_start_time, start_timestamp, final_state, 
                processed_signal, ticker, user_id, session_id=None
            )
            
        except Exception as e:
            logger.error(f"Analysis failed for task {task_id}: {e}")
            
            # Update task status to failed
            self.analysis_task_repo.update_analysis_task_status(task_id, "failed", 
                                          error_message=str(e))
            raise
    
    def _process_analysis_results(self,
                                task_id: str,
                                analysis_start_time: datetime,
                                start_timestamp: float,
                                final_state: Dict[str, Any],
                                processed_signal: Any,
                                ticker: str,
                                user_id: str,
                                session_id: str = None) -> Dict[str, Any]:
        """
        Process and store analysis results.
        
        Args:
            task_id: Task identifier
            analysis_start_time: When analysis started
            start_timestamp: Start timestamp for duration calculation
            final_state: Final state from analysis
            processed_signal: Processed signal
            ticker: Stock ticker
            user_id: User identifier
            session_id: Optional session ID for memory tracking
            
        Returns:
            Dict containing processed results
        """
        # Calculate execution duration
        analysis_end_time = datetime.now()
        end_timestamp = time.time()
        execution_duration = end_timestamp - start_timestamp
        
        # Extract reports from final state
        reports = self.extract_reports_from_state(final_state)
        
        # Generate analysis_id for further operations
        analysis_id = str(uuid.uuid4())
        
        # Save unified report with all sections and timing information
        non_empty_reports = {report_type: content for report_type, content in reports.items() if content}
        if non_empty_reports:
            self.report_repo.save_unified_report(
                analysis_id=analysis_id,
                user_id=user_id,
                ticker=ticker,
                sections=non_empty_reports,
                title=f"{ticker.upper()} Complete Analysis Report",
                session_id=session_id,
                analysis_started_at=analysis_start_time,
                analysis_completed_at=analysis_end_time
            )
        
        # Finalize conversation memory if enabled
        if session_id:
            self.finalize_conversation(session_id, final_state, processed_signal)
        
        # Create and store task results
        task_result = self.create_task_result(analysis_id, reports, processed_signal)
        if session_id:
            task_result["session_id"] = session_id
        
        # Update task with results and mark as completed
        self.analysis_task_repo.update_analysis_task_status(task_id, "completed", 
                                      analysis_id=analysis_id,
                                      result_data=task_result,
                                      progress=100)
        
        # Log system event for successful completion
        self.system_repo.log_system_event("analysis_completed", {
            "task_id": task_id,
            "analysis_id": analysis_id,
            "ticker": ticker,
            "status": "completed",
            "session_id": session_id
        })
        
        return {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "reports": reports,
            "decision": processed_signal,
            "final_state": final_state
        }
