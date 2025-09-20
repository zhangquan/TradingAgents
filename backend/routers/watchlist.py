from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from backend.repositories import WatchlistRepository
from backend.services.analysis_services import analysis_service
from backend.services.scheduler_service import scheduler_service

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and storage
router = APIRouter(prefix="/watchlist", tags=["watchlist"])
watchlist_repo = WatchlistRepository()

# Pydantic models
class WatchlistItemRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    notes: Optional[str] = Field(None, description="Optional notes about the stock")
    priority: int = Field(1, ge=1, le=5, description="Priority level (1=highest, 5=lowest)")
    alerts_enabled: bool = Field(True, description="Whether to enable alerts for this stock")

class WatchlistItemUpdate(BaseModel):
    notes: Optional[str] = Field(None, description="Optional notes about the stock")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority level (1=highest, 5=lowest)")
    alerts_enabled: Optional[bool] = Field(None, description="Whether to enable alerts for this stock")

class BulkWatchlistRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of ticker symbols")

class WatchlistResponse(BaseModel):
    id: str
    ticker: str
    added_date: Optional[str]
    notes: Optional[str]
    priority: int
    alerts_enabled: bool
    created_at: Optional[str]
    updated_at: Optional[str]

# API Endpoints
@router.get("", response_model=List[str])
async def get_watchlist(user_id: str = "demo_user"):
    """Get user's watchlist ticker symbols"""
    try:
        watchlist = watchlist_repo.get_user_watchlist(user_id)
        return watchlist
    except Exception as e:
        logger.error(f"Error getting watchlist for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detailed", response_model=List[WatchlistResponse])
async def get_watchlist_detailed(user_id: str = "demo_user"):
    """Get user's watchlist with detailed information"""
    try:
        watchlist = watchlist_repo.get_user_watchlist_detailed(user_id)
        return watchlist
    except Exception as e:
        logger.error(f"Error getting detailed watchlist for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
async def add_to_watchlist(item: WatchlistItemRequest, user_id: str = "demo_user"):
    """Add a stock to user's watchlist and create analysis task"""
    try:
        # Step 1: Add to watchlist
        success = watchlist_repo.add_to_watchlist(
            user_id=user_id,
            symbol=item.ticker,
            notes=item.notes,
            priority=item.priority,
            alerts_enabled=item.alerts_enabled
        )
        
        if not success:
            raise HTTPException(
                status_code=409, 
                detail=f"Stock {item.ticker} is already in watchlist"
            )
        
        # Step 2: Create analysis task for the new stock (without immediate execution)
        analysis_task_info = None
        analysis_error = None
        
        try:
            # Get user config for default analysts and research depth
            user_config = analysis_service.get_user_config_with_defaults(user_id)
            
            # Create analysis task (stored but not executed)
            task_data = analysis_service.create_analysis_task(
                ticker=item.ticker,
                analysts=user_config.get("default_analysts", ["market", "news", "fundamentals"]),
                research_depth=user_config.get("default_research_depth", 1),
                schedule_type="daily",
                schedule_time="09:00",  # Daily at 9 AM
                timezone="UTC",
                enabled=True,
                user_id=user_id
            )
            
            # Add the task to scheduler service
            scheduler_success = scheduler_service.add_task_to_scheduler(task_data["task_id"])
            if scheduler_success:
                # Update task status to scheduled
                analysis_service.update_analysis_task_status(task_data["task_id"], "scheduled")
                analysis_task_info = {
                    "task_id": task_data["task_id"],
                    "status": "scheduled"
                }
            else:
                # If scheduler failed, update status to error
                analysis_service.update_analysis_task_status(task_data["task_id"], "error", 
                                                            error="Failed to add to scheduler")
                analysis_task_info = {
                    "task_id": task_data["task_id"],
                    "status": "error",
                    "error": "Failed to add to scheduler"
                }
            
            logger.info(f"Created and scheduled analysis task for {item.ticker}: {task_data['task_id']}")
            
        except Exception as analysis_exception:
            # Log the error but don't fail the watchlist addition
            analysis_error = str(analysis_exception)
            logger.warning(f"Failed to create analysis task for {item.ticker}: {analysis_error}")
        
        # Step 3: Return response with both watchlist and analysis task status
        response = {
            "success": True,
            "message": f"Added {item.ticker} to watchlist",
            "ticker": item.ticker.upper(),
            "analysis_task": analysis_task_info
        }
        
        if analysis_error:
            response["analysis_task_error"] = analysis_error
            response["message"] += " (analysis task creation failed)"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding {item.ticker} to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{ticker}")
async def remove_from_watchlist(ticker: str, user_id: str = "demo_user"):
    """Remove a stock from user's watchlist and delete related analysis tasks"""
    try:
        # Step 1: Remove from watchlist
        success = watchlist_repo.remove_from_watchlist(user_id, ticker)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Stock {ticker} not found in watchlist"
            )
        
        # Step 2: Find and delete related analysis tasks
        deleted_tasks = []
        task_deletion_errors = []
        
        try:
            # Get all scheduled tasks for this user and ticker
            all_tasks = analysis_service.list_analysis_tasks(user_id=user_id, limit=1000)
            related_tasks = [task for task in all_tasks if task.get("ticker", "").upper() == ticker.upper()]
            
            for task in related_tasks:
                task_id = task.get("task_id")
                if task_id:
                    try:
                        # Delete from scheduler first
                        scheduler_deleted = scheduler_service.delete_analysis_task(task_id)
                        # Delete from storage
                        storage_deleted = analysis_service.delete_analysis_task(task_id)
                        
                        if scheduler_deleted and storage_deleted:
                            deleted_tasks.append({
                                "task_id": task_id,
                                "status": "deleted"
                            })
                            logger.info(f"Deleted analysis task {task_id} for {ticker}")
                        else:
                            task_deletion_errors.append({
                                "task_id": task_id,
                                "error": "Failed to delete from scheduler or storage"
                            })
                    except Exception as task_error:
                        task_deletion_errors.append({
                            "task_id": task_id,
                            "error": str(task_error)
                        })
                        logger.warning(f"Failed to delete task {task_id}: {task_error}")
            
        except Exception as task_search_error:
            logger.warning(f"Failed to search for related tasks for {ticker}: {task_search_error}")
            task_deletion_errors.append({
                "error": f"Failed to search for related tasks: {str(task_search_error)}"
            })
        
        # Step 3: Prepare response
        response = {
            "success": True,
            "message": f"Removed {ticker} from watchlist",
            "ticker": ticker.upper(),
            "deleted_tasks": deleted_tasks
        }
        
        if task_deletion_errors:
            response["task_deletion_errors"] = task_deletion_errors
            response["message"] += f" (with {len(task_deletion_errors)} task deletion errors)"
        else:
            response["message"] += f" and deleted {len(deleted_tasks)} related analysis tasks"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing {ticker} from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{ticker}")
