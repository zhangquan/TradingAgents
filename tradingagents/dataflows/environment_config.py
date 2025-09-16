"""
环境配置模块
根据环境变量控制数据源选择：正式环境使用Yahoo Finance，开发环境使用Polygon API
"""

import os
from typing import Dict, Any
from enum import Enum

class Environment(Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class DataSource(Enum):
    """数据源类型枚举"""
    YAHOO_FINANCE = "yahoo_finance"
    POLYGON = "polygon"

class EnvironmentConfig:
    """环境配置管理器"""
    
    def __init__(self):
        self._environment = self._detect_environment()
        self._data_source = self._get_data_source_for_environment()
    
    def _detect_environment(self) -> Environment:
        """检测当前环境"""
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        
        if env_str in ["production", "prod", "pro"]:
            return Environment.PRODUCTION
        elif env_str in ["development", "dev"]:
            return Environment.DEVELOPMENT
        else:
            # 默认根据其他环境变量判断
            if os.getenv("NODE_ENV") == "production":
                return Environment.PRODUCTION
            return Environment.DEVELOPMENT
    
    def _get_data_source_for_environment(self) -> DataSource:
        """根据环境获取数据源"""
        # 允许通过环境变量强制指定数据源
        data_source_override = os.getenv("DATA_SOURCE", "").lower()
        
        if data_source_override in ["yahoo", "yahoo_finance", "yfinance"]:
            return DataSource.YAHOO_FINANCE
        elif data_source_override in ["polygon", "polygon_api"]:
            return DataSource.POLYGON
        
        # 根据环境自动选择
        if self._environment == Environment.PRODUCTION:
            return DataSource.YAHOO_FINANCE
        else:
            return DataSource.POLYGON
    
    @property
    def environment(self) -> Environment:
        """获取当前环境"""
        return self._environment
    
    @property
    def data_source(self) -> DataSource:
        """获取当前数据源"""
        return self._data_source
    
    @property
    def is_production(self) -> bool:
        """是否为正式环境"""
        return self._environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self._environment == Environment.DEVELOPMENT
    
    @property
    def use_yahoo_finance(self) -> bool:
        """是否使用Yahoo Finance"""
        return self._data_source == DataSource.YAHOO_FINANCE
    
    @property
    def use_polygon(self) -> bool:
        """是否使用Polygon API"""
        return self._data_source == DataSource.POLYGON
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return {
            "environment": self._environment.value,
            "data_source": self._data_source.value,
            "is_production": self.is_production,
            "is_development": self.is_development,
            "use_yahoo_finance": self.use_yahoo_finance,
            "use_polygon": self.use_polygon,
            "api_keys": {
                "polygon": os.getenv("POLYGON_API_KEY", ""),
                "yahoo_finance": "N/A",  # Yahoo Finance不需要API密钥
            }
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"EnvironmentConfig(env={self._environment.value}, data_source={self._data_source.value})"

# 全局配置实例
env_config = None

def get_environment_config() -> EnvironmentConfig:
    """获取环境配置实例"""
    global env_config
    if env_config is None:
        env_config = EnvironmentConfig()
    return env_config

def reset_environment_config():
    """重置环境配置实例（用于测试）"""
    global env_config
    env_config = None