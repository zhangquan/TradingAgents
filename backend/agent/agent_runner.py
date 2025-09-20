"""
Analysis Runner Service - Orchestrator for modular trading analysis components.
This service coordinates the config handler, memory tracker, and analysis executor
to provide a unified interface for trading analysis execution.
"""

import logging
from typing import Dict, Any, List

from .analysis_executor import AnalysisExecutor
from backend.repositories import ConversationRepository

logger = logging.getLogger(__name__)


class AgentRunner:
    """
    Orchestrator service for trading analysis execution.
    Coordinates modular components to provide a unified analysis interface.
    """
    
    def __init__(self):
        """Initialize the analysis runner service."""
        self.analysis_executor = AnalysisExecutor()
 
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
        Delegates to the analysis executor with memory tracking enabled.
        
        Args:
            task_id: Unique task identifier
            ticker: Stock ticker symbol
            analysis_date: Date for analysis
            analysts: List of analyst types to use
            research_depth: Depth of research (default: 1)
            user_id: User identifier (default: "demo_user")
            enable_memory: Whether to enable conversation memory (default: True)
            execution_type: Type of execution (manual/scheduled)
            
        Returns:
            Dict containing analysis results and session_id for chat recovery
        """
        if enable_memory:
            return self.analysis_executor.execute_analysis_with_memory(
                task_id=task_id,
                ticker=ticker,
                analysis_date=analysis_date,
                analysts=analysts,
                research_depth=research_depth,
                user_id=user_id,
                execution_type=execution_type
            )
        else:
            return self.analysis_executor.execute_standard_analysis(
                task_id=task_id,
                ticker=ticker,
                analysis_date=analysis_date,
                analysts=analysts,
                research_depth=research_depth,
                user_id=user_id
            )

 


# Global service instance
agent_runner = AgentRunner()
