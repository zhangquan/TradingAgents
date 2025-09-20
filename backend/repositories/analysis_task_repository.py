"""
Analysis Task Repository - 分析任务相关数据访问
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from .base import BaseRepository
from ..database.models import AnalysisTask

logger = logging.getLogger(__name__)


class AnalysisTaskRepository(BaseRepository[AnalysisTask]):
    """分析任务数据访问Repository"""
    
    def __init__(self):
        super().__init__(AnalysisTask)
    
    def create_analysis_task(self, task_data: Dict[str, Any]) -> str:
        """创建新的分析任务（立即或调度执行）"""
        try:
            with self._get_session() as db:
                task_id = task_data.get("task_id") or f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                
                task = AnalysisTask(
                    task_id=task_id,
                    user_id=task_data.get("user_id", "demo_user"),
                    ticker=task_data["ticker"],
                    analysis_date=task_data.get("analysis_date"),
                    analysts=task_data.get("analysts", []),
                    research_depth=task_data.get("research_depth", 1),
                    schedule_type=task_data.get("schedule_type", "immediate"),
                    schedule_time=task_data.get("schedule_time"),
                    schedule_date=task_data.get("schedule_date"),
                    cron_expression=task_data.get("cron_expression"),
                    status=task_data.get("status", "created"),
                    enabled=task_data.get("enabled", True),
                    progress=task_data.get("progress", 0),
                    current_step=task_data.get("current_step"),
                    result_data=task_data.get("result_data", {}),
                    trace=task_data.get("trace", [])
                )
                
                db.add(task)
                db.commit()
                db.refresh(task)
                
                logger.info(f"Created scheduled task: {task_id}")
                return task_id
                
        except Exception as e:
            logger.error(f"Error creating scheduled task: {e}")
            raise
    
    def get_analysis_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取调度任务"""
        try:
            with self._get_session() as db:
                task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
                
                if not task:
                    return None
                
                return self._to_dict(task)
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    def list_analysis_tasks(self, user_id: str = None, status: str = None, 
                           schedule_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """列出分析任务"""
        try:
            with self._get_session() as db:
                query = db.query(AnalysisTask)
                
                if user_id:
                    query = query.filter(AnalysisTask.user_id == user_id)
                if status:
                    query = query.filter(AnalysisTask.status == status)
                if schedule_type:
                    query = query.filter(AnalysisTask.schedule_type == schedule_type)
                
                tasks = query.order_by(desc(AnalysisTask.created_at)).limit(limit).all()
                
                return [self._to_dict(task) for task in tasks]
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return []
    


    def update_analysis_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新分析任务"""
        try:
            with self._get_session() as db:
                task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
                
                if task:
                    for key, value in updates.items():
                        if hasattr(task, key):
                            if key == "last_run" and isinstance(value, str):
                                setattr(task, key, datetime.fromisoformat(value))
                            elif key in ["started_at", "completed_at"] and isinstance(value, str):
                                setattr(task, key, datetime.fromisoformat(value))
                            else:
                                setattr(task, key, value)
                    
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating analysis task {task_id}: {e}")
            return False
    
    def update_analysis_task_status(self, task_id: str, status: str, **kwargs) -> bool:
        """更新分析任务状态和附加数据"""
        try:
            updates = {"status": status}
            
            # 处理时间戳更新
            if status == "running" and "started_at" not in kwargs:
                updates["started_at"] = datetime.now()
            elif status in ["completed", "failed", "error"] and "completed_at" not in kwargs:
                updates["completed_at"] = datetime.now()
            
            # 添加其他参数
            updates.update(kwargs)
            
            return self.update_analysis_task(task_id, updates)
        except Exception as e:
            logger.error(f"Error updating analysis task status {task_id}: {e}")
            return False
    
    def update_task_progress(self, task_id: str, progress: int, current_step: str = None) -> bool:
        """更新任务进度"""
        try:
            updates = {"progress": progress}
            if current_step:
                updates["current_step"] = current_step
            
            return self.update_analysis_task(task_id, updates)
        except Exception as e:
            logger.error(f"Error updating task progress {task_id}: {e}")
            return False
    
    def record_task_execution(self, task_id: str, result_data: Dict[str, Any] = None, 
                            error_message: str = None) -> bool:
        """记录任务执行结果"""
        try:
            with self._get_session() as db:
                task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
                
                if task:
                    task.last_run = datetime.now()
                    task.execution_count = (task.execution_count or 0) + 1
                    
                    if result_data:
                        task.result_data = result_data
                    
                    if error_message:
                        task.error_message = error_message
                        task.last_error = error_message
                    
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error recording task execution {task_id}: {e}")
            return False
    
    def delete_analysis_task(self, task_id: str) -> bool:
        """删除分析任务"""
        try:
            with self._get_session() as db:
                task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
                
                if task:
                    db.delete(task)
                    db.commit()
                    
                    logger.info(f"Deleted analysis task: {task_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting analysis task {task_id}: {e}")
            return False
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        return self.update_analysis_task(task_id, {"enabled": True})
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        return self.update_analysis_task(task_id, {"enabled": False})
    
    def toggle_task(self, task_id: str ) -> bool:
        """Toggle task status and additional data"""
       
        status = self.get_analysis_task(task_id)["enabled"]
        kwargs = {"enabled": not status}
        return self.update_analysis_task(task_id, kwargs)
    
    def get_tasks_by_ticker(self, ticker: str, user_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tasks filtered by ticker symbol and optionally by user"""
        try:
            with self._get_session() as db:
                query = db.query(AnalysisTask).filter(AnalysisTask.ticker == ticker.upper())
                
                if user_id:
                    query = query.filter(AnalysisTask.user_id == user_id)
                
                tasks = query.order_by(desc(AnalysisTask.created_at)).limit(limit).all()
                
                return [self._to_dict(task) for task in tasks]
        except Exception as e:
            logger.error(f"Error getting tasks for ticker {ticker}: {e}")
            return []
    
    def get_task_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            with self._get_session() as db:
                query = db.query(AnalysisTask)
                if user_id:
                    query = query.filter(AnalysisTask.user_id == user_id)
                
                from sqlalchemy import func
                stats = db.query(
                    AnalysisTask.status,
                    func.count(AnalysisTask.id).label('count')
                ).group_by(AnalysisTask.status)
                
                if user_id:
                    stats = stats.filter(AnalysisTask.user_id == user_id)
                
                status_counts = dict(stats.all())
                
                total_tasks = sum(status_counts.values())
                
                return {
                    "total_tasks": total_tasks,
                    "status_breakdown": status_counts,
                    "user_id": user_id
                }
        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {}
    
    def _to_dict(self, task: AnalysisTask) -> Dict[str, Any]:
        """将AnalysisTask模型转换为字典"""
        return {
            "task_id": task.task_id,
            "user_id": task.user_id,
            "ticker": task.ticker,
            "analysis_date": task.analysis_date,
            "analysts": task.analysts,
            "research_depth": task.research_depth,
            "schedule_type": task.schedule_type,
            "schedule_time": task.schedule_time,
            "schedule_date": task.schedule_date,
            "cron_expression": task.cron_expression,
            "status": task.status,
            "enabled": task.enabled,
            "progress": task.progress,
            "current_step": task.current_step,
            "result_data": task.result_data,
            "error_message": task.error_message,
            "trace": task.trace,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "execution_count": task.execution_count,
            "last_error": task.last_error,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None
        }
