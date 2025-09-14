"""
数据服务模块
提供股票数据获取、缓存管理和技术指标计算功能
使用 Polygon.io 作为数据源，支持智能缓存机制
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Annotated
import logging
import json
from pathlib import Path

# 导入项目内部模块
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tradingagents.dataflows.polygon_utils import PolygonUtils
from tradingagents.dataflows.stockstats_polygon_utils import StockstatsPolygonUtils

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataServices:
    """
    数据服务类，提供股票数据获取和技术指标计算功能
    """
    
    def __init__(self, require_api_key: bool = False):
        """
        初始化数据服务
        
        Args:
            require_api_key (bool): 是否需要API密钥，False时仅使用缓存数据
        """
        self.require_api_key = require_api_key
        
        # 初始化PolygonUtils
        try:
            self.polygon_utils = PolygonUtils(require_api_key=require_api_key)
            logger.info(f"PolygonUtils初始化成功，require_api_key={require_api_key}")
        except Exception as e:
            logger.warning(f"初始化PolygonUtils失败: {e}")
            self.polygon_utils = None
        
        # 初始化StockstatsPolygonUtils
        self.stockstats_utils = StockstatsPolygonUtils()
        
        # 支持的技术指标列表
        self.supported_indicators = {
            # 移动平均线
            "close_50_sma": "50日简单移动平均线",
            "close_200_sma": "200日简单移动平均线", 
            "close_10_ema": "10日指数移动平均线",
            "close_20_ema": "20日指数移动平均线",
            
            # MACD指标
            "macd": "MACD指标",
            "macds": "MACD信号线",
            "macdh": "MACD柱状图",
            
            # 动量指标
            "rsi": "相对强弱指数",
            "rsi_6": "6日RSI",
            "rsi_14": "14日RSI",
            
            # 布林带
            "boll": "布林带中轨",
            "boll_ub": "布林带上轨",
            "boll_lb": "布林带下轨",
            
          
        }
    
    def get_available_stocks(self) -> List[str]:
        """
        获取缓存中可用的股票列表
        
        Returns:
            List[str]: 可用股票代码列表
        """
        try:
            return sorted(['TSLA','AAPL','NVDA',"CRCL"])
        except Exception as e:
            logger.error(f"获取可用股票列表失败: {str(e)}")
            return []
    
    
    
    def get_stock_data_window(
        self,
        symbol: Annotated[str, "股票代码"],
        curr_date: Annotated[str, "当前日期 YYYY-MM-DD"],
        look_back_days: Annotated[int, "回看天数"],
    ) -> pd.DataFrame:
        """
        获取指定窗口期的股票数据
        
        Args:
            symbol (str): 股票代码
            curr_date (str): 当前日期
            look_back_days (int): 回看天数
            
        Returns:
            pd.DataFrame: 股票数据
        """
        try:
            return self.get_stock_data_window_cached(symbol, curr_date, look_back_days)
        except Exception as e:
            logger.error(f"获取窗口期股票数据失败 {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_stock_data_window_cached(
        self,
        symbol: Annotated[str, "股票代码"],
        curr_date: Annotated[str, "当前日期 YYYY-MM-DD"],
        look_back_days: Annotated[int, "回看天数"],
    ) -> pd.DataFrame:
        """
        从缓存获取指定窗口期的股票数据
        
        Args:
            symbol (str): 股票代码
            curr_date (str): 当前日期
            look_back_days (int): 回看天数
            
        Returns:
            pd.DataFrame: 股票数据
        """
        try:
            if self.polygon_utils is None:
                logger.warning("PolygonUtils未初始化，无法获取数据")
                return pd.DataFrame()
            
            # 使用 PolygonUtils 获取窗口期数据（完全使用缓存，不联网）
            data = self.polygon_utils.get_stock_data_window_cached(
                symbol=symbol,
                curr_date=curr_date,
                look_back_days=look_back_days,
                extend_cache=False  # 不扩展缓存，仅使用现有缓存数据
            )
            
            return data
        except Exception as e:
            logger.error(f"从缓存获取窗口期股票数据失败 {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def calculate_technical_indicator(
        self,
        symbol: Annotated[str, "股票代码"],
        indicator: Annotated[str, "技术指标名称"],
        curr_date: Annotated[str, "当前日期 YYYY-MM-DD"],
        look_back_days: Annotated[int, "回看天数"] = 100,
        return_format: Annotated[str, "返回格式 'dataframe' 或 'string'"] = "dataframe"
    ) -> Union[pd.DataFrame, str]:
        """
        计算技术指标
        
        Args:
            symbol (str): 股票代码
            indicator (str): 技术指标名称
            curr_date (str): 当前日期
            look_back_days (int): 回看天数
            return_format (str): 返回格式，'dataframe' 返回数据框，'string' 返回格式化字符串
            
        Returns:
            Union[pd.DataFrame, str]: 根据return_format返回数据框或格式化字符串
        """
        if indicator not in self.supported_indicators:
            raise ValueError(f"不支持的指标: {indicator}。支持的指标: {list(self.supported_indicators.keys())}")
        
        try:
            # 直接使用 StockstatsPolygonUtils 计算指标
            result_df = self.stockstats_utils.get_stock_stats_window(
                symbol=symbol,
                indicator=indicator,
                curr_date=curr_date,
                look_back_days=look_back_days,
                extend_cache=False

            )
            
            return result_df
                
        except Exception as e:
            logger.error(f"计算技术指标失败 {symbol} {indicator}: {str(e)}")
            raise e
            
    
    def get_multiple_indicators(
        self,
        symbol: Annotated[str, "股票代码"],
        indicators: Annotated[List[str], "技术指标列表"],
        curr_date: Annotated[str, "当前日期 YYYY-MM-DD"],
        look_back_days: Annotated[int, "回看天数"] = 100,
        return_format: Annotated[str, "返回格式 'dataframe' 或 'string'"] = "dataframe"
    ) -> Union[Dict[str, pd.DataFrame], Dict[str, str]]:
        """
        计算多个技术指标
        
        Args:
            symbol (str): 股票代码
            indicators (List[str]): 技术指标列表
            curr_date (str): 当前日期
            look_back_days (int): 回看天数
            return_format (str): 返回格式，'dataframe' 返回数据框字典，'string' 返回格式化字符串字典
            
        Returns:
            Union[Dict[str, pd.DataFrame], Dict[str, str]]: 根据return_format返回相应格式的结果字典
        """
        results = {}
        for indicator in indicators:
            try:
                result = self.calculate_technical_indicator(
                    symbol, indicator, curr_date, look_back_days
                )
                results[indicator] = result
            except Exception as e:
                logger.error(f"计算指标失败 {indicator}: {str(e)}")
                if return_format == "string":
                    results[indicator] = f"Error: {str(e)}"
                else:
                    results[indicator] = pd.DataFrame()
        
        return results
    
    def get_stock_summary(
        self,
        symbol: Annotated[str, "股票代码"],
        curr_date: Annotated[str, "当前日期 YYYY-MM-DD"],
        look_back_days: Annotated[int, "回看天数"] = 30
    ) -> Dict:
        """
        获取股票数据摘要
        
        Args:
            symbol (str): 股票代码
            curr_date (str): 当前日期
            look_back_days (int): 回看天数
            
        Returns:
            Dict: 股票数据摘要
        """
        try:
            # 获取价格数据
            data = self.get_stock_data_window(symbol, curr_date, look_back_days)
            
            if data.empty:
                return {
                    "error": f"No data available for {symbol}",
                    "error_type": "no_data",
                    "symbol": symbol.upper(),
                    "requested_period": f"{look_back_days} days",
                    "requested_date": curr_date,
                    "suggestions": [
                        "Try a different date range",
                        "Check if the symbol is correct",
                        "Verify if data exists for this time period"
                    ],
                    "available_symbols": self.get_available_stocks()
                }
            
            # 计算基本统计信息
            latest_data = data.iloc[-1]
            first_data = data.iloc[0]
            
            # 价格变化
            price_change = latest_data['Close'] - first_data['Close']
            price_change_pct = (price_change / first_data['Close']) * 100
            
            # 波动率
            daily_returns = data['Close'].pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100  # 年化波动率
            
            # 成交量统计
            avg_volume = data['Volume'].mean()
            latest_volume = latest_data['Volume']
            volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 0
            
            summary = {
                "symbol": symbol.upper(),
                "period": f"{look_back_days} days",
                "data_range": {
                    "start_date": data.index[0].strftime("%Y-%m-%d"),
                    "end_date": data.index[-1].strftime("%Y-%m-%d"),
                    "total_days": len(data)
                },
                "price_info": {
                    "current_price": round(latest_data['Close'], 2),
                    "open_price": round(first_data['Open'], 2),
                    "high_price": round(data['High'].max(), 2),
                    "low_price": round(data['Low'].min(), 2),
                    "price_change": round(price_change, 2),
                    "price_change_pct": round(price_change_pct, 2)
                },
                "volume_info": {
                    "latest_volume": int(latest_volume),
                    "avg_volume": int(avg_volume),
                    "volume_ratio": round(volume_ratio, 2),
                    "total_volume": int(data['Volume'].sum())
                },
                "volatility": {
                    "daily_volatility": round(daily_returns.std() * 100, 2),
                    "annualized_volatility": round(volatility, 2)
                },
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return summary
        except Exception as e:
            logger.error(f"获取股票摘要失败 {symbol}: {str(e)}")
            return {"error": str(e)}
    


    def get_supported_indicators(self) -> Dict[str, str]:
        """
        获取支持的技术指标列表
        
        Returns:
            Dict[str, str]: 指标代码到描述的映射
        """
        return self.supported_indicators
    
   
    def validate_date(self, date_string: str) -> bool:
        """
        验证日期格式
        
        Args:
            date_string (str): 日期字符串
            
        Returns:
            bool: 是否为有效日期格式
        """
        try:
            datetime.strptime(date_string, "%Y-%m-%d")
            return True
        except ValueError:
            return False


