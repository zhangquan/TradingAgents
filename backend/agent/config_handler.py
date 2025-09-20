"""
Configuration Handler for Agent Runner Service.
Handles user configuration, language settings, and trading graph initialization.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Tuple

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from backend.repositories import UserConfigRepository


class ConfigHandler:
    """
    Handles configuration management for trading analysis.
    Manages user preferences, language settings, and trading graph instances.
    """
    
    def __init__(self):
        """Initialize the configuration handler."""
        self.user_config_repo = UserConfigRepository()
        self.trading_graphs = {}  # Local cache for trading graph instances
    
    def get_trading_graph(self, config: Dict[str, Any]) -> TradingAgentsGraph:
        """
        Get or create trading graph instance with proper caching.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            TradingAgentsGraph instance
        """
        config_key = str(hash(json.dumps(config, sort_keys=True)))
        
        if config_key not in self.trading_graphs:
            # Create new trading graph with config
            updated_config = DEFAULT_CONFIG.copy()
            updated_config.update(config)
            
            # Add unique identifier to avoid collection name conflicts
            updated_config["instance_id"] = f"{int(time.time() * 1000)}_{hash(config_key) % 10000}"
            
            # Pass analysts to TradingAgentsGraph constructor to ensure proper initialization
            analysts = config.get("analysts", ["market", "news", "fundamentals"])
            print(f"Creating trading graph with config: {updated_config}")
            
            self.trading_graphs[config_key] = TradingAgentsGraph(
                selected_analysts=analysts, 
                config=updated_config
            )
        
        return self.trading_graphs[config_key]
    
    def get_user_config_with_defaults(self, user_id: str) -> Dict[str, Any]:
        """
        Get user configuration with fallback to system defaults.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing user configuration with defaults
        """
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
        """
        Prepare configuration for analysis execution.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (analysis_config, user_config)
        """
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
        """
        Normalize Accept-Language header to supported language codes.
        
        Args:
            accept_language: Language string to normalize
            
        Returns:
            Normalized language code
        """
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