async def update_watchlist_item(ticker: str, updates: WatchlistItemUpdate, user_id: str = "demo_user"):
    """Update a watchlist item's properties"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        success = watchlist_repo.update_watchlist_item(user_id, ticker, update_data)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Stock {ticker} not found in watchlist"
            )
        
        return {
            "success": True,
            "message": f"Updated {ticker} in watchlist",
            "ticker": ticker.upper(),
            "updated_fields": list(update_data.keys())
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating {ticker} in watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk/add")
async def add_bulk_to_watchlist(request: BulkWatchlistRequest, user_id: str = "demo_user"):
    """Add multiple stocks to user's watchlist and create analysis tasks"""
    try:
        results = []
        user_config = analysis_service.get_user_config_with_defaults(user_id)
        
        for ticker in request.tickers:
            try:
                success = watchlist_repo.add_to_watchlist(user_id, ticker)
                result = {
                    "ticker": ticker.upper(),
                    "success": success,
                    "message": "Added successfully" if success else "Already in watchlist"
                }
                
                # If watchlist addition was successful, create analysis task
                if success:
                    try:
                        # Create analysis task
                        task_data = analysis_service.create_analysis_task(
                            ticker=ticker,
                            analysts=user_config.get("default_analysts", ["market", "news", "fundamentals"]),
                            research_depth=user_config.get("default_research_depth", 1),
                            schedule_type="daily",
                            schedule_time="09:00",  # Daily at 9 AM
                            timezone="UTC",
                            enabled=True,
                            user_id=user_id
                        )
                        
                        # Add the task to scheduler service
                        scheduler_success = scheduler_service.add_task_to_scheduler(task_data["task_id"])
                        if scheduler_success:
                            # Update task status to scheduled
                            analysis_service.update_analysis_task_status(task_data["task_id"], "scheduled")
                            result["analysis_task"] = {
                                "task_id": task_data["task_id"],
                                "status": "scheduled"
                            }
                        else:
                            # If scheduler failed, update status to error
                            analysis_service.update_analysis_task_status(task_data["task_id"], "error", 
                                                                        error="Failed to add to scheduler")
                            result["analysis_task"] = {
                                "task_id": task_data["task_id"],
                                "status": "error",
                                "error": "Failed to add to scheduler"
                            }
                        
                    except Exception as analysis_exception:
                        result["analysis_task_error"] = str(analysis_exception)
                        logger.warning(f"Failed to create analysis task for {ticker}: {analysis_exception}")
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    "ticker": ticker.upper(),
                    "success": False,
                    "error": str(e)
                })
        
        successful_count = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "message": f"Processed {len(request.tickers)} stocks: {successful_count} added successfully",
            "results": results,
            "total_processed": len(request.tickers),
            "successful_additions": successful_count
        }
    except Exception as e:
        logger.error(f"Error in bulk add to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/bulk/replace")
async def replace_watchlist(request: BulkWatchlistRequest, user_id: str = "demo_user"):
    """Replace user's entire watchlist"""
    try:
        success = watchlist_repo.update_watchlist(user_id, request.tickers)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update watchlist")
        
        return {
            "success": True,
            "message": f"Watchlist updated with {len(request.tickers)} stocks",
            "tickers": [ticker.upper() for ticker in request.tickers],
            "count": len(request.tickers)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replacing watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}/check")
async def check_in_watchlist(ticker: str, user_id: str = "demo_user"):
    """Check if a stock is in user's watchlist"""
    try:
        in_watchlist = watchlist_repo.is_symbol_in_watchlist(user_id, ticker)
        
        return {
            "ticker": ticker.upper(),
            "in_watchlist": in_watchlist,
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error checking {ticker} in watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/priority/{priority}")
async def get_watchlist_by_priority(priority: int, user_id: str = "demo_user"):
    """Get watchlist items by priority level"""
    try:
        if priority < 1 or priority > 5:
            raise HTTPException(status_code=400, detail="Priority must be between 1 and 5")
        
        detailed_watchlist = watchlist_repo.get_user_watchlist_detailed(user_id)
        filtered_items = [item for item in detailed_watchlist if item["priority"] == priority]
        
        return {
            "priority": priority,
            "count": len(filtered_items),
            "items": filtered_items
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting watchlist by priority {priority}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
