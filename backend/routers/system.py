from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import os
from datetime import datetime

from backend.database.storage_service import DatabaseStorage

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and storage
router = APIRouter(prefix="/system", tags=["system"])
storage = DatabaseStorage()

# Pydantic models for user preferences (not API keys)
class UserPreferencesRequest(BaseModel):
    llm_provider: Optional[str] = None
    backend_url: Optional[str] = None
    shallow_thinker: Optional[str] = None
    deep_thinker: Optional[str] = None
    default_research_depth: Optional[int] = None
    default_analysts: Optional[list] = None
    notification_settings: Optional[dict] = None
    # Language settings
    default_language: Optional[str] = None
    report_language: Optional[str] = None

@router.get("/config")
async def get_config():
    """Get current system configuration and status"""
    # Get user preferences from storage
    user_config = storage.get_user_config("demo_user")
    
    # Return system status and configuration (without sensitive API keys)
    config = {
        "system_status": {
            "api_keys_configured": {
                "finnhub": bool(os.getenv("FINNHUB_API_KEY")),
                "openai": bool(os.getenv("OPENAI_API_KEY")),
                "google": bool(os.getenv("GOOGLE_API_KEY")),
                "aliyun": bool(os.getenv("ALIYUN_API_KEY")),
                "polygon": bool(os.getenv("POLYGON_API_KEY")),
                "reddit": bool(os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"))
            },
            "data_sources_available": {
                "market_data": bool(os.getenv("POLYGON_API_KEY") or os.getenv("FINNHUB_API_KEY")),
                "news_data": bool(os.getenv("FINNHUB_API_KEY")),
                "social_data": bool(os.getenv("REDDIT_CLIENT_ID"))
            }
        },
        "user_preferences": user_config or {}
    }
    
    return config

@router.post("/preferences")
async def update_user_preferences(preferences: UserPreferencesRequest, request: Request):
    """Update user preferences (not API keys)"""
    try:
        # Update user preferences
        pref_updates = {}
        if preferences.llm_provider:
            pref_updates["llm_provider"] = preferences.llm_provider
        if preferences.backend_url:
            pref_updates["backend_url"] = preferences.backend_url
        if preferences.shallow_thinker:
            pref_updates["shallow_thinker"] = preferences.shallow_thinker
        if preferences.deep_thinker:
            pref_updates["deep_thinker"] = preferences.deep_thinker
        if preferences.default_research_depth:
            pref_updates["default_research_depth"] = preferences.default_research_depth
        if preferences.default_analysts:
            pref_updates["default_analysts"] = preferences.default_analysts
        if preferences.notification_settings:
            pref_updates["notification_settings"] = preferences.notification_settings
        if preferences.default_language:
            pref_updates["default_language"] = preferences.default_language
        if preferences.report_language:
            pref_updates["report_language"] = preferences.report_language
        
        # If no explicit language preferences are provided, try to use Accept-Language header
        if not preferences.default_language and not preferences.report_language:
            accept_language = request.headers.get("Accept-Language")
            if accept_language:
                # Import the language normalization function
                from backend.services.analysis_runner_service import AnalysisRunnerService
                runner_service = AnalysisRunnerService()
                normalized_language = runner_service._normalize_language(accept_language)
                pref_updates["default_language"] = normalized_language
                pref_updates["report_language"] = normalized_language
                logger.info(f"Auto-detected language from browser: {accept_language} -> {normalized_language}")
            
        # Save preferences to storage
        storage.save_user_config("demo_user", pref_updates)
        
        # Log system event
        storage.log_system_event("preferences_updated", {
            "updated_preferences": list(pref_updates.keys())
        })
            
        return {"message": "User preferences updated successfully", "updated": list(pref_updates.keys())}
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysts")
async def get_available_analysts():
    """Get list of available analyst types"""
    return {
        "analysts": [
            {"value": "market", "label": "Market Analyst"},
            {"value": "social", "label": "Social Media Analyst"},
            {"value": "news", "label": "News Analyst"},
            {"value": "fundamentals", "label": "Fundamentals Analyst"}
        ]
    }

@router.get("/models")
async def get_available_models():
    """Get list of available LLM models"""
    return {
        "openai": {
            "models": [
                "gpt-4o",
                "gpt-4o-mini", 
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ],
            "default_backend_url": "https://api.openai.com/v1"
        },
        "google": {
            "models": [
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ],
            "default_backend_url": "https://generativelanguage.googleapis.com/v1beta"
        },
        "aliyun": {
            "models": [
                "qwen-max",
                "qwen-plus",
                "qwen-turbo",
                "qwen3-235b-a22b-instruct-2507"
            ],
            "default_backend_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        }
    }

@router.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        stats = storage.get_storage_stats()
        
        # Add runtime stats by querying database
        active_tasks = storage.list_scheduled_tasks(status="running", limit=1000)
        completed_tasks = storage.list_scheduled_tasks(status="completed", limit=1000)
        
        stats["runtime"] = {
            "active_tasks": len(active_tasks),
            "completed_tasks": len(completed_tasks),
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_system_logs(date: str = None, event_type: str = None):
    """Get system logs"""
    try:
        logs = storage.get_system_logs(date, event_type)
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_system():
    """Cleanup expired cache and old logs"""
    try:
        storage.clear_expired_cache()
        
        # Clean up old completed tasks (older than 24 hours)
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Get old completed tasks
        old_tasks = storage.list_scheduled_tasks(status="completed", limit=1000)
        expired_tasks_count = 0
        
        for task in old_tasks:
            if task.get("completed_at"):
                from datetime import datetime
                completed_at = datetime.fromisoformat(task["completed_at"].replace('Z', '+00:00'))
                if completed_at < cutoff_time:
                    storage.delete_scheduled_task(task["task_id"])
                    expired_tasks_count += 1
        
        return {
            "message": "System cleanup completed",
            "expired_tasks_removed": expired_tasks_count
        }
    except Exception as e:
        logger.error(f"Error during system cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
