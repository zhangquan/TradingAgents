"""
Memory Tracker for Agent Runner Service.
Handles conversation memory tracking and real-time state updates during analysis.
"""

import logging
from typing import Dict, Any, Tuple, Set

from tradingagents.graph.trading_graph import TradingAgentsGraph
from backend.repositories import ConversationRepository

logger = logging.getLogger(__name__)


class MemoryTracker:
    """
    Handles conversation memory tracking during analysis execution.
    Provides real-time tracking and state updates for streaming analysis.
    """
    
    def __init__(self):
        """Initialize the memory tracker."""
        self.conversation_repo = ConversationRepository()
    
    def add_message(self, session_id: str, message_type: str, content: str) -> bool:
        """Add message to conversation state"""
        try:
            state = self.conversation_repo.get_conversation_state(session_id)
            if not state:
                return False
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            messages = state.get("messages", [])
            messages.append((timestamp, message_type, content))
            
            return self.conversation_repo.update_conversation_state(session_id, {"messages": messages})
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False
    
    def add_tool_call(self, session_id: str, tool_name: str, args: Dict[str, Any]) -> bool:
        """Add tool call to conversation state"""
        try:
            state = self.conversation_repo.get_conversation_state(session_id)
            if not state:
                return False
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            tool_calls = state.get("tool_calls", [])
            tool_calls.append((timestamp, tool_name, args))
            
            return self.conversation_repo.update_conversation_state(session_id, {"tool_calls": tool_calls})
        except Exception as e:
            logger.error(f"Error adding tool call to session {session_id}: {e}")
            return False
    
    def update_report_section(self, session_id: str, section_name: str, content: str) -> bool:
        """Update report section in conversation state"""
        try:
            state = self.conversation_repo.get_conversation_state(session_id)
            if not state:
                return False
            
            report_sections = state.get("report_sections", {})
            report_sections[section_name] = content
            
            return self.conversation_repo.update_conversation_state(session_id, {"report_sections": report_sections})
        except Exception as e:
            logger.error(f"Error updating report section for session {session_id}: {e}")
            return False
    
    def update_agent_status(self, session_id: str, agent_name: str, status: str) -> bool:
        """Update agent status in conversation state"""
        try:
            state = self.conversation_repo.get_conversation_state(session_id)
            if not state:
                return False
            
            agent_status = state.get("agent_status", {})
            agent_status[agent_name] = status
            
            return self.conversation_repo.update_conversation_state(session_id, {
                "agent_status": agent_status,
                "current_agent": agent_name
            })
        except Exception as e:
            logger.error(f"Error updating agent status for session {session_id}: {e}")
            return False
    
    def run_analysis_with_memory_tracking(self, 
                                        trading_graph: TradingAgentsGraph,
                                        ticker: str,
                                        analysis_date: str,
                                        session_id: str) -> Tuple[Dict[str, Any], Any]:
        """
        Run analysis with real-time memory tracking similar to CLI interface.
        
        Args:
            trading_graph: TradingAgentsGraph instance
            ticker: Stock ticker symbol
            analysis_date: Date for analysis
            session_id: Conversation session ID
            
        Returns:
            Tuple of (final_state, processed_signal)
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
                self.add_message(session_id, msg_type, content)
                
                # If it's a tool call, add it to memory
                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        if isinstance(tool_call, dict):
                            self.add_tool_call(
                                session_id, tool_call["name"], tool_call["args"]
                            )
                        else:
                            self.add_tool_call(
                                session_id, tool_call.name, tool_call.args
                            )
                
                # Update reports and agent status based on chunk content
                self._update_memory_from_chunk(session_id, chunk, started_agents)
            
            trace.append(chunk)
        
        # Get final state and decision
        final_state = trace[-1]
        processed_signal = trading_graph.process_signal(final_state["final_trade_decision"])
        
        return final_state, processed_signal
    
    def _update_memory_from_chunk(self, session_id: str, chunk: Dict[str, Any], started_agents: Set[str]):
        """
        Update conversation memory based on chunk data (similar to CLI logic).
        
        Args:
            session_id: Conversation session ID
            chunk: Data chunk from analysis stream
            started_agents: Set of agents that have started
        """
        # Analyst Team Reports
        if "market_report" in chunk and chunk["market_report"]:
            self.update_report_section(
                session_id, "market_report", chunk["market_report"]
            )
            self.update_agent_status(session_id, "Market Analyst", "completed")
            
        if "sentiment_report" in chunk and chunk["sentiment_report"]:
            self.update_report_section(
                session_id, "sentiment_report", chunk["sentiment_report"]
            )
            self.update_agent_status(session_id, "Social Analyst", "completed")
            
        if "news_report" in chunk and chunk["news_report"]:
            self.update_report_section(
                session_id, "news_report", chunk["news_report"]
            )
            self.update_agent_status(session_id, "News Analyst", "completed")
            
        if "fundamentals_report" in chunk and chunk["fundamentals_report"]:
            self.update_report_section(
                session_id, "fundamentals_report", chunk["fundamentals_report"]
            )
            self.update_agent_status(session_id, "Fundamentals Analyst", "completed")
        
        # Research Team - Handle Investment Debate State
        if "investment_debate_state" in chunk and chunk["investment_debate_state"]:
            debate_state = chunk["investment_debate_state"]
            
            if "judge_decision" in debate_state and debate_state["judge_decision"]:
                # Research team has completed their decision
                investment_plan = f"### Research Manager Decision\n{debate_state['judge_decision']}"
                self.update_report_section(
                    session_id, "investment_plan", investment_plan
                )
                self.update_agent_status(session_id, "Research Manager", "completed")
        
        # Trading Team
        if "trader_investment_plan" in chunk and chunk["trader_investment_plan"]:
            self.update_report_section(
                session_id, "trader_investment_plan", chunk["trader_investment_plan"]
            )
            self.update_agent_status(session_id, "Trader", "completed")
        
        # Risk Management Team - Handle Risk Debate State  
        if "risk_debate_state" in chunk and chunk["risk_debate_state"]:
            risk_state = chunk["risk_debate_state"]
            
            if "judge_decision" in risk_state and risk_state["judge_decision"]:
                # Portfolio manager has made final decision
                final_decision = f"### Portfolio Manager Decision\n{risk_state['judge_decision']}"
                self.update_report_section(
                    session_id, "final_trade_decision", final_decision
                )
                self.update_agent_status(session_id, "Portfolio Manager", "completed")
    
    def _extract_content_string(self, content):
        """
        Extract string content from various message formats (similar to CLI).
        
        Args:
            content: Message content in various formats
            
        Returns:
            String representation of the content
        """
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
