"""
Analysis Runner Service - Independent service for running trading analysis.
This service contains the core analysis execution logic without dependencies on other services.
"""

import logging
import json
import os
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from backend.database.storage_service import DatabaseStorage

logger = logging.getLogger(__name__)


class AnalysisRunnerService:
    """
    Independent service for running trading analysis.
    Contains all logic needed to execute analysis without depending on other services.
    """
    
    def __init__(self):
        """Initialize the analysis runner service."""
        self.storage = DatabaseStorage()
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
        user_config = self.storage.get_user_config(user_id)
        
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
    
    def prepare_analysis_config(self, user_id: str, language: str = "en-US") -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Prepare configuration for analysis."""
        user_config = self.get_user_config_with_defaults(user_id)
        
        # Use user's saved language preference if available, otherwise use the provided language
        saved_language = user_config.get("report_language") or user_config.get("default_language")
        # Only use saved language if it's not 'auto' or empty
        if saved_language and saved_language != 'auto':
            report_language = saved_language
        else:
            report_language = language
        
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
            "zh-HK": "zh-TW",
            "zh-Hant": "zh-TW",
            "zh-Hans": "zh-CN",
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
            "pt": "pt-BR",
            "pt-BR": "pt-BR",
            "pt-PT": "pt-BR",
            "it": "it-IT",
            "it-IT": "it-IT",
            "ru": "ru-RU",
            "ru-RU": "ru-RU",
            "ar": "ar-SA",
            "ar-SA": "ar-SA",
            "hi": "hi-IN",
            "hi-IN": "hi-IN"
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
        # Update task status
        self.storage.update_scheduled_task_status(task_id, "running")
        
 
        # Get language from task data if available
        task_data = self.storage.get_scheduled_task(task_id)
        language = task_data.get("language", "en-US") if task_data else "en-US"
        
        # Prepare configuration
        config, user_config = self.prepare_analysis_config(user_id, language)
        
        # Add analysts to config before getting trading graph
        config["analysts"] = analysts
        
        # Get trading graph instance
        trading_graph = self.get_trading_graph(config)
        
        # Run the actual analysis (synchronous)
        final_state, processed_signal = trading_graph.propagate(ticker, analysis_date)
        
        # Extract reports from final state
        reports = self.extract_reports_from_state(final_state)
        

        
        # Generate analysis_id for further operations
        analysis_id = str(uuid.uuid4())
        
        # Save unified report with all sections
        # Filter out empty reports
        non_empty_reports = {report_type: content for report_type, content in reports.items() if content}
        if non_empty_reports:
            self.storage.save_unified_report(
                analysis_id=analysis_id,
                user_id=user_id,
                ticker=ticker,
                sections=non_empty_reports,
                title=f"{ticker.upper()} Complete Analysis Report"
            )
        
        # Create and store task results
        task_result = self.create_task_result(analysis_id, reports, processed_signal)
        print(task_result)
        # Update task with results and mark as completed
        self.storage.update_scheduled_task_status(task_id, "completed", 
                                      analysis_id=analysis_id,
                                      result_data=task_result,
                                      progress=100)
        
        # Log system event for successful completion
        self.storage.log_system_event("analysis_completed", {
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


# Global service instance
analysis_runner_service = AnalysisRunnerService()
