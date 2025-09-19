"""
Watchlist Repository - 观察列表相关数据访问
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
import logging

from .base import BaseRepository
from ..database.models import Watchlist

logger = logging.getLogger(__name__)


class WatchlistRepository(BaseRepository[Watchlist]):
    """观察列表数据访问Repository"""
    
    def __init__(self, session_factory=None):
        super().__init__(Watchlist)
    
    def get_user_watchlist(self, user_id: str) -> List[str]:
        """获取用户观察列表的股票代码"""
        try:
            with self._get_session() as db:
                watchlist_items = db.query(Watchlist).filter(
                    Watchlist.user_id == user_id
                ).order_by(Watchlist.priority, Watchlist.ticker).all()
                
                return [item.ticker for item in watchlist_items]
        except Exception as e:
            logger.error(f"Error getting watchlist for user {user_id}: {e}")
            return []
    
    def get_user_watchlist_detailed(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户观察列表的详细信息"""
        try:
            with self._get_session() as db:
                watchlist_items = db.query(Watchlist).filter(
                    Watchlist.user_id == user_id
                ).order_by(Watchlist.priority, Watchlist.ticker).all()
                
                return [self._to_dict(item) for item in watchlist_items]
        except Exception as e:
            logger.error(f"Error getting detailed watchlist for user {user_id}: {e}")
            return []
    
    def add_to_watchlist(self, user_id: str, symbol: str, notes: str = None, 
                        priority: int = 1, alerts_enabled: bool = True) -> bool:
        """添加股票到用户观察列表"""
        try:
            with self._get_session() as db:
                symbol = symbol.upper()
                
                # 检查是否已存在
                existing = db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user_id, Watchlist.ticker == symbol)
                ).first()
                
                if existing:
                    return False  # 已在观察列表中
                
                # 创建新观察列表项
                watchlist_item = Watchlist(
                    user_id=user_id,
                    ticker=symbol,
                    added_date=datetime.now().strftime('%Y-%m-%d'),
                    notes=notes,
                    priority=priority,
                    alerts_enabled=alerts_enabled
                )
                
                db.add(watchlist_item)
                db.commit()
                
                logger.info(f"Added {symbol} to watchlist for user {user_id}")
                return True
                
        except IntegrityError:
            logger.warning(f"Symbol {symbol} already in watchlist for user {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error adding {symbol} to watchlist for user {user_id}: {e}")
            return False
    
    def remove_from_watchlist(self, user_id: str, symbol: str) -> bool:
        """从用户观察列表中移除股票"""
        try:
            with self._get_session() as db:
                symbol = symbol.upper()
                
                watchlist_item = db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user_id, Watchlist.ticker == symbol)
                ).first()
                
                if not watchlist_item:
                    return False  # 不在观察列表中
                
                db.delete(watchlist_item)
                db.commit()
                
                logger.info(f"Removed {symbol} from watchlist for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing {symbol} from watchlist for user {user_id}: {e}")
            return False
    
    def update_watchlist(self, user_id: str, symbols: List[str]) -> bool:
        """更新用户整个观察列表"""
        try:
            with self._get_session() as db:
                # 移除所有现有项
                db.query(Watchlist).filter(Watchlist.user_id == user_id).delete()
                
                # 添加新项
                symbols = list(set([symbol.upper() for symbol in symbols]))
                for symbol in sorted(symbols):
                    watchlist_item = Watchlist(
                        user_id=user_id,
                        ticker=symbol,
                        added_date=datetime.now().strftime('%Y-%m-%d'),
                        priority=1,  # 默认优先级
                        alerts_enabled=True
                    )
                    db.add(watchlist_item)
                
                db.commit()
                
                logger.info(f"Updated watchlist for user {user_id} with {len(symbols)} symbols")
                return True
                
        except Exception as e:
            logger.error(f"Error updating watchlist for user {user_id}: {e}")
            return False
    
    def update_watchlist_item(self, user_id: str, symbol: str, updates: Dict[str, Any]) -> bool:
        """更新特定观察列表项属性"""
        try:
            with self._get_session() as db:
                symbol = symbol.upper()
                
                watchlist_item = db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user_id, Watchlist.ticker == symbol)
                ).first()
                
                if not watchlist_item:
                    return False
                
                # 更新允许的字段
                allowed_fields = ['notes', 'priority', 'alerts_enabled']
                for key, value in updates.items():
                    if key in allowed_fields and hasattr(watchlist_item, key):
                        setattr(watchlist_item, key, value)
                
                db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating watchlist item {symbol} for user {user_id}: {e}")
            return False
    
    def is_symbol_in_watchlist(self, user_id: str, symbol: str) -> bool:
        """检查股票是否在用户观察列表中"""
        try:
            with self._get_session() as db:
                symbol = symbol.upper()
                
                exists = db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user_id, Watchlist.ticker == symbol)
                ).first() is not None
                
                return exists
                
        except Exception as e:
            logger.error(f"Error checking if {symbol} in watchlist for user {user_id}: {e}")
            return False
    
    def get_watchlist_count(self, user_id: str) -> int:
        """获取用户观察列表数量"""
        try:
            with self._get_session() as db:
                count = db.query(Watchlist).filter(Watchlist.user_id == user_id).count()
                return count
        except Exception as e:
            logger.error(f"Error getting watchlist count for user {user_id}: {e}")
            return 0
    
    def get_symbols_with_alerts(self, user_id: str = None) -> List[str]:
        """获取启用了警报的股票代码"""
        try:
            with self._get_session() as db:
                query = db.query(Watchlist.ticker).filter(Watchlist.alerts_enabled == True)
                
                if user_id:
                    query = query.filter(Watchlist.user_id == user_id)
                
                symbols = query.distinct().all()
                return [symbol[0] for symbol in symbols]
        except Exception as e:
            logger.error(f"Error getting symbols with alerts: {e}")
            return []
    
    def _to_dict(self, watchlist_item: Watchlist) -> Dict[str, Any]:
        """将Watchlist模型转换为字典"""
        return {
            "id": watchlist_item.id,
            "ticker": watchlist_item.ticker,
            "added_date": watchlist_item.added_date,
            "notes": watchlist_item.notes,
            "priority": watchlist_item.priority,
            "alerts_enabled": watchlist_item.alerts_enabled,
            "created_at": watchlist_item.created_at.isoformat() if watchlist_item.created_at else None,
            "updated_at": watchlist_item.updated_at.isoformat() if watchlist_item.updated_at else None
        }

