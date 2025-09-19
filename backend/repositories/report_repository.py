"""
Report Repository - 报告相关数据访问
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from .base import BaseRepository
from ..database.models import Report, ConversationState

logger = logging.getLogger(__name__)


class ReportRepository(BaseRepository[Report]):
    """报告数据访问Repository"""
    
    def __init__(self, session_factory=None):
        super().__init__(Report)
    
    def save_unified_report(self, analysis_id: str, user_id: str, ticker: str, sections: Dict[str, str], 
                           title: str = None, session_id: str = None,
                           analysis_started_at: datetime = None, analysis_completed_at: datetime = None, 
                           analysis_duration_seconds: float = None) -> str:
        """保存统一报告"""
        try:
            with self._get_session() as db:
                # 检查报告是否已存在
                existing_report = db.query(Report).filter(
                    and_(Report.analysis_id == analysis_id, Report.user_id == user_id)
                ).first()
                
                if existing_report:
                    # 更新现有报告
                    existing_report.sections = sections
                    existing_report.title = title or existing_report.title
                    if session_id:
                        existing_report.session_id = session_id
                    if analysis_started_at:
                        existing_report.analysis_started_at = analysis_started_at
                    if analysis_completed_at:
                        existing_report.analysis_completed_at = analysis_completed_at
                    if analysis_duration_seconds is not None:
                        existing_report.analysis_duration_seconds = analysis_duration_seconds
                    existing_report.updated_at = datetime.now()
                    db.commit()
                    logger.info(f"Updated unified report: {existing_report.report_id} for analysis {analysis_id}")
                    return existing_report.report_id
                else:
                    # 生成报告ID
                    report_id = f"report_{ticker}_{analysis_id.split('_')[-1]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    # 创建新统一报告记录
                    report = Report(
                        report_id=report_id,
                        analysis_id=analysis_id,
                        user_id=user_id,
                        ticker=ticker.upper(),
                        title=title or f"{ticker.upper()} Complete Analysis Report",
                        sections=sections,
                        session_id=session_id,
                        analysis_started_at=analysis_started_at,
                        analysis_completed_at=analysis_completed_at,
                        analysis_duration_seconds=analysis_duration_seconds,
                        status="generated"
                    )
                    
                    db.add(report)
                    db.commit()
                    db.refresh(report)
                    
                    logger.info(f"Saved unified report: {report_id} for analysis {analysis_id}")
                    return report_id
                
        except Exception as e:
            logger.error(f"Error saving unified report for analysis {analysis_id}: {e}")
            raise
    
    def get_report(self, user_id: str, report_id: str) -> Optional[Dict[str, Any]]:
        """获取指定报告"""
        try:
            with self._get_session() as db:
                report = db.query(Report).filter(
                    and_(Report.user_id == user_id, Report.report_id == report_id)
                ).first()
                
                if not report:
                    return None
                
                return self._to_dict(report)
        except Exception as e:
            logger.error(f"Error getting report {report_id}: {e}")
            return None
    
    def get_report_by_analysis_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """根据分析ID获取报告"""
        try:
            with self._get_session() as db:
                report = db.query(Report).filter(Report.analysis_id == analysis_id).first()
                if not report:
                    return None
                return self._to_dict(report)
        except Exception as e:
            logger.error(f"Error getting report by analysis_id {analysis_id}: {e}")
            return None
    
    def list_reports(self, user_id: str, ticker: str = None, analysis_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """列出报告"""
        try:
            with self._get_session() as db:
                # 关联ConversationState获取execution_type
                query = db.query(Report, ConversationState.execution_type).outerjoin(
                    ConversationState, Report.session_id == ConversationState.session_id
                ).filter(Report.user_id == user_id)
                
                if ticker:
                    query = query.filter(Report.ticker == ticker.upper())
                if analysis_id:
                    query = query.filter(Report.analysis_id == analysis_id)

                results = query.order_by(desc(Report.created_at)).limit(limit).all()
                
                return [
                    self._to_dict_with_execution_type(report, execution_type)
                    for report, execution_type in results
                ]
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            return []
    
    def list_reports_by_ticker(self, user_id: str, ticker: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取特定股票的所有报告"""
        try:
            with self._get_session() as db:
                reports = db.query(Report).filter(
                    and_(Report.user_id == user_id, Report.ticker == ticker.upper())
                ).order_by(desc(Report.created_at)).limit(limit).all()
                
                return [self._to_dict(report) for report in reports]
        except Exception as e:
            logger.error(f"Error listing reports for ticker {ticker}: {e}")
            return []
    
    def update_report(self, report_id: str, updates: Dict[str, Any]) -> bool:
        """更新报告"""
        try:
            with self._get_session() as db:
                report = db.query(Report).filter(Report.report_id == report_id).first()
                if not report:
                    return False
                
                # 更新字段
                for key, value in updates.items():
                    if hasattr(report, key):
                        if key in ["analysis_started_at", "analysis_completed_at"] and isinstance(value, str):
                            try:
                                setattr(report, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                            except ValueError:
                                continue
                        else:
                            setattr(report, key, value)
                
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating report {report_id}: {e}")
            return False
    
    def delete_report(self, user_id: str, report_id: str) -> bool:
        """删除报告"""
        try:
            with self._get_session() as db:
                report = db.query(Report).filter(
                    and_(Report.user_id == user_id, Report.report_id == report_id)
                ).first()
                
                if not report:
                    return False
                
                db.delete(report)
                db.commit()
                
                logger.info(f"Deleted report {report_id} for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting report {report_id}: {e}")
            return False
    
    def get_reports_by_session_id(self, session_id: str) -> List[Dict[str, Any]]:
        """根据会话ID获取报告"""
        try:
            with self._get_session() as db:
                reports = db.query(Report).filter(Report.session_id == session_id).all()
                return [self._to_dict(report) for report in reports]
        except Exception as e:
            logger.error(f"Error getting reports by session_id {session_id}: {e}")
            return []
    
    def _to_dict(self, report: Report) -> Dict[str, Any]:
        """将Report模型转换为字典"""
        return {
            "report_id": report.report_id,
            "session_id": report.session_id,
            "analysis_id": report.analysis_id,
            "user_id": report.user_id,
            "ticker": report.ticker,
            "title": report.title,
            "sections": report.sections,
            "status": report.status,
            "analysis_started_at": report.analysis_started_at.isoformat() + 'Z' if report.analysis_started_at else None,
            "analysis_completed_at": report.analysis_completed_at.isoformat() + 'Z' if report.analysis_completed_at else None,
            "analysis_duration_seconds": report.analysis_duration_seconds,
            "created_at": report.created_at.isoformat() + 'Z' if report.created_at else None,
            "updated_at": report.updated_at.isoformat() + 'Z' if report.updated_at else None,
            # 向后兼容字段
            "report_type": "unified_analysis",
            "content": report.sections  # 将sections映射到content以保持向后兼容
        }
    
    def _to_dict_with_execution_type(self, report: Report, execution_type: str = None) -> Dict[str, Any]:
        """将Report模型转换为字典，包含execution_type"""
        result = self._to_dict(report)
        result["execution_type"] = execution_type or "manual"
        return result
