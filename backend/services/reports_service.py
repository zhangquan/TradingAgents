"""
Reports Service Layer for TradingAgents backend.
Handles all report-related business logic including creation, retrieval, 
updating, and deletion of trading analysis reports.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from backend.database.storage_service import DatabaseStorage

logger = logging.getLogger(__name__)


class ReportsService:
    """Service class for handling trading analysis reports operations"""
    
    def __init__(self):
        """Initialize reports service with database storage."""
        self.storage = DatabaseStorage()
    
    def _format_duration(self, duration_seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        if duration_seconds is None:
            return None
        
        if duration_seconds < 1:
            return f"{duration_seconds:.2f}s"
        elif duration_seconds < 60:
            return f"{duration_seconds:.1f}s"
        elif duration_seconds < 3600:
            minutes = int(duration_seconds // 60)
            seconds = duration_seconds % 60
            return f"{minutes}m {seconds:.1f}s"
        else:
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = duration_seconds % 60
            return f"{hours}h {minutes}m {seconds:.1f}s"
    
    # Core Report Management
    def create_unified_report(self, 
                             analysis_id: str, 
                             user_id: str, 
                             ticker: str, 
                             sections: Dict[str, str], 
                             title: str = None) -> str:
        """
        Create a unified report with multiple sections for an analysis.
        
        Args:
            analysis_id: ID of the related analysis
            user_id: User identifier
            ticker: Stock ticker symbol
            sections: Dictionary containing report sections (e.g., market_report, investment_plan)
            title: Optional custom title for the report
            
        Returns:
            str: Report ID of the created report
            
        Raises:
            Exception: If report creation fails
        """
        try:
            # Validate input parameters
            if not analysis_id or not user_id or not ticker:
                raise ValueError("analysis_id, user_id, and ticker are required")
            
            if not sections or not isinstance(sections, dict):
                raise ValueError("sections must be a non-empty dictionary")
            
            # Create the report through storage service
            report_id = self.storage.save_unified_report(
                analysis_id=analysis_id,
                user_id=user_id,
                ticker=ticker.upper(),
                sections=sections,
                title=title
            )
            
            # Log report creation
            self.storage.log_system_event("report_created", {
                "report_id": report_id,
                "analysis_id": analysis_id,
                "user_id": user_id,
                "ticker": ticker.upper(),
                "sections_count": len(sections),
                "title": title
            })
            
            logger.info(f"Created unified report {report_id} for analysis {analysis_id}")
            return report_id
            
        except Exception as e:
            logger.error(f"Error creating unified report for analysis {analysis_id}: {e}")
            raise
    
    def get_report_by_id(self, report_id: str, user_id: str = "demo_user") -> Optional[Dict[str, Any]]:
        """
        Get specific report by ID.
        
        Args:
            report_id: Report identifier
            user_id: User identifier
            
        Returns:
            dict: Report data or None if not found
        """
        try:
            if not report_id:
                raise ValueError("report_id is required")
            
            report = self.storage.get_report(user_id, report_id)
            
            if not report:
                logger.warning(f"Report {report_id} not found for user {user_id}")
                return None
            
            # Enhanced report data with computed fields
            enhanced_report = {
                **report,
                "report_type": "unified_analysis",  # All reports are now unified
                "sections_count": len(report.get("sections", {})) if report.get("sections") else 0,
                "has_investment_plan": "investment_plan" in report.get("sections", {}),
                "has_market_report": "market_report" in report.get("sections", {}),
                "has_trade_decision": "final_trade_decision" in report.get("sections", {}),
                # Execution timing information
                "execution_started_at": report.get("analysis_started_at"),
                "execution_completed_at": report.get("analysis_completed_at"),
                "execution_duration_seconds": report.get("analysis_duration_seconds"),
                "execution_duration_formatted": self._format_duration(report.get("analysis_duration_seconds"))
            }
            
            return enhanced_report
            
        except Exception as e:
            logger.error(f"Error getting report {report_id}: {e}")
            return None
    
    def list_reports(self, 
                    user_id: str = "demo_user", 
                    ticker: str = None, 
                    analysis_id: str = None,
                    watchlist_only: bool = False,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of reports with optional filters.
        
        Args:
            user_id: User identifier
            ticker: Optional ticker filter
            analysis_id: Optional analysis ID filter
            watchlist_only: Filter by user's watchlist (currently all reports are considered in watchlist)
            limit: Maximum number of reports to return
            
        Returns:
            list: List of report summaries
        """
        try:
            # Get reports from storage
            reports = self.storage.list_reports(
                user_id=user_id,
                ticker=ticker,
                analysis_id=analysis_id,
                limit=limit
            )
            
            # Enhance report data with additional fields
            enhanced_reports = []
            user_watchlist = self.storage.get_user_watchlist(user_id) if watchlist_only else None
            
            for report in reports:
                # Check if ticker is in watchlist (if filtering)
                if watchlist_only and user_watchlist and report["ticker"] not in user_watchlist:
                    continue
                
                enhanced_report = {
                    "report_id": report["report_id"],
                    "analysis_id": report["analysis_id"],
                    "ticker": report["ticker"],
                    "date": report["created_at"],
                    "report_type": "unified_analysis",  # All reports are unified
                    "title": report["title"],
                    "sections": report.get("sections", {}),
                    "sections_count": len(report.get("sections", {})) if report.get("sections") else 0,
                    "status": report["status"],
                    "created_at": report["created_at"],
                    "updated_at": report["updated_at"],
                    "in_watchlist": self.storage.is_symbol_in_watchlist(user_id, report["ticker"]),
                    # Additional computed fields
                    "has_investment_plan": "investment_plan" in report.get("sections", {}),
                    "has_market_report": "market_report" in report.get("sections", {}),
                    "has_trade_decision": "final_trade_decision" in report.get("sections", {}),
                    # Execution timing information
                    "execution_started_at": report.get("analysis_started_at"),
                    "execution_completed_at": report.get("analysis_completed_at"),
                    "execution_duration_seconds": report.get("analysis_duration_seconds"),
                    "execution_duration_formatted": self._format_duration(report.get("analysis_duration_seconds"))
                }
                
                enhanced_reports.append(enhanced_report)
            
            # Sort by creation date (newest first)
            enhanced_reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            logger.info(f"Retrieved {len(enhanced_reports)} reports for user {user_id}")
            return enhanced_reports
            
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            return []
    
    def get_reports_by_ticker(self, 
                             ticker: str, 
                             user_id: str = "demo_user",
                             limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all reports for a specific ticker symbol.
        
        Args:
            ticker: Stock ticker symbol
            user_id: User identifier
            limit: Maximum number of reports to return
            
        Returns:
            list: List of reports for the ticker
        """
        try:
            if not ticker:
                raise ValueError("ticker is required")
            
            # Get reports for the ticker
            reports = self.storage.list_reports(
                user_id=user_id,
                ticker=ticker.upper(),
                limit=limit
            )
            
            # Enhance report data
            enhanced_reports = []
            for report in reports:
                enhanced_report = {
                    "report_id": report["report_id"],
                    "analysis_id": report["analysis_id"],
                    "ticker": report["ticker"],
                    "date": report["created_at"],
                    "report_type": "unified_analysis",
                    "title": report["title"],
                    "sections": report["sections"],
                    "sections_count": len(report.get("sections", {})) if report.get("sections") else 0,
                    "status": report["status"],
                    "created_at": report["created_at"],
                    "updated_at": report["updated_at"],
                    "in_watchlist": self.storage.is_symbol_in_watchlist(user_id, report["ticker"]),
                    # Execution timing information
                    "execution_started_at": report.get("analysis_started_at"),
                    "execution_completed_at": report.get("analysis_completed_at"),
                    "execution_duration_seconds": report.get("analysis_duration_seconds"),
                    "execution_duration_formatted": self._format_duration(report.get("analysis_duration_seconds"))
                }
                enhanced_reports.append(enhanced_report)
            
            logger.info(f"Retrieved {len(enhanced_reports)} reports for ticker {ticker}")
            return enhanced_reports
            
        except Exception as e:
            logger.error(f"Error getting reports for ticker {ticker}: {e}")
            return []
    
    def delete_report(self, report_id: str, user_id: str = "demo_user") -> Dict[str, Any]:
        """
        Delete a specific report by ID.
        
        Args:
            report_id: Report identifier
            user_id: User identifier
            
        Returns:
            dict: Operation result with success status and details
        """
        try:
            if not report_id:
                raise ValueError("report_id is required")
            
            # Get report details before deletion
            report = self.storage.get_report(user_id, report_id)
            if not report:
                return {
                    "success": False,
                    "error": "Report not found",
                    "report_id": report_id
                }
            
            # Delete the report
            success = self.storage.delete_report(user_id, report_id)
            if not success:
                return {
                    "success": False,
                    "error": "Failed to delete report",
                    "report_id": report_id
                }
            
            # Log the deletion
            self.storage.log_system_event("report_deleted", {
                "user_id": user_id,
                "report_id": report_id,
                "analysis_id": report.get("analysis_id"),
                "ticker": report.get("ticker"),
                "title": report.get("title")
            })
            
            logger.info(f"Deleted report {report_id} for user {user_id}")
            
            return {
                "success": True,
                "message": f"Report {report_id} has been deleted",
                "report_id": report_id,
                "deleted_report": {
                    "ticker": report.get("ticker"),
                    "title": report.get("title"),
                    "analysis_id": report.get("analysis_id")
                }
            }
            
        except Exception as e:
            logger.error(f"Error deleting report {report_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "report_id": report_id
            }
    
    def batch_delete_reports(self, report_ids: List[str], user_id: str = "demo_user") -> Dict[str, Any]:
        """
        Delete multiple reports in batch.
        
        Args:
            report_ids: List of report identifiers
            user_id: User identifier
            
        Returns:
            dict: Batch operation results
        """
        try:
            if not report_ids:
                raise ValueError("report_ids list is required")
            
            results = []
            successful_deletions = 0
            
            for report_id in report_ids:
                try:
                    result = self.delete_report(report_id, user_id)
                    results.append({
                        "report_id": report_id,
                        "success": result["success"],
                        "message": result.get("message"),
                        "error": result.get("error")
                    })
                    
                    if result["success"]:
                        successful_deletions += 1
                        
                except Exception as e:
                    results.append({
                        "report_id": report_id,
                        "success": False,
                        "error": str(e)
                    })
            
            logger.info(f"Batch deleted {successful_deletions}/{len(report_ids)} reports for user {user_id}")
            
            return {
                "success": True,
                "message": f"Processed {len(report_ids)} reports: {successful_deletions} deleted successfully",
                "results": results,
                "total_processed": len(report_ids),
                "successful_deletions": successful_deletions,
                "failed_deletions": len(report_ids) - successful_deletions
            }
            
        except Exception as e:
            logger.error(f"Error in batch delete reports: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_processed": 0,
                "successful_deletions": 0
            }
    
    # Report Analytics and Statistics
    def get_report_statistics(self, user_id: str = "demo_user") -> Dict[str, Any]:
        """
        Get report statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: Report statistics
        """
        try:
            # Get all reports for user
            all_reports = self.storage.list_reports(user_id=user_id, limit=1000)
            
            # Calculate statistics
            total_reports = len(all_reports)
            tickers = set()
            reports_by_ticker = {}
            reports_by_month = {}
            section_counts = {
                "with_investment_plan": 0,
                "with_market_report": 0,
                "with_trade_decision": 0
            }
            
            for report in all_reports:
                ticker = report["ticker"]
                tickers.add(ticker)
                
                # Count by ticker
                reports_by_ticker[ticker] = reports_by_ticker.get(ticker, 0) + 1
                
                # Count by month
                if report["created_at"]:
                    month_key = report["created_at"][:7]  # YYYY-MM
                    reports_by_month[month_key] = reports_by_month.get(month_key, 0) + 1
                
                # Count sections
                sections = report.get("sections", {})
                if "investment_plan" in sections:
                    section_counts["with_investment_plan"] += 1
                if "market_report" in sections:
                    section_counts["with_market_report"] += 1
                if "final_trade_decision" in sections:
                    section_counts["with_trade_decision"] += 1
            
            # Find most analyzed ticker
            most_analyzed_ticker = max(reports_by_ticker.items(), key=lambda x: x[1]) if reports_by_ticker else ("", 0)
            
            statistics = {
                "total_reports": total_reports,
                "unique_tickers": len(tickers),
                "most_analyzed_ticker": {
                    "ticker": most_analyzed_ticker[0],
                    "count": most_analyzed_ticker[1]
                },
                "reports_by_ticker": dict(sorted(reports_by_ticker.items(), key=lambda x: x[1], reverse=True)),
                "reports_by_month": dict(sorted(reports_by_month.items())),
                "section_statistics": section_counts,
                "average_reports_per_ticker": round(total_reports / len(tickers), 2) if tickers else 0,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Generated report statistics for user {user_id}: {total_reports} reports, {len(tickers)} tickers")
            return statistics
            
        except Exception as e:
            logger.error(f"Error generating report statistics: {e}")
            return {
                "error": str(e),
                "total_reports": 0,
                "unique_tickers": 0
            }
    
    def get_recent_reports(self, user_id: str = "demo_user", days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent reports within specified days.
        
        Args:
            user_id: User identifier
            days: Number of days to look back
            limit: Maximum number of reports to return
            
        Returns:
            list: Recent reports
        """
        try:
            # Get all reports and filter by date
            all_reports = self.storage.list_reports(user_id=user_id, limit=limit * 2)  # Get more to filter
            
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Filter recent reports
            recent_reports = [
                report for report in all_reports
                if report.get("created_at", "") >= cutoff_date
            ]
            
            # Limit results
            recent_reports = recent_reports[:limit]
            
            # Enhance with additional fields
            for report in recent_reports:
                report["in_watchlist"] = self.storage.is_symbol_in_watchlist(user_id, report["ticker"])
                report["sections_count"] = len(report.get("sections", {}))
                # Add execution timing information
                report["execution_started_at"] = report.get("analysis_started_at")
                report["execution_completed_at"] = report.get("analysis_completed_at")
                report["execution_duration_seconds"] = report.get("analysis_duration_seconds")
                report["execution_duration_formatted"] = self._format_duration(report.get("analysis_duration_seconds"))
            
            logger.info(f"Retrieved {len(recent_reports)} recent reports for user {user_id} (last {days} days)")
            return recent_reports
            
        except Exception as e:
            logger.error(f"Error getting recent reports: {e}")
            return []
    
 

# Global service instance for easy access
reports_service = ReportsService()
