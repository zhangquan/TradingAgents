"""
Yahoo Finance 数据获取工具类
提供与PolygonUtils相同接口的Yahoo Finance数据获取功能
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Annotated, Optional, Dict, Any
import logging
from pathlib import Path
import yfinance as yf

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YahooDataUtils:
    """Yahoo Finance 数据获取工具类"""
    
    def __init__(self, require_api_key: bool = False):
        """
        初始化Yahoo Finance工具
        
        Args:
            require_api_key (bool): Yahoo Finance不需要API密钥，此参数仅为接口兼容性保留
        """
        self.require_api_key = require_api_key
        logger.info("YahooDataUtils初始化成功")
    
    def get_stock_data_online(
        self,
        symbol: Annotated[str, "ticker symbol"],
        start_date: Annotated[str, "start date for retrieving stock price data, YYYY-mm-dd"],
        end_date: Annotated[str, "end date for retrieving stock price data, YYYY-mm-dd"],
    ) -> pd.DataFrame:
        """
        使用Yahoo Finance获取股票价格数据
        
        Args:
            symbol (str): 股票代码 (e.g., 'AAPL', 'TSLA')
            start_date (str): 开始日期 YYYY-mm-dd 格式
            end_date (str): 结束日期 YYYY-mm-dd 格式
            
        Returns:
            pd.DataFrame: 股票价格数据，包含列: Open, High, Low, Close, Volume, VWAP, Transactions
        """
        try:
            # 转换日期为datetime对象
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # 验证日期范围
            if start_dt > end_dt:
                raise ValueError(f"Start date ({start_date}) cannot be after end date ({end_date})")
            
            # 获取股票数据
            ticker = yf.Ticker(symbol.upper())
            
            # Yahoo Finance的end_date是排他的，需要加1天
            end_date_inclusive = (end_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            
            data = ticker.history(
                start=start_date,
                end=end_date_inclusive,
                auto_adjust=True,
                back_adjust=True,
                prepost=True,
                threads=True
            )
            
            if data.empty:
                logger.warning(f"No data found for symbol '{symbol}' between {start_date} and {end_date}")
                return pd.DataFrame()
            
            # 重命名列以匹配Polygon格式
            data = data.rename(columns={
                'Open': 'Open',
                'High': 'High', 
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            
            # 添加VWAP和Transactions列（Yahoo Finance不直接提供）
            data['VWAP'] = ((data['High'] + data['Low'] + data['Close']) / 3).round(2)
            data['Transactions'] = 0  # Yahoo Finance不提供交易次数
            
            # 确保索引是日期格式
            if not isinstance(data.index, pd.DatetimeIndex):
                data.index = pd.to_datetime(data.index)
            
            # 四舍五入数值列
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'VWAP']
            for col in numeric_columns:
                if col in data.columns:
                    data[col] = data[col].round(2)
            
            # 确保Volume是整数
            if 'Volume' in data.columns:
                data['Volume'] = data['Volume'].astype(int)
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {str(e)}")
            raise
    
    def get_stock_data_window_online(
        self,
        symbol: Annotated[str, "ticker symbol of the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"],
    ) -> pd.DataFrame:
        """
        获取指定窗口期的股票数据
        
        Args:
            symbol (str): 股票代码
            curr_date (str): 当前日期 yyyy-mm-dd 格式
            look_back_days (int): 回看天数
            
        Returns:
            pd.DataFrame: 指定窗口期的股票数据
        """
        # 计算开始日期
        curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_dt = curr_dt - timedelta(days=look_back_days)
        
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = curr_date
        
        # 验证计算的日期范围
        if start_dt > curr_dt:
            raise ValueError(f"Invalid look_back_days ({look_back_days}): results in start date after current date")
        
        return self.get_stock_data_online(symbol, start_date, end_date)
    
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
        try:
            # 验证输入日期
            requested_start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            requested_end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            if requested_start_dt > requested_end_dt:
                raise ValueError(f"Start date ({start_date}) cannot be after end date ({end_date})")
            
            cache_file_path = self._get_cache_file_path(symbol)
            cached_data = self._load_cached_data(cache_file_path)
            
            # 确定需要获取的数据范围
            fetch_ranges = []
            final_data = cached_data.copy() if cached_data is not None and not cached_data.empty else pd.DataFrame()
            
            if cached_data is None or cached_data.empty:
                # 没有缓存，需要获取所有数据
                if extend_cache:
                    # 扩展日期范围以缓存更多历史数据
                    extended_start = requested_start_dt - timedelta(days=365)  # 获取1年历史数据
                    extended_end = datetime.now()  # Yahoo Finance支持当前日数据
                    if extended_end >= extended_start:
                        fetch_ranges.append((extended_start, extended_end))
                else:
                    fetch_ranges.append((requested_start_dt, requested_end_dt))
                logger.info(f"No cache found for {symbol}, will fetch new data")
            else:
                cached_start = cached_data.index.min()
                cached_end = cached_data.index.max()
                
                # 检查缓存是否覆盖请求范围且不过期
                cache_valid = self._is_cache_valid(cached_data, start_date, end_date, max_cache_age_days)
                
                if cache_valid:
                    logger.info(f"Using cached data for {symbol}")
                else:
                    # 计算需要获取的数据范围
                    target_start = requested_start_dt
                    target_end = requested_end_dt
                    
                    if extend_cache:
                        # 扩展范围以获得更好的未来覆盖
                        target_start = min(requested_start_dt, requested_start_dt - timedelta(days=365))
                        target_end = max(requested_end_dt, datetime.now())
                    
                    # 添加缓存中缺失的范围
                    if target_start < cached_start:
                        before_end = cached_start - timedelta(days=1)
                        if target_start <= before_end:
                            fetch_ranges.append((target_start, before_end))
                    
                    if target_end > cached_end:
                        after_start = cached_end + timedelta(days=1)
                        if after_start <= target_end:
                            fetch_ranges.append((after_start, target_end))
                    
                    # 检查缓存是否过期（需要刷新最近数据）
                    if (datetime.now() - cached_end).days > max_cache_age_days:
                        refresh_start = max(cached_end - timedelta(days=max_cache_age_days), cached_start)
                        refresh_end = datetime.now()
                        if refresh_end > refresh_start:
                            fetch_ranges.append((refresh_start, refresh_end))
            
            # 获取缺失的数据范围
            api_fetch_success = False
            if extend_cache:
                for fetch_start, fetch_end in fetch_ranges:
                    if fetch_start > fetch_end:
                        logger.warning(f"Skipping invalid date range for {symbol}: start ({fetch_start}) > end ({fetch_end})")
                        continue
                    
                    fetch_start_str = fetch_start.strftime("%Y-%m-%d")
                    fetch_end_str = fetch_end.strftime("%Y-%m-%d")
                    
                    logger.info(f"Fetching Yahoo Finance data for {symbol} from {fetch_start_str} to {fetch_end_str}")
                    try:
                        api_data = self.get_stock_data_online(symbol, fetch_start_str, fetch_end_str)
                        
                        if not api_data.empty:
                            if final_data.empty:
                                final_data = api_data
                            else:
                                # 合并新数据与现有缓存，去除重复
                                combined_data = pd.concat([final_data, api_data])
                                final_data = combined_data[~combined_data.index.duplicated(keep='last')].sort_index()
                            api_fetch_success = True
                        else:
                            logger.warning(f"No data returned for {symbol} from {fetch_start_str} to {fetch_end_str}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to fetch new data for {symbol} from {fetch_start_str} to {fetch_end_str}: {str(e)}")
                        if not final_data.empty:
                            logger.info(f"Using existing cached data for {symbol} due to API fetch failure")
                        else:
                            logger.error(f"No cached data available and API fetch failed for {symbol}")
            else:
                logger.info(f"extend_cache=False for {symbol}, using cached data only")
            
            # 如果成功获取新数据则保存更新的缓存
            if api_fetch_success and not final_data.empty:
                self._save_cached_data(final_data, cache_file_path)
                logger.info(f"Updated cache for {symbol} with new data")
            
            # 过滤请求日期范围的数据
            if final_data.empty:
                logger.warning(f"No data available for symbol '{symbol}' between {start_date} and {end_date}")
                return pd.DataFrame()
            
            filtered_data = final_data[
                (final_data.index >= requested_start_dt) & (final_data.index <= requested_end_dt)
            ]
            
            if filtered_data.empty:
                logger.warning(f"No data found for symbol '{symbol}' between {start_date} and {end_date}")
                if not final_data.empty:
                    logger.info(f"Returning available cached data for {symbol} outside requested range")
                    return final_data
                return pd.DataFrame()
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error fetching cached Yahoo Finance data for {symbol}: {str(e)}")
            raise
    
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
        # 计算开始日期
        curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_dt = curr_dt - timedelta(days=look_back_days)
        
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = curr_date
        
        # 验证计算的日期范围
        if start_dt > curr_dt:
            raise ValueError(f"Invalid look_back_days ({look_back_days}): results in start date after current date")
        
        return self.get_stock_data_cached(
            symbol, start_date, end_date, extend_cache, max_cache_age_days
        )
    
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
        try:
            ticker = yf.Ticker(symbol.upper())
            info = ticker.info
            
            return {
                "Company Name": info.get("longName", info.get("shortName", "N/A")),
                "Industry": info.get("industry", "N/A"),
                "Sector": info.get("sector", "N/A"),
                "Country": info.get("country", "N/A"),
                "Website": info.get("website", "N/A"),
                "Market Cap": info.get("marketCap", "N/A"),
                "Employees": info.get("fullTimeEmployees", "N/A"),
                "Description": info.get("longBusinessSummary", "N/A"),
            }
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
            return {
                "Company Name": "N/A",
                "Industry": "N/A",
                "Sector": "N/A",
                "Country": "N/A",
                "Website": "N/A",
                "Market Cap": "N/A",
                "Employees": "N/A",
                "Description": "N/A",
            }
    
    def get_company_info(
        self,
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取公司信息并返回DataFrame
        
        Args:
            symbol (str): 股票代码
            save_path (str, optional): 保存路径
            
        Returns:
            pd.DataFrame: 公司信息
        """
        info = self.get_stock_info(symbol)
        company_info_df = pd.DataFrame([info])
        
        if save_path:
            company_info_df.to_csv(save_path)
            logger.info(f"Company info for {symbol} saved to {save_path}")
        
        return company_info_df
    
    def _get_cache_file_path(self, symbol: str) -> str:
        """获取缓存文件路径"""
        try:
            from .config import get_config
            config = get_config()
            cache_dir = config["data_cache_dir"]
            os.makedirs(cache_dir, exist_ok=True)
            return os.path.join(cache_dir, f"{symbol.upper()}-Yahoo-data.csv")
        except Exception as e:
            logger.error(f"Error getting cache file path: {str(e)}")
            # 回退到默认目录
            cache_dir = "tradingagents/dataflows/data_cache"
            os.makedirs(cache_dir, exist_ok=True)
            return os.path.join(cache_dir, f"{symbol.upper()}-Yahoo-data.csv")
    
    def _load_cached_data(self, cache_file_path: str) -> Optional[pd.DataFrame]:
        """从文件加载缓存数据"""
        if not os.path.exists(cache_file_path):
            return None
            
        try:
            cached_data = pd.read_csv(cache_file_path)
            cached_data["Date"] = pd.to_datetime(cached_data["Date"])
            cached_data = cached_data.set_index("Date")
            return cached_data
        except Exception as e:
            logger.warning(f"Could not load cached data from {cache_file_path}: {e}")
            return None
    
    def _save_cached_data(self, data: pd.DataFrame, cache_file_path: str) -> None:
        """保存数据到缓存文件"""
        try:
            data_to_save = data.reset_index()
            data_to_save.to_csv(cache_file_path, index=False)
            logger.info(f"Data saved to cache: {cache_file_path}")
        except Exception as e:
            logger.error(f"Error saving data to cache {cache_file_path}: {str(e)}")
    
    def _is_cache_valid(self, cached_data: pd.DataFrame, start_date: str, end_date: str, max_age_days: int = 7) -> bool:
        """检查缓存数据是否有效"""
        if cached_data is None or cached_data.empty:
            return False
            
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 检查缓存数据是否覆盖请求的日期范围
        cached_start = cached_data.index.min()
        cached_end = cached_data.index.max()
        
        if cached_start > start_dt or cached_end < end_dt:
            return False
            
        # 检查数据是否足够新（结束日期在max_age_days内）
        if (datetime.now() - cached_end).days > max_age_days:
            return False
            
        return True
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """清除缓存文件"""
        try:
            if symbol:
                cache_file_path = self._get_cache_file_path(symbol)
                if os.path.exists(cache_file_path):
                    os.remove(cache_file_path)
                    logger.info(f"Cache cleared for {symbol}")
            else:
                from .config import get_config
                config = get_config()
                cache_dir = config["data_cache_dir"]
                if os.path.exists(cache_dir):
                    for file in os.listdir(cache_dir):
                        if file.endswith("-Yahoo-data.csv"):
                            os.remove(os.path.join(cache_dir, file))
                    logger.info("All Yahoo Finance cache files cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    
    def get_cache_info(self, symbol: str) -> dict:
        """获取符号的缓存信息"""
        try:
            cache_file_path = self._get_cache_file_path(symbol)
            
            if not os.path.exists(cache_file_path):
                return {"exists": False, "path": cache_file_path}
            
            cached_data = self._load_cached_data(cache_file_path)
            if cached_data is None or cached_data.empty:
                return {"exists": False, "path": cache_file_path}
            
            file_stats = os.stat(cache_file_path)
            
            return {
                "exists": True,
                "path": cache_file_path,
                "start_date": cached_data.index.min().strftime("%Y-%m-%d"),
                "end_date": cached_data.index.max().strftime("%Y-%m-%d"),
                "record_count": len(cached_data),
                "file_size_bytes": file_stats.st_size,
                "last_modified": datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info for {symbol}: {str(e)}")
            return {"exists": False, "error": str(e)}