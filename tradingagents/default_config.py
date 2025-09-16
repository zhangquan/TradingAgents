import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.getenv("TRADINGAGENTS_DATA_DIR", "./data"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": os.getenv("LLM_PROVIDER", "aliyun"),
    "deep_think_llm": os.getenv("DEEP_THINK_LLM", "qwen3-235b-a22b-instruct-2507"),
    "quick_think_llm": os.getenv("QUICK_THINK_LLM", "qwen-plus"),
    "backend_url": os.getenv("LLM_BACKEND_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    # Debate and discussion settings
    "max_debate_rounds": int(os.getenv("MAX_DEBATE_ROUNDS", "1")),
    "max_risk_discuss_rounds": int(os.getenv("MAX_RISK_DISCUSS_ROUNDS", "1")),
    "max_recur_limit": int(os.getenv("MAX_RECUR_LIMIT", "100")),
    # Tool settings
    "online_tools": os.getenv("ONLINE_TOOLS", "true").lower() == "true",
    # Language settings
    "default_language": os.getenv("DEFAULT_LANGUAGE", "en-US"),
    "report_language": os.getenv("REPORT_LANGUAGE", "auto"),  # auto, en-US, zh-CN, etc.
    # Environment and Data Source Configuration
    "environment": os.getenv("ENVIRONMENT", "development"),
    "data_source": os.getenv("DATA_SOURCE", ""),  # Empty means auto-detect based on environment
    "require_api_key": os.getenv("REQUIRE_API_KEY", "false").lower() == "true",
    
    # API Keys - all loaded from environment variables
    "api_keys": {
        "polygon": os.getenv("POLYGON_API_KEY", ""),
        "finnhub": os.getenv("FINNHUB_API_KEY", ""),
        "openai": os.getenv("OPENAI_API_KEY", ""),
        "google": os.getenv("GOOGLE_API_KEY", ""),
        "aliyun": os.getenv("ALIYUN_API_KEY", ""),
        "reddit_client_id": os.getenv("REDDIT_CLIENT_ID", ""),
        "reddit_client_secret": os.getenv("REDDIT_CLIENT_SECRET", ""),
    },
    # Legacy support - will be deprecated
    "polygon_api_key": os.getenv("POLYGON_API_KEY", ""),
}
