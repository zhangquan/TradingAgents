"""
Config Repository - 配置相关数据访问
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from .base import BaseRepository
from ..database.models import SystemConfig, UserConfig

logger = logging.getLogger(__name__)


class SystemConfigRepository(BaseRepository[SystemConfig]):
    """系统配置数据访问Repository"""
    
    def __init__(self, session_factory=None):
        super().__init__(SystemConfig)
    
    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """保存系统配置"""
        try:
            with self._get_session() as db:
                config = db.query(SystemConfig).filter(SystemConfig.config_name == config_name).first()
                
                if config:
                    # 更新现有配置
                    config.config_data = config_data
                    config.updated_at = datetime.now()
                else:
                    # 创建新配置
                    config = SystemConfig(
                        config_name=config_name,
                        config_data=config_data
                    )
                    db.add(config)
                
                db.commit()
                logger.info(f"Saved system config: {config_name}")
                return True
        except Exception as e:
            logger.error(f"Error saving config {config_name}: {e}")
            return False
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """获取系统配置"""
        try:
            with self._get_session() as db:
                config = db.query(SystemConfig).filter(SystemConfig.config_name == config_name).first()
                
                if config:
                    return config.config_data
                return {}
        except Exception as e:
            logger.error(f"Error getting config {config_name}: {e}")
            return {}
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """列出所有系统配置"""
        try:
            with self._get_session() as db:
                configs = db.query(SystemConfig).all()
                return [self._to_dict(config) for config in configs]
        except Exception as e:
            logger.error(f"Error listing configs: {e}")
            return []
    
    def delete_config(self, config_name: str) -> bool:
        """删除系统配置"""
        try:
            with self._get_session() as db:
                config = db.query(SystemConfig).filter(SystemConfig.config_name == config_name).first()
                if config:
                    db.delete(config)
                    db.commit()
                    logger.info(f"Deleted system config: {config_name}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting config {config_name}: {e}")
            return False
    
    def _to_dict(self, config: SystemConfig) -> Dict[str, Any]:
        """将SystemConfig模型转换为字典"""
        return {
            "config_name": config.config_name,
            "config_data": config.config_data,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }


class ConfigRepository:
    """配置Repository统一入口"""
    
    def __init__(self, session_factory):
        self.system_config = SystemConfigRepository(session_factory)
        # UserConfig通过UserRepository访问，保持一致性

