"""
数据源管理器
根据环境配置自动选择合适的数据源（Yahoo Finance 或 Polygon API）
"""

import logging
from typing import Optional, Union, Annotated
import pandas as pd
from datetime import datetime, timedelta

from .environment_config import get_environment_config, DataSource
from .polygon_utils import PolygonUtils
from .yahoo_data_utils import YahooDataUtils

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSourceManager:
    """数据源管理器，根据环境自动选择数据源"""
    
    def __init__(self, require_api_key: bool = False):
        """
        初始化数据源管理器
        
        Args:
            require_api_key (bool): 是否需要API密钥
        """
        self.require_api_key = require_api_key
        self.env_config = get_environment_config()
        
        # 初始化数据源
        self._polygon_utils = None
        self._yahoo_utils = None
        self._current_data_source = None
        
        self._initialize_data_sources()
        
        logger.info(f"DataSourceManager initialized: {self.env_config}")
    
    def _initialize_data_sources(self):
        """初始化数据源"""
        try:
            if self.env_config.use_polygon:
                self._polygon_utils = PolygonUtils(require_api_key=self.require_api_key)
                self._current_data_source = DataSource.POLYGON
                logger.info("Polygon API data source initialized")
            elif self.env_config.use_yahoo_finance:
                self._yahoo_utils = YahooDataUtils(require_api_key=False)  # Yahoo不需要API密钥
                self._current_data_source = DataSource.YAHOO_FINANCE
                logger.info("Yahoo Finance data source initialized")
            else:
                raise ValueError("No valid data source configured")
        except Exception as e:
            logger.error(f"Failed to initialize data sources: {e}")
            # 尝试回退到Yahoo Finance
            try:
                self._yahoo_utils = YahooDataUtils(require_api_key=False)
                self._current_data_source = DataSource.YAHOO_FINANCE
                logger.warning(f"Fell back to Yahoo Finance due to initialization error: {e}")
            except Exception as fallback_error:
                logger.error(f"Failed to initialize fallback data source: {fallback_error}")
                raise
    
    @property
    def current_data_source(self) -> DataSource:
        """获取当前使用的数据源"""
        return self._current_data_source
    
    @property
    def is_using_polygon(self) -> bool:
        """是否使用Polygon API"""
        return self._current_data_source == DataSource.POLYGON
    
    @property
    def is_using_yahoo_finance(self) -> bool:
        """是否使用Yahoo Finance"""
        return self._current_data_source == DataSource.YAHOO_FINANCE
    
    def get_stock_data_online(
        self,
        symbol: Annotated[str, "ticker symbol"],
        start_date: Annotated[str, "start date for retrieving stock price data, YYYY-mm-dd"],
        end_date: Annotated[str, "end date for retrieving stock price data, YYYY-mm-dd"],
    ) -> pd.DataFrame:
        """
        获取股票数据（在线）
        
        Args:
            symbol (str): 股票代码
            start_date (str): 开始日期 YYYY-mm-dd 格式
            end_date (str): 结束日期 YYYY-mm-dd 格式
            
        Returns:
            pd.DataFrame: 股票价格数据
        """
        if self.is_using_polygon and self._polygon_utils:
            return self._polygon_utils.get_stock_data_online(symbol, start_date, end_date)
        elif self.is_using_yahoo_finance and self._yahoo_utils:
            return self._yahoo_utils.get_stock_data_online(symbol, start_date, end_date)
        else:
            raise ValueError("No valid data source available")
    
    def get_stock_data_window_online(
        self,
        symbol: Annotated[str, "ticker symbol of the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"],
    ) -> pd.DataFrame:
        """
        获取指定窗口期的股票数据（在线）
        
        Args:
            symbol (str): 股票代码
            curr_date (str): 当前日期 yyyy-mm-dd 格式
            look_back_days (int): 回看天数
            
        Returns:
            pd.DataFrame: 指定窗口期的股票数据
        """
        if self.is_using_polygon and self._polygon_utils:
            return self._polygon_utils.get_stock_data_window_online(symbol, curr_date, look_back_days)
        elif self.is_using_yahoo_finance and self._yahoo_utils:
            return self._yahoo_utils.get_stock_data_window_online(symbol, curr_date, look_back_days)
        else:
            raise ValueError("No valid data source available")
    
    def get_stock_data_cached(
        self,
        symbol: Annotated[str, "ticker symbol"],
        start_date: Annotated[str, "start date for retrieving stock price data, YYYY-mm-dd"],
        end_date: Annotated[str, "end date for retrieving stock price data, YYYY-mm-dd"],
        extend_cache: Annotated[bool, "whether to extend cache with additional historical data"] = True,
        max_cache_age_days: Annotated[int, "maximum age of cached data in days"] = 7,
    ) -> pd.DataFrame:
        """
        获取带缓存的股票数据
        
        Args:
            symbol (str): 股票代码
            start_date (str): 开始日期 YYYY-mm-dd 格式
            end_date (str): 结束日期 YYYY-mm-dd 格式
            extend_cache (bool): 是否扩展缓存
            max_cache_age_days (int): 缓存数据最大年龄（天）
            
        Returns:
            pd.DataFrame: 股票价格数据
        """
        if self.is_using_polygon and self._polygon_utils:
            return self._polygon_utils.get_stock_data_cached(
                symbol, start_date, end_date, extend_cache, max_cache_age_days
            )
        elif self.is_using_yahoo_finance and self._yahoo_utils:
            return self._yahoo_utils.get_stock_data_cached(
                symbol, start_date, end_date, extend_cache, max_cache_age_days
            )
        else:
            raise ValueError("No valid data source available")
    
    def get_stock_data_window_cached(
        self,
        symbol: Annotated[str, "ticker symbol of the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"],
        extend_cache: Annotated[bool, "whether to extend cache with additional historical data"] = True,
        max_cache_age_days: Annotated[int, "maximum age of cached data in days"] = 7,
    ) -> pd.DataFrame:
        """
        获取指定窗口期的股票数据（带缓存）
        
        Args:
            symbol (str): 股票代码
            curr_date (str): 当前日期 yyyy-mm-dd 格式
            look_back_days (int): 回看天数
            extend_cache (bool): 是否扩展缓存
            max_cache_age_days (int): 缓存数据最大年龄（天）
            
        Returns:
            pd.DataFrame: 指定窗口期的股票数据
        """
        if self.is_using_polygon and self._polygon_utils:
            return self._polygon_utils.get_stock_data_window_cached(
                symbol, curr_date, look_back_days, extend_cache, max_cache_age_days
            )
        elif self.is_using_yahoo_finance and self._yahoo_utils:
            return self._yahoo_utils.get_stock_data_window_cached(
                symbol, curr_date, look_back_days, extend_cache, max_cache_age_days
            )
        else:
            raise ValueError("No valid data source available")
    
    def get_stock_info(
        self,
        symbol: Annotated[str, "ticker symbol"],
    ) -> dict:
        """
        获取股票信息
        
        Args:
            symbol (str): 股票代码
            
        Returns:
            dict: 股票信息
        """
        if self.is_using_polygon and self._polygon_utils:
            return self._polygon_utils.get_stock_info(symbol)
        elif self.is_using_yahoo_finance and self._yahoo_utils:
            return self._yahoo_utils.get_stock_info(symbol)
        else:
            raise ValueError("No valid data source available")
    
    def get_company_info(
        self,
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取公司信息
        
        Args:
            symbol (str): 股票代码
            save_path (str, optional): 保存路径
            
        Returns:
            pd.DataFrame: 公司信息
        """
        if self.is_using_polygon and self._polygon_utils:
            return self._polygon_utils.get_company_info(symbol, save_path)
        elif self.is_using_yahoo_finance and self._yahoo_utils:
            return self._yahoo_utils.get_company_info(symbol, save_path)
        else:
            raise ValueError("No valid data source available")
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """清除缓存"""
        if self.is_using_polygon and self._polygon_utils:
            self._polygon_utils.clear_cache(symbol)
        elif self.is_using_yahoo_finance and self._yahoo_utils:
            self._yahoo_utils.clear_cache(symbol)
        else:
            logger.warning("No valid data source available for cache clearing")
    
    def get_cache_info(self, symbol: str) -> dict:
        """获取缓存信息"""
        if self.is_using_polygon and self._polygon_utils:
            return self._polygon_utils.get_cache_info(symbol)
        elif self.is_using_yahoo_finance and self._yahoo_utils:
            return self._yahoo_utils.get_cache_info(symbol)
        else:
            return {"exists": False, "error": "No valid data source available"}
    
    def get_status(self) -> dict:
        """获取数据源状态"""
        return {
            "current_data_source": self._current_data_source.value if self._current_data_source else None,
            "environment": self.env_config.environment.value,
            "is_production": self.env_config.is_production,
            "is_development": self.env_config.is_development,
            "polygon_available": self._polygon_utils is not None,
            "yahoo_finance_available": self._yahoo_utils is not None,
            "config": self.env_config.get_config()
        }