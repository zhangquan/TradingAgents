"""
Analysis Runner Service - Independent service for running trading analysis.
This service contains the core analysis execution logic without dependencies on other services.
Enhanced with conversation memory for session persistence and chat-based recovery.
"""

import logging
import json
import os
import uuid
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from backend.repositories import (
    UserConfigRepository, ScheduledTaskRepository, ReportRepository,
    SystemRepository, SessionLocal
)
from backend.services.conversation_memory_service import conversation_memory_service

logger = logging.getLogger(__name__)


class AnalysisRunnerService:
    """
    Independent service for running trading analysis.
    Contains all logic needed to execute analysis without depending on other services.
    """
    
    def __init__(self):
        """Initialize the analysis runner service."""
        self.user_config_repo = UserConfigRepository(SessionLocal)
        self.scheduled_task_repo = ScheduledTaskRepository(SessionLocal)
        self.report_repo = ReportRepository(SessionLocal)
        self.system_repo = SystemRepository(SessionLocal)
        self.trading_graphs = {}  # Local cache for trading graph instances
    
    def get_trading_graph(self, config: Dict[str, Any]) -> TradingAgentsGraph:
        """Get or create trading graph instance."""
        config_key = str(hash(json.dumps(config, sort_keys=True)))
        
        if config_key not in self.trading_graphs:
            # Create new trading graph with config
            updated_config = DEFAULT_CONFIG.copy()
            updated_config.update(config)
            
            # Add unique identifier to avoid collection name conflicts
            import time
            updated_config["instance_id"] = f"{int(time.time() * 1000)}_{hash(config_key) % 10000}"
            
            # Pass analysts to TradingAgentsGraph constructor to ensure proper initialization
            analysts = config.get("analysts", ["market", "news", "fundamentals"])
            print(f"updated_config: {updated_config}")
            self.trading_graphs[config_key] = TradingAgentsGraph(
                selected_analysts=analysts, 
                config=updated_config
            )
        
        return self.trading_graphs[config_key]
    
    def get_user_config_with_defaults(self, user_id: str) -> Dict[str, Any]:
        """Get user configuration with fallback to system defaults."""
        user_config = self.user_config_repo.get_user_config(user_id)
        
        # Use user preferences or fallback to defaults from DEFAULT_CONFIG
        return {
            "llm_provider": user_config.get("llm_provider", DEFAULT_CONFIG["llm_provider"]),
            "backend_url": user_config.get("backend_url", DEFAULT_CONFIG["backend_url"]),
            "deep_think_llm": user_config.get("deep_thinker", DEFAULT_CONFIG["deep_think_llm"]),
            "quick_think_llm": user_config.get("shallow_thinker", DEFAULT_CONFIG["quick_think_llm"]),
            "default_research_depth": user_config.get("default_research_depth", 1),
            "default_analysts": user_config.get("default_analysts", ["market", "news", "fundamentals"]),
            # Language settings
            "default_language": user_config.get("default_language", DEFAULT_CONFIG["default_language"]),
            "report_language": user_config.get("report_language", DEFAULT_CONFIG["report_language"])
        }
    
    def prepare_analysis_config(self, user_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Prepare configuration for analysis."""
        user_config = self.get_user_config_with_defaults(user_id)
        
        # Use user's saved language preference from system configuration
        saved_language = user_config.get("report_language") or user_config.get("default_language")
        # Use saved language if available, otherwise use default
        if saved_language and saved_language != 'auto':
            report_language = saved_language
        else:
            report_language = "en-US"  # Default fallback
        
        config = {
            "llm_provider": user_config["llm_provider"],
            "backend_url": user_config["backend_url"],
            "deep_think_llm": user_config["deep_think_llm"],
            "quick_think_llm": user_config["quick_think_llm"],
            "online_tools": True,
            "project_dir": str(Path.cwd()),
            "report_language": self._normalize_language(report_language),
            "default_language": self._normalize_language(report_language)
        }
        
        # Add API key based on LLM provider
        if user_config["llm_provider"].lower() == "aliyun":
            config["aliyun_api_key"] = os.getenv("ALIYUN_API_KEY")
        elif user_config["llm_provider"].lower() == "openai":
            config["api_key"] = os.getenv("OPENAI_API_KEY")
        elif user_config["llm_provider"].lower() == "google":
            config["api_key"] = os.getenv("GOOGLE_API_KEY")
        
        return config, user_config
    
    def _normalize_language(self, accept_language: str) -> str:
        """Normalize Accept-Language header to supported language codes."""
        # Extract primary language from Accept-Language header (e.g., "zh-CN,zh;q=0.9,en;q=0.8" -> "zh-CN")
        if not accept_language:
            return "en-US"
        
        primary_lang = accept_language.split(',')[0].strip()
        
        # Map common language codes to supported ones
        language_map = {
            "zh-CN": "zh-CN",
            "zh-TW": "zh-TW", 
            "zh": "zh-CN",
            "en-US": "en-US",
            "en-GB": "en-US",
            "en": "en-US",
            "ja": "ja-JP",
            "ja-JP": "ja-JP",
            "ko": "ko-KR",
            "ko-KR": "ko-KR",
            "fr": "fr-FR",
            "fr-FR": "fr-FR",
            "de": "de-DE",
            "de-DE": "de-DE",
            "es": "es-ES",
            "es-ES": "es-ES",
        }
        
        return language_map.get(primary_lang, "en-US")
    
 
    def extract_reports_from_state(self, final_state: Dict[str, Any]) -> Dict[str, str]:
        """Extract reports from final state."""
        return {
            "market_report": final_state.get("market_report", ""),
            "sentiment_report": final_state.get("sentiment_report", ""),
            "news_report": final_state.get("news_report", ""),
            "fundamentals_report": final_state.get("fundamentals_report", ""),
            "investment_plan": final_state.get("investment_plan", ""),
            "final_trade_decision": final_state.get("final_trade_decision", "")
        }
    
    def save_reports_to_files(self, reports: Dict[str, str], report_dir: Path) -> None:
        """Save reports to individual files."""
        for report_name, content in reports.items():
            if content:
                report_file = report_dir / f"{report_name}.md"
                with open(report_file, "w", encoding="utf-8") as f:
                    f.write(str(content))
    
   
    def create_task_result(self, 
                          analysis_id: str,
                          reports: Dict[str, str],
                          processed_signal: Any) -> Dict[str, Any]:
        """Create task result structure."""
        return {
            "analysis_id": analysis_id,
            "final_state": reports,
            "decision": processed_signal,
            "trace": ["initialization", "market_analysis", "sentiment_analysis", "news_analysis", "final_decision"],
            "completed_at": datetime.now().isoformat()
        }
    
    def run_sync_analysis_with_memory(self,
                                     task_id: str,
                                     ticker: str,
                                     analysis_date: str,
                                     analysts: List[str],
                                     research_depth: int = 1,
                                     user_id: str = "demo_user",
                                     enable_memory: bool = True,
                                     execution_type: str = "manual") -> Dict[str, Any]:
        """
        Run analysis with conversation memory support for session persistence.
        
        Args:
            task_id: Unique task identifier
            ticker: Stock ticker symbol
            analysis_date: Date for analysis
            analysts: List of analyst types to use
            research_depth: Depth of research (default: 1)
            user_id: User identifier (default: "demo_user")
            enable_memory: Whether to enable conversation memory (default: True)
            
        Returns:
            Dict containing analysis results and session_id for chat recovery
        """
        # Record analysis start time
        analysis_start_time = datetime.now()
        start_timestamp = time.time()
        
        # Update task status
        self.scheduled_task_repo.update_scheduled_task_status(task_id, "running")
        
        # Prepare configuration using system-wide language settings
        config, user_config = self.prepare_analysis_config(user_id)
        
        # Add analysts to config before getting trading graph
        config["analysts"] = analysts
        
        session_id = None
        if enable_memory:
            # Create conversation session with execution type
            session_id = conversation_memory_service.create_conversation_session(
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
        trading_graph = self.get_trading_graph(config)
        
        try:
            # Create custom streaming callback for memory integration
            if enable_memory and session_id:
                final_state, processed_signal = self._run_analysis_with_memory_tracking(
                    trading_graph, ticker, analysis_date, session_id
                )
            else:
                # Run standard analysis
                final_state, processed_signal = trading_graph.propagate(ticker, analysis_date)
            
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
                    session_id=session_id if enable_memory else None,
                    analysis_started_at=analysis_start_time,
                    analysis_completed_at=analysis_end_time,
                    analysis_duration_seconds=execution_duration
                )
            
            # Finalize conversation memory
            if enable_memory and session_id:
                conversation_memory_service.finalize_conversation(session_id, final_state, processed_signal)
            
            # Create and store task results
            task_result = self.create_task_result(analysis_id, reports, processed_signal)
            if enable_memory and session_id:
                task_result["session_id"] = session_id
            
            # Update task with results and mark as completed
            self.scheduled_task_repo.update_scheduled_task_status(task_id, "completed", 
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
            
        except Exception as e:
            logger.error(f"Analysis failed for task {task_id}: {e}")
            
            # Update task status to failed
            self.scheduled_task_repo.update_scheduled_task_status(task_id, "failed", 
                                          error_message=str(e))
            
            # Update conversation memory if enabled
            if enable_memory and session_id:
                conversation_memory_service.update_conversation_state(session_id, {
                    "status": "failed",
                    "error_message": str(e)
                })
            
            raise

    def run_sync_analysis(self, 
                          task_id: str,
                          ticker: str,
                          analysis_date: str,
                          analysts: List[str],
                          research_depth: int = 1,
                          user_id: str = "demo_user") -> Dict[str, Any]:
        """
        Run the complete trading analysis process synchronously.
        
        This is a pure analysis execution function without async wrapper.
        Background task management is handled by scheduler_service.
        
        Args:
            task_id: Unique task identifier
            ticker: Stock ticker symbol
            analysis_date: Date for analysis
            analysts: List of analyst types to use
            research_depth: Depth of research (default: 1)
            user_id: User identifier (default: "demo_user")
            
        Returns:
            Dict containing analysis results
            
        Raises:
            Exception: If analysis fails
        """
        # Record analysis start time
        analysis_start_time = datetime.now()
        start_timestamp = time.time()
        
        # Update task status
        self.scheduled_task_repo.update_scheduled_task_status(task_id, "running")
        
        # Prepare configuration using system-wide language settings
        config, user_config = self.prepare_analysis_config(user_id)
        
        # Add analysts to config before getting trading graph
        config["analysts"] = analysts
        
        # Get trading graph instance
        trading_graph = self.get_trading_graph(config)
        
        # Run the actual analysis (synchronous)
        final_state, processed_signal = trading_graph.propagate(ticker, analysis_date)
        
        # Calculate execution duration
        analysis_end_time = datetime.now()
        end_timestamp = time.time()
        execution_duration = end_timestamp - start_timestamp
        
        # Extract reports from final state
        reports = self.extract_reports_from_state(final_state)
        
        # Generate analysis_id for further operations
        analysis_id = str(uuid.uuid4())
        
        # Save unified report with all sections and timing information
        # Filter out empty reports
        non_empty_reports = {report_type: content for report_type, content in reports.items() if content}
        if non_empty_reports:
            self.report_repo.save_unified_report(
                analysis_id=analysis_id,
                user_id=user_id,
                ticker=ticker,
                sections=non_empty_reports,
                title=f"{ticker.upper()} Complete Analysis Report",
                session_id=None,  # No session for standard analysis
                analysis_started_at=analysis_start_time,
                analysis_completed_at=analysis_end_time,
                analysis_duration_seconds=execution_duration
            )
        
        # Create and store task results
        task_result = self.create_task_result(analysis_id, reports, processed_signal)
        print(task_result)
        # Update task with results and mark as completed
        self.scheduled_task_repo.update_scheduled_task_status(task_id, "completed", 
                                      analysis_id=analysis_id,
                                      result_data=task_result,
                                      progress=100)
        
        # Log system event for successful completion
        self.system_repo.log_system_event("analysis_completed", {
            "task_id": task_id,
            "analysis_id": analysis_id,
            "ticker": ticker,
            "status": "completed"
        })
        
        return {
            "analysis_id": analysis_id,
            "reports": reports,
            "decision": processed_signal,
            "final_state": final_state
        }
    
    def _run_analysis_with_memory_tracking(self, 
                                          trading_graph: TradingAgentsGraph,
                                          ticker: str,
                                          analysis_date: str,
                                          session_id: str) -> Tuple[Dict[str, Any], Any]:
        """
        Run analysis with real-time memory tracking similar to CLI interface.
        """
        # Initialize state
        init_agent_state = trading_graph.propagator.create_initial_state(ticker, analysis_date)
        args = trading_graph.propagator.get_graph_args()
        
        # Track which agents have started
        started_agents = set()
        
        # Stream the analysis with memory tracking
        trace = []
        for chunk in trading_graph.graph.stream(init_agent_state, **args):
            if len(chunk["messages"]) > 0:
                # Get the last message from the chunk
                last_message = chunk["messages"][-1]
                
                # Extract message content and type
                if hasattr(last_message, "content"):
                    content = self._extract_content_string(last_message.content)
                    msg_type = "Reasoning"
                else:
                    content = str(last_message)
                    msg_type = "System"
                
                # Add message to memory
                conversation_memory_service.add_message(session_id, msg_type, content)
                
                # If it's a tool call, add it to memory
                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        if isinstance(tool_call, dict):
                            conversation_memory_service.add_tool_call(
                                session_id, tool_call["name"], tool_call["args"]
                            )
                        else:
                            conversation_memory_service.add_tool_call(
                                session_id, tool_call.name, tool_call.args
                            )
                
                # Update reports and agent status based on chunk content
                self._update_memory_from_chunk(session_id, chunk, started_agents)
            
            trace.append(chunk)
        
        # Get final state and decision
        final_state = trace[-1]
        processed_signal = trading_graph.process_signal(final_state["final_trade_decision"])
        
        return final_state, processed_signal
    
    def _update_memory_from_chunk(self, session_id: str, chunk: Dict[str, Any], started_agents: set):
        """Update conversation memory based on chunk data (similar to CLI logic)"""
        
        # Analyst Team Reports
        if "market_report" in chunk and chunk["market_report"]:
            conversation_memory_service.update_report_section(
                session_id, "market_report", chunk["market_report"]
            )
            conversation_memory_service.update_agent_status(session_id, "Market Analyst", "completed")
            
        if "sentiment_report" in chunk and chunk["sentiment_report"]:
            conversation_memory_service.update_report_section(
                session_id, "sentiment_report", chunk["sentiment_report"]
            )
            conversation_memory_service.update_agent_status(session_id, "Social Analyst", "completed")
            
        if "news_report" in chunk and chunk["news_report"]:
            conversation_memory_service.update_report_section(
                session_id, "news_report", chunk["news_report"]
            )
            conversation_memory_service.update_agent_status(session_id, "News Analyst", "completed")
            
        if "fundamentals_report" in chunk and chunk["fundamentals_report"]:
            conversation_memory_service.update_report_section(
                session_id, "fundamentals_report", chunk["fundamentals_report"]
            )
            conversation_memory_service.update_agent_status(session_id, "Fundamentals Analyst", "completed")
        
        # Research Team - Handle Investment Debate State
        if "investment_debate_state" in chunk and chunk["investment_debate_state"]:
            debate_state = chunk["investment_debate_state"]
            
            if "judge_decision" in debate_state and debate_state["judge_decision"]:
                # Research team has completed their decision
                investment_plan = f"### Research Manager Decision\n{debate_state['judge_decision']}"
                conversation_memory_service.update_report_section(
                    session_id, "investment_plan", investment_plan
                )
                conversation_memory_service.update_agent_status(session_id, "Research Manager", "completed")
        
        # Trading Team
        if "trader_investment_plan" in chunk and chunk["trader_investment_plan"]:
            conversation_memory_service.update_report_section(
                session_id, "trader_investment_plan", chunk["trader_investment_plan"]
            )
            conversation_memory_service.update_agent_status(session_id, "Trader", "completed")
        
        # Risk Management Team - Handle Risk Debate State  
        if "risk_debate_state" in chunk and chunk["risk_debate_state"]:
            risk_state = chunk["risk_debate_state"]
            
            if "judge_decision" in risk_state and risk_state["judge_decision"]:
                # Portfolio manager has made final decision
                final_decision = f"### Portfolio Manager Decision\n{risk_state['judge_decision']}"
                conversation_memory_service.update_report_section(
                    session_id, "final_trade_decision", final_decision
                )
                conversation_memory_service.update_agent_status(session_id, "Portfolio Manager", "completed")
    
    def _extract_content_string(self, content):
        """Extract string content from various message formats (similar to CLI)"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle Anthropic's list format
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                    elif item.get('type') == 'tool_use':
                        text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
                else:
                    text_parts.append(str(item))
            return ' '.join(text_parts)
        else:
            return str(content)
    
    def get_conversation_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation session for chat restoration"""
        return conversation_memory_service.restore_conversation_for_chat(session_id)
    
    def list_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """List user's conversation sessions"""
        return conversation_memory_service.list_user_conversations(user_id)


# Global service instance
analysis_runner_service = AnalysisRunnerService()
