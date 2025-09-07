from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
from pathlib import Path

from backend.services.reports_service import reports_service

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/reports", tags=["reports"])

# Pydantic models
class ReportResponse(BaseModel):
    ticker: str
    date: str
    reports: Dict[str, Any]

class BatchDeleteRequest(BaseModel):
    analysis_ids: List[str]

class BatchDeleteReportsRequest(BaseModel):
    report_ids: List[str]

# API Endpoints
@router.get("")
async def list_reports(watchlist_only: bool = False, ticker: str = None, user_id: str = "demo_user"):
    """Get list of available reports, optionally filtered by watchlist or ticker"""
    try:
        # Use reports service to get reports with enhanced data
        reports = reports_service.list_reports(
            user_id=user_id,
            ticker=ticker,
            watchlist_only=watchlist_only,
            limit=100
        )
        
        return reports
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{report_id}")
async def get_report_by_id(report_id: str, user_id: str = "demo_user"):
    """Get specific report content by report ID"""
    try:
        # Use reports service to get enhanced report data
        report = reports_service.get_report_by_id(report_id, user_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ticker/{ticker}")
async def get_reports_by_ticker(ticker: str, limit: int = 50, user_id: str = "demo_user"):
    """Get all reports for a specific ticker symbol"""
    try:
        # Use reports service to get enhanced reports for ticker
        reports = reports_service.get_reports_by_ticker(
            ticker=ticker,
            user_id=user_id,
            limit=limit
        )
        
        return reports
    except Exception as e:
        logger.error(f"Error getting reports for ticker {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}")
async def delete_report(report_id: str, user_id: str = "demo_user"):
    """Delete a specific report by ID"""
    try:
        # Use reports service to delete report
        result = reports_service.delete_report(report_id, user_id)
        
        if not result["success"]:
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/batch/reports")
async def delete_multiple_reports(request: BatchDeleteReportsRequest, user_id: str = "demo_user"):
    """Delete multiple reports by report IDs"""
    try:
        # Use reports service for batch deletion
        result = reports_service.batch_delete_reports(request.report_ids, user_id)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Batch deletion failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch delete reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# New enhanced endpoints using ReportsService

@router.get("/statistics")
async def get_report_statistics(user_id: str = "demo_user"):
    """Get comprehensive report statistics for the user"""
    try:
        statistics = reports_service.get_report_statistics(user_id)
        return statistics
    except Exception as e:
        logger.error(f"Error getting report statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_reports(days: int = 7, limit: int = 20, user_id: str = "demo_user"):
    """Get recent reports within specified days"""
    try:
        if days <= 0 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
            
        recent_reports = reports_service.get_recent_reports(user_id, days, limit)
        return recent_reports
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recent reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CreateReportRequest(BaseModel):
    analysis_id: str
    ticker: str
    sections: Dict[str, str]
    title: str = None


@router.post("")
async def create_report(request: CreateReportRequest, user_id: str = "demo_user"):
    """Create a new unified report"""
    try:
        # Validate sections before creating
      
        
        # Create the report
        report_id = reports_service.create_unified_report(
            analysis_id=request.analysis_id,
            user_id=user_id,
            ticker=request.ticker,
            sections=request.sections,
            title=request.title
        )
        
        # Get the created report
        created_report = reports_service.get_report_by_id(report_id, user_id)
        
        return {
            "success": True,
            "message": f"Report {report_id} created successfully",
            "report_id": report_id,
            "report": created_report,

        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ValidateReportRequest(BaseModel):
    sections: Dict[str, str]


