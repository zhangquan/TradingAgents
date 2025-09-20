"""
User Repository - 用户相关数据访问
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from .base import BaseRepository
from ..database.models import User, UserConfig

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """用户数据访问Repository"""
    
    def __init__(self):
        super().__init__(User)
    
    def create_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """创建用户"""
        try:
            with self._get_session() as db:
                # 检查用户是否已存在
                existing_user = db.query(User).filter(User.user_id == user_id).first()
                if existing_user:
                    return False
                
                # 创建新用户
                user = User(
                    user_id=user_id,
                    email=user_data.get("email"),
                    name=user_data.get("name"),
                    status=user_data.get("status", "active")
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                logger.info(f"Created user: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return False
    
    def get_user_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据user_id获取用户"""
        try:
            with self._get_session() as db:
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return None
                
                return self._to_dict(user)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """更新用户数据"""
        try:
            with self._get_session() as db:
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return False
                
                # 更新字段
                for key, value in updates.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    def list_users(self) -> List[Dict[str, Any]]:
        """列出所有用户"""
        try:
            with self._get_session() as db:
                users = db.query(User).order_by(User.created_at).all()
                return [self._to_dict(user) for user in users]
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        try:
            with self._get_session() as db:
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return False
                
                db.delete(user)
                db.commit()
                
                logger.info(f"Deleted user: {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def _to_dict(self, user: User) -> Dict[str, Any]:
        """将User模型转换为字典"""
        return {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }


class UserConfigRepository(BaseRepository[UserConfig]):
    """用户配置数据访问Repository"""
    
    def __init__(self):
        super().__init__(UserConfig)
    
    def save_user_config(self, user_id: str, config_data: Dict[str, Any]) -> bool:
        """保存用户配置"""
        try:
            with self._get_session() as db:
                user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
                
                if user_config:
                    # 更新现有配置
                    user_config.config_data = config_data
                else:
                    # 创建新配置
                    user_config = UserConfig(
                        user_id=user_id,
                        config_data=config_data
                    )
                    db.add(user_config)
                
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving user config for {user_id}: {e}")
            return False
    
    def get_user_config(self, user_id: str) -> Dict[str, Any]:
        """获取用户配置"""
        try:
            with self._get_session() as db:
                user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
                
                if user_config:
                    return user_config.config_data
                return {}
        except Exception as e:
            logger.error(f"Error getting user config for {user_id}: {e}")
            return {}
    
    def delete_user_config(self, user_id: str) -> bool:
        """删除用户配置"""
        try:
            with self._get_session() as db:
                user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
                if user_config:
                    db.delete(user_config)
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting user config for {user_id}: {e}")
            return False
