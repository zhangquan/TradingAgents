from langchain_core.tools import tool
from typing import Annotated
import pandas as pd
import os
from tradingagents.default_config import DEFAULT_CONFIG, get_data_provider_for_environment
from tradingagents.dataflows.yfin_utils import get_yfinance_data


class ConfigurableDataToolkit:
    """
    A configurable data toolkit that can switch between different data providers
    based on configuration (Polygon, Yahoo Finance, etc.)
    """
    
    def __init__(self, config=None):
        """
        Initialize the configurable data toolkit
        
        Args:
            config: Configuration dictionary containing data provider settings
        """
        self.config = config or DEFAULT_CONFIG.copy()
        self.data_provider = self.config.get("data_provider", get_data_provider_for_environment())
        
        # Import providers based on configuration
        if self.data_provider == "polygon":
            from tradingagents.dataflows.polygon_interface import get_polygon_data_window, get_polygon_stock_stats_indicators_window
            self._get_data_window = get_polygon_data_window
            self._get_stock_stats = get_polygon_stock_stats_indicators_window
        elif self.data_provider == "yahoo":
            # Yahoo Finance functions will be created dynamically
            self._get_data_window = self._get_yahoo_data_window
            self._get_stock_stats = self._get_yahoo_stock_stats  # Placeholder
        else:
            # Default to polygon
            from tradingagents.dataflows.polygon_interface import get_polygon_data_window, get_polygon_stock_stats_indicators_window
            self._get_data_window = get_polygon_data_window
            self._get_stock_stats = get_polygon_stock_stats_indicators_window
    
    def _get_yahoo_data_window(self, symbol: str, curr_date: str, look_back_days: int) -> str:
        """Get Yahoo Finance data for the specified window"""
        try:
            # Use the existing Yahoo Finance utility
            csv_data = get_yfinance_data(symbol, look_back_days)
            return csv_data
        except Exception as e:
            return f"Error fetching Yahoo Finance data for {symbol}: {str(e)}"
    
    def _get_yahoo_stock_stats(self, symbol: str, indicator: str, curr_date: str, look_back_days: int) -> str:
        """Placeholder for Yahoo Finance technical indicators"""
        return f"Yahoo Finance technical indicators not yet implemented for {symbol} {indicator}"
    
    @tool
    def get_stock_data_window(
        self,
        symbol: Annotated[str, "ticker symbol of the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"],
    ) -> str:
        """
        Retrieve stock price data for a window of days from current date.
        Automatically uses the configured data provider (Polygon, Yahoo Finance, etc.)
        
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): Number of days to look back
        Returns:
            str: A formatted dataframe containing the stock price data for the specified window.
        """
        try:
            result_data = self._get_data_window(symbol, curr_date, look_back_days)
            return result_data
        except Exception as e:
            return f"Error retrieving data from {self.data_provider} for {symbol}: {str(e)}"

    @tool
    def get_stockstats_indicators_report_window(
        self,
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[str, "technical indicator to get the analysis and report of"],
        curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Automatically uses the configured data provider.
        
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """
        try:
            result_stockstats = self._get_stock_stats(symbol, indicator, curr_date, look_back_days)
            return result_stockstats
        except Exception as e:
            return f"Error retrieving technical indicators from {self.data_provider} for {symbol}: {str(e)}"
    
    def get_provider_info(self) -> dict:
        """Get information about the current data provider"""
        return {
            "provider": self.data_provider,
            "environment": self.config.get("environment", "dev")
        }


def create_data_toolkit(config=None, data_provider=None):
    """
    Factory function to create a data toolkit with specified configuration
    
    Args:
        config: Configuration dictionary
        data_provider: Override the data provider (polygon, yahoo, etc.)
    
    Returns:
        ConfigurableDataToolkit: Configured data toolkit instance
    """
    effective_config = config or DEFAULT_CONFIG.copy()
    
    if data_provider:
        effective_config = effective_config.copy()
        effective_config["data_provider"] = data_provider
    
    return ConfigurableDataToolkit(effective_config)