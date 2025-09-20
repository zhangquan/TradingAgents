"""
Cache Repository - 缓存相关数据访问
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from .base import BaseRepository
from ..database.models import CacheEntry

logger = logging.getLogger(__name__)


class CacheRepository(BaseRepository[CacheEntry]):
    """缓存数据访问Repository"""
    
    def __init__(self):
        super().__init__(CacheEntry)
    
    def save_cache(self, cache_key: str, data: Any, ttl_hours: int = 24) -> bool:
        """保存缓存数据"""
        try:
            with self._get_session() as db:
                expires_at = datetime.now() + timedelta(hours=ttl_hours)
                
                cache_entry = db.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()
                
                if cache_entry:
                    # 更新现有缓存
                    cache_entry.data = data
                    cache_entry.expires_at = expires_at
                    cache_entry.created_at = datetime.now()  # 重置创建时间
                else:
                    # 创建新缓存条目
                    cache_entry = CacheEntry(
                        cache_key=cache_key,
                        data=data,
                        expires_at=expires_at
                    )
                    db.add(cache_entry)
                
                db.commit()
                logger.debug(f"Saved cache: {cache_key} (TTL: {ttl_hours}h)")
                return True
        except Exception as e:
            logger.error(f"Error saving cache {cache_key}: {e}")
            return False
    
    def get_cache(self, cache_key: str) -> Optional[Any]:
        """获取缓存数据（如果未过期）"""
        try:
            with self._get_session() as db:
                cache_entry = db.query(CacheEntry).filter(
                    and_(
                        CacheEntry.cache_key == cache_key,
                        CacheEntry.expires_at > datetime.now()
                    )
                ).first()
                
                if cache_entry:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cache_entry.data
                else:
                    logger.debug(f"Cache miss: {cache_key}")
                    return None
        except Exception as e:
            logger.error(f"Error getting cache {cache_key}: {e}")
            return None
    
    def delete_cache(self, cache_key: str) -> bool:
        """删除指定缓存"""
        try:
            with self._get_session() as db:
                cache_entry = db.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()
                if cache_entry:
                    db.delete(cache_entry)
                    db.commit()
                    logger.debug(f"Deleted cache: {cache_key}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting cache {cache_key}: {e}")
            return False
    
    def clear_expired_cache(self) -> int:
        """清理所有过期的缓存条目"""
        try:
            with self._get_session() as db:
                expired_entries = db.query(CacheEntry).filter(
                    CacheEntry.expires_at <= datetime.now()
                ).all()
                
                count = len(expired_entries)
                for entry in expired_entries:
                    db.delete(entry)
                
                db.commit()
                logger.info(f"Cleared {count} expired cache entries")
                return count
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return 0
    
    def clear_cache_by_pattern(self, pattern: str) -> int:
        """根据模式清理缓存（简单字符串包含匹配）"""
        try:
            with self._get_session() as db:
                matching_entries = db.query(CacheEntry).filter(
                    CacheEntry.cache_key.contains(pattern)
                ).all()
                
                count = len(matching_entries)
                for entry in matching_entries:
                    db.delete(entry)
                
                db.commit()
                logger.info(f"Cleared {count} cache entries matching pattern: {pattern}")
                return count
        except Exception as e:
            logger.error(f"Error clearing cache by pattern {pattern}: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            with self._get_session() as db:
                total_count = db.query(CacheEntry).count()
                expired_count = db.query(CacheEntry).filter(
                    CacheEntry.expires_at <= datetime.now()
                ).count()
                valid_count = total_count - expired_count
                
                return {
                    "total_entries": total_count,
                    "valid_entries": valid_count,
                    "expired_entries": expired_count,
                    "hit_rate": None  # 需要额外统计才能计算命中率
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def list_cache_keys(self, pattern: str = None, valid_only: bool = True) -> List[str]:
        """列出缓存键"""
        try:
            with self._get_session() as db:
                query = db.query(CacheEntry.cache_key)
                
                if valid_only:
                    query = query.filter(CacheEntry.expires_at > datetime.now())
                
                if pattern:
                    query = query.filter(CacheEntry.cache_key.contains(pattern))
                
                cache_keys = query.all()
                return [key[0] for key in cache_keys]
        except Exception as e:
            logger.error(f"Error listing cache keys: {e}")
            return []
    
    def extend_cache_ttl(self, cache_key: str, additional_hours: int = 24) -> bool:
        """延长缓存TTL"""
        try:
            with self._get_session() as db:
                cache_entry = db.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()
                if cache_entry:
                    cache_entry.expires_at += timedelta(hours=additional_hours)
                    db.commit()
                    logger.debug(f"Extended cache TTL: {cache_key} (+{additional_hours}h)")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error extending cache TTL {cache_key}: {e}")
            return False
    
    def _to_dict(self, cache_entry: CacheEntry) -> Dict[str, Any]:
        """将CacheEntry模型转换为字典"""
        return {
            "cache_key": cache_entry.cache_key,
            "data": cache_entry.data,
            "created_at": cache_entry.created_at.isoformat() if cache_entry.created_at else None,
            "expires_at": cache_entry.expires_at.isoformat() if cache_entry.expires_at else None,
            "is_expired": cache_entry.expires_at <= datetime.now() if cache_entry.expires_at else True
        }
